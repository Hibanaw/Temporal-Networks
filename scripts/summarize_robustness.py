"""Consolidate half-period and nested null-count checks without mixing ensembles."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/robustness'


def main():
    OUT.mkdir(exist_ok=True);rows=[]
    def add(owner,ds,period,n,metric,value,mean=np.nan,sd=np.nan):
        rows.append(dict(owner=owner,dataset=ds,period=period,nulls=n,metric=metric,value=value,null_mean=mean,null_std=sd))
    a=pd.read_csv(ROOT/'results/ac/a_robustness.csv'); c=pd.read_csv(ROOT/'results/ac/c_robustness.csv')
    for _,r in a.iterrows():add('A',r.dataset,r.period,0,r.metric,r.value)
    for _,r in c.iterrows():add('C',r.dataset,r.period,r.nulls,r.metric,r.value,r.null_mean,r.null_std)
    for period,path,n in [('full',ROOT/'results/d_summary.csv',20),('full',ROOT/'results/d/summary_60.csv',60),
                          ('first',ROOT/'results/d/first/d_summary.csv',20),('second',ROOT/'results/d/second/d_summary.csv',20)]:
        if path.exists():
            for _,r in pd.read_csv(path).iterrows():add('D',r.dataset,period,n,r.metric,r.value,r.null_mean,r.null_std)
    for path in (OUT/'e').glob('summary_*.csv'):
        for _,r in pd.read_csv(path).iterrows():
            if r.metric in ['m4_adj_nmi_mean','m4_static_nmi_mean','m3b_tau_unweighted','m3b_tau_weighted']:
                add('E',r.dataset,r.period,r.nulls,r.metric,r.value,r.null_mean,r.null_std)
    path=OUT/'b/per_network.csv'
    if path.exists():
        b=pd.read_csv(path)
        for (period,mode),g in b[b['mode']!='Real'].groupby(['period','mode']):
            real=b[(b.period==period)&(b['mode']=='Real')].iloc[0]
            for n in ([20,60] if period=='full' else [20]):
                for metric in ['alpha','mean_age','diameter90']:
                    vals=g[g.iteration<n][metric]
                    add('B','CIT',period,n,metric+'__'+mode,real[metric],vals.mean(),vals.std())
    # Retain existing B observation-split growth-law results as separate measured checks.
    br=json.loads((ROOT/'results/b/robustness.json').read_text())
    for r in br:
        period={'years_1990_2004':'first','years_2005_2020':'second'}.get(r['variant'])
        if period:add('B','CIT',period,0,'densification_a',r['densification']['a'])
    windows=pd.read_csv(ROOT/'results/b/windows.csv')
    for period,lo,hi in [('first',1990,2004),('second',2005,2020)]:
        g=windows[(windows.year>=lo)&(windows.year<=hi)]
        for key in ['density_directed','mean_total_degree','clustering_weak','lcc_fraction']:
            # B's original H1 convention: relative range across widths at each end year, then average.
            byyear=g.groupby('year')[key].agg(['min','max','mean'])
            add('B','CIT',period,0,'H1_window_sensitivity_'+key,((byyear['max']-byyear['min'])/byyear['mean'].replace(0,np.nan)).mean())
    predictions=pd.read_csv(ROOT/'results/b/wsb_predictions.csv')
    for period,lo,hi in [('first_cohort',1990,1997),('second_cohort',1998,2005)]:
        g=predictions[(predictions.birth_year>=lo)&(predictions.birth_year<=hi)&(predictions.evaluation=='age15')]
        for model in ['wsb','linear','pa_no_age']:
            add('B','CIT',period,0,'forecast_mae_'+model,float(np.mean(np.abs(g[model]-g.observed))))
    allrows=pd.DataFrame(rows);allrows.to_csv(OUT/'all_checks.csv',index=False)
    counts=[]
    for (owner,ds,metric),g in allrows[allrows.period=='full'].groupby(['owner','dataset','metric']):
        twenty=g[g.nulls==20]; sixty=g[g.nulls==60]
        if len(twenty) and len(sixty):
            a,b=twenty.iloc[0],sixty.iloc[0]
            counts.append(dict(owner=owner,dataset=ds,metric=metric,mean20=a.null_mean,mean60=b.null_mean,
                value20=a.value,value60=b.value,sd20=a.null_std,sd60=b.null_std,mean_change=b.null_mean-a.null_mean,
                real_minus_null20=a.value-a.null_mean,real_minus_null60=b.value-b.null_mean))
    pd.DataFrame(counts).to_csv(OUT/'null_count_sensitivity.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'all_checks.csv',index=False)
    manifest=dict(primary_nulls=20,sensitivity_nulls=60,PS_CM_split='elapsed observation-time midpoint',
        CIT_split='1990--2004 vs 2005--2020; history retained',
        coverage={'A':'all five M1 metrics','C':'M2a/M2b','D':'M3a/all four SIR settings',
                  'E':'primary M4/M3b; existing resolution grid retained','B':'PA/age P3 counts and halves; existing growth-law splits'},
        limits=['WSB forecasts retain their established fixed-horizon evaluation; not reinterpreted as stationary halves',
                'CIT diameter uses cumulative endpoint graphs in each analysis segment; not an induced graph of only new papers',
                'Half-window node populations and effective observation horizons differ',
                'H7 ratios condition on major outbreaks; ratio null_mean=1 is the reference, not a measured peak mean'])
    (OUT/'protocol.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Wrote',len(rows),'robustness checks and',len(counts),'20/60 comparisons')
if __name__=='__main__':main()
