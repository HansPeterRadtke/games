#!/usr/bin/env python3
"""Select CC0 side-view art from Raspberry-Pi SQLite, deploy only selected PNGs.

No external image service is required. Source remains in the larger Pi archive.
"""
import pathlib,subprocess,json,re,hashlib,shutil,os,sys,math
ROOT=pathlib.Path(__file__).resolve().parents[1]
LIBRARY=ROOT/'assets/catalog';LIBRARY.mkdir(exist_ok=True,parents=True)
SCENE_BANK=ROOT/'generated/story-region-bank.json'
MANIFEST=ROOT/'generated/semantic-asset-manifest.json'
MODULE=ROOT/'generated/semantic-asset-manifest.js'
REMOTE='raspi.lan'
REMOTE_CODE='''import sqlite3,json
c=sqlite3.connect('/data/assets/game/catalog/assets.sqlite3');rows=c.execute("SELECT pack,name,path,width,height,sha256,license,source FROM assets WHERE format='.png' AND (path LIKE '%/Side/%' OR path LIKE '%/Sprites/Tiles/Default/%' OR path LIKE '%/Previews/%') AND width>=20 AND height>=15").fetchall();print(json.dumps(rows,separators=(',',':')))'''

def ssh(*args, input=None):
 return subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=4','-o','StrictHostKeyChecking=yes',REMOTE,*args],input=input,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)

def candidates():
 data=ssh('python3','-',input=REMOTE_CODE)
 return [dict(zip(['pack','name','path','width','height','sha256','license','source'],row)) for row in json.loads(data.stdout) if row[6]=='CC0']

def normalize(txt):return set(re.findall('[a-z0-9]+',txt.lower()))

def best(rows,kind,description=''):
 aliases={
  'tree':('tree','oak','nature'),
  'rock':('rock','stone','moss'),
  'shelter':('tent','hut','house'),
  'spring':('waterfall','cliff','water'),
  'destination':('sign','direction','trail'),
  'bridge':('bridge','wood'),
 }
 if kind not in aliases:return None
 terms=set(aliases[kind]);d=normalize(description);terms|=d&set(['oak','moss','arch','tent','stone','split','cliff','fallen','river'])
 options=[]
 for row in rows:
  name=row['name'].lower();tags=normalize(name.replace('_','-'))
  matches=terms&tags
  if not matches:continue
  if kind=='spring' and 'spring' in name and 'water' not in name:continue # reject mechanical coil
  if kind=='shelter' and not tags&{'tent','hut','house'}:continue
  score=len(matches)*4 + (8 if 'nature-kit/Side/' in row['path'] else 2 if '/Side/' in row['path'] else 0)
  score+=(5 if kind=='tree' and 'oak' in tags else 0)
  score+=(4 if kind=='rock' and 'moss' in tags else 0)
  score+=(4 if kind=='spring' and 'waterfall' in name else 0)
  score+=2 if 35<=row['width']<=260 and 25<=row['height']<=250 else 0
  score-=4 if row['name'].lower().endswith(('ne','nw','se','sw')) else 0
  if kind=='destination' and 'sign' not in tags:continue
  options.append((score,row))
 return max(options,key=lambda pair:(pair[0],-len(pair[1]['name'])))[1] if options else None

def export_record(row):
 digest=row['sha256'];dest=LIBRARY/(digest[:20]+'.png')
 if not dest.exists():
  subprocess.run(['scp','-q','-B','-o','BatchMode=yes','-o','ConnectTimeout=5',REMOTE+':'+row['path'],str(dest)],timeout=30,check=True)
 data=dest.read_bytes();received=hashlib.sha256(data).hexdigest();
 if received!=digest:dest.unlink(missing_ok=True);raise RuntimeError('Asset SHA-256 mismatch')
 return {**row,'relative_path':'catalog/'+dest.name,'bytes':len(data)}

def main():
 rows=candidates();bank=json.loads(SCENE_BANK.read_text())
 requests=[{'key':'tree','kind':'tree','description':'old oak tree'},{'key':'rock','kind':'rock','description':'mossy split granite boulder'},{'key':'spring','kind':'spring','description':'spring water on rocky hillside'},{'key':'destination','kind':'destination','description':'direction signpost trail'},{'key':'shelter','kind':'shelter','description':'open woodland campsite tent'}, {'key':'bridge','kind':'bridge','description':'wooden foot bridge over water'}]
 for scene in bank.get('scenes',[]):
  for index,obj in enumerate(scene['objects']):
   requests.append({'key':f"{scene['region']}:{scene['branch']}:{index}",'kind':obj['kind'],'description':obj['name']+' '+obj['description']})
 mapping={};missing=[]
 for req in requests:
  row=best(rows,req['kind'],req['description'])
  if row is None:missing.append(req);continue
  path=export_record(row);mapping[req['key']]={'kind':req['kind'],'description':req['description'],'artifact':path}
 print('ASSET_CATALOG_SEARCH',len(rows),'eligible PNG candidates','DEPLOYED',len(mapping),'REFERENCES','MISSING',len(missing))
 content={'version':1,'license':'CC0','storage_source':'raspi.lan:/data/assets/game/catalog/assets.sqlite3','selection':mapping,'missing':missing}
 tmp=MANIFEST.with_suffix('.tmp');tmp.write_text(json.dumps(content,ensure_ascii=False,indent=2));os.replace(tmp,MANIFEST)
 text='// CC0 assets selected from Raspi SQLite, checked with SHA-256.\nexport const semanticAssetManifest='+json.dumps(content,ensure_ascii=True,separators=(',',':'))+';\n'
 tmp=MODULE.with_suffix('.tmp');tmp.write_text(text);os.replace(tmp,MODULE)
 for kind in ['tree','rock','spring','shelter','destination','bridge']:
  if kind in mapping:print(kind,mapping[kind]['artifact']['pack'],mapping[kind]['artifact']['name'],mapping[kind]['artifact']['relative_path'])
 if missing:print('MISSING',[m['key'] for m in missing])
if __name__=='__main__':main()
