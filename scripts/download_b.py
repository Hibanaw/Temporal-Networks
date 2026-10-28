"""Resumable, validated HTTP Range downloader, bounded memory."""
import concurrent.futures, hashlib, json, math, os, shutil, time, urllib.request
from pathlib import Path
URL='https://originalfileserver.aminer.cn/misc/dblp_v14.tar.gz'
SIZE=6079589707
EXPECTED_SHA256="729cc2c107d8abbe586d9801340246fd94e94d916ba1cebe64dd93a399f0cd28"
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'data/raw/dblp_v14.tar.gz';parts=ROOT/'data/raw/dblp_v14.parts8';parts.mkdir(parents=True,exist_ok=True)
CHUNK=8*1024*1024

def fetch(i):
 lo=i*CHUNK;hi=min(SIZE,(i+1)*CHUNK)-1;p=parts/f'{i:04d}.part';done=p.stat().st_size if p.exists() else 0
 if done==hi-lo+1:return i
 if done>hi-lo+1:raise RuntimeError('Oversized download part')
 for attempt in range(10):
  try:
   done=p.stat().st_size if p.exists() else 0
   if done==hi-lo+1:return i
   req=urllib.request.Request(URL,headers={'Range':f'bytes={lo+done}-{hi}','User-Agent':'PC5253 academic research download'})
   with urllib.request.urlopen(req,timeout=90) as r:
    if r.status!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {lo+done}-'):raise RuntimeError(f'Invalid range response {r.status} {r.headers}')
    with p.open('ab') as f:
     while True:
      b=r.read(256*1024)
      if not b:break
      f.write(b)
   if p.stat().st_size!=hi-lo+1:raise RuntimeError('Incomplete part')
   print('complete',i,flush=True);return i
  except Exception as exc:
   print('retry',i,attempt,str(exc),flush=True);time.sleep(min(30,2**attempt))
 raise RuntimeError(f'Unable to download part {i}')
if __name__=='__main__':
 # Reuse validated bytes from the initial 64 MB attempt; never discard progress.
 legacy=ROOT/'data/raw/dblp_v14.parts'
 for old in sorted(legacy.glob('*.part')):
  old_index=int(old.stem)
  with old.open('rb') as source:
   j=0
   while True:
    b=source.read(CHUNK)
    if not b:break
    dest=parts/f'{old_index*8+j:04d}.part'
    if not dest.exists() or dest.stat().st_size<len(b):dest.write_bytes(b)
    j+=1
 if not out.exists() or out.stat().st_size!=SIZE:
  with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:list(pool.map(fetch,range(math.ceil(SIZE/CHUNK))))
  temp=out.with_suffix('.assembling')
  with temp.open('wb') as f:
   for p in sorted(parts.glob('*.part')):
    with p.open('rb') as r:shutil.copyfileobj(r,f,1024*1024)
  if temp.stat().st_size!=SIZE:raise RuntimeError('Wrong assembled size')
  os.replace(temp,out)
 h=hashlib.sha256()
 with out.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 if h.hexdigest()!=EXPECTED_SHA256:raise RuntimeError('V14 corpus checksum differs from the archived experiment version')
 (ROOT/'results/b/raw_sha256.txt').write_text(f'{h.hexdigest()}  data/raw/dblp_v14.tar.gz\n')
 (ROOT/'results/b/download.json').write_text(json.dumps({'url':URL,'size':SIZE,'sha256':h.hexdigest(),'etag':'63d8c912-16a5f2d4b','last_modified':'2023-01-31T07:53:54Z'},indent=2))
