#!/usr/bin/env python3
"""Render measured B results; never draw expected values as measurements."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import ndtr
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'results/b';F=ROOT/'figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150,'savefig.bbox':'tight','pdf.fonttype':42})
COL={'real':'#173F5F','P3a':'#D27D2D','P3b':'#2C8A78'}
def save(fig,name):
 fig.savefig(F/(name+'.pdf'));fig.savefig(F/(name+'.png'),dpi=180);plt.close(fig)
def plots():
 agg=pd.read_csv(O/'aggregation.csv');win=pd.read_csv(O/'windows.csv')
 fig,axs=plt.subplots(2,2,figsize=(7.2,5.0),constrained_layout=True)
 for ax,metric,label in zip(axs.flat,['density_directed','mean_total_degree','clustering_weak','lcc_fraction'],['Directed density','Mean total degree','Weak clustering','Weak LCC / all born nodes']):
  for mode,color in [('annual','#C36A2B'),('cumulative',COL['real'])]:
   d=agg[agg['mode']==mode];ax.plot(d.year,d[metric],label=mode,color=color)
  ax.set(xlabel='Year',ylabel=label);ax.grid(alpha=.18)
 axs[0,0].legend(frameon=False)
 save(fig,'b_aggregation')
 fig,axs=plt.subplots(1,2,figsize=(7.2,2.5),constrained_layout=True)
 ac=agg[agg['mode']=='annual'];axs[0].bar(ac.year,ac.E,color=COL['real']);axs[0].set(xlabel='Year',ylabel='New observed citations')
 nd=pd.read_csv(ROOT/'data/processed/CIT/nodes.csv');nd.groupby('year').size().plot(ax=axs[1],color=COL['P3b']);axs[1].set(xlabel='Year',ylabel='New selected publications');save(fig,'b_activity')
 fig,axs=plt.subplots(1,2,figsize=(7.2,2.6),constrained_layout=True)
 pa=json.loads((O/'pa.json').read_text());k=pd.read_csv(O/'pa_kernel.csv');k=k[(k.hits>=5)&(k.uniform_expected>0)]
 axs[0].scatter(k.k+1,k.relative_rate,s=10,alpha=.6,color=COL['real'],label='Observed / uniform expectation')
 # Fit normalization for display only; alpha itself uses yearly conditional likelihood.
 x=np.geomspace(1,max(k.k)+1,100);scale=np.median(k.relative_rate/(k.k+1)**pa['alpha']);axs[0].plot(x,scale*x**pa['alpha'],color='black',lw=1,label=f"alpha={pa['alpha']:.2f}")
 axs[0].set(xscale='log',yscale='log',xlabel='Prior in-degree + 1',ylabel='Relative attachment rate');axs[0].legend(fontsize=7,frameon=False)
 real_age=pd.read_csv(O/'age_curve.csv');axs[1].plot(real_age.age,real_age.relative_rate,color=COL['real'],label='Observed')
 for kind in ['P3a','P3b']:
  curves=[]
  for i in range(20):
   a=pd.read_csv(O/'null_events'/f'{kind}_{i:02d}_age.csv');curves.append(np.divide(a.hits,a.expected_uniform,out=np.full(len(a),np.nan),where=a.expected_uniform>0))
  a=np.array(curves);valid=np.isfinite(a).sum(axis=0)>1;mean=np.full(a.shape[1],np.nan);sd=np.full(a.shape[1],np.nan);mean[valid]=np.nanmean(a[:,valid],0);sd[valid]=np.nanstd(a[:,valid],0,ddof=1);axs[1].plot(real_age.age,mean,color=COL[kind],label=kind);axs[1].fill_between(real_age.age,mean-sd,mean+sd,color=COL[kind],alpha=.15)
 axs[1].set(xlabel='Paper age (years)',ylabel='Age rate / uniform expectation',xlim=(1,40));axs[1].legend(frameon=False)
 save(fig,'b_attachment_ageing')
 null=pd.read_csv(O/'null_metrics.csv');fig,axs=plt.subplots(1,2,figsize=(7.2,2.5),constrained_layout=True)
 axs[0].hist([null[null.kind==kind].alpha for kind in ['P3a','P3b']],bins=10,color=[COL['P3a'],COL['P3b']],label=['P3a','P3b']);axs[0].axvline(pa['alpha'],color=COL['real'],label='Observed');axs[0].set(xlabel='Estimated PA alpha',ylabel='Null realizations');axs[0].legend(frameon=False)
 fits=json.loads((O/'age_fits.json').read_text());best=min(r['aic'] for r in fits);axs[1].bar([r['model'] for r in fits],[r['aic']-best for r in fits],color=COL['real']);axs[1].tick_params(axis='x',labelrotation=20);axs[1].set(ylabel='AIC - minimum AIC');save(fig,'b_null_and_age_models')
 fig,axs=plt.subplots(1,2,figsize=(7.2,2.6),constrained_layout=True)
 d=agg[(agg['mode']=='cumulative')&(agg.year>=1990)];den=json.loads((O/'densification.json').read_text());axs[0].scatter(d.N,d.E,c=d.year,cmap='viridis',s=18);xx=np.geomspace(d.N.min(),d.N.max(),100);axs[0].plot(xx,np.exp(den['intercept'])*xx**den['a'],color='black',lw=1,label=f"a={den['a']:.3f}");axs[0].set(xscale='log',yscale='log',xlabel='Cumulative N (including isolates)',ylabel='Cumulative directed E');axs[0].legend(frameon=False)
 diam=pd.read_csv(O/'diameter_real.csv');dn=pd.read_csv(O/'diameter_null.csv');axs[1].plot(diam.year,diam.diameter90,label='Observed',color=COL['real'])
 for kind in ['P3a','P3b']:
  v=dn[dn.kind==kind].groupby('year').diameter90.agg(['mean','std']);axs[1].plot(v.index,v['mean'],label=kind,color=COL[kind]);axs[1].fill_between(v.index,v['mean']-v['std'],v['mean']+v['std'],alpha=.15,color=COL[kind])
 axs[1].set(xlabel='Year',ylabel='Weak-LCC effective diameter (90%)');axs[1].legend(frameon=False);save(fig,'b_densification_diameter')
 pars=pd.read_csv(O/'wsb_full_parameters.csv');collapse=pd.read_csv(O/'wsb_collapse.csv');pred=pd.read_csv(O/'wsb_predictions.csv');pred=pred[pred.evaluation=='age15']
 fig,axs=plt.subplots(1,3,figsize=(10.2,2.7),constrained_layout=True)
 axs[0].hist([pars['lambda'],pars.mu,pars.sigma],bins=20,label=['lambda','mu','sigma'],alpha=.7);axs[0].set(xlabel='Full-history fitted parameter',ylabel='Papers');axs[0].legend(frameon=False,fontsize=7)
 axs[1].scatter(collapse.scaled_time,collapse.scaled_citations,s=2,alpha=.08,color=COL['real'],rasterized=True);xx=np.linspace(-4,4,200);axs[1].plot(xx,ndtr(xx),color='black',lw=1);axs[1].set(xlim=(-4,4),ylim=(-.05,1.5),xlabel='(ln age - mu) / sigma',ylabel='ln(1+c/m) / lambda',title='Descriptive in-sample collapse')
 for model,color in [('wsb',COL['real']),('pa_no_age',COL['P3a']),('linear',COL['P3b'])]:axs[2].scatter(pred.observed+1,pred[model]+1,s=7,alpha=.28,color=color,label=model)
 hi=max(pred.observed.max()+1,2);axs[2].plot([1,hi],[1,hi],color='black',lw=1);axs[2].set(xscale='log',yscale='log',xlabel='Observed c(15) + 1',ylabel='5-year forecast c(15) + 1');axs[2].legend(frameon=False,fontsize=7);save(fig,'b_wsb')
 # Held-out comparison at readable report width; no-age PA is retained in
 # b_wsb and the numerical tables, while this panel resolves WSB vs linear.
 summary=json.loads((O/'wsb_summary.json').read_text())
 fig,axs=plt.subplots(1,2,figsize=(7.2,2.6),constrained_layout=True)
 hi=max(float(pred.observed.max()+1),float(pred.wsb.max()+1),float(pred.linear.max()+1))
 for model,color in [('wsb',COL['real']),('linear',COL['P3b'])]:
  axs[0].scatter(pred.observed+1,pred[model]+1,s=8,alpha=.32,color=color,label=model)
 axs[0].plot([1,hi],[1,hi],color='black',lw=1)
 axs[0].set(xscale='log',yscale='log',xlim=(1,hi),ylim=(1,hi),xlabel='Observed c(15) + 1',ylabel='Predicted c(15) + 1',title='Prediction from first five years')
 axs[0].legend(frameon=False,fontsize=8)
 comparisons=[r for r in summary['evaluation'] if r.get('paired_difference')=='WSB minus linear']
 vals=np.array([r['mean_MAE_difference'] for r in comparisons]);ci=np.array([r['ci95'] for r in comparisons])
 axs[1].errorbar(vals,np.arange(len(vals)),xerr=np.array([vals-ci[:,0],ci[:,1]-vals]),fmt='o',capsize=4,color=COL['real'])
 axs[1].axvline(0,ls='--',lw=1,color='gray');axs[1].set(yticks=[0,1],yticklabels=['Age 15','2020 endpoint'],ylim=(-.6,1.6),xlabel='MAE(WSB) - MAE(linear)',title='Paired bootstrap 95% intervals')
 save(fig,'b_wsb_validation')
 fig,axs=plt.subplots(1,2,figsize=(7.2,2.6),constrained_layout=True)
 for width,d in win.groupby('window'):
  axs[0].plot(d.year,d.clustering_weak,label=f'{width} yr');axs[1].plot(d.year,d.lcc_fraction,label=f'{width} yr')
 axs[0].set(xlabel='Window endpoint',ylabel='Weak clustering');axs[1].set(xlabel='Window endpoint',ylabel='Weak LCC / all born nodes');axs[1].legend(frameon=False,ncol=2);save(fig,'b_window_sensitivity')
if __name__=='__main__':plots()
