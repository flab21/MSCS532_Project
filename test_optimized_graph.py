"""
test_optimized_graph.py

Unit tests for OptimizedSocialGraph. Reuses the behavioral expectations
from the Phase 2 suite and adds cache-specific tests, since the whole
risk of memoization is serving stale answers after a mutation.

Run with:
    python3 -m unittest test_optimized_graph -v

Author: Frenie Labrador
"""

import random
import unittest

from social_graph import SocialGraph
from optimized_graph import OptimizedSocialGraph, SlimProfile


class TestBasicBehavior(unittest.TestCase):
    """The optimized graph must behave exactly like the baseline."""

    def setUp(self):
        self.g = OptimizedSocialGraph()
        self.g.add_user("alice", "Alice")
        self.g.add_user("bob", "Bob")
        self.g.add_user("carol", "Carol")

    def test_add_user_duplicate_raises(self):
        with self.assertRaises(ValueError):
            self.g.add_user("alice", "Alice Again")

    def test_profile_is_slim(self):
        self.assertIsInstance(self.g.get_profile("alice"), SlimProfile)
        self.assertFalse(hasattr(self.g.get_profile("alice"), "__dict__"))

    def test_follow_and_degree(self):
        self.g.add_follow("alice", "carol")
        self.g.add_follow("bob", "carol")
        self.assertEqual(self.g.degree_centrality("carol"), 2)
        self.assertEqual(self.g.degree_centrality("alice"), 0)

    def test_self_follow_raises(self):
        with self.assertRaises(ValueError):
            self.g.add_follow("bob", "bob")

    def test_unknown_user_raises(self):
        with self.assertRaises(KeyError):
            self.g.add_follow("alice", "ghost")

    def test_duplicate_follow_does_not_inflate_counter(self):
        self.g.add_follow("alice", "bob")
        self.g.add_follow("alice", "bob")
        self.assertEqual(self.g.degree_centrality("bob"), 1)
        self.assertEqual(self.g.edge_count(), 1)

    def test_remove_follow_updates_counter(self):
        self.g.add_follow("alice", "bob")
        self.g.remove_follow("alice", "bob")
        self.assertEqual(self.g.degree_centrality("bob"), 0)
        # Removing a follow that is already gone must be a no-op.
        self.g.remove_follow("alice", "bob")
        self.assertEqual(self.g.degree_centrality("bob"), 0)

    def test_remove_user_updates_counters(self):
        self.g.add_follow("alice", "carol")
        self.g.add_follow("bob", "carol")
        self.g.add_follow("carol", "alice")
        self.g.remove_user("carol")
        self.assertEqual(self.g.degree_centrality("alice"), 0)
        self.assertEqual(self.g.user_count(), 2)
        with self.assertRaises(KeyError):
            self.g.degree_centrality("carol")


class TestRankingCache(unittest.TestCase):
    """Cache correctness: hits must be fast, but never stale."""

    def setUp(self):
        self.g = OptimizedSocialGraph()
        for uid in ("a", "b", "c", "d"):
            self.g.add_user(uid, uid.upper())
        self.g.add_follow("a", "d")
        self.g.add_follow("b", "d")
        self.g.add_follow("c", "d")
        self.g.add_follow("a", "c")

    def test_repeated_calls_agree(self):
        first = self.g.top_influencers(k=2)
        second = self.g.top_influencers(k=2)
        self.assertEqual(first, second)
        self.assertEqual(first, [("d", 3), ("c", 1)])

    def test_cache_invalidated_by_new_follow(self):
        self.g.top_influencers(k=2)
        self.g.add_follow("d", "b")
        self.g.add_follow("c", "b")
        self.assertEqual(self.g.top_influencers(k=2),
                         [("d", 3), ("b", 2)])

    def test_cache_invalidated_by_unfollow(self):
        self.g.top_influencers(k=1)
        self.g.remove_follow("a", "d")
        self.g.remove_follow("b", "d")
        self.g.remove_follow("c", "d")
        self.assertEqual(self.g.top_influencers(k=1), [("c", 1)])

    def test_cache_invalidated_by_user_removal(self):
        self.g.top_influencers(k=1)
        self.g.remove_user("d")
        self.assertEqual(self.g.top_influencers(k=1), [("c", 1)])

    def test_returned_list_is_a_copy(self):
        result = self.g.top_influencers(k=2)
        result.append(("junk", 999))
        self.assertEqual(self.g.top_influencers(k=2),
                         [("d", 3), ("c", 1)])

    def test_k_zero_and_negative(self):
        self.assertEqual(self.g.top_influencers(k=0), [])
        self.assertEqual(self.g.top_influencers(k=-1), [])

    def test_k_larger_than_n(self):
        result = self.g.top_influencers(k=50)
        self.assertEqual(len(result), 4)


class TestEquivalenceWithBaseline(unittest.TestCase):
    """Random workloads must give identical answers on both versions."""

    def test_random_graph_matches_baseline(self):
        rng = random.Random(99)
        base = SocialGraph()
        opt = OptimizedSocialGraph()
        n = 200
        for i in range(n):
            base.add_user(f"u{i}", f"U{i}")
            opt.add_user(f"u{i}", f"U{i}")
        for _ in range(3000):
            a, b = f"u{rng.randrange(n)}", f"u{rng.randrange(n)}"
            if a == b:
                continue
            if rng.random() < 0.8:
                base.add_follow(a, b)
                opt.add_follow(a, b)
            else:
                base.remove_follow(a, b)
                opt.remove_follow(a, b)

        self.assertEqual(base.top_influencers(k=15),
                         opt.top_influencers(k=15))
        self.assertEqual(base.edge_count(), opt.edge_count())
        for i in range(n):
            self.assertEqual(base.degree_centrality(f"u{i}"),
                             opt.degree_centrality(f"u{i}"))
        self.assertEqual(base.reachable_within("u0", 2),
                         opt.reachable_within("u0", 2))


if __name__ == "__main__":
    unittest.main()
