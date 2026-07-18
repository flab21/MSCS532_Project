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

## Phase 3 (Optimization and Scaling)

Phase 3 adds an optimized implementation and the tooling to compare it
against the Phase 2 baseline at up to 100,000 users.

| File | Purpose |
|------|---------|
| `optimized_graph.py` | `OptimizedSocialGraph` with incremental in-degree counts, a memoized ranking cache, and `__slots__` profiles |
| `test_optimized_graph.py` | 16 unit tests, including cache invalidation and baseline equivalence checks |
| `benchmark.py` | Builds both implementations at 5k, 25k, 50k, and 100k users; writes `benchmark_results.csv` plus two charts |
| `stress_test.py` | Celebrity node, 50k-deep chain BFS, 20k-operation churn with baseline cross-checks, hostile input |

```bash
python3 -m unittest test_optimized_graph -v
python3 benchmark.py      # takes a couple of minutes at 100k
python3 stress_test.py
```

Headline result on the test machine: 100 repeated top-10 rankings on
the 100,000-user network dropped from about 1,850 ms (baseline) to
under 0.1 ms (optimized) because the memoized cache turns repeat
queries into a list copy. Timing numbers will vary by hardware.

## Phase 2 Baseline Numbers

On the test machine, the synthetic network (5,000 users, 87,288 edges,
seed fixed at 42):

- Build time: ~0.7 s
- Top-10 ranking: < 7 ms
- 2-hop BFS from a mid-ranked user: < 1 ms (213 users reached)

These serve as the baseline for Phase 3 optimization comparisons.

## Author

Frenie Labrador
