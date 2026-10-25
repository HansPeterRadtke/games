#!/usr/bin/env python3
"""Independent official SceneEval-500 count/attribute annotation audit AFTER
the frozen PRSE source-proposal -> actual GameCore/Rapier physical output.

This scorer is the ONLY place that reads independent author gold. Neither
quantifier projection nor the physics compiler sees these labels.

Counts are exact/at-least/greater-than *within the annotated scene*.
Unknown geometry/scene rejection remains UNKNOWN, not counted as a negative.
A physically counted compiler-produced object is not independent validation
that a source sentence referred to that object.
"""
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
import csv,io,zipfile,json,stat

R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert digest(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
raw=PRIVATE/'prse_source_quantity_physics_200_raw_v1.json'
assert raw.exists() and stat.S_IMODE(raw.stat().st_mode)==0o600
observed=read(raw)
frozen=read(FROZEN)['proposalsAll500']
assert len(frozen)==500
ids=list(range(100))+list(range(100,500,4))
assert [r['sourceID'] for r in observed['results']]==ids
def canonical(k):
 v=k.lower().replace(' ','_')
 return {'television':'tv','bunk_bed':'bed','refrigerator':'fridge',
   'bedside_lamp':'lamp'}.get(v,v)
def gold_rows(field):
 claims=[]
 for part in field.split(';'):
  f=[x.strip() for x in part.strip().split(',')]
  if len(f)<3:continue
  try:n=int(f[1])
  except ValueError:continue
  if f[0] not in ('eq','ge','gt'):continue
  claims.append({'type':canonical(f[2]),'op':f[0],'num':n,
   'attribute':f[3] if len(f)>3 else None})
 return claims
def correct(op,n,current):
 if op=='eq':return current==n
 if op=='ge':return current>=n
 if op=='gt':return current>n
 return None
def attrEquivalent(a,b):
 x=a.lower().replace(' ','_');y=b.lower().replace(' ','_')
 lookup={'wood':'wooden','gray':'grey','king_size':'king_size','big':'large'}
 return lookup.get(x,x)==lookup.get(y,y)
perCase=[]
metrics=defaultdict(Counter)
for id,one in zip(ids,observed['results']):
 p=frozen[id]
 assert p['text']==rows[id]['Description']
 group='human100' if id<100 else 'assisted100'
 goldCount=gold_rows(rows[id]['ObjCount'])
 goldAttr=gold_rows(rows[id]['ObjAttr'])
 valid=one['status']=='native_3d_verified'
 typeCounts={canonical(x['type']):x['materialized'] for x in one.get('physicalTypeCounts',[])}
 parsedCounts={canonical(k):(v['op'],v['count']) for k,v in p['quantities'].items()}
 predAttrs=defaultdict(set)
 for m in p['mentions']:
  predAttrs[canonical(m['type'])].update(m['attributes'])
 actual=metrics[group]
 actual['descriptions']+=1
 if not valid:
  actual['physicalSceneRejectedOrFailed']+=1
  actual['independentlyAnnotatedCountClausesUnableToCheck']+=len(goldCount)
  actual['independentlyAnnotatedAttributeClausesUnableToCheck']+=len(goldAttr)
  perCase.append({'id':id,'subset':group,'status':one['status'],
   'goldCountClauses':len(goldCount),'unverified':'not_materialized'})
  continue
 actual['physicallyValidatedScenes']+=1
 entry={'id':id,'subset':group,'status':one['status'],'countClaims':[],
  'attributes':[]}
 for goldClaim in goldCount:
  k=goldClaim['type'];actualN=typeCounts.get(k,0)
  answer=correct(goldClaim['op'],goldClaim['num'],actualN)
  naive=parsedCounts.get(k)
  parsedAnswer=(naive is not None and
      correct(goldClaim['op'],goldClaim['num'],
       naive[1]+(1 if naive[0]=='gt' else 0)))
  actual['goldCountClauses']+=1
  if answer:actual['goldCountSatisfiedByPhysicalWorld']+=1
  else:
   actual['goldCountContradictedByPhysicalWorld']+=1
   if goldClaim['num']>actualN:actual['goldPhysicalUnderCount']+=1
   elif goldClaim['num']<actualN:actual['goldPhysicalOverCount']+=1
  if parsedAnswer:actual['goldCountSatisfiedBySourceLexicalProposal']+=1
  if k in parsedCounts:actual['goldCountClausesWithRecognizedNoun']+=1
  if goldClaim['num']==0:
   actual['goldExplicitZeroClaims']+=1
   if answer:actual['goldExplicitZeroPhysicallySatisfied']+=1
   if naive and naive[1]==0:actual['goldExplicitZeroParsedAsAbsence']+=1
   if naive and naive[1]==0 and answer:
    actual['goldExplicitZeroParsedAndPhysicallySatisfied']+=1
  entry['countClaims'].append({'kind':k,'goldNum':goldClaim['num'],
   'goldOperator':goldClaim['op'],'physicalNum':actualN,
   'physicalSatisfied':answer,'parserCount':naive,'parserClauseAlsoCompatible':bool(parsedAnswer)})
 for claim in goldAttr:
  typ=claim['type'];found=any(attrEquivalent(a,claim['attribute']) for a in predAttrs[typ])
  actual['goldAttributeClauses']+=1
  if found:actual['lexicalAttributeMatchesGold']+=1
  entry['attributes'].append({'type':typ,'attribute':claim['attribute'],
   'parsedSourceAttributeMatches':found,
   'independentlyPhysicsValidated':False,
   'reason':'Material, visual color, appearance and geometry were source-derived approximations, not independent measured properties.'})
 perCase.append(entry)
combined=Counter()
for s in metrics.values():combined.update(s)
safe={'metadata':{
 'source':'Official SceneEval-500 annotated ObjCount and ObjAttr, only loaded after original source/physics predictions frozen',
 'sourceSha256':digest(GOLD),'frozenParserProposalSha256':digest(FROZEN),
 'frozenPhysicsRawSha256':digest(raw),
 "countSemantics": "Gold eq/ge/gt interpreted as within-scene type count; the source parser's eq may not mean exhaustive universe closure",
 'attributeCaveat':'Attributes guessed from source text or assigned by same compiler are not independent physical/visual verification',
 'unsupported':'No semantic source coreference, negation scope, full scene entailment or human evaluation is claimed',
 'humanAndAssistedSampling':'Same first100 human and every4th 100 from assisted400 source data'},
 'splits':{k:dict(v) for k,v in metrics.items()},'combined':dict(combined)}
file=PRIVATE/'prse_source_quantity_official_gold_per_case_v1.json'
with file.open('x') as f:json.dump({'metadata':safe['metadata'],'cases':perCase},f,indent=2);f.write('\n')
file.chmod(0o600)
safe['metadata']['privateGoldAuditRawSHA256']=digest(file)
safe['metadata']['privateGoldAuditRawFile']=str(file)
pub=R/'prse_source_quantity_official_gold_200_aggregate_v1.json'
with pub.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
for split in ('human100','assisted100'):
 m=metrics[split]
 print(split,'accepted',m['physicallyValidatedScenes'],
  'gold count clauses',m['goldCountClauses'],
  'physical matches',m['goldCountSatisfiedByPhysicalWorld'],
  'mismatches',m['goldCountContradictedByPhysicalWorld'],
  'parser supports',m['goldCountSatisfiedBySourceLexicalProposal'],
  'gold attr clauses',m['goldAttributeClauses'],
  'text attr candidate matches',m['lexicalAttributeMatchesGold'])
print('total',dict(combined))
