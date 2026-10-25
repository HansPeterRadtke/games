#!/usr/bin/env python3
"""Independent read-only PRSE source-quantity/3D-world provenance verifier.

This checks the very strong *negative* benchmark: an interpreter-generated
physical world perfectly matches its OWN object counts but frequently fails
independent source annotation requirements. It also verifies that no exact
global count/coreference/appearance claim is promoted without evidence.

The original SceneEval corpus, complete source proposals, generated per-case
physical state, author gold audit and negative authored tests remain owner-
private under Nitro. Git contains safe metrics/source with exact SHA-256.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
import json,zipfile,io,csv
R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance')
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
PARSER=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def digest(x):return sha256(x.read_bytes()).hexdigest()
def read(x):return json.loads(x.read_text())
assert digest(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(PRIVATE.stat().st_mode)==0o700
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as f:labels=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(labels)==500
ids=list(range(100))+list(range(100,500,4))
names=['prse_source_quantity_physics_200_raw_v1.json',
       'prse_source_quantity_official_gold_per_case_v1.json',
       'prse_scoped_quantity_world_text_200_raw_v1.json',
       'prse_scoped_quantity_world_text_200_raw_v2.json']
manifest={}
for name in names:
 p=PRIVATE/name
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600
 manifest[name]={'sha256':digest(p),'bytes':p.stat().st_size,'ownerPrivate':True}
initial=read(R/'prse_source_quantity_physics_200_aggregate_v1.json')
base=read(PRIVATE/names[0])
assert initial['metadata']['privateRawSHA256']==digest(PRIVATE/names[0])
assert initial['summary']==base['summary']
s=base['summary']
assert (s['sourceDescriptionsTotal'],s['physicalSampleDescriptions'],
 s['acceptedAndActuallySaved'],s['rejectedSceneGeometry'],s['failureCases'])==(500,200,197,3,0)
assert (s['sourceMentionSpansTotal'],s['sourceMentionsExplicitlyQuantified'],
 s['sourceMentionsWithoutExplicitNumericalQuantifier'])==(2787,736,2051)
assert s['descriptionsWithRepeatedObjectTypeMentions']==300
assert s['sourceTypeClaimsWithRepeatedReferents']==171
assert s['physicalBodiesAcrossAcceptedScenes']==938
assert s['numericSourceProposalCount']==s['numericalCompilerMatchTrue']==844
assert s['numericalCompilerMatchFalse']==s['numericalCompilerMatchUnknown']==0
assert s['explicitSourceAbsencesChecked']==6
assert s['explicitSourceAbsencesPhysicallyPresentDespiteNegation']==0
assert s['originalExactCountClaimsIndependentlyEntailed']==0
assert s['objectVisualAttributesIndependentlyVerified']==0
assert s['matchedNativeSaveCounts']==s['originalProsePreserved']==197
assert [r['sourceID'] for r in base['results']]==ids
assert all(labels[i]['ID']==str(i) for i in ids)
for row in base['results']:
 if row['status']!='native_3d_verified':continue
 assert row['sourceMentionSpanIntegrity']
 assert row['identicalCountsAfterActualGameCoreSave']
 assert row['identicalCountClaimEvidenceAfterSave']
 assert row['sourceProseUnchanged']
 assert row.get('countUnchangedByMovement') is not False
 assert all(c['sourceExactGlobalCountEntailed']=='unknown' and
  c['referenceUniqueness']=='unknown' and
  not c['physicallyVerifiedAttributes'] for c in row['sourceClaims'])
 assert sum(c['physicallyMaterializedCount'] for c in row['sourceClaims'])<=row['rawWorldObjectCount']

gold=read(R/'prse_source_quantity_official_gold_200_aggregate_v1.json')
assert gold['metadata']['sourceSha256']==digest(CORPUS)
assert gold['metadata']['frozenParserProposalSha256']==digest(PARSER)
assert gold['metadata']['frozenPhysicsRawSha256']==digest(PRIVATE/names[0])
assert gold['metadata']['privateGoldAuditRawSHA256']==digest(PRIVATE/names[1])
total=gold['combined']
assert total['physicallyValidatedScenes']==197
assert total['goldCountClauses']==1237
assert total['goldCountSatisfiedByPhysicalWorld']==565
assert total['goldCountContradictedByPhysicalWorld']==672
assert total['goldPhysicalUnderCount']==670
assert total['goldAttributeClauses']==972
assert total['lexicalAttributeMatchesGold']==139
assert total['goldExplicitZeroClaims']==total['goldExplicitZeroPhysicallySatisfied']==6
assert total['goldExplicitZeroParsedAsAbsence']==6
assert total['goldExplicitZeroParsedAndPhysicallySatisfied']==6
assert total['goldCountSatisfiedBySourceLexicalProposal']==total['goldCountSatisfiedByPhysicalWorld']
assert total['independentlyAnnotatedCountClausesUnableToCheck']==19

scoped={}
for version,bytesExpected in [('v1',26017),('v2',18509)]:
 pub=read(R/f'prse_scoped_quantity_world_text_200_aggregate_{version}.json')
 raw=read(PRIVATE/f'prse_scoped_quantity_world_text_200_raw_{version}.json')
 assert pub['metadata']['privateRawSHA256']==digest(PRIVATE/f'prse_scoped_quantity_world_text_200_raw_{version}.json')
 assert pub['summary']==raw['summary']
 info=raw['summary']
 assert (info['sourceScenes'],info['acceptedNativeSavedWorlds'],info['realExecutionFailures'])==(200,197,0)
 assert info['exactNativePhysicsSourceTextAndCountRestoration']==197
 assert info['referentialUniquenessStillUnknown']==info['meaningfulQuantitySourceClaims']==844
 assert info['previousPerObjectTextBytes']==22913
 assert info['scopedGroupedPhysicalTextBytes']==bytesExpected
 assert info['initialLiterarySourceBytes']==51707
 assert [r['sourceID'] for r in raw['results']]==ids
 assert all(r['status']!='failed' for r in raw['results'])
 assert all(r['sameHistoricalLiteraryText'] and r['unchangedHistoryDoesNotRepeat']
   for r in raw['results'] if r['status']=='verified')
 scoped[version]={'bytes':info['scopedGroupedPhysicalTextBytes'],'baselineBytes':info['previousPerObjectTextBytes'],
  'nativeSaveVerifications':197}
# Difference from the v1 verbose attempt must be retained as a NEGATIVE.
assert scoped['v1']['bytes']>scoped['v1']['baselineBytes']
assert scoped['v2']['bytes']<scoped['v2']['baselineBytes']
adverse=read(R/'prse_source_quantity_causal_negation_cases_v1.json')
assert adverse['originalHumanNegation']['unloadedRegionCorrectlyUnknown']
assert adverse['originalHumanNegation']['noForbiddenObjectCreatedByNativeRematerialization']
assert adverse['deliberatelyContradictedPhysicalScene']['sourceNegationProvedPhysicallyFalse']
assert adverse['deliberatelyContradictedPhysicalScene']['truthConflictPersistsAcrossTrustedNativeSave']
assert adverse['offscreenAuthoredFire']['sourceNoteNowPhysicallyAbsent']
assert adverse['offscreenAuthoredFire']['physicallyDistinctAshPresentWithNativeCollider']
assert adverse['offscreenAuthoredFire']['originalNoteIdentityHistoricalDestroyed']

out={'metadata':{
 'source':'SceneEval-500 official author-supplied source and annotations, separated from the actual physics interpreter',
 'sceneEvalSHA256':digest(CORPUS),
 'sourceParserRawSHA256':digest(PARSER),
 'noGoldDuringInterpreterOrRapierPhysics':True,
 'frozenSourceIDs':'Human rows 0..99 and assisted rows 100,104,...496',
 'ownerPrivateCompleteRawResults':True,
 'noGPUorLLMorHumanEvaluation':True,
 'sourceCountWarning':'Self-consistency with compiler-generated scene populations is tautological and DOES NOT validate the literary source.',
 'attributeWarning':'Visual and material properties parsed from prose are not independently verified by Rapier objects.'},
 'observedSourceParserAmbiguity':{
  'totalMentions':2787,'withoutExplicitQuantification':2051,'explicitQuantifiedMentions':736,
  'scenesWithRepeatedObjectTypeMentions':300},
 'actualPhysicalWorldCountVsIndependentSourceLabels':{
  'physicallyAcceptedScenes':197,'compilerCountClaimsSelfMatched':844,
  'independentGoldCountClauses':1237,'goldClausesMatchedByRealBodies':565,
  'goldClausesContradicted':672,'mostlyUnderCounted':670,
  'goldSourceNegationsRealized':6,
  'annotatedAttributesNotIndependentlyMeasured':972},
 'scopedCurrentText':scoped,
 'adversarialNativeCausalTruth':{
  'realOriginalSourceNegationSurvivesUnloading':True,
  'deliberatelyContradictoryPhysicalObjectIsCaught':True,
  'authoredOffscreenDestructionDoesNotReuseOldSourceCount':True},
 'privateRawManifest':manifest}
dest=R/'prse_source_quantity_evidence_manifest_v1.json'
if dest.exists():assert read(dest)==out,'Do not overwrite different previously consumed research evidence'
else:
 with dest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED: 500 original sources show quantity/coreference ambiguity;')
print('VERIFIED: 197 real native GameCore 3D worlds and immutable source IDs/save;')
print('VERIFIED: 844/844 circular compiler count matches vs only 565/1237 independent author count claims;')
print('VERIFIED: original 6 explicit source absences, new negative contradictions, authored ash rematerialization;')
print('VERIFIED: verbose v1 output preserved; v2 scoped physical count prose shorter than old per-object baseline.')
