"""Member D: temporal reachability and event-driven SIR. Python 3.10+."""
from pathlib import Path
import argparse
import gzip
import urllib.request
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nullmodels import timestamp_shuffle, edge_shuffle

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'results'
FIG = ROOT / 'figures'
URLS = {'PS': 'https://sociopatterns.org/assets/data/primaryschool.csv.gz',
        'CM': 'https://snap.stanford.edu/data/CollegeMsg.txt.gz'}


def load_events(dataset):
    if dataset == "PS":
        path = RAW / "PS_events.csv"
        directed = False

    elif dataset == "CM":
        path = RAW / "CM_events.csv"
        directed = True

    else:
        raise ValueError("Only PS and CM are supported")

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    events = pd.read_csv(path)

    events = events[["u", "v", "t"]]

# Check duplicate events
    n_before = len(events)
    n_duplicates = events.duplicated(subset=["u", "v", "t"]).sum()

    print(f"Duplicate events: {n_duplicates}")

# Remove exact duplicate events
    events = events.drop_duplicates(subset=["u", "v", "t"])

# Remove self-loops
    events = events[events["u"] != events["v"]]

    events = events.sort_values("t").reset_index(drop=True)

    print(f"Events before cleaning: {n_before}")
    print(f"Events after cleaning: {len(events)}")

    return events, directed



def earliest_arrival(events, source, start_time=None, directed=False):
    """Strictly increasing event times. Source is active at start_time.
    A contact at t is usable only when arrival < t; equal-time multi-hop is forbidden.
    """
    if start_time is None:
        start_time = int(events.t.min()) - 1
    arrival = {int(source): int(start_time)}
    for t, group in events.groupby('t', sort=True):
        if t < start_time:
            continue
        old = arrival.copy()
        for u,v in group[['u','v']].itertuples(index=False, name=None):
            u,v=int(u),int(v)
            if u in old and old[u] < t:
                arrival[v] = min(arrival.get(v, np.inf), t)
            if not directed and v in old and old[v] < t:
                arrival[u] = min(arrival.get(u, np.inf), t)
    return arrival


def static_reachability(events, directed):
    graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_edges_from(events[['u','v']].itertuples(index=False,name=None))
    n=graph.number_of_nodes()
    reachable=sum(len(nx.descendants(graph,s)) if directed else len(nx.node_connected_component(graph,s))-1 for s in graph.nodes())
    return reachable/(n*(n-1)) if n>1 else 0


def temporal_reachability(events, directed=False, sources=None):
    nodes=np.unique(events[['u','v']].to_numpy())
    if sources is None: sources=nodes
    start=int(events.t.min())-1
    counts=[]; delays=[]
    for s in sources:
        arrival=earliest_arrival(events,int(s),start,directed)
        counts.append((len(arrival)-1)/(len(nodes)-1))
        delays.extend([(t-start) for node,t in arrival.items() if node != s])
    return float(np.mean(counts)), float(np.mean(delays)) if delays else np.nan


def randomize(events, mode, rng, directed):
    seed = int(rng.integers(0, 2**31 - 1))

    if mode == 'P1':
        out = timestamp_shuffle(events, seed=seed)

    elif mode == 'P2':
        out = edge_shuffle(events, seed=seed,directed=directed)

    else:
        raise ValueError(mode)

    return out.sort_values(
        't', kind='stable'
    ).reset_index(drop=True)


def simulate_sir(events, directed, source, beta, infectious_seconds, seed):
    """Fixed infectious duration, per-event Bernoulli transmission.
    State changes from contacts at t become effective after processing the timestamp.
    Return infected prevalence sampled after each unique event time.
    """
    rng=np.random.default_rng(seed)
    start=int(events.t.min())-1
    infection={int(source):start}
    nodes=np.unique(events[['u','v']].to_numpy())
    times=[]; infected=[]; recovered=[]
    for t,group in events.groupby('t',sort=True):
        t=int(t)
        previous=infection.copy()
        new=set()
        for u,v in group[['u','v']].itertuples(index=False,name=None):
            pairs=[(int(u),int(v))] if directed else [(int(u),int(v)),(int(v),int(u))]
            for a,b in pairs:
                if a in previous and previous[a] <= t < previous[a]+infectious_seconds and b not in previous and b not in new:
                    if rng.random()<beta: new.add(b)
        for v in new: infection[v]=t
        current=sum(s<=t<s+infectious_seconds for s in infection.values())
        times.append(t-start)
        infected.append(current/len(nodes))
        recovered.append(sum(s+infectious_seconds<=t for s in infection.values())/len(nodes))
    peak_idx=int(np.argmax(infected))
    return {'peak_time':times[peak_idx], 'final_size':len(infection)/len(nodes),
            'times':times, 'I':infected, 'R':recovered}


def run(dataset, null_samples=20, seeds=100, source_count=100, beta=0.15, duration=None):
    events,directed=load_events(dataset)
    OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    nodes=np.unique(events[['u','v']].to_numpy())
    rng=np.random.default_rng(2026)
    sources=rng.choice(nodes,size=min(source_count,len(nodes)),replace=False)
    if duration is None:
        duration=3600 if dataset=='PS' else (86400 if dataset=='CM' else 25)
    print(dataset, 'nodes',len(nodes),'events',len(events),'directed',directed)
    print('Computing reachability; this can take time...')
    records=[]; trajectories={}
    for mode in ['Real','P1','P2']:
        repetitions=1 if mode=='Real' else null_samples
        for j in range(repetitions):
            ev=events if mode=='Real' else randomize(events,mode,np.random.default_rng(1000+j),directed)
            r,delay=temporal_reachability(ev,directed,sources)
            records.append(dict(dataset=dataset,experiment='M3a',mode=mode,iteration=j,metric='reachability',value=r))
            records.append(dict(dataset=dataset,experiment='M3a',mode=mode,iteration=j,metric='mean_arrival_delay_seconds',value=delay))
            peaks=[]; sizes=[]
            for k in range(seeds):
                s=int(sources[k%len(sources)])
                res=simulate_sir(ev,directed,s,beta,duration,seed=50000+k)
                peaks.append(res['peak_time']); sizes.append(res['final_size'])
                if j==0 and k==0: trajectories[mode]=res
            for metric,values in [('peak_time_seconds',peaks),('final_size',sizes)]:
                records.append(dict(dataset=dataset,experiment='M3c',mode=mode,iteration=j,metric=metric,value=float(np.mean(values))))
        print('Finished',mode)
    detail=pd.DataFrame(records)
    detail.to_csv(OUT/f'{dataset}_D_detail.csv',index=False)
    summary=detail.groupby(['dataset','experiment','mode','metric']).value.agg(['mean','std']).reset_index()
    summary.to_csv(OUT/f'{dataset}_D_summary.csv',index=False)
    print(summary.to_string(index=False))
    for metric in ['reachability','peak_time_seconds','final_size']:
        part=summary[summary.metric==metric]
        plt.figure(figsize=(6,4))
        plt.bar(part['mode'],part['mean'],yerr=part['std'].fillna(0),capsize=4)
        plt.title(f'{dataset}: {metric}');plt.ylabel(metric);plt.tight_layout()
        plt.savefig(FIG/f'{dataset}_{metric}.png',dpi=160);plt.close()
    plt.figure(figsize=(7,4))
    for mode,res in trajectories.items():
        plt.plot(np.array(res['times'])/3600,res['I'],label=mode)
    plt.xlabel('Hours from observation start');plt.ylabel('Infected fraction')
    plt.legend();plt.tight_layout();plt.savefig(FIG/f'{dataset}_sir_curve.png',dpi=160);plt.close()
    print('Static reachability:',static_reachability(events,directed))


def self_test():
    toy=pd.DataFrame([(2,3,9),(1,2,10)],columns=['u','v','t'])
    assert 3 not in earliest_arrival(toy,1,0,False)
    toy2=pd.DataFrame([(1,2,10),(2,3,20)],columns=['u','v','t'])
    assert earliest_arrival(toy2,1,0,False)[3]==20
    assert 1 not in earliest_arrival(toy2,3,0,True)
    simultaneous=pd.DataFrame([(1,2,10),(2,3,10)],columns=['u','v','t'])
    assert 3 not in earliest_arrival(simultaneous,1,0,False)
    result=simulate_sir(toy2,False,1,1.0,100,1)
    assert abs(result['final_size']-1)<1e-9
    print('All tests passed')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',choices=['PS','CM'],default='CM')
    parser.add_argument('--null-samples',type=int,default=20)
    parser.add_argument('--seeds',type=int,default=100)
    parser.add_argument('--sources',type=int,default=100)
    parser.add_argument('--beta',type=float,default=0.15)
    parser.add_argument('--duration',type=int,default=None)
    parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    self_test()
    if not args.test:
        run(args.dataset,args.null_samples,args.seeds,args.sources,args.beta,args.duration)
