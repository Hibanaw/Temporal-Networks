import itertools
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from community import (adjacent_nmi, leiden, multislice_partitions, n_communities, nmi,  # noqa: E402
                       nmi_to_reference, self_consistency, snapshot_partitions,
                       snapshot_windows, static_partition, to_igraph)
from nullmodels import timestamp_shuffle  # noqa: E402


def clique_events(nodes, times):
    """One event per pair of `nodes` at every time in `times`."""
    return [(a, b, t) for t in times for a, b in itertools.combinations(nodes, 2)]


def frame(rows):
    return pd.DataFrame(rows, columns=["u", "v", "t"])


def weights(g):
    return {tuple(sorted((g.vs[e.source]["id"], g.vs[e.target]["id"]))): e["weight"] for e in g.es}


class CommunityTests(unittest.TestCase):
    def test_to_igraph_counts_events_and_ignores_direction_and_self_loops(self):
        g = to_igraph(frame([(1, 2, 0), (2, 1, 5), (1, 3, 5), (4, 4, 5)]))
        self.assertEqual(sorted(g.vs["id"]), [1, 2, 3])
        self.assertEqual(weights(g), {(1, 2): 2.0, (1, 3): 1.0})

    def test_leiden_separates_two_cliques_with_weak_bridge(self):
        rows = clique_events(range(5), [0, 1]) + clique_events(range(5, 10), [0, 1]) + [(0, 5, 0)]
        p = static_partition(frame(rows))
        self.assertEqual(n_communities(p), 2)
        self.assertAlmostEqual(nmi(p, {n: n // 5 for n in range(10)}), 1.0)

    def test_nmi_uses_common_nodes_and_ignores_labels(self):
        p = {1: 0, 2: 0, 3: 1, 4: 1, 9: 5}
        self.assertAlmostEqual(nmi(p, {1: 7, 2: 7, 3: 8, 4: 8}), 1.0)
        self.assertTrue(np.isnan(nmi(p, {1: 0})))

    def test_snapshot_windows_drop_empty_and_sparse_windows(self):
        ev = frame([(1, 2, 0), (1, 3, 10), (2, 3, 250), (1, 2, 420), (1, 3, 430)])
        self.assertEqual([s for s, _ in snapshot_windows(ev, 100)], [0, 200, 400])
        self.assertEqual([s for s, _ in snapshot_windows(ev, 100, min_events=2)], [0, 400])
        self.assertEqual([len(w) for _, w in snapshot_windows(ev, 100)], [2, 1, 2])

    def test_adjacent_nmi_skips_pairs_across_a_gap(self):
        p = {1: 0, 2: 0, 3: 1, 4: 1}
        out = adjacent_nmi([p, p, p], starts=[0, 100, 300], width=100)
        self.assertTrue(np.isnan(out[0]) and np.isnan(out[2]))
        self.assertAlmostEqual(out[1], 1.0)

    def test_snapshots_see_reorganisation_that_static_partition_hides(self):
        # Phase 1: groups {0..3}, {4..7}. Phase 2: groups {0,1,4,5}, {2,3,6,7}.
        phase1 = clique_events([0, 1, 2, 3], range(0, 100, 20)) + clique_events([4, 5, 6, 7], range(0, 100, 20))
        phase2 = (clique_events([0, 1, 4, 5], range(100, 200, 20))
                  + clique_events([2, 3, 6, 7], range(100, 200, 20)))
        ev = frame(phase1 + phase2)
        windows = snapshot_windows(ev, 100)
        snaps = snapshot_partitions(windows)
        self.assertAlmostEqual(nmi(snaps[0], {n: n // 4 for n in range(8)}), 1.0)
        self.assertAlmostEqual(nmi(snaps[1], {n: (n // 2) % 2 for n in range(8)}), 1.0)
        self.assertAlmostEqual(adjacent_nmi(snaps, [s for s, _ in windows], 100)[1], 0.0, places=12)
        # One static partition cannot match both phases.
        self.assertLess(min(nmi_to_reference(snaps, static_partition(ev))), 1.0)

    def test_multislice_labels_are_consistent_for_stable_communities(self):
        rows = clique_events(range(4), range(0, 300, 20)) + clique_events(range(4, 8), range(0, 300, 20))
        ms = multislice_partitions(snapshot_windows(frame(rows), 100))
        self.assertEqual(len(ms), 3)
        self.assertTrue(ms[0] == ms[1] == ms[2])
        self.assertEqual(n_communities(ms[0]), 2)

    def test_self_consistency_is_one_on_clear_structure(self):
        rows = clique_events(range(5), range(0, 200, 20)) + clique_events(range(5, 10), range(0, 200, 20))
        np.testing.assert_allclose(self_consistency(snapshot_windows(frame(rows), 100)), [1.0, 1.0])

    def test_leiden_is_reproducible_with_fixed_seed(self):
        rng = np.random.default_rng(0)
        rows = [(int(a), int(b), t) for t, (a, b) in enumerate(rng.integers(0, 30, size=(400, 2))) if a != b]
        g = to_igraph(frame(rows))
        self.assertEqual(leiden(g, seed=3), leiden(g, seed=3))

    def test_p1_keeps_static_graph_and_timestamp_multiset(self):
        rng = np.random.default_rng(1)
        rows = [(int(a), int(b), int(t)) for a, b, t in zip(rng.integers(0, 10, 200), rng.integers(10, 20, 200),
                                                            rng.integers(0, 1000, 200))]
        ev = frame(rows)
        null = timestamp_shuffle(ev, seed=0)
        self.assertEqual(weights(to_igraph(null)), weights(to_igraph(ev)))
        self.assertEqual(sorted(null["t"]), sorted(ev["t"]))
        key = ["u", "v", "t"]
        self.assertFalse(np.array_equal(null.sort_values(key).to_numpy(), ev.sort_values(key).to_numpy()))


if __name__ == "__main__":
    unittest.main()
