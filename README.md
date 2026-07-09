# Social Network Influence Detection

MSCS 532 course project. Data structures for identifying influential users in a directed social network, implemented in Python with the standard library only.

## Structures

Adjacency list (dict of sets) for the follow graph, with a mirrored reverse index so follower lookups are O(1). Hash table (dict) for user profiles. Max-heap (heapq) for top-k influencer ranking. BFS with an explicit deque for hop-limited reachability.

## Files

`social_graph.py` contains the SocialGraph class and all core operations.
`demo.py` runs a small hand-built example and a 5,000-user synthetic benchmark.
`test_social_graph.py` contains 18 unit tests covering normal and edge cases.

## Usage

```
python demo.py
python -m unittest test_social_graph -v
```

Requires Python 3.8+. No external dependencies.
