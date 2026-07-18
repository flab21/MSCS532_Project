"""
benchmark.py

Phase 3 benchmark harness. Builds the same synthetic network with the
Phase 2 baseline (SocialGraph) and the Phase 3 version
(OptimizedSocialGraph) at several sizes, then times the operations
that matter for the influence analysis workload.

Measurements per size, per implementation:
    - build time (users + edges)
    - one cold top-10 ranking
    - 100 repeated top-10 rankings (the read-heavy dashboard case)
    - 2-hop BFS from a mid-ranked user
    - peak memory of a full build, measured with tracemalloc

Results go to benchmark_results.csv and two charts are written as PNG
files for the report.

Note on the generator: the Phase 2 demo passed weights= to
random.choices, which recomputes the cumulative table on every call.
That is fine at 5,000 users but turns into an O(n^2) trap at 100,000.
Precomputing cum_weights once fixes it. Same distribution, same seed.

Run with:
    python3 benchmark.py

Author: Frenie Labrador
"""

import csv
import itertools
import random
import time
import tracemalloc

from social_graph import SocialGraph
from optimized_graph import OptimizedSocialGraph

SIZES = [5000, 25000, 50000, 100000]
AVG_FOLLOWS = 20
SEED = 42
REPEAT_RANKINGS = 100


def build_network(graph, n_users, seed=SEED):
    """Populate a graph with the same skewed network the demo used.

    Low-numbered users get most of the followers, which mimics the
    heavy-tailed follower distributions seen in real social networks.
    """
    rng = random.Random(seed)
    for i in range(n_users):
        graph.add_user(f"user{i}", f"User {i}")

    user_ids = [f"user{i}" for i in range(n_users)]
    weights = [1.0 / (i + 1) for i in range(n_users)]
    # Cumulative table built once instead of once per user. This is
    # what makes 100k feasible at all.
    cum_weights = list(itertools.accumulate(weights))
    for uid in user_ids:
        targets = rng.choices(user_ids, cum_weights=cum_weights,
                              k=AVG_FOLLOWS)
        for t in targets:
            if t != uid:
                graph.add_follow(uid, t)
    return graph


def time_once(fn):
    t0 = time.perf_counter()
    result = fn()
    return time.perf_counter() - t0, result


def measure(graph_cls, n_users):
    """Run the full measurement set for one implementation and size."""
    label = graph_cls.__name__
    print(f"  {label}, n={n_users}")

    build_secs, g = time_once(lambda: build_network(graph_cls(), n_users))

    # Median of three cold calls. A single sample can eat a garbage
    # collection pause and look wildly slow. The optimized version
    # caches, so its cache is cleared between attempts to keep every
    # attempt genuinely cold.
    cold_samples = []
    for _ in range(3):
        if hasattr(g, "_rank_cache"):
            g._rank_cache.clear()
        secs, top_cold = time_once(lambda: g.top_influencers(k=10))
        cold_samples.append(secs)
    cold_secs = sorted(cold_samples)[1]

    t0 = time.perf_counter()
    for _ in range(REPEAT_RANKINGS):
        top_warm = g.top_influencers(k=10)
    repeat_secs = time.perf_counter() - t0

    mid_user = f"user{n_users // 2}"
    bfs_secs, reached = time_once(lambda: g.reachable_within(mid_user, 2))

    # Memory: rebuild the whole thing under tracemalloc so the peak
    # reflects a real build, not leftovers from the timing runs.
    del g
    tracemalloc.start()
    g2 = build_network(graph_cls(), n_users)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    edge_count = g2.edge_count()
    del g2

    return {
        "implementation": label,
        "n_users": n_users,
        "edges": edge_count,
        "build_secs": round(build_secs, 4),
        "cold_rank_ms": round(cold_secs * 1000, 4),
        "repeat100_rank_ms": round(repeat_secs * 1000, 4),
        "bfs_2hop_ms": round(bfs_secs * 1000, 4),
        "bfs_reached": len(reached),
        "peak_mem_mb": round(peak / (1024 * 1024), 2),
        "top10_first": top_cold[0][0],
    }


def profile_memory_experiment(n=100000):
    """Measure profile objects in isolation, dict-based vs __slots__.

    The full-graph numbers turned out nearly identical because edge
    sets dominate total memory and the optimized version adds a counter
    dict. Measuring the profiles alone shows where __slots__ actually
    helps and by how much per object.
    """
    from social_graph import Profile
    from optimized_graph import SlimProfile

    results = {}
    for label, cls in (("Profile (dict)", Profile),
                       ("SlimProfile (__slots__)", SlimProfile)):
        tracemalloc.start()
        objs = [cls(f"user{i}", f"User {i}") for i in range(n)]
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        per_obj = peak / n
        results[label] = per_obj
        print(f"  {label}: {peak / (1024 * 1024):.2f} MB total, "
              f"{per_obj:.0f} bytes per object")
        del objs
    return results


def write_charts(rows, profile_mem):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = [r for r in rows if r["implementation"] == "SocialGraph"]
    opt = [r for r in rows if r["implementation"] == "OptimizedSocialGraph"]
    xs = [r["n_users"] for r in base]

    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.plot(xs, [r["repeat100_rank_ms"] for r in base], marker="o",
            label="Phase 2 baseline")
    ax.plot(xs, [r["repeat100_rank_ms"] for r in opt], marker="s",
            label="Phase 3 optimized")
    ax.set_xlabel("Users in network")
    ax.set_ylabel("Time for 100 top-10 rankings (ms)")
    ax.set_title("Repeated ranking cost, baseline vs optimized")
    ax.legend()
    ax.grid(True, linewidth=0.4)
    fig.tight_layout()
    fig.savefig("chart_ranking.png", dpi=150)

    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    labels = list(profile_mem.keys())
    values = list(profile_mem.values())
    bars = ax.bar(labels, values, width=0.5,
                  color=["#888888", "#4477aa"])
    ax.set_ylabel("Memory per profile object (bytes)")
    ax.set_title("Profile object memory, dict layout vs __slots__ "
                 "(100,000 objects)")
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 2,
                f"{v:.0f}", ha="center")
    ax.grid(True, axis="y", linewidth=0.4)
    fig.tight_layout()
    fig.savefig("chart_memory.png", dpi=150)
    print("Charts written: chart_ranking.png, chart_memory.png")


def main():
    rows = []
    for n in SIZES:
        print(f"Size {n}:")
        for cls in (SocialGraph, OptimizedSocialGraph):
            rows.append(measure(cls, n))

    with open("benchmark_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("Results written: benchmark_results.csv")

    for r in rows:
        print(r)

    print("Profile memory experiment (100,000 objects each):")
    profile_mem = profile_memory_experiment()

    try:
        write_charts(rows, profile_mem)
    except ImportError:
        print("matplotlib not available, skipping charts.")


if __name__ == "__main__":
    main()
