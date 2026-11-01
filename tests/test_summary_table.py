"""Regression checks for contrast semantics; no new experiment is run."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from make_summary_table import build_cross_table


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.rows = pd.DataFrame([
            ('H1_window_sensitivity_density', 3.36, np.nan),
            ('m2_burstiness', .53, .51),
            ('m2_adjacent_jaccard', .22, .37),
            ('m4_adj_nmi_mean_w15min_g1', .82, .91),
            ('m3a_R_vsP1', .86, 1.), ('m3a_R_vsP2', .86, .98),
            ('m3c_b0.05_D4h_peak_time_s_vsP1', 120., 100.),
            ('m3c_b0.05_D4h_peak_time_s_vsP2', 120., 150.),
        ], columns=['metric','value','null_mean']).assign(dataset='PS', null_std=.01, source='synthetic')
        self.rows = pd.concat([self.rows, pd.DataFrame([dict(dataset='CIT', metric='pa_alpha__P3a', value=.7, null_mean=.2, null_std=.01, source='synthetic')])], ignore_index=True)
        self.table = build_cross_table(self.rows)

    def test_all_finite_effects_are_raw_differences(self):
        g = self.table[self.table.effect.notna()]
        np.testing.assert_allclose(g.effect, g.value - g.null_mean)
        for h, expected in [('H3', -.15), ('H5', -.09), ('H6', -.14)]:
            r = self.table[(self.table.hypothesis == h) & (self.table.dataset == 'PS') & (self.table.reference == 'P1')].iloc[0]
            self.assertAlmostEqual(r.effect, expected)

    def test_h1_has_no_invented_null_effect(self):
        r = self.table[(self.table.hypothesis == 'H1') & (self.table.dataset == 'PS')].iloc[0]
        self.assertEqual(r.status, 'measured'); self.assertEqual(r.value, 3.36)
        self.assertTrue(np.isnan(r.effect)); self.assertEqual(r.estimate_type, 'descriptive_no_null')

    def test_h7_keeps_both_references_and_separates_ratio_from_difference(self):
        g = self.table[(self.table.hypothesis == 'H7') & (self.table.dataset == 'PS')].set_index('reference')
        self.assertEqual(set(g.index), {'P1','P2'})
        self.assertEqual(g.loc['P1','effect'], 20.); self.assertAlmostEqual(g.loc['P1','ratio'], 1.2)
        self.assertEqual(g.loc['P2','effect'], -30.); self.assertAlmostEqual(g.loc['P2','ratio'], .8)
        self.assertTrue((g.value_unit == 'seconds').all())

    def test_undefined_peak_does_not_become_zero(self):
        self.rows.loc[self.rows.metric.str.endswith('peak_time_s_vsP1'), 'value'] = np.nan
        g = build_cross_table(self.rows)
        r = g[(g.hypothesis == 'H7') & (g.dataset == 'PS') & (g.reference == 'P1')].iloc[0]
        self.assertEqual(r.status, 'undefined'); self.assertTrue(np.isnan(r.effect)); self.assertTrue(np.isnan(r.ratio))

if __name__ == '__main__': unittest.main()
