#!/usr/bin/env python3
"""Independent read-only verification of the PRSE grounded-facts experiment.

External annotation labels are used ONLY to crosscheck the already written
private v3 results. Physically credible claims are not assumed to be original
text entailments unless the independent annotation agrees. Original failed
v1 and corrected v2/v3 remain immutable.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
import json,csv,io,zipfile

ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-grounded-prose')
SOURCE=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert digest(SOURCE)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(SOURCE) as z:
 with z.open('annotations.csv') as fp:rows=list(csv.DictReader(io.TextIOWrapper(fp,encoding='utf-8-sig')))
assert len(rows)==500
sample=list(range(100))+list(range(100,500,4))
manifest={}
for version in ('v1','v2','v3','v4','v5'):
 public=read(ROOT/f'prse_grounded_prose_200_aggregate_{version}.json')
 assert len(public['variants'])==2
 for item in public['variants']:
  method=item['summary']['method'];name=f'prse_grounded_prose_{method}_200_raw_{version}.json'
  raw=PRIVATE/name
  assert raw.is_file() and S_IMODE(raw.stat().st_mode)==0o600
  assert digest(raw)==item['privateRawSHA256']
  r=read(raw);recs=r['records'];summary=r['summary']
  assert len(recs)==200 and [int(v['id']) for v in recs]==sample
  assert summary==item['summary']
  assert summary['noSourceProseMutation']
  assert summary['sameFactRepeatedOnSameObserver']==0
  assert summary['independentOracleDisagreements']==0
  if version=='v1' and method=='deterministic':
   assert summary['verifiedSceneSaves']==195 and summary['failed']==1
   assert any(v['id']==240 and v['status']=='failed' for v in recs)
  elif method=='deterministic':
   assert summary['verifiedSceneSaves']==196 and summary['failed']==0
  elif method=='union':
   assert summary['verifiedSceneSaves']==194 and summary['failed']==0
  if version in ('v3','v4','v5'):
   for record in recs:
    if record['status']=='verified-world-and-facts':
     assert len(record['relationEvidence'])==record['proposedRelations']
     for e in record['relationEvidence']:
      assert e['kind'] in ('object','room') and e['truth'] in ('true','false','unknown')
     assert sum(e['truth']=='true' for e in record['relationEvidence'])==record['trueRelations']
     assert sum(e['truth']=='false' for e in record['relationEvidence'])==record['falseRelations']
     assert sum(e['truth']=='unknown' for e in record['relationEvidence'])==record['unknownRelations']
  manifest[name]={'sha256':digest(raw),'bytes':raw.stat().st_size,'ownerPrivate':True}
negative=PRIVATE/'prse_relation_restore_discontinuity_source240_negative.json'
assert negative.exists() and S_IMODE(negative.stat().st_mode)==0o600
first=read(negative)
assert len(first['pairedMismatches'])==1
assert first['pairedMismatches'][0]['before']['truth']=='true'
assert first['pairedMismatches'][0]['after']['truth']=='unknown'
assert first['pairedMismatches'][0]['after']['reason']=='dynamic_contact_not_confirmed'
manifest[negative.name]={'sha256':digest(negative),'bytes':negative.stat().st_size,'ownerPrivate':True}
correction=read(ROOT/'prse_restore_prior_verified_contact_fix_v2.json')
assert correction['immediatelyAfterNativeReload']['withoutProvenance']=='unknown'
assert correction['immediatelyAfterNativeReload']['withPriorVerifiedEvidence']=='true'
assert correction['onceActualPhysicsResumed']['truth']=='true'
assert not correction['onceActualPhysicsResumed']['stillDependsOnSavedEvidence']
assert all(correction['tampering'].values())
audit=read(ROOT/'prse_grounded_prose_source_annotation_audit_v1.json')
auditV4=read(ROOT/'prse_grounded_prose_source_annotation_audit_v2.json')
auditV5=read(ROOT/'prse_grounded_prose_source_annotation_audit_v3.json')
assert audit['metadata']['sourceSHA256']==auditV4['metadata']['sourceSHA256']==auditV5['metadata']['sourceSHA256']==digest(SOURCE)
assert auditV4['version']=='v4' and auditV5['version']=='v5'
expected={
 'deterministic':{'human':(478,44,16),'assisted':(743,56,11)},
 'union':{'human':(478,56,18),'assisted':(743,77,13)}
}
for method,splits in expected.items():
 assert audit['results'][method]['privateRawSHA256']==manifest[f'prse_grounded_prose_{method}_200_raw_v3.json']['sha256']
 assert auditV4['results'][method]['privateRawSHA256']==manifest[f'prse_grounded_prose_{method}_200_raw_v4.json']['sha256']
 assert auditV5['results'][method]['privateRawSHA256']==manifest[f'prse_grounded_prose_{method}_200_raw_v5.json']['sha256']
 for group,(gold,physical,matching) in splits.items():
  for report in (audit,auditV4,auditV5):
   info=report['results'][method]['sourceAudit']['object_unordered'][group]
   assert (info['independentlyAnnotatedClaimCount'],info['confirmedActualPhysicalTypePairs'],
           info['matchedGoldAndPhysicallyVerified'])==(gold,physical,matching)
nearBefore=read(ROOT/'prse_false_near_vertical_gap_prefixed_negative.json')
diagonalBefore=read(ROOT/'prse_false_diagonal_near_before_distance_fix.json')
spatialGuard=read(ROOT/'prse_3d_surface_distance_guard_results.json')
assert nearBefore['wronglyVerified'] and nearBefore['actualVerticalGapMeters']>4
assert diagonalBefore['incorrectIfNear'] and diagonalBefore['actualSurfaceEuclideanClearanceMetres']>1.5
assert spatialGuard['preFixCounterexamples']['verticalWrong']
assert spatialGuard['preFixCounterexamples']['diagonalWrong']
assert [r['truth'] for r in spatialGuard['corrected']]==['false','false','true']
ending=read(ROOT/'prse_grounded_literary_reentry_source22.json')
assert ending['initial']['verifiedNarration']==['lamp 1 rests on nightstand 1.']
assert ending['savedReentry']['observableCorrectRetraction']=='lamp 1 no longer rests on nightstand 1.'
assert ending['savedReentry']['keptOriginalProse'] and ending['savedReentry']['noDuplicateNextRead']
assert ending['savedReentry']['sameEntityIdentity']
out={'metadata':{
 'source':'Author official SceneEval-500 ZIP, independent annotations only in scorer',
 'sha256SceneEvalZIP':digest(SOURCE),
 'fullCorpusNotRepublished':True,
 'method':'Actual existing PRSE GameCore/Rapier, conservative source-linked relation facts; no GPU/LLM generation',
 'limitations':'Optimistic type-pair annotations ignore instance-level source fidelity; physically true but unannotated need not be hallucination',
 'selection':'First 100 human, systematic assisted 100 source IDs; selected illustrative case 22 and negative case 240 documented'},
 'sourceCaseIntegrity':{
  'originalFailedReloadPreserved':True,
  'conditionalPreviouslyVerifiedContactAtSamePose':True,
  'noHiddenGamePhysicsTickAtLoad':True,
  'invalidSourcePoseTimeEvidenceRejected':True,
  'verifiedProseRetractionAfterReentry':'lamp 1 no longer rests on nightstand 1.'},
 'methodGroups':{
   m:{'human':{'physicallyVerified':expected[m]['human'][1],'sourceAnnotationConcordant':expected[m]['human'][2],
              'annotations':expected[m]['human'][0]},
      'assisted':{'physicallyVerified':expected[m]['assisted'][1],
                  'sourceAnnotationConcordant':expected[m]['assisted'][2],
                  'annotations':expected[m]['assisted'][0]}}
   for m in expected},
 'actualFull3DNegative':{
  'previouslyIncorrectHorizontalOnlyNear':True,
  'measuredActualVerticalGapMetres':nearBefore['actualVerticalGapMeters'],
  'correctedFullCorpusV5UsesEuclidean3DSurfaceDistanceAndRetainsMeasuredSourceConcordance':True},
 'rawPrivateArtifactManifest':manifest}
destination=ROOT/'prse_grounded_prose_evidence_manifest_v3.json'
if destination.exists():
 assert read(destination)==out,'Refusing to overwrite already claimed manifest'
else:
 with destination.open('x') as fp:json.dump(out,fp,indent=2);fp.write('\n')
print('Verified complete v1 negative, corrected v2/v3/v4/v5 at identical external source IDs, '
      'physical facts versus independent annotations, immutable private hashes, '
      'reentry no-duplicate and provenance-guarded contact continuity.')
