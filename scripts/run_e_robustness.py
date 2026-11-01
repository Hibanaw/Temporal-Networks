"""Primary E settings: elapsed-time halves and nested 20/60 P1 samples.

M4 gamma/window sensitivity is already complete and is not repeated.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from e_datasets import load
from m4_communities import analyse
from m3b_closeness import static_closeness, compare
from temporal_paths_placeholder import temporal_closeness
from nullmodels import timestamp_shuffle


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--dataset', choices=['PS','CM']);ap.add_argument('--period', choices=['full','first','second']);args=ap.parse_args()
    out=ROOT/'results/robustness/e';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name in ([args.dataset] if args.dataset else ('PS','CM')):
        for period in ([args.period] if args.period else ('full','first','second')):
            ds=load(name,period); nodes=sorted(set(ds.events.u)|set(ds.events.v))
            su,sw=static_closeness(ds.events,nodes,ds.directed)
            for i in range(-1,60 if period=='full' else 20):
                path=out/f'{name}_{period}_{i}.csv'
                if path.exists(): rows.extend(pd.read_csv(path).to_dict('records'));continue
                # Retain E's original seeds separately for M4 and M3b.
                e4=ds.events if i<0 else timestamp_shuffle(ds.events,seed=1000+i)
                e3=ds.events if i<0 else timestamp_shuffle(ds.events,seed=2000+i)
                _,sc,_=analyse(e4,ds.labels,900 if name=='PS' else 7*86400,1.,1.,0,ds.min_events,int(ds.events.t.min()),full=False)
                sc.update(compare(su,sw,temporal_closeness(e3,nodes,ds.closeness_starts,ds.directed)))
                new=[dict(dataset=name,period=period,iteration=i,metric=k,value=v) for k,v in sc.items()]
                pd.DataFrame(new).to_csv(path,index=False);rows.extend(new)
                print(name,period,i,flush=True)
    raw=pd.DataFrame(rows);raw.to_csv(out/f'per_network_{args.dataset}_{args.period}.csv',index=False)
    summaries=[]
    for (ds,period,metric),g in raw.groupby(['dataset','period','metric']):
        for n in ([20,60] if period=='full' else [20]):
            nul=g[(g.iteration>=0)&(g.iteration<n)].value
            summaries.append(dict(dataset=ds,period=period,metric=metric,nulls=n,value=g[g.iteration==-1].value.iloc[0],null_mean=nul.mean(),null_std=nul.std()))
    pd.DataFrame(summaries).to_csv(out/f'summary_{args.dataset}_{args.period}.csv',index=False)
if __name__=='__main__':main()
