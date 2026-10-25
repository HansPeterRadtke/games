#!/usr/bin/env python3
"""Official independent gold audit of the ALREADY FROZEN extra native GameCore
3D bodies proposed by the pretrained open-vocabulary noun extractor.

The body layout, counts, source text, source spans and all native Rapier saves
were completed WITHOUT loading official author labels. This script is only
a scorer and cannot alter the frozen candidate model or physics.

Generic fallback collider dimensions are intentionally NOT counted as
credible physical objects or matching source attributes/relations.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter
import csv,io,zipfile,json
R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery')
DATA=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance/prse_source_quantity_physics_200_raw_v1.json')
NEW=PRIVATE/'prse_spacy_open_vocab_native_200_raw_v1.json'
TEXT=PRIVATE/'prse_spacy_open_vocab_500_proposals_raw_v1.json'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert sha(DATA)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(DATA) as z:
 with z.open('annotations.csv') as f:labels=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(labels)==500
for file in (BASE,NEW,TEXT):assert S_IMODE(file.stat().st_mode)==0o600
original=load(BASE)['results'];added=load(NEW)['records']
ids=list(range(100))+list(range(100,500,4))
assert [a['sourceID'] for a in original]==ids
assert [a['sourceID'] for a in added]==ids
def normalize(s):
 k=s.strip().lower().replace(' ','_')
 return {'television':'tv','refrigerator':'fridge','bunk_bed':'bed',
  'bedside_lamp':'lamp'}.get(k,k)
def gclaim(row):
 out=[]
 for item in row['ObjCount'].split(';'):
  vals=[x.strip() for x in item.split(',')]
  if len(vals)<3:continue
  try:n=int(vals[1])
  except ValueError:continue
  if vals[0] in ('eq','ge','gt'):out.append((normalize(vals[2]),vals[0],n))
 return out
def true(n,op,g):
 return n==g if op=='eq' else n>=g if op=='ge' else n>g
sums={x:Counter() for x in ['human','assisted']}
privateRecords=[]
for baseline,revised in zip(original,added):
 id=baseline['sourceID'];group='human' if id<100 else 'assisted'
 z=sums[group];z['sourceScenes']+=1
 if revised['status']!='native_saved_and_reentered':
  z['physicalSceneUnacceptedOrFailure']+=1
  z['unverifiedSourceClauses']+=len(gclaim(labels[id]))
  privateRecords.append({'id':id,'status':revised['status']})
  continue
 if baseline['status']!='native_3d_verified':
  raise ValueError('Augmented accepted a source not accepted in frozen baseline')
 old={normalize(x['type']):x['materialized'] for x in baseline['physicalTypeCounts']}
 new={normalize(k):n for k,n in revised['finalPhysicalCounts'].items()}
 assert all(new.get(k,0)>=n for k,n in old.items()),'Previously real physical bodies were lost'
 assert revised['sourceHistoricTextUnchanged'] and revised['originalIDsUnaffected']
 assert revised['addedActuallyNativePhysicalBodies']==revised['added']
 official=gclaim(labels[id])
 groundTypes={kind for kind,op,n in official}
 candidates=revised['addedProvenance']
 addedTypes={normalize(r['kind']) for r in candidates}
 z['acceptedScenes']+=1
 z['nativeGenericExtraBodies']+=revised['added']
 z['extraTypeInstances']+=len(addedTypes)
 z['extraCandidateTypesInAuthorLabels']+=len(addedTypes&groundTypes)
 z['extraCandidateTypesNotAuthorAnnotated']+=len(addedTypes-groundTypes)
 z['unverifiedPhysicalDimensionsAndAppearance']+=revised['added']
 z['annotationCountClauses']+=len(official)
 before=after=corrected=broken=0
 for k,op,g in official:
  a=true(old.get(k,0),op,g);b=true(new.get(k,0),op,g)
  before+=a;after+=b
  corrected+=(not a and b)
  broken+=(a and not b)
  if k not in old and k in addedTypes and b:z['fromPreviouslyUnknownPhysicalKindsNowGoldMatched']+=1
  if not b:
   z['goldStillUnsatisfied']+=1
   if new.get(k,0)<g:z['stillUndercounted']+=1
 z['baselineGoldClausesMatched']+=before
 z['augmentedGoldClausesMatched']+=after
 z['formerlyIncorrectNowCorrect']+=corrected
 z['formerlyCorrectNowBroken']+=broken
 privateRecords.append({'id':id,'original':old,'actualAugmentedNativeCounts':new,
  'officialSourceCount':official,'goldMatchedBefore':before,'goldMatchedAfter':after,
  'addedCandidate3DPlaceholders':candidates,
  'unannotatedExtraKindProposals':sorted(addedTypes-groundTypes)})
total=Counter()
for row in sums.values():total.update(row)
private=PRIVATE/'prse_spacy_open_vocab_native_independent_gold_cases_v1.json'
with private.open('x') as f:json.dump({'meta':{
 'score':'Only official SceneEval author count labels, separately from real 3D native saved worlds',
 'warning':'Extra generic boxes are correct native physics counts but NOT calibrated 3D objects'},
 'cases':privateRecords},f,indent=2);f.write('\n')
private.chmod(0o600)
out={'meta':{
 'authorSceneEvalSHA256':sha(DATA),
 'baselineFrozenNativeSHA256':sha(BASE),
 'frozenPretrainedNounProposalSHA256':sha(TEXT),
 'frozenNativeAugmentedWorldSHA256':sha(NEW),
 'privateFullGoldAuditSHA256':sha(private),
 'sameSourceIds':True,
 'physicalWorld':'Real existing PRSE GameCore/Rapier rigid bodies + trusted native full-world save',
 'model':'Pretrained spaCy en_core_web_sm 3.8.0 plus transparent generic noun-chunk/compound heuristics, NOT a language generative LLM',
 'epistemicLimit':'Unknown noun types represented by tiny generic fallback box; correctness only count/category proxy, NOT physically faithful geometry/asset/affordance/relations, no original literary rewriting',
 'noGoldDuringSourceNounExtractionOrPhysicalMaterialization':True},
 'groups':{k:dict(v) for k,v in sums.items()},'total':dict(total)}
public=R/'prse_spacy_open_vocab_native_gold_200_aggregate_v1.json'
with public.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for k,r in sums.items():
 print(k,'native accepted',r['acceptedScenes'],'gold clauses',r['annotationCountClauses'],
 'baseline',r['baselineGoldClausesMatched'],'augmented',r['augmentedGoldClausesMatched'],
 'corrected',r['formerlyIncorrectNowCorrect'],'previously correct broken',r['formerlyCorrectNowBroken'],
 'unannotated new candidate types',r['extraCandidateTypesNotAuthorAnnotated'])
print('COMBINED',dict(total))
