"""Citation growth estimators and degree/age selective reference models.
All target risk sets are frozen at the start of the citing year.
"""
import numpy as np
import pandas as pd
import networkx as nx
from scipy.optimize import minimize, minimize_scalar, least_squares
from scipy.special import logsumexp, ndtr, gammaln
from scipy.sparse.csgraph import shortest_path

SEED=5253

def p3(events, nodes, seed, kind='P3a', age_rates=None):
 """Preserve source, year, distinct reference count; older targets, no loops.
 P3b samples targets with pooled exposure-adjusted age weights, without degree.
 Weighted rejection implements successive sampling without replacement.
 """
 rng=np.random.default_rng(seed); years=nodes.set_index('id')['year'].sort_index().to_numpy()
 groups={y:np.flatnonzero(years==y) for y in np.unique(years)}
 result=[]
 for y,part in events.groupby('t',sort=True):
  eligible=np.flatnonzero(years<y)
  gy=np.array([z for z in groups if z<y]); gn=np.array([len(groups[z]) for z in gy])
  if kind=='P3b':
   weights=gn*np.maximum(age_rates[np.minimum(y-gy,len(age_rates)-1)],1e-12)
   weights=weights/weights.sum()
  for u,d in part.groupby('u',sort=True).size().items():
   if d>len(eligible):raise ValueError('Reference count exceeds risk set')
   if kind=='P3a': targets=rng.choice(eligible,size=d,replace=False)
   else:
    chosen=set()
    while len(chosen)<d:
     yy=rng.choice(gy,size=max(8,2*(d-len(chosen))),p=weights)
     for z in yy:
      pool=groups[z];chosen.add(int(pool[rng.integers(len(pool))]))
      if len(chosen)==d:break
    targets=sorted(chosen)
   result.extend((int(u),int(v),int(y)) for v in targets)
 return pd.DataFrame(result,columns=['u','v','t']).astype('int64')

def pa_tables(events,nodes,start=1990,end=2020,offset=1.):
 years=nodes.sort_values('id')['year'].to_numpy();degree=np.zeros(len(nodes),int); tables=[]
 for y in sorted(events.t.unique()):
  e=events[events.t==y];eligible=np.flatnonzero(years<y)
  if start<=y<=end and len(eligible):
   k=degree[eligible];n=np.bincount(k);h=np.bincount(degree[e.v],minlength=len(n))[:len(n)]
   tables.append({'year':int(y),'n':n,'h':h,'k':np.arange(len(n)),'L':len(e)})
  np.add.at(degree,e.v,1)
 return tables

def pa_fit(tables,offset=1.):
 if not tables:return np.nan
 def nll(alpha):
  val=0.
  for t in tables:
   mask=t['n']>0;x=np.log(t['k'][mask]+offset);h=t['h'][mask];ln=np.log(t['n'][mask])
   val+=t['L']*logsumexp(ln+alpha*x)-np.dot(h,alpha*x)
  return val
 return float(minimize_scalar(nll,bounds=(-2,3),method='bounded').x)

def pa_bootstrap(tables,n=400,seed=SEED):
 rng=np.random.default_rng(seed)
 vals=[pa_fit([tables[i] for i in rng.integers(len(tables),size=len(tables))]) for _ in range(n)]
 return np.quantile(vals,[.025,.975]),np.array(vals)

def kernel_frame(tables):
 n=max(len(t['n']) for t in tables);h=np.zeros(n);ex=np.zeros(n)
 for t in tables:
  m=len(t['n']);h[:m]+=t['h'];ex[:m]+=t['n']*t['L']/t['n'].sum()
 return pd.DataFrame({'k':np.arange(n),'hits':h,'uniform_expected':ex,'relative_rate':np.divide(h,ex,out=np.zeros(n),where=ex>0)})

def age_tables(events,nodes,start=1990,end=2020,cohort=None,max_age=60):
 years=nodes.sort_values('id')['year'].to_numpy();nmat=[];hmat=[];ys=[]
 for y in sorted(events.t.unique()):
  if not start<=y<=end:continue
  eligible=(years<y)&(y-years<=max_age)
  if cohort is not None:eligible&=(years>=cohort[0])&(years<=cohort[1])
  e=events[events.t==y];targets=e.v.to_numpy();keep=eligible[targets];ages=y-years[targets[keep]]
  nn=np.bincount((y-years[eligible]).astype(int),minlength=max_age+1)[1:max_age+1]
  hh=np.bincount(ages.astype(int),minlength=max_age+1)[1:max_age+1]
  if hh.sum() and nn.sum():nmat.append(nn);hmat.append(hh);ys.append(y)
 return np.array(nmat),np.array(hmat),np.array(ys)

def age_fit(n,h):
 ages=np.arange(1,n.shape[1]+1);la=np.log(ages)
 def logshape(model,p):
  if model=='lognormal':return -la-np.log(p[1])-.5*((la-p[0])/p[1])**2
  if model=='exponential':return -p[0]*ages
  if model=='powerlaw':return -p[0]*la
  return np.zeros_like(ages,dtype=float)
 def likelihood(model,p):
  lf=logshape(model,p);logw=np.log(np.maximum(n,1e-300))+lf
  return float(np.sum(h*lf)-np.dot(h.sum(axis=1),logsumexp(logw,axis=1)))
 rows=[]
 for model,p0,bounds in [('lognormal',[1.5,1.],[( -3,5),(.15,4)]),('exponential',[.1],[(0,3)]),('powerlaw',[1.],[(0,5)]),('uniform',[],[])]:
  if p0:
   r=minimize(lambda p:-likelihood(model,p),p0,bounds=bounds);p=r.x;ok=r.success
  else:p=np.array([]);ok=True
  ll=likelihood(model,p);rows.append({'model':model,'parameters':p.tolist(),'loglik':ll,'aic':2*len(p)-2*ll,'success':bool(ok)})
 return rows

def age_rates(events,nodes):
 """Fit a nonparametric age-only choice kernel conditional on citing year.
 Pooled exposure ratios initialize the fit; year-specific normalizers are
 then optimized rather than assuming that a pooled ratio preserves ages.
 """
 n,h,_=age_tables(events,nodes,start=1960,max_age=60)
 totals=h.sum(axis=1);hits=h.sum(axis=0)
 exposure=(n*totals[:,None]/np.maximum(n.sum(axis=1,keepdims=True),1)).sum(axis=0)
 rate=np.divide(hits,exposure,out=np.full(60,1e-12),where=exposure>0)
 anchor=int(np.argmax(hits));free=np.array([i for i in range(60) if i!=anchor])
 logn=np.full(n.shape,-np.inf);np.log(n,out=logn,where=n>0)
 initial=np.log(np.maximum(rate,1e-12));initial-=initial[anchor]
 def objective(v):
  lw=np.zeros(60);lw[free]=v
  ln=logn+lw;normalizer=logsumexp(ln,axis=1)
  value=np.dot(totals,normalizer)-np.dot(hits,lw)
  grad=(totals[:,None]*np.exp(ln-normalizer[:,None])).sum(axis=0)-hits
  return value,grad[free]
 result=minimize(objective,np.clip(initial[free],-25,25),jac=True,method='L-BFGS-B',bounds=[(-25,25)]*59,options={'maxiter':1000,'ftol':1e-12,'gtol':1e-6})
 if not result.success:raise RuntimeError('Age-only null calibration failed: '+str(result.message))
 lw=np.zeros(60);lw[free]=result.x
 return np.r_[0,np.exp(lw)]

def graph_metrics(events,nodes,year,mode='cumulative',cluster=True):
 es=events[events.t<=year] if mode=='cumulative' else events[events.t==year]
 ns=nodes[nodes.year<=year].id.to_numpy()
 # Common born-node denominator makes annual/cumulative density comparable.
 g=nx.Graph();g.add_nodes_from(ns);g.add_edges_from(es[['u','v']].itertuples(index=False,name=None))
 comps=list(nx.connected_components(g));big=max(map(len,comps),default=0)
 return {'year':year,'mode':mode,'N':len(g),'E':len(es),'density_directed':len(es)/max(1,len(g)*(len(g)-1)),
 'mean_total_degree':2*len(es)/max(1,len(g)),'clustering_weak':nx.average_clustering(g) if cluster else np.nan,
 'weak_components':len(comps),'lcc_fraction':big/max(1,len(g))}

def diameter(events,nodes,year,samples=128,seed=SEED):
 e=events[events.t<=year];g=nx.Graph();g.add_nodes_from(nodes[nodes.year<=year].id);g.add_edges_from(e[['u','v']].itertuples(index=False,name=None))
 big=sorted(max(nx.connected_components(g),key=len));sub=g.subgraph(big)
 if len(big)<2:return np.nan,len(big),0
 rng=np.random.default_rng(seed+int(year));idx=rng.choice(len(big),min(samples,len(big)),replace=False)
 a=nx.to_scipy_sparse_array(sub,nodelist=big,format='csr',dtype=np.float64)
 # scipy 1.13 csgraph requires int32 sparse indices.
 a.indices=a.indices.astype(np.int32);a.indptr=a.indptr.astype(np.int32)
 d=shortest_path(a,directed=False,unweighted=True,indices=idx)
 d=d[np.isfinite(d)&(d>0)]
 return float(np.quantile(d,.9)),len(big),len(idx)

def densification(metrics,start=1990,end=2020):
 d=metrics[(metrics['year']>=start)&(metrics['year']<=end)&(metrics['mode']=='cumulative')&(metrics.E>0)&(metrics.N>1)]
 x=np.log(d.N.to_numpy());y=np.log(d.E.to_numpy());p=np.polyfit(x,y,1);pred=np.polyval(p,x)
 return {'a':float(p[0]),'intercept':float(p[1]),'r2':float(1-np.sum((y-pred)**2)/np.sum((y-y.mean())**2)),'n_years':len(d),'start':start,'end':end}

def wsb(t,lam,mu,sigma,m):
 return m*np.expm1(np.clip(lam*ndtr((np.log(np.maximum(t,1e-10))-mu)/sigma),0,30))

def fit_wsb(t,c,m):
 best=None
 for mu in [0.,1.5,3.]:
  r=least_squares(lambda p:np.log1p(wsb(t,*p,m))-np.log1p(c),[max(.1,np.log1p(c[-1]/m)),mu,1.],bounds=([.0001,-3,.2],[10,5,3]),max_nfev=500)
  if best is None or np.dot(r.fun,r.fun)<np.dot(best.fun,best.fun):best=r
 boundary=bool(np.any(best.x-np.array([.0001,-3,.2])<1e-3) or np.any(np.array([10,5,3])-best.x<1e-3))
 return best.x,bool(best.success),boundary
