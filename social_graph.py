"""
social_graph.py

Data structures for influence detection in a directed social network.
MSCS 532 Course Project, Phase 2 (Proof of Concept).

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
        """Register a new user. Raises ValueError if the user exists."""
        if user_id in self.profiles:
            raise ValueError(f"User {user_id!r} already exists.")
        self.profiles[user_id] = Profile(user_id, name, joined)
        self.following[user_id] = set()
        self.followers[user_id] = set()

    def remove_user(self, user_id):
        """Delete a user and clean up every edge that touches them."""
        self._require_user(user_id)
        # Remove this user from everyone they follow
        for target in self.following[user_id]:
            self.followers[target].discard(user_id)
        # Remove this user from everyone who follows them
        for source in self.followers[user_id]:
            self.following[source].discard(user_id)
        del self.following[user_id]
        del self.followers[user_id]
        del self.profiles[user_id]

    def get_profile(self, user_id):
        """Return the Profile for a user. O(1) hash table lookup."""
        self._require_user(user_id)
        return self.profiles[user_id]

    def user_count(self):
        return len(self.profiles)

    # ------------------------------------------------------------------
    # Edge (follow) management
    # ------------------------------------------------------------------

    def add_follow(self, follower_id, followee_id):
        """Record that follower_id follows followee_id.

        Both users must already exist. Self-follows are rejected.
        Duplicate follows are ignored silently because sets absorb them.
        """
        self._require_user(follower_id)
        self._require_user(followee_id)
        if follower_id == followee_id:
            raise ValueError("A user cannot follow themselves.")
        self.following[follower_id].add(followee_id)
        self.followers[followee_id].add(follower_id)

    def remove_follow(self, follower_id, followee_id):
        """Remove a follow edge if it exists."""
        self._require_user(follower_id)
        self._require_user(followee_id)
        self.following[follower_id].discard(followee_id)
        self.followers[followee_id].discard(follower_id)

    def is_following(self, follower_id, followee_id):
        """O(1) membership check on the adjacency set."""
        self._require_user(follower_id)
        self._require_user(followee_id)
        return followee_id in self.following[follower_id]

    def get_followers(self, user_id):
        """Return a copy of the follower set so callers can't mutate it."""
        self._require_user(user_id)
        return set(self.followers[user_id])

    def get_following(self, user_id):
        """Return a copy of the following set."""
        self._require_user(user_id)
        return set(self.following[user_id])

    def edge_count(self):
        return sum(len(s) for s in self.following.values())

    # ------------------------------------------------------------------
    # Influence analysis
    # ------------------------------------------------------------------

    def degree_centrality(self, user_id):
        """In-degree centrality: raw follower count. O(1) with the
        mirrored followers structure."""
        self._require_user(user_id)
        return len(self.followers[user_id])

    def top_influencers(self, k=10):
        """Return the k most-followed users as (user_id, followers) pairs.

        Builds a list of negated counts and heapifies it, then pops k
        times. heapify is O(n) and each pop is O(log n), so the whole
        thing is O(n + k log n), which beats a full O(n log n) sort
        when k is small relative to n.
        """
        if k <= 0:
            return []
        heap = [(-len(f), uid) for uid, f in self.followers.items()]
        heapq.heapify(heap)
        result = []
        for _ in range(min(k, len(heap))):
            neg_count, uid = heapq.heappop(heap)
            result.append((uid, -neg_count))
        return result

    def reachable_within(self, user_id, hops):
        """Breadth-first search out to a fixed number of hops.

        Returns the set of users whose content could reach user_id's
        network within that many hops (following direction). Iterative
        with a deque to avoid recursion limits on deep graphs.
        """
        self._require_user(user_id)
        if hops < 0:
            raise ValueError("hops must be non-negative.")
        visited = {user_id}
        frontier = deque([(user_id, 0)])
        while frontier:
            current, depth = frontier.popleft()
            if depth == hops:
                continue
            for neighbor in self.following[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    frontier.append((neighbor, depth + 1))
        visited.discard(user_id)
        return visited

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_user(self, user_id):
        if user_id not in self.profiles:
            raise KeyError(f"Unknown user: {user_id!r}")
