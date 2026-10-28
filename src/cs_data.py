"""Stream AMiner V14; retain a preregistered database-venue induced subgraph."""
import argparse, collections, csv, hashlib, io, json, re, tarfile
from pathlib import Path

VENUES = {
 'sigmod', 'sigmod conference', 'international conference on management of data',
 'proceedings of the acm sigmod international conference on management of data',
 'vldb', 'very large data bases', 'international conference on very large data bases',
 'proceedings of the vldb endowment', 'pvldb',
 'icde', 'international conference on data engineering',
 'pods', 'symposium on principles of database systems',
 'edbt', 'extending database technology',
 'icdt', 'international conference on database theory',
 'acm transactions on database systems', 'tods',
 'the vldb journal', 'vldb journal', 'data & knowledge engineering',
 'data and knowledge engineering', 'information systems',
}
def normalize(s):
 return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
VENUES = {normalize(v) for v in VENUES}
def db_venue(v):
 if isinstance(v,dict): v=v.get('raw',v.get('name',''))
 v=normalize(v)
 if v in VENUES: return True
 # Formal long names with year / conference prefix; avoid matching title/abstract.
 return any(k in v for k in ['international conference on management of data',
 'international conference on very large data bases','international conference on data engineering',
 'symposium on principles of database systems','international conference on extending database technology',
 'international conference on database theory','transactions on database systems','proceedings of the vldb endowment'])

def records(stream):
 import ijson
 # V14 uses an array; tolerate newline-delimited JSON from alternate releases.
 b=stream.read(4096); stream=io.BufferedReader(PrefixReader(b,stream))
 if b.lstrip().startswith(b'['): yield from ijson.items(stream,'item')
 else:
  for line in stream:
   line=line.strip().rstrip(b',')
   if line and line not in (b'[',b']'): yield json.loads(line)
class PrefixReader(io.RawIOBase):
 def __init__(self,prefix,rest): self.prefix=io.BytesIO(prefix); self.rest=rest
 def readable(self): return True
 def readinto(self,b):
  data=self.prefix.read(len(b))
  if not data: data=self.rest.read(len(b))
  if not data: return 0
  b[:len(data)]=data; return len(data)

def build(archive,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 counts=collections.Counter(); selected={};venue_counts=collections.Counter()
 with tarfile.open(archive,'r|gz') as tar:
  for member in tar:
   if not member.isfile() or not re.search(r'\.json(l)?$',member.name): continue
   print('Parsing',member.name,member.size,flush=True)
   for p in records(tar.extractfile(member)):
    counts['records']+=1
    if counts['records']%250000==0: print(dict(counts),flush=True)
    if not db_venue(p.get('venue','')): continue
    counts['venue_matches']+=1
    try: year=int(p.get('year',0))
    except (ValueError,TypeError): counts['invalid_year']+=1;continue
    if not 1960<=year<=2020:counts['outside_1960_2020']+=1;continue
    pid=str(p.get('id',p.get('_id','')))
    if not pid:counts['missing_id']+=1;continue
    v=p.get('venue','');v=v.get('raw',v.get('name','')) if isinstance(v,dict) else v
    if pid in selected: counts['duplicate_id']+=1;continue
    selected[pid]={'year':year,'venue':str(v),'title':p.get('title',''), 'refs':[str(r) for r in (p.get('references') or [])]}
    venue_counts[str(v)]+=1
 counts['selected_nodes']=len(selected)
 if not selected: raise RuntimeError('No matching venue records: inspect schema before proceeding')
 ids=sorted(selected,key=lambda x:(selected[x]['year'],x));mapping={v:i for i,v in enumerate(ids)}
 with (out/'nodes.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['id','original_id','year','venue','title'])
  for pid in ids:w.writerow([mapping[pid],pid,selected[pid]['year'],selected[pid]['venue'],selected[pid]['title']])
 edges=[];same=[]
 for pid in ids:
  p=selected[pid]; seen=set()
  for target in p['refs']:
   counts['selected_source_references']+=1
   if target in seen:counts['duplicate_reference']+=1;continue
   seen.add(target)
   if target not in selected:counts['target_outside_subset']+=1;continue
   if target==pid:counts['self_loop']+=1;continue
   delta=p['year']-selected[target]['year']
   if delta<0:counts['future_reference']+=1;continue
   edge=(mapping[pid],mapping[target],p['year'])
   if delta==0:same.append(edge);counts['same_year_excluded_primary']+=1;continue
   edges.append(edge)
 edges.sort(key=lambda x:(x[2],x[0],x[1]))
 for name,rows in [('events.csv',edges),('same_year_events.csv',same)]:
  with (out/name).open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['u','v','t']);w.writerows(rows)
 counts['edges']=len(edges)
 meta={'source_url':'https://originalfileserver.aminer.cn/misc/dblp_v14.tar.gz',
 'source_page':'https://www.aminer.cn/aboutus/en-US/articles/655db2202ab17a072284bc0c',
 'version':'DBLP-Citation-network V14 (2023-01-31)', 'download_date':'2026-10-27',
 'usage':'AMiner: research purpose only; no additional open-data licence inferred',
 'selection':'Database venue whitelist, induced graph; publication years 1960--2020; includes isolates',
 'venue_whitelist_normalized':sorted(VENUES),'venue_counts':dict(venue_counts),
 'counts':dict(counts),'year_min':min(p['year'] for p in selected.values()),'year_max':max(p['year'] for p in selected.values()),
 'time_rule':'t=source publication year; primary requires target.year < source.year; same-year separately saved',
 'caveats':['Induced-subfield citations, not global citation counts','Left-truncated and right-censored','Year ties cannot identify ordering','Uncited isolates retained','No assumption that metadata-reported n_citation is an observed edge count']}
 (out/'data_card.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))
 print(json.dumps(meta,indent=2,ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.archive,a.out)
