import unittest
import pandas as pd
import numpy as np
from src.m1_aggregate import aggregate, snapshots, graph_metrics, window_metrics
from scripts.run_m1 import summarise, sensitivity


def events(rows):
    return pd.DataFrame(rows, columns=['u','v','t'])


class AggregationTests(unittest.TestCase):
    def test_undirected_triangle_and_isolates(self):
        e = events([(1,2,0),(2,3,0),(3,1,0),(1,2,1)])
        g = aggregate(e, [1,2,3,4,5])
        m = graph_metrics(g)
        self.assertEqual(m['n_edges'], 3)
        self.assertAlmostEqual(m['density'], .3)
        self.assertAlmostEqual(m['mean_degree'], 1.2)
        self.assertAlmostEqual(m['clustering'], .6)
        self.assertEqual(m['n_components'], 3)
        self.assertAlmostEqual(m['largest_component_fraction'], .6)

    def test_directed_cycle(self):
        e = events([(1,2,0),(2,3,0),(3,1,0)])
        m = graph_metrics(aggregate(e, [1,2,3,4,5], directed=True))
        self.assertAlmostEqual(m['density'], .15)
        self.assertAlmostEqual(m['mean_degree'], 1.2)
        self.assertAlmostEqual(m['mean_in_degree'], .6)
        self.assertAlmostEqual(m['mean_out_degree'], .6)
        self.assertAlmostEqual(m['clustering'], .3)
        self.assertEqual(m['n_components'], 3)

    def test_weak_components_do_not_require_directed_return_path(self):
        e = events([(1,2,0),(2,3,0),(4,5,0)])
        m = graph_metrics(aggregate(e, range(1,6), directed=True))
        self.assertEqual(m['n_components'], 2)
        self.assertEqual(m['largest_component_size'], 3)

    def test_reciprocal_edges_and_repetitions(self):
        e = events([(1,2,0),(2,1,0),(1,2,1)])
        self.assertEqual(aggregate(e, range(1,6), True).number_of_edges(), 2)
        self.assertEqual(aggregate(e, range(1,6), False).number_of_edges(), 1)

    def test_window_boundary_empty_and_partial(self):
        e = events([(1,2,0),(2,3,10),(4,5,35)])
        w = list(snapshots(e, 10, 0, 36))
        self.assertEqual([x.events.t.tolist() for x in w], [[0],[10],[],[35]])
        self.assertEqual([x.complete for x in w], [True,True,True,False])
        self.assertEqual(w[-1].stop, 36)

    def test_stop_is_exclusive(self):
        e = events([(1,2,0),(2,3,10),(4,5,20)])
        w = list(snapshots(e, 10, 0, 20))
        self.assertEqual(sum(len(x.events) for x in w), 2)

    def test_empty_fixed_graph(self):
        m = graph_metrics(aggregate(events([]), range(1,6)))
        self.assertEqual(m['n_components'], 5)
        self.assertEqual(m['clustering'], 0)
        self.assertEqual(m['density'], 0)
        self.assertAlmostEqual(m['largest_component_fraction'], .2)

    def test_active_basis(self):
        e = events([(1,2,0),(2,3,0),(3,1,0)])
        m = graph_metrics(aggregate(e, range(1,6)), 'active')
        self.assertEqual(m['n_nodes'], 3)
        self.assertAlmostEqual(m['density'], 1)
        self.assertAlmostEqual(m['clustering'], 1)
        empty = graph_metrics(aggregate(events([]), range(1,6)), 'active')
        self.assertTrue(np.isnan(empty['density']))

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            aggregate(events([(1,6,0)]), range(1,6))
        with self.assertRaises(ValueError):
            aggregate(events([(1,1,0)]), range(1,6))
        with self.assertRaises(ValueError):
            list(snapshots(events([(1,2,10),(2,3,0)]), 10, 0, 20))

    def test_summary_excludes_partial_but_includes_empty(self):
        frame = window_metrics(events([(1,2,0),(2,3,25)]), range(1,6), 10, 0, 26)
        frame['dataset'], frame['period'] = 'toy', 'full'
        summary = summarise(frame)
        row = summary.loc[(summary.metric=='density') & (summary.window_policy=='complete_only')].iloc[0]
        self.assertEqual(row.n_windows, 2)
        self.assertEqual(row.n_empty, 1)
        self.assertAlmostEqual(row['mean'], .05)

    def test_no_complete_window_is_undefined(self):
        frame = window_metrics(events([(1,2,0)]), range(1,6), 100, 0, 20)
        frame['dataset'], frame['period'] = 'toy', 'full'
        summary = summarise(frame)
        complete = summary.loc[summary.window_policy=='complete_only']
        self.assertTrue((complete.n_windows==0).all())
        self.assertTrue(complete['mean'].isna().all())
        self.assertTrue(sensitivity(summary).sensitivity.isna().all())


if __name__ == '__main__':
    unittest.main()
