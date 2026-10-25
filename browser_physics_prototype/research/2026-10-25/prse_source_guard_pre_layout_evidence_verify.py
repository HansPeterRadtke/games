#!/usr/bin/env python3
"""Independent PRSE full-loop source-role/physics/observer evidence verifier.

Must preserve, not silently overwrite:
  - original gold-blind native dynamic support eligibility;
  - 54 source-only original parser ON claims and nine grammar candidates;
  - independent author relation scorer run AFTER decisions were frozen;
  - four actually simulated distinct impulse settings on eight predeclared
    physically eligible source scenes, with honest limited sample size;
  - full 197-source pre-layout source role abstention first raw v1 buggy
    report field, then corrected v2 native GameCore materialization;
  - independent AUTHOR ON gold scorer created after those v2 physical states.

Trusted source raw and complete third-party stories stay owner-private Nitro.
Only aggregate counts, reproduction, report, hashes and code go to Git.
"""
import json,zipfile,csv,io
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
DIR=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_baseline_200_raw_v2.json')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(P.stat().st_mode)==0o700
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:sourceLabels=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(sourceLabels)==500
ids=list(range(100))+list(range(100,500,4))
assert len(ids)==200
oldManifest=read(DIR/'prse_support_full_loop_evidence_manifest_v1.json')
assert oldManifest['nativeFullLoops']['physicalEpisodes']==32
assert oldManifest['nativeFullLoops']['physicalContactBecameFalseOrUnknownAfterImpulse']==30
assert oldManifest['nativeFullLoops']['sourceSyntacticApprovedRelationshipRetractions']==16
assert oldManifest['nativeFullLoops']['unseenImpulseEyewitnessLeaks']==0
assert oldManifest['sourceRoleVsIndependentAuthorCategoryLabels']['originalParsedOnClaims']==54
assert oldManifest['sourceRoleVsIndependentAuthorCategoryLabels']['syntaxRoleAccept']==9
assert oldManifest['sourceRoleVsIndependentAuthorCategoryLabels']['syntaxRoleAnnotationConcordant']==6
assert oldManifest['independentGoldEightSelected']['syntaxAcceptedAlsoAuthorAnnotated']==3
record={}
for v in ('v1','v2','v3'):
 file=P/('prse_source_syntax_guarded_native_200_raw_'+v+'.json')
 assert file.exists() and S_IMODE(file.stat().st_mode)==0o600
 pub=read(DIR/('prse_source_syntax_guarded_native_200_aggregate_'+v+'.json'))
 assert pub['metadata']['privateNativeRawSHA256']==sha(file)
 raw=read(file)
 assert pub['summary']==raw['summary']
 assert [x['sourceId'] for x in raw['results']]==ids
 assert [x['sourceId'] for x in pub['cases']]==ids
 s=raw['summary']
 assert s['originalAcceptedNativeScenes']==197
 assert s['sourceGuardedAcceptedNativeScenes']==197
 assert s['sourceGuardedPhysicsFailures']==s['sourceGuardedGeometryRejections']==0
 assert s['originalLiterarySourcesAndRealBodyIDsPreserved']==197
 assert s['parsedOnClaimsInAccepted']==50
 assert s['roleAcceptedOnClaims']==7 and s['roleAbstainedOnClaims']==43
 assert s['actual3DOnRelationsTrue']==s['actual3DOnRelationsTrueWithSourceSyntaxGate']==6
 assert s['physicalOnTrueButNoSourceRoleProof']==0
 assert s['actualNativeInterobjectRapierContactPairs']==6
 assert s['changedPhysicalBodyPositionsRelativeToBaseline']==28
 assert s['currentDocumentNativeSaveVerifications']==197
 assert s['actualNativeGameCorePhysicalActions']==64
 assert s['originalSourceRepresentationNotRewritten']==197
 if v=='v1':
  assert s['actionProducedMeaningfulSemanticRevision'] is None, 'Original reporting bug was overwritten!'
 else:
  assert s['actionProducedMeaningfulSemanticRevision']==57
  assert all(x['status']!='failure' for x in raw['results'])
  assert sum(x['status']=='native_valid_source_guarded' for x in raw['results'])==197
  for x in raw['results']:
   if x['status']!='native_valid_source_guarded':continue
   assert x['originalBodyIDsPreserved'] and x['fullOriginalLiterarySourcePreserved']
   assert x['exactCurrentTextAfterNativeReentry']
   assert x['nativeWorldAndSemanticClockEqual'] and x['unchangedSemanticRecordDoesNotRepeat']
   assert x['initial3DBodyCount']==len(x['initialBodyStates'])
   assert x['sourceClaimedPhysicallyTrueAndRoleAbstained']==0
   if v=='v3':
    assert x['narratedTrueSourceOnCount']==x['sourceClaimedPhysicallyTrueAndRoleAccepted']
   else:
    assert x['narratedTrueSourceOnCount']>=x['sourceClaimedPhysicallyTrueAndRoleAccepted']
   assert x['currentInitialSourceClaimCount']['false']>=0
 record[file.name]={'sha256':sha(file),'bytes':file.stat().st_size,'ownerPrivate':True}

goldRaw=P/'prse_pre_layout_role_guard_on_gold_200_raw_v1.json'
assert goldRaw.exists() and S_IMODE(goldRaw.stat().st_mode)==0o600
gold=read(DIR/'prse_pre_layout_source_role_gold_200_aggregate_v1.json')
assert gold['metadata']['authorSceneEvalSHA256']==sha(GOLD)
assert gold['metadata']['frozenNativeBaselineSHA256']==sha(BASE)
assert gold['metadata']['frozenRoleGuardNativeSHA256']==record['prse_source_syntax_guarded_native_200_raw_v2.json']['sha256']
assert gold['metadata']['privateOfficialPerCaseSHA256']==sha(goldRaw)
c=gold['counter']
assert c['acceptedScenes']==197
assert c['authorOnClauses']==354
assert c['bothTypesBaselinePresent']==c['bothTypesGuardedPresent']==47
assert c['authorOnPhysicallyConfirmedBaseline']==3
assert c['authorOnPhysicallyConfirmedGuarded']==2
assert c['newlyGainedPhysicalAuthorOn']==0
assert c['previouslyVerifiedAuthorOnNowLost']==1
gr=read(goldRaw)
assert len(gr['rows'])==197
assert sum(len(x['independentAuthorOn']) for x in gr['rows'])==354
record[goldRaw.name]={'sha256':sha(goldRaw),'bytes':goldRaw.stat().st_size,'ownerPrivate':True}
fullLoopKeyMetrics={
 'distinctPhysicalSourceScenesInDynamicStudy':8,
 'predeclaredImpulseVectors':4,
 'realPhysicallyUnloadedAndReenteredEpisodes':32,
 'contactTruthChangedFalseOrUnknown':30,
 'sourceSyntaxAcceptedObserverRetractions':16,
 'unseenCauseEyewitnessLeaks':0,
 'unchangedObserverNarrationDuplicates':0,
 'postSourceSyntaxGateScenesAccepted':197,
 'prelayoutAuthorContactSupportLost':1,
 'nativeCurrentWorldAndObserverSavesPassed':197}
result={'metadata':{
 'source':'Owner original PRSE literary ↔ native 3D ↔ true semantic/observer source study',
 'frozenSourceParserSHA256':sha(FROZEN),
 'originalSceneEvalGoldSHA256':sha(GOLD),
 'frozenPriorNative3DWorldSHA256':sha(BASE),
 'goldReadONLYPosthocAndNeverForGeometryOrActionSelection':True,
 'method':'Two separate interventions: source-only role gate before narration and before native 3D spatial compiler',
 'limitation':'Very small dynamic-source support eligible set (8), repeated physical conditions are not independent story samples, and type-pair source annotations are not full entailment/coreference',
 'productionScope':'Research worktree only, no live GameCore integration, no model GPUs or asset generation'},
 'frozenSourceRoleAndFullLoop':oldManifest['sourceRoleVsIndependentAuthorCategoryLabels'],
 'prelayoutOriginalV1AndCorrectedV2AndV3':{
  'originalVersionHasNullRevisionSummaryFromResearchCodeBug':True,
  'correctedAcceptedSceneCount':197,
  'correctedMeaningfulSemanticChanges':57,
  'v2MisnamedOnCountIncludedOtherVerifiedSourceRelations':True,
  'v3OnOnlyMetricVerifiedInSameFrozenScenes':True,
  'originalPhysicalContactPairs':11,
  'sourceGuardedPhysicalContactPairs':6,
  'sourceOnConstraintsWithheldInAcceptedScenes':43,
  'allOriginalPhysicalBodyIDsPreserved':True},
 'postFrozenIndependentAuthorSourceOnResult':c,
 'fullNativeBidirectionalLoop':fullLoopKeyMetrics,
 'rawAdditionalEvidenceManifest':record,
 'earlierUnmodifiedBidirectionalRawManifest':oldManifest['privateRawManifest']}
destination=DIR/'prse_source_guard_pre_layout_evidence_manifest_v1.json'
if destination.exists():assert read(destination)==result,'Mismatch; do not overwrite earlier evidence'
else:
 with destination.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('VERIFIED 54 parsed source ON claims; syntax gate 9, independently author label-concordant 6, incomplete source recall.')
print('VERIFIED 8 source-blind native eligible contacts x 4 input directions=32 real physical/semantic/offscreen/observer loops, 30 contact changes, 16 truthful retractions, zero hidden cause leaks.')
print('VERIFIED 197 source-blind guarded GameCore 3D scenes across original v1 and corrected v2/v3; source IDs, contact, physical/semantic saving, 43 ON constraints withheld and contact pairs 11->6.')
print('VERIFIED independent author gold supports drop 3->2 with new source role gate; one author-supported contact lost; no new contact added.')
print('VERIFIED original v1 missing revision metric, original v2 mislabeled source-ON count, fully corrected v3; private SHA evidence complete.')
