import io, json, sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from growth import *
from cs_data import records,db_venue

class CitationTests(unittest.TestCase):
 def setUp(self):
  self.nodes=pd.DataFrame({'id':range(7),'year':[1988,1989,1990,1991,1992,1993,1994]})
  self.e=pd.DataFrame([(2,0,1990),(3,0,1991),(3,1,1991),(4,0,1992),(4,2,1992),(5,1,1993),(6,0,1994),(6,2,1994)],columns=['u','v','t'])
 def test_p3_preservation_and_reproducibility(self):
  for kind in ['P3a','P3b']:
   for seed in range(10):
    a=p3(self.e,self.nodes,seed,kind,age_rates(self.e,self.nodes))
    self.assertTrue(a.groupby(['u','t']).size().equals(self.e.groupby(['u','t']).size()))
    self.assertTrue((self.nodes.year.to_numpy()[a.v]<a.t.to_numpy()).all())
    self.assertFalse(a.duplicated(['u','v']).any())
    pd.testing.assert_frame_equal(a,p3(self.e,self.nodes,seed,kind,age_rates(self.e,self.nodes)))
 def test_pa_degree_is_preyear(self):
  ts=pa_tables(self.e,self.nodes)
  np.testing.assert_array_equal(ts[0]['n'],[2]);np.testing.assert_array_equal(ts[0]['h'],[1])
  # 1991: paper 0 already has one citation, papers 1/2 have zero.
  np.testing.assert_array_equal(ts[1]['n'],[2,1]);np.testing.assert_array_equal(ts[1]['h'],[1,1])
 def test_age_exposure(self):
  n,h,y=age_tables(self.e,self.nodes,start=1990,end=1990,max_age=10)
  self.assertEqual(n[0,0],1);self.assertEqual(n[0,1],1);self.assertEqual(h[0,1],1)
 def test_diameter_path(self):
  nd=pd.DataFrame({'id':range(5),'year':[1980]*5})
  e=pd.DataFrame([(0,1,1990),(1,2,1990),(2,3,1990)],columns=['u','v','t'])
  d,n,s=diameter(e,nd,1990,samples=10)
  self.assertAlmostEqual(d,2.9);self.assertEqual(n,4);self.assertEqual(s,4)
 def test_wsb_known_history(self):
  t=np.arange(1,16);truth=[1.2,1.5,.8];c=wsb(t,*truth,5.)
  p,ok,b=fit_wsb(t,c,5.);self.assertTrue(ok);np.testing.assert_allclose(p,truth,atol=.01)
 def test_densification_invariant_under_p3(self):
  a=p3(self.e,self.nodes,9)
  for y in range(1990,1995):self.assertEqual(int(sum(a.t<=y)),int(sum(self.e.t<=y)))
 def test_parser_array_and_jsonl(self):
  objs=[{'id':1,'title':'a'}, {'id':2,'title':'b'}]
  self.assertEqual(list(records(io.BytesIO(json.dumps(objs).encode()))),objs)
  self.assertEqual(list(records(io.BytesIO(('\n'.join(map(json.dumps,objs))).encode()))),objs)
 def test_venue_no_title_matching(self):
  self.assertTrue(db_venue({'raw':'Proceedings of the VLDB Endowment'}));self.assertTrue(db_venue('SIGMOD Conference'))
  self.assertFalse(db_venue('Nature'));self.assertFalse(db_venue('Machine Learning'))
 def test_synthetic_uniform_pa(self):
  # Conditional likelihood should return zero for exactly uniform per-node hits.
  t=[{'k':np.arange(4),'n':np.array([100,60,30,10]),'h':np.array([1000,600,300,100]),'L':2000}]
  self.assertAlmostEqual(pa_fit(t),0,places=4)
 def test_streaming_build_filters(self):
  import tempfile,tarfile,contextlib
  from cs_data import build
  papers=[{'id':'a','year':1980,'venue':'SIGMOD Conference','references':[]},
   {'id':'b','year':1981,'venue':'SIGMOD Conference','references':['a','a','b','c','d','outside']},
   {'id':'c','year':1981,'venue':'SIGMOD Conference','references':[]},
   {'id':'d','year':1982,'venue':'SIGMOD Conference','references':[]},
   {'id':'x','year':1980,'venue':'Nature','references':[]}]
  with tempfile.TemporaryDirectory() as tmp:
   archive=Path(tmp)/'data.tgz';blob=json.dumps(papers).encode()
   with tarfile.open(archive,'w:gz') as tar:
    info=tarfile.TarInfo('papers.json');info.size=len(blob);tar.addfile(info,io.BytesIO(blob))
   with contextlib.redirect_stdout(io.StringIO()):build(archive,Path(tmp)/'out')
   d=Path(tmp)/'out';meta=json.loads((d/'data_card.json').read_text())
   self.assertEqual(meta['counts']['selected_nodes'],4);self.assertEqual(meta['counts']['edges'],1)
   self.assertEqual(meta['counts']['same_year_excluded_primary'],1);self.assertEqual(meta['counts']['future_reference'],1)
   self.assertEqual(meta['counts']['self_loop'],1);self.assertEqual(meta['counts']['duplicate_reference'],1)
 def test_known_attachment_exponent(self):
  k=np.arange(6);n=np.array([100,60,30,20,10,5]);h=np.round(10000*n*(k+1)**1.2).astype(int)
  t=[{'k':k,'n':n,'h':h,'L':int(h.sum())}]
  self.assertAlmostEqual(pa_fit(t),1.2,places=4)
 def test_known_densification(self):
  n=np.arange(10,41,dtype=float)
  d=pd.DataFrame({'year':np.arange(1990,2021),'mode':'cumulative','N':n,'E':n**1.5})
  self.assertAlmostEqual(densification(d)['a'],1.5,places=10)
 def test_age_null_uses_year_specific_normalizers(self):
  n,h,_=age_tables(self.e,self.nodes,start=1960)
  exposure=(n*h.sum(1,keepdims=True)/n.sum(1,keepdims=True)).sum(0)
  pooled=np.divide(h.sum(0),exposure,out=np.full(60,1e-12),where=exposure>0)
  pooled=np.maximum(pooled,1e-12)
  fitted=age_rates(self.e,self.nodes)[1:]
  def ll(w):return float(np.sum(h*np.log(w))-np.dot(h.sum(1),np.log(n@w)))
  self.assertGreaterEqual(ll(fitted)+1e-6,ll(pooled))
if __name__=='__main__':unittest.main()
