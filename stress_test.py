"""
stress_test.py

Phase 3 stress and edge case testing for OptimizedSocialGraph.

Four scenarios that go past what the unit tests cover:

    1. Celebrity node: one user followed by everyone else. Checks that
       ranking, degree lookups, and deleting the celebrity all survive
       an extremely skewed degree distribution.
    2. Deep chain: a 50,000 user follow chain traversed end to end.
       The BFS is iterative, so this should not hit Python's recursion
       limit the way a recursive version would.
    3. Churn: thousands of interleaved follows and unfollows with the
       ranking recomputed along the way, checked against the Phase 2
       baseline to prove the cache never serves stale results.
    4. Hostile input: empty graphs, k larger than n, k of zero,
       unknown users, duplicate and self follows.

Run with:
    python3 stress_test.py

Author: Frenie Labrador
"""

import random
import time

from social_graph import SocialGraph
from optimized_graph import OptimizedSocialGraph


def banner(title):
    print("=" * 60)
    print(title)
    print("=" * 60)


def celebrity_test(n=100000):
    banner(f"1. Celebrity node ({n} users, all following user0)")
    g = OptimizedSocialGraph()
    t0 = time.perf_counter()
    for i in range(n):
        g.add_user(f"user{i}", f"User {i}")
    for i in range(1, n):
        g.add_follow(f"user{i}", "user0")
    print(f"Build: {time.perf_counter() - t0:.2f} s")

    t0 = time.perf_counter()
    top = g.top_influencers(k=5)
    print(f"Top-5 ranking: {(time.perf_counter() - t0) * 1000:.2f} ms")
    assert top[0] == ("user0", n - 1), "Celebrity should rank first"
    print(f"Celebrity degree: {g.degree_centrality('user0')}")

    t0 = time.perf_counter()
    g.remove_user("user0")
    print(f"Deleting the celebrity: {time.perf_counter() - t0:.2f} s")
    assert g.user_count() == n - 1
    top_after = g.top_influencers(k=1)
    assert top_after[0][1] == 0, "Nobody should have followers now"
    print("Ranking after deletion is consistent. PASS")
    print()


def deep_chain_test(length=50000):
    banner(f"2. Deep chain ({length} users, single file)")
    g = OptimizedSocialGraph()
    for i in range(length):
        g.add_user(f"user{i}", f"User {i}")
    for i in range(length - 1):
        g.add_follow(f"user{i}", f"user{i + 1}")

    t0 = time.perf_counter()
    reached = g.reachable_within("user0", length)
    secs = time.perf_counter() - t0
    assert len(reached) == length - 1, "Should reach every other user"
    print(f"Full-depth BFS reached {len(reached)} users in {secs:.2f} s "
          f"without touching the recursion limit. PASS")
    print()


def churn_test(n=2000, operations=20000, seed=7):
    banner(f"3. Churn ({operations} random follow/unfollow ops)")
    rng = random.Random(seed)
    base = SocialGraph()
    opt = OptimizedSocialGraph()
    for i in range(n):
        base.add_user(f"user{i}", f"User {i}")
        opt.add_user(f"user{i}", f"User {i}")

    checks = 0
    for step in range(operations):
        a = f"user{rng.randrange(n)}"
        b = f"user{rng.randrange(n)}"
        if a == b:
            continue
        if rng.random() < 0.7:
            base.add_follow(a, b)
            opt.add_follow(a, b)
        else:
            base.remove_follow(a, b)
            opt.remove_follow(a, b)
        # Every so often, make sure the cached ranking still agrees
        # with the baseline computed from scratch.
        if step % 500 == 0:
            assert base.top_influencers(k=10) == opt.top_influencers(k=10)
            checks += 1

    assert base.edge_count() == opt.edge_count()
    for i in range(n):
        uid = f"user{i}"
        assert base.degree_centrality(uid) == opt.degree_centrality(uid)
    print(f"{checks} mid-churn ranking checks and {n} final degree "
          f"comparisons all matched the baseline. PASS")
    print()


def hostile_input_test():
    banner("4. Hostile input")
    g = OptimizedSocialGraph()

    assert g.top_influencers(k=10) == [], "Empty graph should give []"
    assert g.top_influencers(k=0) == []
    assert g.top_influencers(k=-3) == []

    g.add_user("a", "A")
    g.add_user("b", "B")
    g.add_follow("a", "b")
    assert g.top_influencers(k=99) == [("b", 1), ("a", 0)], \
        "k larger than n should just return everyone"

    try:
        g.add_follow("a", "a")
        raise AssertionError("Self-follow should have raised")
    except ValueError:
        pass

    try:
        g.degree_centrality("ghost")
        raise AssertionError("Unknown user should have raised")
    except KeyError:
        pass

    before = g.edge_count()
    g.add_follow("a", "b")
    assert g.edge_count() == before, "Duplicate follow must not add edges"
    assert g.degree_centrality("b") == 1, \
        "Duplicate follow must not inflate the counter"

    g.remove_follow("a", "b")
    g.remove_follow("a", "b")
    assert g.degree_centrality("b") == 0, \
        "Double unfollow must not push the counter negative"

    print("Empty graph, oversized k, self-follows, unknown users, and "
          "duplicate operations all handled. PASS")
    print()


if __name__ == "__main__":
    celebrity_test()
    deep_chain_test()
    churn_test()
    hostile_input_test()
    print("All stress tests passed.")
