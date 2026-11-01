"""B primary PA/age/densification: nested 20/60 P3 and elapsed-year halves.

Existing nodes remain eligible as targets in each half; only events are truncated.
Annual counts, PA exposure, and citation-age risk sets retain publication history.
WSB forecasting is an out-of-time protocol and is not a stationary half-window test.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from growth import p3,pa_tables,pa_fit,age_tables,age_fit,age_rates,diameter,SEED


def main():
    nodes=pd.read_csv(ROOT/'data/processed/CIT/nodes.csv').sort_values('id')
    events=pd.read_csv(ROOT/'data/processed/CIT/events.csv')
    out=ROOT/'results/robustness/b';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    # Use the analysis interval 1990--2020, matching B's primary fits.
    for period,lo,hi in [('full',1990,2020),('first',1990,2004),('second',2005,2020)]:
        for mode in ('Real','P3a','P3b'):
            for i in range(1 if mode=='Real' else (60 if period=='full' else 20)):
                path=out/f'{period}_{mode}_{i}.csv'
                if path.exists():rows.extend(pd.read_csv(path).to_dict('records'));continue
                e=events if mode=='Real' else p3(events,nodes,SEED+i+(10000 if mode=='P3b' else 0),mode,age_rates(events,nodes))
                n,h,_=age_tables(e,nodes,lo,hi);fits=age_fit(n,h);best=min(fits,key=lambda x:x['aic'])
                age=e[(e.t>=lo)&(e.t<=hi)]
                row=dict(dataset='CIT',period=period,mode=mode,iteration=i,alpha=pa_fit(pa_tables(e,nodes,lo,hi)),
                         mean_age=float(np.mean(age.t.to_numpy()-nodes.year.to_numpy()[age.v])),age_best=best['model'],
                         diameter90=diameter(e,nodes,hi,samples=128)[0])
                pd.DataFrame([row]).to_csv(path,index=False);rows.append(row);print(period,mode,i,flush=True)
    pd.DataFrame(rows).to_csv(out/'per_network.csv',index=False)
if __name__=='__main__':main()
