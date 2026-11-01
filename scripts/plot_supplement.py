"""Measured A/C/D figures from saved tables (no simulation during plotting)."""
import os
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/pc5253-mpl')
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures'
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
COLORS=['#2878a0','#e58a2b','#4b9560']


def save(fig,name):
    fig.tight_layout();fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight');fig.savefig(OUT/f'{name}.png',dpi=170,bbox_inches='tight');plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    fig,axs=plt.subplots(2,3,figsize=(10,5))
    keys=['density','mean_total_degree','clustering','components','lcc_fraction']
    for name,c in zip(['PS','CM'],COLORS):
        m=pd.read_csv(ROOT/f'results/ac/m1_{name}_full_means.csv')
        static=pd.read_csv(ROOT/f'results/ac/m1_{name}_full_static.csv').iloc[0] if (ROOT/f'results/ac/m1_{name}_full_static.csv').exists() else None
        for ax,key in zip(axs.flat,keys):
            ax.plot(m.width_s/3600,m[key],'-o',label=name,color=c,ms=3);ax.set_xscale('log');ax.set_title(key.replace('_',' '));ax.set_xlabel('Window (hours)')
            if static is not None: ax.axhline(static[key],color=c,ls='--',lw=.7,alpha=.6)
    axs.flat[-1].axis('off');axs.flat[0].legend();save(fig,'ac_m1_windows')
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
