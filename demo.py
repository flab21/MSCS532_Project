"""
demo.py

Demonstration script for the SocialGraph proof of concept.
MSCS 532 Course Project, Phase 2.

Two parts:
    1. A small hand-built network with verifiable results.
    2. A synthetic 5,000-user network with basic timing numbers
       that serve as the Phase 3 optimization baseline.

Run with:
    python3 demo.py

Author: Frenie Labrador
"""

import random
import time

from social_graph import SocialGraph


def small_demo():
    print("=" * 60)
    print("Part 1: Small hand-built network")
    print("=" * 60)

    g = SocialGraph()
    people = [("alice", "Alice"), ("bob", "Bob"), ("carol", "Carol"),
              ("dave", "Dave"), ("erin", "Erin")]
    for uid, name in people:
        g.add_user(uid, name)

    follows = [("alice", "bob"), ("alice", "carol"), ("bob", "carol"),
               ("dave", "carol"), ("dave", "alice")]
    for a, b in follows:
        g.add_follow(a, b)

    print(f"Users: {g.user_count()}, Follow edges: {g.edge_count()}")
    print()

    print("Follower counts (degree centrality):")
    for uid, _ in people:
        print(f"  {uid:>6}: {g.degree_centrality(uid)}")
    print()

    print("Top 3 influencers:")
    for uid, count in g.top_influencers(k=3):
        print(f"  {uid:>6}: {count} followers")
    print()

    print("Reachability from dave:")
    print(f"  1 hop : {sorted(g.reachable_within('dave', 1))}")
    print(f"  2 hops: {sorted(g.reachable_within('dave', 2))}")
    print()

    print("Edge case checks:")
    try:
        g.add_follow("alice", "alice")
    except ValueError as e:
        print(f"  Self-follow rejected: {e}")
    try:
        g.get_profile("ghost")
    except KeyError as e:
        print(f"  Unknown user rejected: {e}")
    before = g.edge_count()
    g.add_follow("alice", "bob")
    print(f"  Duplicate follow ignored: edge count still {g.edge_count()}"
          f" (was {before})")
    print()


def synthetic_demo(n_users=5000, avg_follows=20, seed=42):
    print("=" * 60)
    print(f"Part 2: Synthetic network ({n_users} users)")
    print("=" * 60)

    rng = random.Random(seed)
    g = SocialGraph()

    t0 = time.perf_counter()
    for i in range(n_users):
        g.add_user(f"user{i}", f"User {i}")

    # Skewed follow pattern: low-numbered users are more popular,
    # which mimics the follower distribution of real networks.
    user_ids = [f"user{i}" for i in range(n_users)]
    weights = [1.0 / (i + 1) for i in range(n_users)]
    for uid in user_ids:
        targets = rng.choices(user_ids, weights=weights, k=avg_follows)
        for t in targets:
            if t != uid:
                g.add_follow(uid, t)
    build_time = time.perf_counter() - t0

    print(f"Build time: {build_time:.2f} s "
          f"({g.user_count()} users, {g.edge_count()} edges)")

    t0 = time.perf_counter()
    top = g.top_influencers(k=10)
    rank_time = (time.perf_counter() - t0) * 1000
    print(f"Top-10 ranking time: {rank_time:.2f} ms")
    print("Top 10 influencers:")
    for uid, count in top:
        print(f"  {uid:>8}: {count} followers")

    t0 = time.perf_counter()
    reach = g.reachable_within("user2500", 2)
    bfs_time = (time.perf_counter() - t0) * 1000
    print(f"2-hop BFS from user2500: {len(reach)} users reached "
          f"in {bfs_time:.2f} ms")
    print()


if __name__ == "__main__":
    small_demo()
    synthetic_demo()
