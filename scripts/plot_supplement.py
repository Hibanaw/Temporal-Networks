"""Measured A/C/D figures from saved tables (no simulation during plotting)."""
import os
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/pc5253-mpl')
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import sys
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import figstyle
figstyle.apply()
COLORS=figstyle.SERIES


def save(fig,name):
    figstyle.save(fig,name,ROOT)


def main():
    OUT.mkdir(exist_ok=True)
    # H1: each metric divided by its mean over the window grid, so the vertical range of a
    # curve equals the window sensitivity; CIT curves are averaged over end years 1990-2020.
    fig,axs=figstyle.grid(None,1,3,figstyle.WIDTH,1.35)
    axs=axs[0]
    # PS/CM: Member A's M1 (complete windows, fixed node set; CM directed clustering).
    keys=[('density','density_directed','Density'),('clustering','clustering_weak','Clustering'),
          ('largest_component_fraction','lcc_fraction','LCC fraction')]
    for ax,name in zip(axs[:2],['PS','CM']):
        s=pd.read_csv(ROOT/f'results/m1/main_fixed/{name}_summary.csv')
        s=s[(s.period=='full')&(s.node_basis=='fixed')&(s.window_policy=='complete_only')]
        m=s.pivot(index='delta_seconds',columns='metric',values='mean')
        for (key,_,label),c in zip(keys,COLORS):
            ax.plot(m.index/3600,m[key]/m[key].mean(),'-o',color=c,label=label)
        ax.set(xscale='log',xlabel='Window width (h)',title=f'({"ab"[name=="CM"]}) {name}')
    w=pd.read_csv(ROOT/'results/b/windows.csv')
    for (_,key,label),c in zip(keys,COLORS):
        rel=w.pivot(index='year',columns='window',values=key)
        rel=rel.div(rel.mean(axis=1),axis=0).mean()
        axs[2].plot(rel.index,rel.values,'-o',color=c,label=label)
    axs[2].set(xscale='log',xlabel='Trailing window (yr)',title='(c) CIT',xticks=[1,2,5,10],xticklabels=['1','2','5','10'])
    axs[0].set_ylabel('Value / grid mean')
    for ax in axs:
        ax.grid(axis='y');ax.minorticks_off()
    axs[2].legend(frameon=False,loc='upper left',handlelength=1.4,labelspacing=.2)
    save(fig,'ac_m1_windows')
    d=pd.read_csv(ROOT/'results/d_summary.csv')
    def row(ds,key):return d[(d.dataset==ds)&(d.metric==key)].iloc[0]
    fig,axs=plt.subplots(1,2,figsize=(7,2.8))
    for ax,ds in zip(axs,['PS','CM']):
        p1,p2=row(ds,'m3a_R_vsP1'),row(ds,'m3a_R_vsP2')
        ax.bar(['Real','P1','P2'],[p1.value,p1.null_mean,p2.null_mean],yerr=[0,p1.null_std,p2.null_std],color=COLORS,capsize=3)
        ax.set_ylim(0,1.07);ax.set_ylabel('Temporal / static reachability');ax.set_title(ds)
    save(fig,'d_reachability_multistart')
    fig,axs=plt.subplots(2,3,figsize=(10,5))
    for ds,axes in zip(['PS','CM'],axs):
        setting='b0.05_D4h' if ds=='PS' else 'b0.2_D336h'
        for ax,metric,label in zip(axes,['final_size','p_major','peak_time_s'],['Final infected fraction','Major outbreak probability','Peak delay (hours)']):
            p1,p2=row(ds,f'm3c_{setting}_{metric}_vsP1'),row(ds,f'm3c_{setting}_{metric}_vsP2')
            scale=3600 if metric=='peak_time_s' else 1
            ax.bar(['Real','P1','P2'],np.array([p1.value,p1.null_mean,p2.null_mean])/scale,yerr=np.array([0,p1.null_std,p2.null_std])/scale,color=COLORS,capsize=3)
            ax.set_title(ds+': '+label)
    save(fig,'d_sir_event_seeds')
    fig,axs=plt.subplots(1,2,figsize=(7,2.8))
    c=pd.read_csv(ROOT/'results/c_summary.csv')
    for ax,ds in zip(axs,['PS','CM']):
        part=c[(c.dataset==ds)&c.metric.isin(['m2_burstiness','m2_memory'])]
        x=np.arange(len(part));ax.bar(x-.17,part.value,.34,label='Real',color=COLORS[0]);ax.bar(x+.17,part.null_mean,.34,yerr=part.null_std,label='P1',color=COLORS[1]);ax.set_xticks(x,['B','M']);ax.set_title(ds);ax.legend()
    save(fig,'c_activity_reproduced')
if __name__=='__main__':main()
