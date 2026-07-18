"""
optimized_graph.py

Phase 3 optimized version of the SocialGraph proof of concept.
MSCS 532 Course Project, Phase 3 (Optimization and Scaling).

Two optimizations over the Phase 2 baseline:

    1. Incremental in-degree tracking plus a memoized ranking cache.
       Phase 2 rebuilt a heap of all n users on every top_influencers
       call. This version keeps a running follower count per user and
       caches ranking results until the graph actually changes.

    2. Slimmer profile objects using __slots__. Regular Python objects
       carry a per-instance __dict__ that costs real memory once you
       have a hundred thousand of them.

The public interface matches SocialGraph so the two versions can be
benchmarked side by side with the same driver code.

Author: Frenie Labrador
"""

import heapq

from social_graph import SocialGraph


class SlimProfile:
    """Profile container with __slots__ to cut per-instance memory.

    With __slots__ Python skips the per-instance attribute dictionary
    and stores the three fields in a fixed layout instead.
    """

    __slots__ = ("user_id", "name", "joined")

    def __init__(self, user_id, name, joined=None):
        self.user_id = user_id
        self.name = name
        self.joined = joined

    def __repr__(self):
        return f"SlimProfile({self.user_id!r}, {self.name!r})"


class OptimizedSocialGraph(SocialGraph):
    """SocialGraph with incremental degree counts and a ranking cache.

    The in-degree of every user is kept in a plain dict that gets
    updated on every follow, unfollow, and user removal. On top of
    that sits a small memoization layer: top_influencers results are
    cached per k and thrown away whenever any mutation happens. In a
    read-heavy workload (rankings recomputed far more often than the
    graph changes) most calls become a cached list copy.
    """

    def __init__(self):
        super().__init__()
        self._in_degree = {}     # user_id -> current follower count
        self._rank_cache = {}    # k -> cached top_influencers result

    # ------------------------------------------------------------------
    # Mutations: every one of these must keep _in_degree correct and
    # invalidate the cache, otherwise the ranking silently goes stale.
    # ------------------------------------------------------------------

    def add_user(self, user_id, name, joined=None):
        if user_id in self.profiles:
            raise ValueError(f"User {user_id!r} already exists.")
        self.profiles[user_id] = SlimProfile(user_id, name, joined)
        self.following[user_id] = set()
        self.followers[user_id] = set()
        self._in_degree[user_id] = 0
        self._rank_cache.clear()

    def remove_user(self, user_id):
        self._require_user(user_id)
        # Everyone this user followed loses one follower.
        for target in self.following[user_id]:
            self.followers[target].discard(user_id)
            self._in_degree[target] -= 1
        for source in self.followers[user_id]:
            self.following[source].discard(user_id)
        del self.following[user_id]
        del self.followers[user_id]
        del self.profiles[user_id]
        del self._in_degree[user_id]
        self._rank_cache.clear()

    def add_follow(self, follower_id, followee_id):
        self._require_user(follower_id)
        self._require_user(followee_id)
        if follower_id == followee_id:
            raise ValueError("A user cannot follow themselves.")
        # Only count the edge if it is actually new. Duplicate follows
        # were absorbed silently in Phase 2 and still are here, but the
        # counter must not drift when that happens.
        if followee_id not in self.following[follower_id]:
            self.following[follower_id].add(followee_id)
            self.followers[followee_id].add(follower_id)
            self._in_degree[followee_id] += 1
            self._rank_cache.clear()

    def remove_follow(self, follower_id, followee_id):
        self._require_user(follower_id)
        self._require_user(followee_id)
        if followee_id in self.following[follower_id]:
            self.following[follower_id].discard(followee_id)
            self.followers[followee_id].discard(follower_id)
            self._in_degree[followee_id] -= 1
            self._rank_cache.clear()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def degree_centrality(self, user_id):
        """O(1) lookup against the maintained counter."""
        self._require_user(user_id)
        return self._in_degree[user_id]

    def top_influencers(self, k=10):
        """Top k users by follower count, memoized until the next change.

        On a cache miss this runs heapq.nlargest over the counter dict,
        which is O(n log k). On a hit it just copies the cached list.
        Ties are broken by user id so results are deterministic and
        match the baseline ordering.
        """
        if k <= 0:
            return []
        if k in self._rank_cache:
            return list(self._rank_cache[k])
        largest = heapq.nlargest(
            min(k, len(self._in_degree)),
            self._in_degree.items(),
            key=lambda item: (item[1], _reverse_key(item[0])),
        )
        result = [(uid, count) for uid, count in largest]
        self._rank_cache[k] = result
        return list(result)


class _reverse_key:
    """Wraps a value so comparisons come out reversed.

    heapq.nlargest picks the largest keys, but the Phase 2 heap popped
    the smallest user id first among ties. Reversing the id comparison
    inside the key keeps the tie-break order identical between the two
    implementations, which matters for the equivalence tests.
    """

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        return other.value < self.value
