"""
demo.py

Small demonstration of the SocialGraph module on a hand-built network,
followed by a synthetic network to show it holds up at a larger size.

Run: python demo.py
"""

import random
import time

from social_graph import SocialGraph


def small_demo():
    print("=== Small hand-built network ===")
    g = SocialGraph()

    users = [
        ("alice", "Alice Adams"),
        ("bob", "Bob Brown"),
        ("carol", "Carol Chen"),
        ("dave", "Dave Diaz"),
        ("erin", "Erin Evans"),
    ]
    for uid, name in users:
        g.add_user(uid, name)

    follows = [
        ("bob", "alice"), ("carol", "alice"), ("dave", "alice"),
        ("erin", "alice"), ("alice", "carol"), ("dave", "carol"),
        ("erin", "dave"), ("carol", "bob"),
    ]
    for src, dst in follows:
        g.add_follow(src, dst)

    print(f"Users: {g.user_count()}, follow edges: {g.edge_count()}")

    for uid, _ in users:
        print(f"  {uid}: {g.degree_centrality(uid)} followers")

    print(f"Top 3 influencers: {g.top_influencers(3)}")
    print(f"Reachable from erin within 2 hops: {g.reachable_within('erin', 2)}")
    print()


def synthetic_demo(num_users=5000, avg_follows=20, seed=42):
    print(f"=== Synthetic network: {num_users} users, ~{avg_follows} follows each ===")
    rng = random.Random(seed)
    g = SocialGraph()

    start = time.perf_counter()
    for i in range(num_users):
        g.add_user(f"user{i}", f"User {i}")

    ids = list(g.profiles.keys())
    for src in ids:
        for dst in rng.sample(ids, avg_follows):
            if src != dst:
                g.add_follow(src, dst)
    build_time = time.perf_counter() - start

    start = time.perf_counter()
    top = g.top_influencers(10)
    rank_time = time.perf_counter() - start

    start = time.perf_counter()
    reach = g.reachable_within(ids[0], 2)
    bfs_time = time.perf_counter() - start

    print(f"Built graph ({g.edge_count()} edges) in {build_time:.3f}s")
    print(f"Top 10 influencers in {rank_time * 1000:.2f}ms: {top}")
    print(f"BFS 2-hop reach of {ids[0]}: {len(reach)} users in {bfs_time * 1000:.2f}ms")


if __name__ == "__main__":
    small_demo()
    synthetic_demo()
