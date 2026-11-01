import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from aggregate import windows, graph_metrics
from stats import activity, persistence
from nullmodels import edge_shuffle, timestamp_shuffle
from collections import Counter


def ev(rows):
    return pd.DataFrame(rows, columns=['u','v','t'])


class ACTests(unittest.TestCase):
    def test_p2_event_invariants_directed_and_undirected(self):
        e=ev([(1,2,1),(1,3,2),(2,4,3),(3,4,4),(4,1,5),(2,3,6)])
        for directed in [False, True]:
            nul=edge_shuffle(e,seed=123,directed=directed,n_swaps=100)
            self.assertEqual(e.t.tolist(),nul.t.tolist())
            self.assertFalse((nul.u==nul.v).any())
            if directed:
                self.assertEqual(Counter(e.u),Counter(nul.u));self.assertEqual(Counter(e.v),Counter(nul.v))
            else:
                self.assertEqual(Counter(list(e.u)+list(e.v)),Counter(list(nul.u)+list(nul.v)))
                keys=[(min(a,b),max(a,b),t) for a,b,t in nul.itertuples(index=False,name=None)]
                self.assertEqual(len(keys),len(set(keys)))

    def test_empty_windows_and_fixed_denominator(self):
        e=ev([(1,2,0),(2,3,20)])
        snaps=list(windows(e,10))
        self.assertEqual([len(g) for _,g in snaps],[1,0,1])
        self.assertAlmostEqual(graph_metrics(snaps[0][1],[1,2,3])['density'],1/3)
        self.assertEqual(graph_metrics(snaps[1][1],[1,2,3])['components'],3)

    def test_p1_coincident_events_keep_message_counts(self):
        e=ev([(1,2,1),(1,2,2),(2,3,1),(2,3,2)])
        found=False
        for seed in range(20):
            nul=timestamp_shuffle(e,seed)
            found=found or nul.duplicated().any()
            result,_=persistence(nul,1,True)
            self.assertEqual(result['repeated_event_fraction'],.5)
        self.assertTrue(found)

    def test_directed_metrics(self):
        m=graph_metrics(ev([(1,2,0),(2,3,1),(1,3,2)]),[1,2,3],True)
        self.assertEqual(m['clustering'],1)
        self.assertEqual(m['density'],.5)

    def test_known_burstiness(self):
        result,gaps=activity(ev([(1,2,0),(1,2,1),(1,2,4)]),True)
        np.testing.assert_equal(gaps,[1,3])
        self.assertAlmostEqual(result['burstiness'],-1/3)

    def test_no_cross_tie_memory(self):
        result,gaps=activity(ev([(1,2,0),(1,2,2),(2,3,100),(2,3,104)]))
        self.assertEqual(len(gaps),2)
        self.assertTrue(np.isnan(result['memory']))

    def test_contact_episode_and_persistence(self):
        e=ev([(1,2,0),(1,2,20),(1,2,40),(1,2,100)])
        _,gaps=activity(e,contact_step=20)
        np.testing.assert_equal(gaps,[100])
        result,j=persistence(e,50)
        self.assertEqual(result['repeated_tie_fraction'],1)
        self.assertAlmostEqual(result['repeated_event_fraction'],.75)
        self.assertEqual(j,[0,0])

if __name__=='__main__': unittest.main()
