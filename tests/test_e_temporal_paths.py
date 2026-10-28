import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from temporal_paths_placeholder import earliest_arrival, temporal_closeness  # noqa: E402


def frame(rows):
    return pd.DataFrame(rows, columns=["u", "v", "t"])


def arrival(events, nodes, source, target, t_start=0, directed=True):
    a = earliest_arrival(frame(events), nodes, t_start, directed)
    return a[nodes.index(target), nodes.index(source)]


def fixed_point_arrival(events, n, t_start, directed):
    """Reference: relax every event, in reverse time order, until nothing changes."""
    arr = np.full((n, n), np.inf)
    np.fill_diagonal(arr, t_start)
    rows = [(u, v, t) for u, v, t in events if t > t_start]
    if not directed:
        rows += [(v, u, t) for u, v, t in rows]
    changed = True
    while changed:
        changed = False
        for u, v, t in sorted(rows, key=lambda r: -r[2]):
            for s in range(n):
                if arr[u, s] < t < arr[v, s]:
                    arr[v, s] = t
                    changed = True
    return arr


class TemporalPathTests(unittest.TestCase):
    def test_time_respecting_chain_is_reachable_only_in_order(self):
        nodes = ["a", "b", "c"]
        self.assertEqual(arrival([("a", "b", 1), ("b", "c", 2)], nodes, "a", "c"), 2)
        self.assertTrue(np.isinf(arrival([("b", "c", 1), ("a", "b", 2)], nodes, "a", "c")))

    def test_no_two_hops_within_one_timestamp(self):
        nodes = ["a", "b", "c"]
        self.assertTrue(np.isinf(arrival([("a", "b", 5), ("b", "c", 5)], nodes, "a", "c")))
        self.assertEqual(arrival([("a", "b", 5), ("b", "c", 6)], nodes, "a", "c"), 6)

    def test_direction_matters_only_for_directed_data(self):
        nodes = ["a", "b"]
        self.assertTrue(np.isinf(arrival([("b", "a", 1)], nodes, "a", "b", directed=True)))
        self.assertEqual(arrival([("b", "a", 1)], nodes, "a", "b", directed=False), 1)

    def test_events_before_or_at_start_are_ignored(self):
        nodes = ["a", "b"]
        self.assertTrue(np.isinf(arrival([("a", "b", 1)], nodes, "a", "b", t_start=2)))
        self.assertTrue(np.isinf(arrival([("a", "b", 2)], nodes, "a", "b", t_start=2)))

    def test_same_cases_as_d_self_test(self):
        # The toy cases in D's self_test(), so both implementations agree on them.
        nodes = [1, 2, 3]
        self.assertTrue(np.isinf(arrival([(2, 3, 9), (1, 2, 10)], nodes, 1, 3, directed=False)))
        self.assertEqual(arrival([(1, 2, 10), (2, 3, 20)], nodes, 1, 3, directed=False), 20)
        self.assertTrue(np.isinf(arrival([(1, 2, 10), (2, 3, 20)], nodes, 3, 1, directed=True)))
        self.assertTrue(np.isinf(arrival([(1, 2, 10), (2, 3, 10)], nodes, 1, 3, directed=False)))

    def test_matches_fixed_point_reference_on_random_events(self):
        rng = np.random.default_rng(42)
        n = 8
        rows = [(int(u), int(v), int(t)) for u, v, t in zip(rng.integers(0, n, 60), rng.integers(0, n, 60),
                                                            rng.integers(0, 30, 60)) if u != v]
        for directed in (True, False):
            with self.subTest(directed=directed):
                got = earliest_arrival(frame(rows), list(range(n)), 5, directed)
                np.testing.assert_array_equal(got, fixed_point_arrival(rows, n, 5, directed))

    def test_temporal_closeness_on_star(self):
        # Hub 0 meets 1, 2, 3 at t = 1, 2, 3 (undirected). From t_start = 0:
        # latencies from 0 are 1, 2, 3, so C(0) = (1 + 1/2 + 1/3) / 3.
        c = temporal_closeness(frame([(0, 1, 1), (0, 2, 2), (0, 3, 3)]), [0, 1, 2, 3], [0], directed=False)
        self.assertAlmostEqual(c[0], (1 + 1 / 2 + 1 / 3) / 3)
        # Node 1 reaches 0 at 1 and then 2, 3 via the later contacts at 2, 3.
        self.assertAlmostEqual(c[1], (1 + 1 / 2 + 1 / 3) / 3)
        # Node 3 only meets the hub at the end; nothing after that.
        self.assertAlmostEqual(c[3], (1 / 3) / 3)


if __name__ == "__main__":
    unittest.main()
