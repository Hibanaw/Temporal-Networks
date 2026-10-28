#!/usr/bin/env python3
"""Concise measured-result audit after the pipeline; no scientific claims invented."""
from pathlib import Path
import json,pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'results/b'
print('DATA CARD');print((R/'data/processed/CIT/data_card.json').read_text())
for fn in ['pa.json','age_fits.json','age_cohorts.json','densification.json','wsb_summary.json','null_comparison.json','robustness.json']:
 print('\n'+fn);print((O/fn).read_text())
print('\nAGGREGATION ENDPOINTS');df=pd.read_csv(O/'aggregation.csv');print(df[df.year.isin([1990,2005,2020])].to_string(index=False))
print('\nDIAMETER ENDPOINTS');d=pd.read_csv(O/'diameter_real.csv');print(d[d.year.isin([1990,2005,2020])].to_string(index=False))
print('\nNULL METRICS');n=pd.read_csv(O/'null_metrics.csv');print(n.groupby('kind')[['alpha','mean_age']].agg(['mean','std','min','max']).to_string())
print('\nWINDOW SENSITIVITY');print(pd.read_csv(O/'window_sensitivity.csv').to_string(index=False))
