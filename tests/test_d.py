import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from paths import earliest_arrival, reachability, static_reachability  # noqa: E402
from spreading import outbreak_summary, simulate_sir  # noqa: E402


def ev(rows):
    return pd.DataFrame(rows, columns=["u", "v", "t"])


class PathTests(unittest.TestCase):
    def test_time_order_blocks_path(self):
        events = ev([(2, 3, 9), (1, 2, 10)])
        a = earliest_arrival(events, [1, 2, 3], 0, False)
        self.assertEqual(a[1, 0], 10)        # 1 -> 2 at 10
        self.assertTrue(np.isinf(a[2, 0]))   # 2-3 happened before 1 reached 2
        self.assertEqual(a[2, 1], 9)         # but 2 -> 3 works

    def test_chain_and_simultaneous(self):
        chain = ev([(1, 2, 10), (2, 3, 20)])
        a = earliest_arrival(chain, [1, 2, 3], 0, False)
        self.assertEqual(a[2, 0], 20)
        simult = ev([(1, 2, 10), (2, 3, 10)])
        a = earliest_arrival(simult, [1, 2, 3], 0, False)
        self.assertTrue(np.isinf(a[2, 0]))
        a = earliest_arrival(simult.iloc[::-1], [1, 2, 3], 0, False)
        self.assertTrue(np.isinf(a[2, 0]))

    def test_directed(self):
        chain = ev([(1, 2, 10), (2, 3, 20)])
        a = earliest_arrival(chain, [1, 2, 3], 0, True)
        self.assertTrue(np.isinf(a[0, 2]))   # 3 cannot reach 1
        self.assertEqual(a[2, 0], 20)

    def test_start_time_excludes_earlier_events(self):
        chain = ev([(1, 2, 10), (2, 3, 20)])
        frac, _ = reachability(chain, [1, 2, 3], 10, False)
        # events at t <= 10 are ignored: only 2-3 at 20 usable -> pairs 2->3 and 3->2
        self.assertAlmostEqual(frac, 2 / 6)

    def test_reachability_and_latency(self):
        chain = ev([(1, 2, 10), (2, 3, 20)])
        frac, lat = reachability(chain, [1, 2, 3], 0, False)
        # reachable: 1->2 (10), 1->3 (20), 2->1 (10), 2->3 (20), 3->2 (20); 3->1: 3-2 at 20, 2-1 only at 10: no
        self.assertAlmostEqual(frac, 5 / 6)
        self.assertAlmostEqual(lat, (10 + 20 + 10 + 20 + 20) / 5)

    def test_static_reachability(self):
        chain = ev([(2, 3, 9), (1, 2, 10)])
        self.assertAlmostEqual(static_reachability(chain, [1, 2, 3], False), 1.0)
        self.assertAlmostEqual(static_reachability(chain, [1, 2, 3], True), 3 / 6)


class SirTests(unittest.TestCase):
    def run_sir(self, rows, source, beta, duration, directed=False, t_start=0):
        e = ev(rows).sort_values("t", kind="stable")
        nodes = sorted(set(e["u"]) | set(e["v"]))
        idx = {n: i for i, n in enumerate(nodes)}
        return simulate_sir(e["u"].map(idx).to_numpy(), e["v"].map(idx).to_numpy(), e["t"].to_numpy(),
                            len(nodes), idx[source], t_start, beta, duration, directed,
                            np.random.default_rng(0))

    def test_chain_with_beta_one(self):
        inf = self.run_sir([(1, 2, 10), (2, 3, 20)], 1, 1.0, 100)
        self.assertEqual(list(inf), [0, 10, 20])

    def test_no_chain_within_one_timestamp(self):
        inf = self.run_sir([(1, 2, 10), (2, 3, 10)], 1, 1.0, 100)
        self.assertTrue(np.isinf(inf[2]))

    def test_recovery_stops_transmission(self):
        inf = self.run_sir([(1, 2, 10), (2, 3, 200)], 1, 1.0, 100)
        self.assertEqual(inf[1], 10)
        self.assertTrue(np.isinf(inf[2]))   # node 2 recovered at 110

    def test_beta_zero(self):
        inf = self.run_sir([(1, 2, 10)], 1, 0.0, 100)
        self.assertEqual(np.isfinite(inf).sum(), 1)

    def test_directed_only_sender_infects(self):
        inf = self.run_sir([(1, 2, 10)], 2, 1.0, 100, directed=True)
        self.assertEqual(np.isfinite(inf).sum(), 1)
        inf = self.run_sir([(1, 2, 10)], 1, 1.0, 100, directed=True)
        self.assertEqual(np.isfinite(inf).sum(), 2)

    def test_events_before_start_ignored(self):
        inf = self.run_sir([(1, 2, 5), (2, 3, 20)], 1, 1.0, 100, t_start=10)
        self.assertEqual(np.isfinite(inf).sum(), 1)

    def test_outbreak_summary(self):
        inf = np.array([0.0, 10.0, 20.0, np.inf])
        size, peak, half = outbreak_summary(inf, 0.0, 100.0)
        self.assertAlmostEqual(size, 0.75)
        self.assertEqual(peak, 20.0)    # all three infectious from t=20
        self.assertEqual(half, 10.0)


if __name__ == "__main__":
    unittest.main()
