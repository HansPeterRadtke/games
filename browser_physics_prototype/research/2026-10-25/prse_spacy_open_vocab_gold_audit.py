#!/usr/bin/env python3
"""INDEPENDENT SceneEval author-label scorer for PREVIOUSLY FROZEN CPU-only
spaCy noun-chunk candidate proposals, and the exact earlier GameCore baseline.

Gold labels are loaded HERE ONLY. They cannot change the parser, its noun
ontology, phrase boundaries, count values, or frozen 500-scene predictions.

Measures both improved annotation recall and unsupported extra type proposals.
An object type missing from the published annotations is NOT necessarily a
hallucination; coverage and type precision are corpus-proxy diagnostics.
No new physical scene is declared valid by this text-only candidate scorer.
"""
import csv,io,json,zipfile
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
from stat import S_IMODE

ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance/prse_source_quantity_physics_200_raw_v1.json')
SOURCE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
PRED=PRIVATE/'prse_spacy_open_vocab_500_proposals_raw_v1.json'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert digest(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert PRED.exists() and S_IMODE(PRED.stat().st_mode)==0o600
assert load(PRED)['summary']['sourceSHA256']==digest(SOURCE)
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
base=load(BASE)['results'];pred=load(PRED)['records']
ids=list(range(100))+list(range(100,500,4))
assert len(pred)==500 and [int(x['id']) for x in pred]==list(range(500))
assert [x['sourceID'] for x in base]==ids
def canon(x):
 k=x.strip().lower().replace(' ','_')
 return {'television':'tv','refrigerator':'fridge','bunk_bed':'bed','bedside_lamp':'lamp'}.get(k,k)
def parse_gold(s):
 out=[]
 for term in s.split(';'):
  bits=[x.strip() for x in term.split(',')]
  if len(bits)<3:continue
  try:n=int(bits[1])
  except ValueError:continue
  if bits[0] not in ('eq','ge','gt'):continue
  out.append((canon(bits[2]),bits[0],n))
 return out
def supports(n,op,g):
 return n==g if op=='eq' else n>=g if op=='ge' else n>g
rows=[]
stats={k:Counter() for k in ('human100','assisted100')}
types=Counter()
for id,b in zip(ids,base):
 if b['status']!='native_3d_verified':continue
 k='human100' if id<100 else 'assisted100'
 source=pred[id]
 assert source['sourceText']==gold[id]['Description']
 original={canon(x['type']):x['materialized'] for x in b['physicalTypeCounts']}
 after=dict(original)
 for cand in source['boundedNewTypes']:
  typ=canon(cand['type'])
  after[typ]=max(after.get(typ,0),cand['count'])
 g=parse_gold(gold[id]['ObjCount'])
 goals={q[0] for q in g}
 matchedBefore=matchedAfter=0
 for typ,op,n in g:
  bb=supports(original.get(typ,0),op,n)
  aa=supports(after.get(typ,0),op,n)
  matchedBefore+=bb;matchedAfter+=aa
  if not bb and aa:types[typ]+=1
 extraTypes={typ for typ,n in after.items() if n>0 and original.get(typ,0)==0}
 recognized=sum(typ in goals for typ in extraTypes)
 agg=stats[k]
 agg['acceptedOriginalScenes']+=1
 agg['goldRequirements']+=len(g)
 agg['matchedGoldByExisting3D']+=matchedBefore
 agg['matchedGoldBySourceNounCandidateOnly']+=matchedAfter
 agg['goldCorrectionsSuggestedBySyntax']+=sum(not supports(original.get(typ,0),op,n) and supports(after.get(typ,0),op,n) for typ,op,n in g)
 agg['goldPreviouslySatisfiedNowContradicted']+=sum(supports(original.get(typ,0),op,n) and not supports(after.get(typ,0),op,n) for typ,op,n in g)
 agg['additionalPositiveTypeProposals']+=len(extraTypes)
 agg['additionalTypeProposalsPresentInAuthorLabel']+=recognized
 agg['additionalTypesNotInAuthorLabels']+=len(extraTypes)-recognized
 agg['numberCandidatePhysicalBodiesNeeded']+=sum(max(0,n-original.get(typ,0)) for typ,n in after.items())
 agg['sourceScenesWithNewCandidates']+=bool(source['boundedNewTypes'])
 rows.append({'id':id,'status':'analyzed','sourceSubset':k,
  'candidateTypes':source['boundedNewTypes'],
  'textOriginal':source['sourceText'],
  'physicalOriginalCounts':original,
  'proposedAugmentedCounts':after,
  'officialGoldCounts':g,
  'goldMatchedOriginal':matchedBefore,
  'goldMatchedHypothetical':matchedAfter,
  'unverifiedTypesOutsidePublishedLabels':list(extraTypes-goals)})
combined=Counter()
for v in stats.values():combined.update(v)
private=PRIVATE/'prse_spacy_open_vocab_independent_gold_per_case_v1.json'
with private.open('x') as f:json.dump({'meta':{
 'source':'Original annotated SceneEval-500 ObjCount author labels, opened ONLY after source-text-only pretrained grammar proposals frozen',
 'thisIsTextOnly':'No added type candidate is physically materialized by this scorer',
 'limitations':'Gold type label omissions and overlap may make unannotated candidate types legitimate objects; not an exact false-positive rate',
 'noPostGoldTuning':True},'bySource':rows},f,indent=2);f.write('\n')
private.chmod(0o600)
out={'meta':{'sourceZIPsha256':digest(GOLD),
 'frozenSourceProposalSHA256':digest(PRED),
 'frozenOriginalGameCorePhysicsSHA256':digest(BASE),
 'privateGoldAuditSHA256':digest(private),
 'sourceGroups':'same first100 human and assisted every fourth descriptions, physically accepted scenes only',
 'caveat':'Text-only proposed extra count coverage, NOT 3D accepted scenes or fluent story entailment',
 'noGoldInputToGrammar':True},
 'splits':{k:dict(v) for k,v in stats.items()},
 'combined':dict(combined),
 'newlyCorrectedTypeClasses':len(types)}
public=ROOT/'prse_spacy_open_vocab_gold_200_aggregate_v1.json'
with public.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for key,v in stats.items():
 print(key,'accepted',v['acceptedOriginalScenes'],'gold count satisfied physical baseline',
 v['matchedGoldByExisting3D'],'text candidate',v['matchedGoldBySourceNounCandidateOnly'],
 'new type suggestions',v['additionalPositiveTypeProposals'],
 'extra source label types',v['additionalTypeProposalsPresentInAuthorLabel'],
 'NOT in source label',v['additionalTypesNotInAuthorLabels'])
print('COMBINED',dict(combined))
