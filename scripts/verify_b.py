#!/usr/bin/env python3
"""Audit formal artifact completeness and preserve explicit checks in JSON."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'results/b'
e=pd.read_csv(R/'data/processed/CIT/events.csv');n=pd.read_csv(R/'data/processed/CIT/nodes.csv').sort_values('id');counts=e.groupby(['u','t']).size();checks={}
checks['strict_past_edges']=bool((n.year.to_numpy()[e.v]<e.t.to_numpy()).all())
checks['no_duplicate_edges']=not bool(e.duplicated(['u','v']).any())
checks['all_five_experiments_present']=all((O/p).exists() for p in ['aggregation.csv','pa.json','age_fits.json','densification.json','diameter_real.csv','wsb_predictions.csv'])
checks['nulls']=[]
for kind in ['P3a','P3b']:
 for i in range(20):
  p=O/'null_events'/f'{kind}_{i:02d}.csv.gz';d=pd.read_csv(p)
  c={'kind':kind,'rep':i,'events':len(d),'same_sources_years_outdegrees':bool(d.groupby(['u','t']).size().equals(counts)),'strict_past':bool((n.year.to_numpy()[d.v]<d.t.to_numpy()).all()),'unique':not bool(d.duplicated(['u','v']).any()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  checks['nulls'].append(c)
  assert all(c[k] for k in ['same_sources_years_outdegrees','strict_past','unique'])
pdct=pd.read_csv(O/'wsb_predictions.csv')
ws=json.loads((O/'wsb_summary.json').read_text())
ages=e.t.to_numpy()-n.year.to_numpy()[e.v]
c5=np.bincount(e.v.to_numpy()[ages<=5],minlength=len(n))
c15=np.bincount(e.v.to_numpy()[ages<=15],minlength=len(n))
eligible=np.flatnonzero((n.year.to_numpy()>=1990)&(n.year.to_numpy()<=2005)&(c5>=5))
expected_ids=set(np.random.default_rng(5253).choice(eligible,min(500,len(eligible)),replace=False).tolist())
checks['forecast_selection_uses_only_training_citations']=set(pdct.id)==expected_ids
checks['forecast_sample_size']=len(expected_ids)
checks['same_papers_at_both_horizons']=all(set(d.id)==expected_ids for _,d in pdct.groupby('evaluation'))
checks['wsb_training_counts_match_raw_edges']=bool(np.array_equal(pdct.c5.to_numpy(),c5[pdct.id]))
checks['wsb_horizon_15_eligible']=bool(((pdct.horizon>=15)&(pdct.c5>=5)).all())
checks['wsb_test_n_by_evaluation']=pdct.groupby('evaluation').size().to_dict()
for _,row in pdct.iterrows():
 actual=int(np.sum((e.v.to_numpy()==int(row.id))&(ages<=int(row.horizon))))
 assert actual==int(row.observed)
 assert int(row.horizon)==(15 if row.evaluation=='age15' else 2020-int(row.birth_year))
full=pd.read_csv(O/'wsb_full_parameters.csv')
checks['full_fit_cohort_and_c15_eligibility']=bool(((n.year.to_numpy()[full.id]>=1990)&(n.year.to_numpy()[full.id]<=2005)&(c15[full.id]>=10)).all())
checks['full_fit_count_matches_summary']=len(full)==ws['n_full_selected']
assert checks['forecast_selection_uses_only_training_citations'] and checks['same_papers_at_both_horizons'] and checks['wsb_training_counts_match_raw_edges'] and checks['full_fit_cohort_and_c15_eligibility'] and checks['full_fit_count_matches_summary']
checks['figures']=[]
for stem in ['b_activity','b_aggregation','b_attachment_ageing','b_densification_diameter','b_null_and_age_models','b_window_sensitivity','b_wsb','b_wsb_validation']:
 for ext in ['pdf','png']:
  p=R/'figures'/f'{stem}.{ext}';assert p.exists() and p.stat().st_size>1000;checks['figures'].append(str(p.relative_to(R)))
sumdf=pd.read_csv(R/'results/b_summary.csv');assert list(sumdf.columns)==['dataset','metric','value','null_mean','null_std'];checks['summary_rows']=len(sumdf)
assert checks['strict_past_edges'] and checks['no_duplicate_edges'] and checks['all_five_experiments_present'] and checks['wsb_horizon_15_eligible']
(O/'validation.json').write_text(json.dumps(checks,indent=2));print('Formal artifact audit passed:',len(e),'events;',len(n),'nodes;',len(checks['nulls']),'nulls;',len(checks['figures']),'figures')
