# Member D post-processing only: NO temporal-network simulation is rerun.
# Paste this entire script into one Jupyter cell, or run as a Python script.
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CHANGE ONLY THIS DIRECTORY if your four CSV files are elsewhere.


# 项目根目录（D_analysis_only.py 所在目录）
ROOT = Path(__file__).resolve().parent

# 读取已有的四个 CSV
RESULTS_DIR = ROOT / "results"

# 所有新生成的图片和统计表保存到 figures
OUT= ROOT / "figures"

OUT.mkdir(parents=True, exist_ok=True)

sns.set_theme(style='whitegrid', context='notebook')
plt.rcParams.update({'figure.dpi':120,'savefig.dpi':220,'axes.spines.top':False,'axes.spines.right':False})
COLORS = {'Real':'#d95f59','P1':'#4b8bbe','P2':'#43a98b'}
ORDER = ['Real','P1','P2']
METRICS = ['reachability','mean_arrival_delay_seconds','peak_time_seconds','final_size']
LABELS = {'reachability':'Reachability','mean_arrival_delay_seconds':'Mean arrival delay','peak_time_seconds':'SIR peak time','final_size':'SIR final size'}

D = pd.concat([pd.read_csv(ROOT/f'{ds}_D_detail.csv') for ds in ('PS','CM')], ignore_index=True)
S = pd.concat([pd.read_csv(ROOT/f'{ds}_D_summary.csv') for ds in ('PS','CM')], ignore_index=True)
for df in (D,S):
    df['mode'] = df['mode'].astype(str)
    df['dataset'] = df['dataset'].astype(str)
D['value'] = pd.to_numeric(D['value'], errors='coerce')
S['mean'] = pd.to_numeric(S['mean'], errors='coerce')
S['std'] = pd.to_numeric(S['std'], errors='coerce')
assert set(D['mode']) == {'Real','P1','P2'}, 'Unexpected mode labels'
print('Loaded detail:',len(D),'rows; summary:',len(S),'rows')
print('Null iterations:', D[D['mode']!='Real'].groupby(['dataset','mode'])['iteration'].nunique().to_dict())

# Convert seconds to hours for PS and days for CM; keep raw seconds for calculations.
def unit(ds, metric):
    if metric.endswith('_seconds'):
        return (3600.0,'hours') if ds=='PS' else (86400.0,'days')
    return 1.0, ('fraction' if metric in ('reachability','final_size') else '')
def value(ds, mode, metric):
    r=S[(S.dataset==ds)&(S['mode']==mode)&(S.metric==metric)]
    return float(r.iloc[0]['mean']) if len(r) else np.nan
def draw_save(name):
    plt.tight_layout()
    plt.savefig(OUT/name, bbox_inches='tight')
    plt.show()
    plt.close()

# Table 1: all metrics, comparisons, and empirical one-sided/two-sided Monte Carlo p values.
records=[]
for ds in ('PS','CM'):
    for metric in METRICS:
        real=value(ds,'Real',metric)
        for mode in ('P1','P2'):
            vals=D[(D.dataset==ds)&(D['mode']==mode)&(D.metric==metric)]['value'].dropna().to_numpy(float)
            if not len(vals): continue
            mu=float(vals.mean()); sd=float(vals.std(ddof=1)) if len(vals)>1 else np.nan
            # +1 correction: minimum p is 1/(n+1), not zero.
            p_lower=(1+np.sum(vals<=real))/(len(vals)+1)
            p_upper=(1+np.sum(vals>=real))/(len(vals)+1)
            p_two=min(1.0,2*min(p_lower,p_upper))
            z=(real-mu)/sd if np.isfinite(sd) and sd>0 else np.nan
            records.append(dict(dataset=ds,experiment='M3a' if metric in METRICS[:2] else 'M3c',metric=metric,null_model=mode,n=len(vals),real=real,null_mean=mu,null_std=sd,real_over_null=real/mu if mu else np.nan,relative_effect=(real-mu)/mu if mu else np.nan,z_score=z,p_lower=p_lower,p_upper=p_upper,p_two_sided=p_two,zero_null_variance=bool(sd==0)))
T=pd.DataFrame(records)
T.to_csv(OUT/'Table1_full_statistics.csv',index=False)
print('\nTABLE 1: Statistics (p-values are Monte Carlo resolution-limited)')
print(T[['dataset','metric','null_model','real_over_null','relative_effect','z_score','p_two_sided']].round(4).to_string(index=False))

# Figure 1: 2 x 2 comparisons, one figure per dataset.
for ds in ('PS','CM'):
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for ax,metric in zip(axs.flat,METRICS):
        factor,un=unit(ds,metric)
        ys=[value(ds,m,metric)/factor for m in ORDER]
        bars=ax.bar(ORDER,ys,color=[COLORS[m] for m in ORDER],width=.65)
        ax.set_title(LABELS[metric]); ax.set_ylabel(un)
        for b,v in zip(bars,ys): ax.annotate(f'{v:.4g}',(b.get_x()+b.get_width()/2,b.get_height()),ha='center',va='bottom',fontsize=9)
        ax.margins(y=.18)
    fig.suptitle(f'Figure 1 — {ds}: Real vs null models',fontsize=15)
    draw_save(f'Fig1_{ds}_four_metrics.png')

# Figure 2: distribution of 20 null samples; real reference line.
for ds in ('PS','CM'):
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for ax,metric in zip(axs.flat,METRICS):
        factor,un=unit(ds,metric)
        sub=D[(D.dataset==ds)&(D.metric==metric)&(D['mode'].isin(['P1','P2']))].copy()
        sub['display_value']=sub['value']/factor
        sns.boxplot(data=sub,x='mode',y='display_value',order=['P1','P2'],ax=ax,showfliers=False,color='#d7e4ee',width=.45)
        sns.stripplot(data=sub,x='mode',y='display_value',order=['P1','P2'],ax=ax,palette=[COLORS['P1'],COLORS['P2']],jitter=.16,size=4,alpha=.75)
        ax.axhline(value(ds,'Real',metric)/factor,color=COLORS['Real'],ls='--',lw=2,label='Real')
        ax.set(title=LABELS[metric],xlabel='',ylabel=un)
        ax.legend(loc='best',fontsize=8)
    fig.suptitle(f'Figure 2 — {ds}: Null-model samples vs Real',fontsize=15)
    draw_save(f'Fig2_{ds}_null_distributions.png')

# Figure 3: M3a temporal reachability and delay; separate units per dataset.
fig,axs=plt.subplots(1,3,figsize=(15,4.5))
for i,ds in enumerate(('PS','CM')):
    ax=axs[i]
    vals=[value(ds,m,'reachability') for m in ORDER]
    ax.bar(ORDER,vals,color=[COLORS[m] for m in ORDER]);ax.set_ylim(0,1.1)
    ax.set_title(f'{ds} reachability');ax.set_ylabel('Fraction reachable')
for ds in ('PS','CM'):
    pass
ax=axs[2]
for ds in ('PS','CM'):
    ratios=[value(ds,'Real','mean_arrival_delay_seconds')/value(ds,m,'mean_arrival_delay_seconds') for m in ('P1','P2')]
    ax.plot(['P1','P2'],ratios,'o-',label=ds,lw=2)
ax.axhline(1,color='gray',ls='--');ax.set(title='Arrival delay ratio (Real / Null)',ylabel='Ratio');ax.legend()
fig.suptitle('Figure 3 — Temporal reachability (M3a)')
draw_save('Fig3_reachability_and_delay.png')

# Figure 4: SIR results, annotate degenerate CM simulations.
fig,axs=plt.subplots(2,2,figsize=(12,8))
for i,ds in enumerate(('PS','CM')):
    for j,metric in enumerate(('peak_time_seconds','final_size')):
        ax=axs[i,j];factor,un=unit(ds,metric)
        vals=[value(ds,m,metric)/factor for m in ORDER]
        ax.bar(ORDER,vals,color=[COLORS[m] for m in ORDER]);ax.set_title(f'{ds} — {LABELS[metric]}');ax.set_ylabel(un)
        if ds=='CM': ax.text(.5,.88,'No observed spread beyond seed',ha='center',transform=ax.transAxes,fontsize=9,color='#b24d45')
fig.suptitle('Figure 4 — Event-driven SIR (M3c)')
draw_save('Fig4_SIR_results.png')

# Figure 5: normalized time effects, (Real-Null)/Null.
heat=T.copy();heat['row']=heat['dataset']+' / '+heat['null_model'];heat['metric_name']=heat['metric'].map(LABELS)
pivot=heat.pivot(index='row',columns='metric_name',values='relative_effect').reindex(index=['PS / P1','PS / P2','CM / P1','CM / P2'],columns=[LABELS[m] for m in METRICS])
plt.figure(figsize=(11,5));sns.heatmap(pivot,annot=True,fmt='.2f',cmap='RdBu_r',center=0,linewidths=.5,mask=pivot.isna(),cbar_kws={'label':'(Real - Null) / Null'})
plt.title('Figure 5 — Normalized temporal effects')
draw_save('Fig5_normalized_effect_heatmap.png')

# Figure 6: z scores (omit zero-variance nulls rather than dividing by zero).
z=T[np.isfinite(T.z_score)].copy();z['label']=z['dataset']+' / '+z['null_model']
fig,axs=plt.subplots(1,2,figsize=(13,5))
for ax,ex in zip(axs,['M3a','M3c']):
    q=z[z.experiment==ex]
    sns.barplot(data=q,x='metric',y='z_score',hue='label',ax=ax)
    ax.axhline(0,color='gray',lw=1);ax.tick_params(axis='x',rotation=20);ax.set_title(ex+' Z-scores')
    ax.set_xlabel('');ax.legend(fontsize=8)
fig.suptitle('Figure 6 — Standardized deviation from null distributions')
draw_save('Fig6_z_scores.png')

# Figure 7: cross-dataset ratios (same dimensionless scale).
fig,axs=plt.subplots(1,2,figsize=(13,5))
for ax,ex in zip(axs,['M3a','M3c']):
    q=T[T.experiment==ex].copy();q['label']=q.metric.map(LABELS)+' / '+q.null_model
    sns.barplot(data=q,x='label',y='real_over_null',hue='dataset',ax=ax,errorbar=None)
    ax.axhline(1,color='gray',ls='--');ax.set_title(ex+' — Real / Null')
    ax.set_ylabel('Ratio');ax.set_xlabel('');ax.tick_params(axis='x',rotation=15)
    ax.legend(title='Dataset')
    # P1 and P2 are different baselines: label bars with null-model names.
    for container in ax.containers:
        try: ax.bar_label(container,fmt='%.2f',padding=2,fontsize=7)
        except Exception: pass
fig.suptitle('Figure 7 — Cross-dataset comparison by null model')
draw_save('Fig7_cross_dataset_ratios.png')

# Table 2: evidence classification, NOT a definitive statistical hypothesis test.
verdicts=[]
for ds in ('PS','CM'):
    r=value(ds,'Real','reachability'); p1=value(ds,'P1','reachability');p2=value(ds,'P2','reachability')
    delay=value(ds,'Real','mean_arrival_delay_seconds')
    d1=value(ds,'P1','mean_arrival_delay_seconds');d2=value(ds,'P2','mean_arrival_delay_seconds')
    verdicts.append({'dataset':ds,'hypothesis':'H6a','interpretation':('Real arrival delay exceeds both null means; reachability is lower than both null means' if delay>d1 and delay>d2 and r<p1 and r<p2 else 'Mixed evidence; inspect individual metrics')})
    size=value(ds,'Real','final_size');s1=value(ds,'P1','final_size');s2=value(ds,'P2','final_size')
    peak=value(ds,'Real','peak_time_seconds');t1=value(ds,'P1','peak_time_seconds');t2=value(ds,'P2','peak_time_seconds')
    # Degenerate if real and both nulls have identical size and peak time.
    degenerate=np.allclose([size,peak],[s1,t1],rtol=0,atol=1e-12) and np.allclose([size,peak],[s2,t2],rtol=0,atol=1e-12)
    verdicts.append({'dataset':ds,'hypothesis':'H7','interpretation':('Inconclusive: identical final size and peak time in Real/P1/P2; inspect simulation setup' if degenerate else 'Real peak time is later and final size smaller than both null means' if peak>t1 and peak>t2 and size<s1 and size<s2 else 'Mixed evidence; inspect SIR metrics')})
V=pd.DataFrame(verdicts);V.to_csv(OUT/'Table2_hypothesis_verdicts.csv',index=False)
print('\nTABLE 2: Hypothesis evidence (descriptive, not proof)')
print(V.to_string(index=False))
print('\nSaved plots and tables to:',OUT.resolve())
print('NOTE: No temporal paths, null-model networks, or SIR simulations were rerun.')
