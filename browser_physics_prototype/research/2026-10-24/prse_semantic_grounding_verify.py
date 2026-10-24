#!/usr/bin/env python3
"""Independent audit + public-safe aggregate of PRSE SceneEval experiments.

Raw, potentially externally copyrighted benchmark prompts remain in private
Nitro evidence storage, not redistributed in the Git research branch. The
source ZIP is separately downloaded from the authors' official release.
"""
import csv, hashlib, io, json, os, zipfile
from pathlib import Path

ROOT=Path(__file__).parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints')
SOURCE=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
FILES=[
 'prse_semantic_constraints_eval_v1.json','prse_semantic_constraints_eval_v2.json',
 'prse_semantic_constraints_eval_all500_v3.json',
 'prse_sceneeval_constraint_physics_v1.json',
 'prse_sceneeval_constraint_physics_v2_after_support.json',
 'prse_sceneeval_assisted_100_physics_v1.json',
 'prse_sceneeval_relation_grounding_score_v1.json',
 'prse_sceneeval_relation_grounding_score_v2.json',
 'prse_sceneeval_assisted_100_grounded_score_v1.json',
 'prse_external_text_causal_relationship_roundtrip.json',
 'prse_external_movable_support_causal_batch_v1.json',
 'prse_constraint_guard_full_physics_regression.json'
]
def location(name):
    q=ROOT/name
    if q.is_file():return q
    q=PRIV/name
    if q.is_file():return q
    raise FileNotFoundError(name)
def read(name):return json.loads(location(name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert SOURCE.is_file() and sha(SOURCE)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(SOURCE) as z:
    with z.open('annotations.csv') as stream:
        rows=list(csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig')))
assert len(rows)==500
text=read('prse_semantic_constraints_eval_v2.json')
assert len(text['proposalsFirst100'])==100
for i in range(100):
    assert text['proposalsFirst100'][i]['sourceId']==str(i)
    assert text['proposalsFirst100'][i]['text']==rows[i]['Description']
all500=read('prse_semantic_constraints_eval_all500_v3.json')
assert len(all500['proposalsAll500'])==500
assert all500['proposalsAll500'][-1]['text']==rows[-1]['Description']
pre=read('prse_sceneeval_constraint_physics_v1.json')
post=read('prse_sceneeval_constraint_physics_v2_after_support.json')
mach=read('prse_sceneeval_assisted_100_physics_v1.json')
assert len(pre['results'])==len(post['results'])==len(mach['results'])==100
assert pre['summary']['scenesWithPhysicalBodies']==post['summary']['scenesWithPhysicalBodies']==97
assert mach['summary']['scenesWithPhysicalBodies']==99
assert [int(r['id']) for r in mach['results']]==list(range(100,500,4))
a=read('prse_sceneeval_relation_grounding_score_v2.json')['results']['originalHuman100']
b=read('prse_sceneeval_assisted_100_grounded_score_v1.json')['results']['machine_assisted_sampled_100']
assert (a['goldAnnotatedTypedPairRelations'],a['physicallyGroundedMatchedGold'])==(478,22)
assert (b['goldAnnotatedTypedPairRelations'],b['physicallyGroundedMatchedGold'])==(743,17)
assert a['groundedRecallIgnoringDirection']<.05 and b['groundedRecallIgnoringDirection']<.03
test=read('prse_external_text_causal_relationship_roundtrip.json')
assert test['provenance']['sourceText']==rows[22]['Description']
assert test['afterPhysical']['supportRemoved']
assert test['saveReentry']['stableIdentity'] and test['saveReentry']['persistedSupportLoss']
batch=read('prse_external_movable_support_causal_batch_v1.json')
assert (batch['summary']['tested'],batch['summary']['passed'])==(2,2)
causal_annotation_audit=[]
for rec in batch['results']:
 assert rec['source']==rows[int(rec['sceneId'])]['Description'] and rec['pass']
 clause=rec['languageRelation']
 relation_gold=[]
 for raw in rows[int(rec['sceneId'])]['OORel'].split(';'):
  parts=[t.strip().lower() for t in raw.strip().split(',')]
  if len(parts)>=6:relation_gold.append((parts[2],{parts[4].split(':')[0],parts[5].split(':')[0]}))
 gold_match=any(t==clause['type'] and participants=={clause['a'].lower(),clause['b'].lower()} for t,participants in relation_gold)
 causal_annotation_audit.append({'sceneId':rec['sceneId'],'physicallyConsistent':rec['pass'],
   'officialAnnotatedRelationAgreement':gold_match,
   'sourceGoldRelationTypes':[v[0] for v in relation_gold],
   'relationFromParser':clause['type']})
assert sum(c['officialAnnotatedRelationAgreement'] for c in causal_annotation_audit)==1,causal_annotation_audit
prelift=read('prse_vertical_support_false_claim_before_fix.json')
frozen=read('prse_offscreen_dynamic_freeze_before_guard.json')
corrected=read('prse_vertical_support_and_dynamic_unload_corrected.json')
assert prelift['after']['incorrectSupportClaim']
assert frozen['velocityStillNonzero'] and frozen['positionFrozen']
assert corrected['correctedLift']['supportClaim'] is None
assert corrected['recontact']['verifiedContactEvent']['details']['cause']=='verified_rigid_body_contact'
assert corrected['finalReentry']['restingSupport'] and corrected['finalReentry']['stableLampId']
assert corrected['activePhysicsUnloadingRefused']['reason'].startswith('Unresolved dynamic motion')
g=read('prse_constraint_guard_full_physics_regression.json')
assert len(g['rooms'])==6 and all(x['stableIds'] for x in g['rooms'])
assert g['offscreenDamage']['offscreenNoLeak']
metrics={
 'human35_development':{k:{v:round(d[v],6) if isinstance(d[v],float) else d[v] for v in ('f1','precision','recall','goldFacts','matchedFacts')}
  for k,d in read('prse_semantic_constraints_eval_v2.json')['scores']['first35_development'].items()},
 'human65_later':{k:{v:round(d[v],6) if isinstance(d[v],float) else d[v] for v in ('f1','precision','recall','goldFacts','matchedFacts')}
  for k,d in read('prse_semantic_constraints_eval_v2.json')['scores']['remaining65_original_human'].items()},
 'assisted400':{k:{v:round(d[v],6) if isinstance(d[v],float) else d[v] for v in ('f1','precision','recall','goldFacts','matchedFacts')}
  for k,d in all500['scores']['machine_assisted_400'].items()}
}
manifest={name:{'sha256':sha(location(name)),'bytes':location(name).stat().st_size,
    'privateAfterArchiving':True} for name in FILES}
agg={
 'metadata':{'researchDate':'2026-10-25',
   'source':'SceneEval-500_v250610, https://github.com/3dlg-hcvc/SceneEval/releases/tag/SceneEval-500_v250610',
   'sourceZipSHA256':sha(SOURCE),
   'sourceTextsNotRepublished':'Raw external descriptions and all original per-case evidence are retained in owner-private Nitro runtime storage; authors release is authoritative.',
   'code':'prse_semantic_constraints.py, prse_sceneeval_constraint_physics.mjs, PRSELoop existing GameCore Rapier adapter',
   'noModelCall':True,'limitations':'The directional ordering of relations and full room attributes are NOT scored; counted matches are optimistic upper bound. This is exploratory and NOT a blind model contest.',
   'sampleProtocol':'Human first100 including development first35; VLM-assisted every fourth row among ID100..499 (exact 100), not a randomized population sample'},
 'language':metrics,
 'physics':{
   'human100':{k:pre['summary'][k] for k in ['sourceProposals','scenesWithPhysicalBodies','physicallyRejected','noRecognizedEntities','physicallyGroundedRelationCount','physicallyViolatedRelationCount','unsupportedRelationCount']},
   'assisted100':{k:mach['summary'][k] for k in ['sourceProposals','scenesWithPhysicalBodies','physicallyRejected','noRecognizedEntities','physicallyGroundedRelationCount','physicallyViolatedRelationCount','unsupportedRelationCount']}
 },
 'externalGoldRelationAudit':{
  'human100':{k:a[k] for k in ('goldAnnotatedTypedPairRelations','physicallyGroundedMatchedGold','extractedMatchedGold','groundedPrecisionIgnoringDirection','groundedRecallIgnoringDirection','groundedF1')},
  'assisted100':{k:b[k] for k in ('goldAnnotatedTypedPairRelations','physicallyGroundedMatchedGold','extractedMatchedGold','groundedPrecisionIgnoringDirection','groundedRecallIgnoringDirection','groundedF1')}},
 'causalSelectedExternalRows':{
  'eligible':batch['summary']['eligibleExplicitMovableSupportRelations'],
  'tested':batch['summary']['tested'],'passed':batch['summary']['passed'],'rowIDs':batch['summary']['sampleIds'],
  'row22SavedPhysicalSupportLoss':test['saveReentry']['persistedSupportLoss'],
  'annotationAudit':causal_annotation_audit,
  'strictOfficialAnnotationAgreementCount':sum(r['officialAnnotatedRelationAgreement'] for r in causal_annotation_audit)},
 'negativeThenCorrected':{
  'preFixVerticalFalseSupportClaim':prelift['after']['incorrectSupportClaim'],
  'preFixUnloadedBodyFrozenWhileMoving':frozen['positionFrozen'] and frozen['velocityStillNonzero'],
  'correctedPhysicalSupportReturn':bool(corrected['recontact']['verifiedContactEvent']),
  'movingUnloadingRefused':bool(corrected['activePhysicsUnloadingRefused']['reason']),
  'savedActiveTrajectoryDifferenceMeters':corrected['recontact']['savedActiveTrajectoryDivergenceMeters'],
  'guardedRerunSixExternallyMappedRooms':all(x['stableIds'] for x in g['rooms'])},
 'privateEvidenceManifest':manifest}
out=ROOT/'prse_semantic_grounding_evidence_aggregate_v2.json'
if not out.exists():
    with out.open('x') as fp:json.dump(agg,fp,indent=2);fp.write('\n')
else:
    existing=json.loads(out.read_text())
    assert existing==agg,'Unintended aggregate mismatch — do not overwrite'
print('EVIDENCE_VERIFIED',
      'human gold grounded',f"{a['physicallyGroundedMatchedGold']}/{a['goldAnnotatedTypedPairRelations']}",
      'assisted gold grounded',f"{b['physicallyGroundedMatchedGold']}/{b['goldAnnotatedTypedPairRelations']}",
      'genuine causal tested',batch['summary']['tested'],
      'original per-case outputs',len(FILES),'source independent label annotation checked')
