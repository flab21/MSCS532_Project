# MSCS532 Course Project: Social Network Influence Analysis

Proof of concept implementation for detecting influential users in a
directed social network. Built for MSCS 532 (Algorithms and Data
Structures), University of the Cumberlands.

## Data Structures

- **Adjacency list** (dict of sets): the directed follow graph, mirrored
  in both directions so follower and following lookups are both O(1)
- **Hash table** (dict): user ID to profile object mapping
- **Max-heap** (heapq with negated keys): top-k influencer ranking in
  O(n + k log n)

## Files

| File | Purpose |
|------|---------|
| `social_graph.py` | Core `SocialGraph` class and `Profile` container |
| `test_social_graph.py` | 18 unit tests (user management, edges, analysis) |
| `demo.py` | Two-part demonstration: hand-built network + 5,000-user synthetic network with timing |

## Running

No dependencies beyond the Python standard library (3.8+).

```bash
# Run the test suite
python3 -m unittest test_social_graph -v

# Run the demonstration
python3 demo.py
```

## Phase 2 Baseline Numbers

On the test machine, the synthetic network (5,000 users, 87,288 edges,
seed fixed at 42):

- Build time: ~0.7 s
- Top-10 ranking: < 7 ms
- 2-hop BFS from a mid-ranked user: < 1 ms (213 users reached)

These serve as the baseline for Phase 3 optimization comparisons.

## Author

Frenie Labrador
