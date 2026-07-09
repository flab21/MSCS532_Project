"""
test_social_graph.py

Unit tests for the SocialGraph module, covering normal operations and
the edge cases mentioned in the Deliverable 1 report (self-follows,
unknown users, duplicate follows, empty graphs).

Run: python -m unittest test_social_graph -v
"""

import unittest

from social_graph import SocialGraph


class TestUsers(unittest.TestCase):

    def setUp(self):
        self.g = SocialGraph()
        self.g.add_user("a", "Alice")
        self.g.add_user("b", "Bob")

    def test_add_and_lookup(self):
        self.assertTrue(self.g.has_user("a"))
        self.assertEqual(self.g.get_profile("a").name, "Alice")
        self.assertEqual(self.g.user_count(), 2)

    def test_duplicate_user_rejected(self):
        with self.assertRaises(ValueError):
            self.g.add_user("a", "Alice Again")

    def test_unknown_user_rejected(self):
        with self.assertRaises(KeyError):
            self.g.get_profile("ghost")

    def test_remove_user_cleans_edges(self):
        self.g.add_follow("a", "b")
        self.g.remove_user("b")
        self.assertFalse(self.g.has_user("b"))
        self.assertEqual(self.g.get_following("a"), set())
        self.assertEqual(self.g.edge_count(), 0)


class TestFollows(unittest.TestCase):

    def setUp(self):
        self.g = SocialGraph()
        for uid in ("a", "b", "c"):
            self.g.add_user(uid, uid.upper())

    def test_follow_recorded_both_directions(self):
        self.g.add_follow("a", "b")
        self.assertTrue(self.g.is_following("a", "b"))
        self.assertIn("a", self.g.get_followers("b"))
        self.assertIn("b", self.g.get_following("a"))

    def test_self_follow_rejected(self):
        with self.assertRaises(ValueError):
            self.g.add_follow("a", "a")

    def test_duplicate_follow_is_idempotent(self):
        self.g.add_follow("a", "b")
        self.g.add_follow("a", "b")
        self.assertEqual(self.g.edge_count(), 1)
        self.assertEqual(self.g.degree_centrality("b"), 1)

    def test_follow_unknown_user_rejected(self):
        with self.assertRaises(KeyError):
            self.g.add_follow("a", "ghost")

    def test_remove_missing_edge_rejected(self):
        with self.assertRaises(ValueError):
            self.g.remove_follow("a", "b")

    def test_defensive_copies(self):
        self.g.add_follow("a", "b")
        stolen = self.g.get_followers("b")
        stolen.add("c")
        self.assertEqual(self.g.degree_centrality("b"), 1)


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.g = SocialGraph()
        for uid in ("a", "b", "c", "d"):
            self.g.add_user(uid, uid.upper())
        # a is followed by b, c, d; b is followed by c
        self.g.add_follow("b", "a")
        self.g.add_follow("c", "a")
        self.g.add_follow("d", "a")
        self.g.add_follow("c", "b")

    def test_degree_centrality(self):
        self.assertEqual(self.g.degree_centrality("a"), 3)
        self.assertEqual(self.g.degree_centrality("b"), 1)
        self.assertEqual(self.g.degree_centrality("d"), 0)

    def test_top_influencers_order(self):
        self.assertEqual(self.g.top_influencers(2), ["a", "b"])

    def test_top_influencers_k_larger_than_graph(self):
        result = self.g.top_influencers(100)
        self.assertEqual(len(result), 4)

    def test_top_influencers_negative_k_rejected(self):
        with self.assertRaises(ValueError):
            self.g.top_influencers(-1)

    def test_bfs_distances(self):
        # c -> a and c -> b are 1 hop; nothing else reachable from c
        reach = self.g.reachable_within("c", 2)
        self.assertEqual(reach, {"a": 1, "b": 1})

    def test_bfs_zero_hops(self):
        self.assertEqual(self.g.reachable_within("c", 0), {})

    def test_bfs_excludes_start_even_in_cycle(self):
        self.g.add_follow("a", "c")   # creates cycle c -> a -> c
        reach = self.g.reachable_within("c", 5)
        self.assertNotIn("c", reach)


class TestEmptyGraph(unittest.TestCase):

    def test_empty_counts(self):
        g = SocialGraph()
        self.assertEqual(g.user_count(), 0)
        self.assertEqual(g.edge_count(), 0)
        self.assertEqual(g.top_influencers(5), [])


if __name__ == "__main__":
    unittest.main()
