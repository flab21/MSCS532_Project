"""
social_graph.py

Data structures for influence detection in a directed social network.
MSCS 532 Project, Phase 1/2.

Structures used:
    - Adjacency list (dict of sets) for the follow graph
    - Hash table (dict) for user profiles
    - Max-heap (heapq with negated keys) for top-k ranking

Author: Frenie Labrador
"""

import heapq
from collections import deque


class Profile:
    """Simple container for user profile data."""

    def __init__(self, user_id, name, joined=None):
        self.user_id = user_id
        self.name = name
        self.joined = joined

    def __repr__(self):
        return f"Profile({self.user_id!r}, {self.name!r})"


class SocialGraph:
    """Directed follow graph with O(1) follower and following lookups.

    Two mirrored adjacency structures are kept so that both directions
    of a follow relationship can be queried in constant time. This
    doubles edge storage on purpose. Follower queries are the hot path
    for degree centrality, so the trade-off favors speed over memory.
    """

    def __init__(self):
        self.following = {}   # user_id -> set of user_ids this user follows
        self.followers = {}   # user_id -> set of user_ids following this user
        self.profiles = {}    # user_id -> Profile

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    def add_user(self, user_id, name, joined=None):
        """Register a new user. Raises if the user already exists."""
        if user_id in self.profiles:
            raise ValueError(f"user {user_id!r} already exists")
        self.profiles[user_id] = Profile(user_id, name, joined)
        self.following[user_id] = set()
        self.followers[user_id] = set()

    def remove_user(self, user_id):
        """Delete a user and every edge that touches them."""
        self._require_user(user_id)
        # Detach this user from everyone who follows them
        for src in self.followers[user_id]:
            self.following[src].discard(user_id)
        # Detach this user from everyone they follow
        for dst in self.following[user_id]:
            self.followers[dst].discard(user_id)
        del self.following[user_id]
        del self.followers[user_id]
        del self.profiles[user_id]

    def has_user(self, user_id):
        return user_id in self.profiles

    def get_profile(self, user_id):
        self._require_user(user_id)
        return self.profiles[user_id]

    def user_count(self):
        return len(self.profiles)

    # ------------------------------------------------------------------
    # Edge management
    # ------------------------------------------------------------------

    def add_follow(self, src, dst):
        """Record that src follows dst. Duplicate follows are ignored
        because the underlying sets absorb them."""
        self._require_user(src)
        self._require_user(dst)
        if src == dst:
            raise ValueError("users cannot follow themselves")
        self.following[src].add(dst)
        self.followers[dst].add(src)

    def remove_follow(self, src, dst):
        """Remove a follow edge. Raises if the edge does not exist."""
        self._require_user(src)
        self._require_user(dst)
        if dst not in self.following[src]:
            raise ValueError(f"{src!r} does not follow {dst!r}")
        self.following[src].remove(dst)
        self.followers[dst].remove(src)

    def is_following(self, src, dst):
        self._require_user(src)
        self._require_user(dst)
        return dst in self.following[src]

    def get_followers(self, user_id):
        self._require_user(user_id)
        return set(self.followers[user_id])   # defensive copy

    def get_following(self, user_id):
        self._require_user(user_id)
        return set(self.following[user_id])

    def edge_count(self):
        return sum(len(s) for s in self.following.values())

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def degree_centrality(self, user_id):
        """In-degree centrality: the raw follower count."""
        self._require_user(user_id)
        return len(self.followers[user_id])

    def top_influencers(self, k):
        """Return the k user ids with the highest follower counts.

        Builds a max-heap (negated counts, since heapq is a min-heap)
        in O(V), then pops k times at O(log V) each. Ties are broken
        by user id so results are deterministic.
        """
        if k < 0:
            raise ValueError("k must be non-negative")
        k = min(k, len(self.profiles))
        heap = [(-len(f), uid) for uid, f in self.followers.items()]
        heapq.heapify(heap)
        return [heapq.heappop(heap)[1] for _ in range(k)]

    def reachable_within(self, user_id, max_hops):
        """All users reachable from user_id in at most max_hops follow
        steps, found with an iterative BFS. The start user is excluded.

        Returns a dict mapping user_id -> hop distance.
        """
        self._require_user(user_id)
        if max_hops < 0:
            raise ValueError("max_hops must be non-negative")
        distances = {user_id: 0}
        queue = deque([user_id])
        while queue:
            current = queue.popleft()
            if distances[current] == max_hops:
                continue
            for neighbor in self.following[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        del distances[user_id]
        return distances

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_user(self, user_id):
        if user_id not in self.profiles:
            raise KeyError(f"unknown user {user_id!r}")
