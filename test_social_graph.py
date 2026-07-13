"""
test_social_graph.py

Unit tests for the SocialGraph proof of concept.
MSCS 532 Course Project, Phase 2.

Run with:
    python3 -m unittest test_social_graph -v

Author: Frenie Labrador
"""

import unittest

from social_graph import SocialGraph


def small_graph():
    """Five users with a known follow pattern.

    alice follows bob, carol
    bob follows carol
    dave follows carol, alice
    erin follows nobody, nobody follows erin

    Follower counts: carol=3, alice=1, bob=1, dave=0, erin=0
    """
    g = SocialGraph()
    for uid, name in [("alice", "Alice"), ("bob", "Bob"),
                      ("carol", "Carol"), ("dave", "Dave"),
                      ("erin", "Erin")]:
        g.add_user(uid, name)
    g.add_follow("alice", "bob")
    g.add_follow("alice", "carol")
    g.add_follow("bob", "carol")
    g.add_follow("dave", "carol")
    g.add_follow("dave", "alice")
    return g


class TestUserManagement(unittest.TestCase):

    def test_add_user_and_lookup(self):
        g = SocialGraph()
        g.add_user("u1", "Test User")
        self.assertEqual(g.get_profile("u1").name, "Test User")

    def test_add_duplicate_user_raises(self):
        g = SocialGraph()
        g.add_user("u1", "Test User")
        with self.assertRaises(ValueError):
            g.add_user("u1", "Someone Else")

    def test_lookup_unknown_user_raises(self):
        g = SocialGraph()
        with self.assertRaises(KeyError):
            g.get_profile("ghost")

    def test_user_count(self):
        g = small_graph()
        self.assertEqual(g.user_count(), 5)

    def test_remove_user_cleans_edges(self):
        g = small_graph()
        g.remove_user("carol")
        self.assertEqual(g.user_count(), 4)
        # No surviving adjacency set may reference carol
        self.assertNotIn("carol", g.get_following("alice"))
        self.assertNotIn("carol", g.get_following("bob"))
        self.assertNotIn("carol", g.get_following("dave"))

    def test_remove_unknown_user_raises(self):
        g = SocialGraph()
        with self.assertRaises(KeyError):
            g.remove_user("ghost")


class TestFollowEdges(unittest.TestCase):

    def test_add_follow_both_directions(self):
        g = small_graph()
        self.assertIn("bob", g.get_following("alice"))
        self.assertIn("alice", g.get_followers("bob"))

    def test_self_follow_rejected(self):
        g = small_graph()
        with self.assertRaises(ValueError):
            g.add_follow("alice", "alice")

    def test_duplicate_follow_is_idempotent(self):
        g = small_graph()
        before = g.edge_count()
        g.add_follow("alice", "bob")  # already exists
        self.assertEqual(g.edge_count(), before)

    def test_follow_unknown_user_raises(self):
        g = small_graph()
        with self.assertRaises(KeyError):
            g.add_follow("alice", "ghost")

    def test_remove_follow(self):
        g = small_graph()
        g.remove_follow("alice", "bob")
        self.assertFalse(g.is_following("alice", "bob"))
        self.assertNotIn("alice", g.get_followers("bob"))

    def test_getters_return_copies(self):
        g = small_graph()
        stolen = g.get_following("alice")
        stolen.add("erin")  # mutating the copy must not touch the graph
        self.assertFalse(g.is_following("alice", "erin"))

    def test_edge_count(self):
        g = small_graph()
        self.assertEqual(g.edge_count(), 5)


class TestInfluenceAnalysis(unittest.TestCase):

    def test_degree_centrality(self):
        g = small_graph()
        self.assertEqual(g.degree_centrality("carol"), 3)
        self.assertEqual(g.degree_centrality("erin"), 0)

    def test_top_influencers_order(self):
        g = small_graph()
        top = g.top_influencers(k=2)
        self.assertEqual(top[0], ("carol", 3))
        self.assertEqual(top[1][1], 1)  # alice or bob, both have 1

    def test_top_influencers_k_larger_than_n(self):
        g = small_graph()
        top = g.top_influencers(k=100)
        self.assertEqual(len(top), 5)

    def test_top_influencers_k_zero_or_negative(self):
        g = small_graph()
        self.assertEqual(g.top_influencers(k=0), [])
        self.assertEqual(g.top_influencers(k=-3), [])

    def test_bfs_reachability(self):
        g = small_graph()
        # 1 hop from dave: carol and alice
        self.assertEqual(g.reachable_within("dave", 1),
                         {"carol", "alice"})
        # 2 hops from dave adds bob and carol via alice
        self.assertEqual(g.reachable_within("dave", 2),
                         {"carol", "alice", "bob"})
        # 0 hops reaches nobody
        self.assertEqual(g.reachable_within("dave", 0), set())


if __name__ == "__main__":
    unittest.main()
