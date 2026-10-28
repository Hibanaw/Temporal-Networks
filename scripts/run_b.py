#!/usr/bin/env python3
"""One command for all B experiments; all numerical work runs in PBS."""
import argparse, concurrent.futures, hashlib, json, os, platform, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import ndtr
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from growth import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/b';FIG=ROOT/'figures'

def save_json(name,obj):
 (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=True,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
def read_data():
 nodes=pd.read_csv(ROOT/'data/processed/CIT/nodes.csv').sort_values('id')
 e=pd.read_csv(ROOT/'data/processed/CIT/events.csv');return e,nodes

def one_null(args):
 kind,rep=args;events,nodes=read_data();seed=SEED+rep+(10000 if kind=='P3b' else 0)
 e=p3(events,nodes,seed,kind,age_rates(events,nodes));path=OUT/'null_events'/f'{kind}_{rep:02d}.csv.gz'
 e.to_csv(path,index=False,compression={'method':'gzip','mtime':0})
 assert np.array_equal(events.groupby(['u','t']).size().values,e.groupby(['u','t']).size().values)
 assert (nodes.year.to_numpy()[e.v]<e.t.to_numpy()).all()
 assert not e.duplicated(['u','v']).any()
 n,h,ys=age_tables(e,nodes);fits=age_fit(n,h);best=min(fits,key=lambda r:r['aic'])
 row={'kind':kind,'rep':rep,'seed':seed,'alpha':pa_fit(pa_tables(e,nodes)),
 'mean_age':float(np.mean(e.t.to_numpy()-nodes.year.to_numpy()[e.v])),
 'age_best':best['model'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 dr=[]
 for y in range(1990,2021,5):
  d,nc,ns=diameter(e,nodes,y,samples=128);dr.append({'kind':kind,'rep':rep,'year':y,'diameter90':d,'lcc_n':nc,'sources':ns})
 row['age_fits']=fits
 # Save null age kernels so the report can verify fitted age controls.
 nn,hh,_=age_tables(e,nodes)
 pd.DataFrame({'age':np.arange(1,61),'hits':hh.sum(0),'expected_uniform':(nn*hh.sum(1,keepdims=True)/nn.sum(1,keepdims=True)).sum(0)}).to_csv(OUT/'null_events'/f'{kind}_{rep:02d}_age.csv',index=False)
 return row,dr

def init_graph_worker():
 global GRAPH_EVENTS,GRAPH_NODES
 GRAPH_EVENTS,GRAPH_NODES=read_data()

def metric_worker(spec):
 year,mode,width=spec
 e=GRAPH_EVENTS
 if width is not None:e=e[(e.t>year-width)&(e.t<=year)]
 row=graph_metrics(e,GRAPH_NODES,year,mode)
 if width is not None:row['window']=width
 return row

def run_real(events,nodes):
 with concurrent.futures.ProcessPoolExecutor(max_workers=4,initializer=init_graph_worker) as pool:
  rows=list(pool.map(metric_worker,[(y,mode,None) for y in range(1980,2021) for mode in ['annual','cumulative']]))
  print('Aggregation snapshots complete',flush=True)
  win=list(pool.map(metric_worker,[(y,'cumulative',width) for y in range(1990,2021) for width in [1,2,5,10]]))
 metrics=pd.DataFrame(rows);metrics.to_csv(OUT/'aggregation.csv',index=False)
 pd.DataFrame(win).to_csv(OUT/'windows.csv',index=False)
 rates=age_rates(events,nodes);nn_all,hh_all,_=age_tables(events,nodes,start=1960)
 weights=nn_all*rates[1:];expected=weights/weights.sum(1,keepdims=True)*hh_all.sum(1,keepdims=True)
 pd.DataFrame({'age':np.arange(1,61),'weight':rates[1:],'observed_hits':hh_all.sum(0),'expected_hits_conditional':expected.sum(0)}).to_csv(OUT/'p3_age_weights.csv',index=False)
 tables=pa_tables(events,nodes);alpha=pa_fit(tables);ci,boot=pa_bootstrap(tables)
 kernel_frame(tables).to_csv(OUT/'pa_kernel.csv',index=False)
 pd.DataFrame({'alpha':boot}).to_csv(OUT/'pa_bootstrap.csv',index=False)
 pa={'alpha':alpha,'ci95':ci.tolist(),'offset':1,'n_years':len(tables)}
 save_json('pa.json',pa)
 nn,hh,ys=age_tables(events,nodes);fits=age_fit(nn,hh);save_json('age_fits.json',fits)
 ex=(nn*hh.sum(1,keepdims=True)/nn.sum(1,keepdims=True)).sum(0)
 pd.DataFrame({'age':np.arange(1,61),'hits':hh.sum(0),'uniform_expected':ex,'relative_rate':np.divide(hh.sum(0),ex,out=np.full(60,np.nan),where=ex>0)}).to_csv(OUT/'age_curve.csv',index=False)
 cohorts=[]
 for lo,hi in [(1970,1989),(1990,1999),(2000,2009)]:
  n,h,y=age_tables(events,nodes,cohort=(lo,hi))
  cohorts.append({'cohort':[lo,hi],'events':int(h.sum()),'fits':age_fit(n,h)})
 save_json('age_cohorts.json',cohorts)
 den=densification(metrics);rng=np.random.default_rng(SEED)
 d=metrics[(metrics['mode']=='cumulative')&(metrics.year>=1990)]
 vals=[]
 for _ in range(1000):
  s=d.iloc[rng.integers(len(d),size=len(d))];vals.append(np.polyfit(np.log(s.N),np.log(s.E),1)[0])
 den['descriptive_year_bootstrap_ci95']=np.quantile(vals,[.025,.975]).tolist();save_json('densification.json',den)
 di=[]
 for y in range(1990,2021):
  z,nc,ns=diameter(events,nodes,y,128);di.append({'kind':'real','rep':-1,'year':y,'diameter90':z,'lcc_n':nc,'sources':ns})
 pd.DataFrame(di).to_csv(OUT/'diameter_real.csv',index=False)
 robustness=[]
 for lo,hi in [(1990,2004),(2005,2020),(1990,2015)]:
  tb=pa_tables(events,nodes,lo,hi);n,h,_=age_tables(events,nodes,lo,hi)
  robustness.append({'variant':f'years_{lo}_{hi}','alpha':pa_fit(tb),'densification':densification(metrics,lo,hi),'age_fits':age_fit(n,h)})
 for offset in [.5,2.]:robustness.append({'variant':f'pa_offset_{offset}','alpha':pa_fit(tables,offset)})
 for ns in [64,256]:
  for y in [1990,2005,2020]:
   z,nc,_=diameter(events,nodes,y,ns);robustness.append({'variant':f'diameter_sources_{ns}','year':y,'diameter90':z})
 ties=pd.read_csv(ROOT/'data/processed/CIT/same_year_events.csv')
 both=pd.concat([events,ties],ignore_index=True)
 tie_metrics=pd.DataFrame([graph_metrics(both,nodes,y,'cumulative') for y in range(1990,2021)])
 tie_metrics.to_csv(OUT/'same_year_structural_sensitivity.csv',index=False)
 robustness.append({'variant':'same_year_included_structural_only','densification':densification(tie_metrics)})
 # Independently defined core venues, no degree/citation outcome threshold.
 from cs_data import normalize
 core=nodes[nodes.venue.fillna('').map(lambda v:'journal' not in normalize(v) and any(k in normalize(v) for k in ['sigmod','vldb','very large data bases','icde','international conference on data engineering']))].copy()
 if len(core)>10:
  ce=events[events.u.isin(core.id)&events.v.isin(core.id)].copy();mapping={old:i for i,old in enumerate(core.id)}
  core.id=core.id.map(mapping);ce.u=ce.u.map(mapping);ce.v=ce.v.map(mapping)
  cm=pd.DataFrame([graph_metrics(ce,core,y,'cumulative') for y in range(1990,2021)])
  cm.to_csv(OUT/'core_venue_structural.csv',index=False)
  robustness.append({'variant':'core_venues','N':len(core),'E':len(ce),'alpha':pa_fit(pa_tables(ce,core)),'densification':densification(cm)})
 save_json('robustness.json',robustness)
 return pa,den

def run_wsb(events,nodes):
 years=nodes.year.to_numpy();hist=np.zeros((len(nodes),61),int)
 age=events.t.to_numpy()-years[events.v];np.add.at(hist,(events.v.to_numpy(),np.minimum(age,60)),1)
 cumulative=np.cumsum(hist,axis=1);rng=np.random.default_rng(SEED)
 early=nodes.year<=1989
 m=float(np.sum(events.t<=1989)/max(1,early.sum()))
 m=max(m,.1);cohort=(years>=1990)&(years<=2005)
 eligible=np.flatnonzero(cohort&(cumulative[:,5]>=5))
 ids=np.sort(rng.choice(eligible,min(500,len(eligible)),replace=False));rows=[]
 for ix,i in enumerate(ids):
  t=np.arange(1,6);c=cumulative[i,1:6];p,success,boundary=fit_wsb(t,c,m)
  rr=minimize_scalar(lambda rate:np.sum((np.log1p(m*np.expm1(np.clip(rate*t,0,30)))-np.log1p(c))**2),bounds=(0,3),method='bounded').x
  for tag,horizon in [('age15',15),('observed_endpoint',int(2020-years[i]))]:
   # Endpoint can also equal age15; keep the two evaluation labels explicitly.
   rows.append({'id':int(i),'birth_year':int(years[i]),'evaluation':tag,'horizon':horizon,'c5':int(c[-1]),'observed':int(cumulative[i,horizon]),'wsb':float(wsb(horizon,*p,m)),
    'pa_no_age':float(m*np.expm1(min(30,rr*horizon))),'linear':float(c[-1]*horizon/5),
    'lambda':p[0],'mu':p[1],'sigma':p[2],'success':success,'boundary':boundary})
  if ix%100==0:print('WSB forecasting',ix,'/',len(ids),flush=True)
 pred=pd.DataFrame(rows).drop_duplicates(['id','evaluation']);pred.to_csv(OUT/'wsb_predictions.csv',index=False)
 summaries=[]
 for ev,dd in pred.groupby('evaluation'):
  for model in ['wsb','pa_no_age','linear']:
   delta=dd[model]-dd.observed;summaries.append({'evaluation':ev,'model':model,'n':len(dd),'MAE':float(abs(delta).mean()),'median_AE':float(abs(delta).median()),'RMSLE':float(np.sqrt(np.mean((np.log1p(dd[model])-np.log1p(dd.observed))**2)))})
  for model in ['pa_no_age','linear']:
   diff=(abs(dd.wsb-dd.observed)-abs(dd[model]-dd.observed)).to_numpy()
   boot=np.array([np.mean(diff[rng.integers(len(diff),size=len(diff))]) for _ in range(1000)])
   summaries.append({'evaluation':ev,'paired_difference':'WSB minus '+model,'mean_MAE_difference':float(diff.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist()})
 # Full histories and descriptive collapse use an independently selected sample.
 elig=np.flatnonzero(cohort&(cumulative[:,15]>=10));ids2=np.sort(rng.choice(elig,min(500,len(elig)),replace=False));pars=[];collapse=[]
 for ix,i in enumerate(ids2):
  t=np.arange(1,16);c=cumulative[i,1:16];p,success,boundary=fit_wsb(t,c,m)
  pars.append({'id':int(i),'birth_year':int(years[i]),'lambda':p[0],'mu':p[1],'sigma':p[2],'success':success,'boundary':boundary,'c15':int(c[-1]),'rmsle_fit':float(np.sqrt(np.mean((np.log1p(wsb(t,*p,m))-np.log1p(c))**2))),'collapse_rmse':float(np.sqrt(np.mean((np.log1p(c/m)/p[0]-ndtr((np.log(t)-p[1])/p[2]))**2))),'collapse_max_abs_error':float(np.max(np.abs(np.log1p(c/m)/p[0]-ndtr((np.log(t)-p[1])/p[2]))))})
  for tt,cc in zip(t,c):collapse.append({'id':int(i),'scaled_time':float((np.log(tt)-p[1])/p[2]),'scaled_citations':float(np.log1p(cc/m)/p[0])})
 pd.DataFrame(pars).to_csv(OUT/'wsb_full_parameters.csv',index=False);pd.DataFrame(collapse).to_csv(OUT/'wsb_collapse.csv',index=False)
 summary={'m_fixed_pre1990':m,'n_forecast_eligible':len(eligible),'n_forecast_selected':len(ids),'n_full_eligible':len(elig),'n_full_selected':len(ids2),
 'forecast_boundary_fraction':float(pred.boundary.mean()),'full_boundary_fraction':float(pd.DataFrame(pars).boundary.mean()),'forecast_fit_success_fraction':float(pred.success.mean()),'evaluation':summaries}
 interior=pred[(~pred.boundary)&pred.success]
 summary['interior_only']=[{'evaluation':ev,'n':len(d),'wsb_MAE':float(abs(d.wsb-d.observed).mean()),'linear_MAE':float(abs(d.linear-d.observed).mean()),'PA_MAE':float(abs(d.pa_no_age-d.observed).mean())} for ev,d in interior.groupby('evaluation')]
 pp=pd.DataFrame(pars)
 summary['full_fit_diagnostics']={'median_RMSLE':float(pp.rmsle_fit.median()),'median_scaled_collapse_RMSE':float(pp.collapse_rmse.median()),'p90_scaled_collapse_RMSE':float(pp.collapse_rmse.quantile(.9)),'median_scaled_collapse_max_abs_error':float(pp.collapse_max_abs_error.median()),'parameter_medians':{x:float(pp[x].median()) for x in ['lambda','mu','sigma']},'interpretation':'Fitted-sample diagnostics only; no goodness-of-fit p-value or universal-collapse claim inferred'}
 save_json('wsb_summary.json',summary)

def summarize():
 pa=json.loads((OUT/'pa.json').read_text());den=json.loads((OUT/'densification.json').read_text());null=pd.read_csv(OUT/'null_metrics.csv');rows=[]
 for metric,value in [('pa_alpha',pa['alpha']),('densification_a',den['a'])]:
  for kind in ['P3a','P3b']:
   vals=null[null.kind==kind].alpha.to_numpy() if metric=='pa_alpha' else np.repeat(value,20)
   rows.append({'dataset':'CIT','metric':metric+'__'+kind,'value':value,'null_mean':vals.mean(),'null_std':vals.std(ddof=1)})
 events,nodes=read_data();age=float(np.mean(events.t.to_numpy()-nodes.year.to_numpy()[events.v]))
 for kind in ['P3a','P3b']:
  d=null[null.kind==kind];rows.append({'dataset':'CIT','metric':'mean_citation_age__'+kind,'value':age,'null_mean':d.mean_age.mean(),'null_std':d.mean_age.std(ddof=1)})
 diam=pd.read_csv(OUT/'diameter_real.csv');nd=pd.read_csv(OUT/'diameter_null.csv')
 for y in [1990,2005,2020]:
  value=float(diam[diam.year==y].diameter90.iloc[0])
  for kind in ['P3a','P3b']:
   d=nd[(nd.kind==kind)&(nd.year==y)].diameter90;rows.append({'dataset':'CIT','metric':f'diameter90_{y}__{kind}','value':value,'null_mean':d.mean(),'null_std':d.std(ddof=1)})
 windows=pd.read_csv(OUT/'windows.csv');sens=[]
 for metric in ['density_directed','mean_total_degree','clustering_weak','lcc_fraction']:
  vals=windows.groupby('year')[metric].agg(['min','max','mean']);v=float(((vals['max']-vals['min'])/vals['mean'].replace(0,np.nan)).mean());sens.append({'metric':metric,'sensitivity':v})
  rows.append({'dataset':'CIT','metric':'H1_window_sensitivity_'+metric,'value':v,'null_mean':np.nan,'null_std':np.nan})
 pd.DataFrame(sens).to_csv(OUT/'window_sensitivity.csv',index=False)
 ws=json.loads((OUT/'wsb_summary.json').read_text())
 for r in ws['evaluation']:
  if 'model' in r:rows.append({'dataset':'CIT','metric':f"{r['evaluation']}_{r['model']}_MAE",'value':r['MAE'],'null_mean':np.nan,'null_std':np.nan})
 pars=pd.read_csv(OUT/'wsb_full_parameters.csv')
 for param in ['lambda','mu','sigma']:
  rows.append({'dataset':'CIT','metric':'WSB_full_fit_median_'+param,'value':float(pars[param].median()),'null_mean':np.nan,'null_std':np.nan})
 af=json.loads((OUT/'age_fits.json').read_text());best=min(af,key=lambda x:x['aic'])
 rows.append({'dataset':'CIT','metric':'age_best_model_'+best['model'],'value':1.,'null_mean':np.nan,'null_std':np.nan})
 for r in af:
  rows.append({'dataset':'CIT','metric':'age_delta_AIC_'+r['model'],'value':r['aic']-best['aic'],'null_mean':np.nan,'null_std':np.nan})
 for j,value in enumerate(best['parameters']):rows.append({'dataset':'CIT','metric':f"age_best_{best['model']}_parameter_{j}",'value':value,'null_mean':np.nan,'null_std':np.nan})
 pd.DataFrame(rows).to_csv(ROOT/'results/b_summary.csv',index=False)
 significance=[]
 for kind in ['P3a','P3b']:
  d=null[null.kind==kind];significance.append({'kind':kind,'alpha_upper_p':float((1+np.sum(d.alpha>=pa['alpha']))/(len(d)+1)),
    'alpha_first10_mean':float(d.alpha.iloc[:10].mean()),'alpha_all20_mean':float(d.alpha.mean()),'mean_age_lower_p':float((1+np.sum(d.mean_age<=age))/(len(d)+1))})
 save_json('null_comparison.json',significance)

def main():
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=4);p.add_argument('--stage',default='all',choices=['all','real','null','wsb','summary']);a=p.parse_args()
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'null_events').mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
 events,nodes=read_data();print('Input',len(nodes),len(events),flush=True)
 manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data/processed/CIT').glob('*') if p.is_file()}
 save_json('processed_sha256.json',manifest)
 if a.stage in ['all','real']:run_real(events,nodes);print('Real analyses complete',flush=True)
 if a.stage in ['all','wsb']:run_wsb(events,nodes);print('WSB complete',flush=True)
 if a.stage in ['all','null']:
  results=[];di=[]
  with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
   for r,d in pool.map(one_null,[(k,i) for k in ['P3a','P3b'] for i in range(20)]):
    results.append(r);di.extend(d);print('Null complete',r['kind'],r['rep'],r['alpha'],flush=True)
    save_json('null_fits.json',results);pd.DataFrame([{k:v for k,v in r.items() if k!='age_fits'} for r in results]).to_csv(OUT/'null_metrics.csv',index=False);pd.DataFrame(di).to_csv(OUT/'diameter_null.csv',index=False)
 if a.stage in ['all','summary']:summarize()
 save_json('execution_'+a.stage+'.json',{'hostname':platform.node(),'python':sys.version,'PBS_JOBID':os.getenv('PBS_JOBID'),'stage':a.stage,'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seed':SEED})
if __name__=='__main__':main()
