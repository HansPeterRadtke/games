#!/usr/bin/env python3
"""Independent official annotation audit of grounded current-state claims.

PRSE projectors MUST NOT see this file's SceneEval gold labels. The physically
classified raw claims must already exist in private v3 output from actual
GameCore/Rapier simulation. Published results are aggregate counts only.

Matching uses the same optimistic unordered type-pair comparator as the prior
benchmark; original relation direction and instance-level semantics are not
declared verified. An unannotated physically true claim is not necessarily
a hallucination, because the external annotation coverage may be incomplete.
"""
import csv,io,zipfile,json,hashlib,collections,stat,sys,re
from pathlib import Path

R=Path(__file__).parent
version=next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith('--version=')),'v3')
if not re.fullmatch(r'v[1-9][0-9]?',version):raise ValueError('Unsafe version')
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-grounded-prose')
SOURCE=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(SOURCE) as z:
 with z.open('annotations.csv') as f:labels=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(labels)==500
REL={'next_to':'next','adjacent':'next','beside':'next','facing':'face',
 'opposite':'across','beneath':'under','side_by_side':'next','around':'surround'}
NOUN={'television':'tv','refrigerator':'fridge','bunk_bed':'bed'}
def noun(v):
 x=v.split(':')[0].strip().lower().replace(' ','_')
 return NOUN.get(x,x)
def kind(v):return REL.get(v.lower(),v.lower())
def key(k,t,a,b,ordered):
 if k=='object':
  names=[noun(a),noun(b)]
  return (k,kind(t),*(names if ordered else sorted(names)))
 return (k,kind(t),noun(a),noun(b))
def gold(row,domain,ordered):
 d=collections.Counter()
 field='OORel' if domain=='object' else 'OARel'
 for text in row[field].split(';'):
  f=[x.strip() for x in text.split(',')]
  if len(f)<(6 if domain=='object' else 5):continue
  try:n=int(f[1])
  except ValueError:continue
  if f[0]=='gt':n+=1
  if f[0] not in ('eq','ge','gt'):continue
  k=key(domain,f[2],f[4],f[5],ordered) if domain=='object' else key(domain,f[2],f[3],f[4],ordered)
  d[k]=max(d[k],n)
 return d
def sources(row,domain,ordered,truth=None):
 d=collections.Counter()
 for e in row.get('relationEvidence',[]):
  if e['kind']!=domain:continue
  if truth is not None and e['truth']!=truth:continue
  k=key(domain,e['type'],e['a'],e['b'],ordered)
  d[k]=max(d[k],1)
 return d
def intersects(a,b):return sum(min(n,b.get(k,0)) for k,n in a.items())
def run(method):
 path=PRIVATE/f'prse_grounded_prose_{method}_200_raw_{version}.json'
 assert stat.S_IMODE(path.stat().st_mode)==0o600
 raw=json.loads(path.read_text())
 assert len(raw['records'])==200
 ids=list(range(100))+list(range(100,500,4))
 assert [int(r['id']) for r in raw['records']]==ids
 assert raw['summary']['failed']==0 and raw['summary']['verifiedSceneSaves']>190
 result={}
 for domain in ('object','room'):
  for ordered in (False,True):
   subset=[]
   for selection,allids in [('human',ids[:100]),('assisted',ids[100:])]:
    sourceGold=sourceNaive=sourceTrue=sourceFalse=sourceUnknown=0
    matchingParsed=matchingVerified=matchingRefuted=0
    per=[]
    for idx,row in zip(allids,raw['records'][:100] if selection=='human' else raw['records'][100:]):
     truth=gold(labels[idx],domain,ordered)
     proposed=sources(row,domain,ordered)
     physicallyTrue=sources(row,domain,ordered,'true') if row['status']=='verified-world-and-facts' else collections.Counter()
     physicallyFalse=sources(row,domain,ordered,'false') if row['status']=='verified-world-and-facts' else collections.Counter()
     physicallyUnknown=sources(row,domain,ordered,'unknown') if row['status']=='verified-world-and-facts' else collections.Counter()
     n=intersects(truth,physicallyTrue)
     sourceGold+=sum(truth.values());sourceNaive+=sum(proposed.values())
     sourceTrue+=sum(physicallyTrue.values());sourceFalse+=sum(physicallyFalse.values())
     sourceUnknown+=sum(physicallyUnknown.values())
     matchingParsed+=intersects(truth,proposed)
     matchingVerified+=n
     matchingRefuted+=intersects(truth,physicallyFalse)
     per.append({'id':idx,'gold':sum(truth.values()),
      'naive':sum(proposed.values()),'physicallyVerified':sum(physicallyTrue.values()),
      'goldMatchedVerified':n,'goldMatchedButPhysicallyFalse':intersects(truth,physicallyFalse)})
    subset.append((selection,{
     'sourceScenes':100,'independentlyAnnotatedClaimCount':sourceGold,
     'naivelyProposedTypePairs':sourceNaive,
     'confirmedActualPhysicalTypePairs':sourceTrue,
     'refutedActualPhysicalTypePairs':sourceFalse,
     'unknownOrAmbiguousTypePairs':sourceUnknown,
     'matchedGoldBeforePhysics':matchingParsed,
     'matchedGoldAndPhysicallyVerified':matchingVerified,
     'matchedGoldButPhysicallyFalse':matchingRefuted,
     'optimisticGoldRecall':matchingVerified/sourceGold if sourceGold else 0,
     'annotationAgreementAmongPhysicalClaims':matchingVerified/sourceTrue if sourceTrue else 0
    }))
   result[domain+('_ordered' if ordered else '_unordered')]=dict(subset)
 return result,sha(path)
runs={}
for method in ('deterministic','union'):
 r,checksum=run(method)
 runs[method]={'privateRawSHA256':checksum,'sourceAudit':r}
 for src in ('human','assisted'):
  row=runs[method]['sourceAudit']['object_unordered'][src]
  print(method,src,'physical yes',row['confirmedActualPhysicalTypePairs'],
   'physically yes AND source annotated',row['matchedGoldAndPhysicallyVerified'],
   'of annotated',row['independentlyAnnotatedClaimCount'],
   'source annotations refuted by generated physics',row['matchedGoldButPhysicallyFalse'])
out={'metadata':{
 'source':'Official SceneEval-500 external annotation ZIP, independent of PRSE source scene generation',
 'sourceSHA256':sha(SOURCE),
 'unmodifiedSourceIDs':'0-99 human, 100-496 every fourth assisted',
 'annotationScope':'Type-pair labels, and conditionally ordered as encoded; no per-instance exact entailment',
 'sourceGoldNeverInGenerator':True,
 'caution':'Physically verified but unannotated relation is not automatically a hallucination; annotation omissions/ambiguity possible',
 'privateRawArtifacts':'Owner-private Nitro research folder, per-case references and exact hashes not copied to Git'},
 'version':version,'results':runs}
with (R/('prse_grounded_prose_source_annotation_audit_v3.json' if version=='v5' else
         'prse_grounded_prose_source_annotation_audit_v2.json' if version=='v4' else
         'prse_grounded_prose_source_annotation_audit_v1.json')).open('x') as f:
 json.dump(out,f,indent=2);f.write('\n')
