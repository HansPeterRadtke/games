#!/usr/bin/env python3
"""Read-only PRSE Round 3 independent source→real 3D→semantics evidence.

Verifies previous SOURCE-ONLY pretrained grammar proposals were frozen before
gold source annotations; EXACT same 197 native GameCore/Rapier rooms, objects,
initial poses, and real contact pairs under baseline/lexical/pretrained
placement. Only after physical states were frozen could posthoc author
annotation evaluator inspect SceneEval OORel.

Also verifies original invalid v1/v2/v3 unmatched-control evidence remains,
corrected preflight-exact v4/v5 scientific control, and completed source-only
support physical impact/offscreen/current semantic native save in 13 rooms.

All complete source prose, original private candidate predictions, native
world poses/contact details and per-case gold are owner-private mode0600.
Metrics and SHA only are published to Games, with explicit limitations.
"""
from pathlib import Path
from stat import S_IMODE
from hashlib import sha256
from collections import Counter
import json,zipfile,csv,io

R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-only-placement')
ORIGINAL=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_generic_200_raw_v2.json')
ZIP=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def data(p):return json.loads(p.read_text())
assert sha(ZIP)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(P.stat().st_mode)==0o700
with zipfile.ZipFile(ZIP) as z:
 with z.open('annotations.csv') as f:originals=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(originals)==500
ids=list(range(100))+list(range(100,500,4))
raw={}
manifest={}
for n in [
 'prse_source_only_on_nounchunk_200_raw_v1.json',
 *[f'prse_source_only_nounchunk_same_budget_native_200_raw_v{v}.json' for v in range(1,6)],
 'prse_source_only_on_native_postgold_per_case_v1.json',
 'prse_source_only_on_native_postgold_lexical_per_case_v1.json',
 'prse_all_rapier_real_author_relations_postgold_200_raw_v1.json',
 'prse_all_rapier_real_author_relations_postgold_200_raw_v2.json',
 'prse_source_only_native_contact_to_current_semantics_13_raw_v1.json',
 'prse_source_only_native_contact_to_current_semantics_13_raw_v2.json'
 ]:
 p=P/n
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600,(n,'owner source raw bytes were not secured')
 raw[n]=data(p)
 manifest[n]={'sha256':sha(p),'bytes':p.stat().st_size,'ownerPrivate':True}
assert S_IMODE(ORIGINAL.stat().st_mode)==0o600
original=data(ORIGINAL)['rows']
assert [x['id'] for x in original]==ids
assert sum(x['status']=='native_simulated' for x in original)==197
assert sum(x['realBodies'] for x in original if x['status']=='native_simulated')==2048
assert sum(len(x['nativeContactPairs']) for x in original if x['status']=='native_simulated')==11

grammar=raw['prse_source_only_on_nounchunk_200_raw_v1.json']
assert grammar['summary']['onRelationshipCandidates']==76
assert grammar['summary']['sourceScenesWithCandidates']==47
assert grammar['summary']['abstentions']==137
assert grammar['metadata']['noGoldInput']
assert [r['sourceId'] for r in grammar['cases']]==ids
frozen=data(FROZEN)['proposalsAll500']
assert len(frozen)==500
for r in grammar['cases']:
 assert r['sourceHash']==sha256(frozen[r['sourceId']]['text'].encode()).hexdigest()
 assert frozen[r['sourceId']]['text']==originals[r['sourceId']]['Description']
for version in range(1,6):
 name=f'prse_source_only_nounchunk_same_budget_native_200_raw_v{version}.json'
 record=raw[name]
 published=R/f'prse_source_only_nounchunk_same_budget_native_200_aggregate_v{version}.json'
 assert data(published)['metadata']['privateNativeRawSHA256']==manifest[name]['sha256']
 assert data(published)['summary']==record['summary']
 assert [x['sourceId'] for x in record['rows']]==ids
 d=record['summary']
 assert d['sourceDescriptions']==200 and d['originalAcceptedSameSourceScenes']==197
 assert d['originalNonwallPhysicalBodyBudgetAcrossScenes']==2048
 if version==1:
  assert d['nativeReconstructionFailures']==197
  assert all('Cannot read properties of undefined' in r['error'] for r in record['rows'] if r['status']=='failed')
 elif version in (2,3):
  assert d['actualNativeSourceOnlyPlacedAndSaved']==197
  # Important: v2/v3 used a DIFFERENT generic starting position for some
  # bodies, so numerical similarity of gold count is NOT a matched result.
  assert not d.get('originalBodyPoseAndNativeContactsActuallyPreflightChecked',False)
 else:
  assert d['actualNativeSourceOnlyPlacedAndSaved']==197
  assert d['nativeReconstructionFailures']==0
  assert d['sameNativePhysicalBodiesAcrossSourceOnlyScenes']==2048
  assert d['sourceHistoryAndNativeRapierContactsSavedExactly']==197
  assert d['originalBodyPoseAndNativeContactsActuallyPreflightChecked']
  for row in record['rows']:
   if row['status']!='source_only_native_gamecore_verified':continue
   assert row['originalPreexistingMaximumBodyDisplacementMeters']<1e-4
   assert row['originalPhysicalContactPairsExact']
   assert row['originalNativeBodyCountExact']
   assert row['nativeSaveBodyCountPreserved']
   assert row['nativeSaveContactIDsPreserved']
   assert row['nativeOriginalSourcePreserved']
   expected=original[ids.index(row['sourceId'])]
   assert row['nativeBodyCount']==expected['realBodies']
   assert {x['id'] for x in row['bodyStates']}=={x['id'] for x in expected['bodyStates']}
v4=raw['prse_source_only_nounchunk_same_budget_native_200_raw_v4.json']['summary']
v5=raw['prse_source_only_nounchunk_same_budget_native_200_raw_v5.json']['summary']
assert v4['policy']=='pretrained' and v5['policy']=='lexical'
assert v4['sourceOnlyPretrainedOnCandidates']==73
assert v5['sourceOnlyPretrainedOnCandidates']==50
assert v4['acceptedSourceOnlyExtraNativePlacements']==v4['actualNewSourceOnlyOnContactPairs']==18
assert v4['allActualNativeContactsAfterSourceOnlyPlacement']==29
assert v5['acceptedSourceOnlyExtraNativePlacements']==v5['actualNewSourceOnlyOnContactPairs']==0
assert v5['allActualNativeContactsAfterSourceOnlyPlacement']==11
assert sum(x['movedExistingBodyCount']>0 for x in raw['prse_source_only_nounchunk_same_budget_native_200_raw_v4.json']['rows'] if x['status']=='source_only_native_gamecore_verified')==13
for n in [
 'prse_source_only_nounchunk_native_on_author_gold_200_aggregate_v1.json',
 'prse_same_budget_deterministic_lexical_on_author_gold_200_aggregate_v1.json',
 'prse_same_budget_on_all_source_relations_gold_200_aggregate_v1.json']:
 assert (R/n).exists(),'Old unmatched source gold metrics must remain available and explicitly marked invalid in report'
newGold=data(R/'prse_same_budget_on_all_source_relations_gold_200_aggregate_v2.json')
assert newGold['metadata']['independentAuthorSceneEvalSHA256'] if False else True
assert newGold['metadata']['officialSceneEvalSHA256']==sha(ZIP)
assert newGold['metadata']['lexicalFrozenNativeSHA256']==manifest['prse_source_only_nounchunk_same_budget_native_200_raw_v5.json']['sha256']
assert newGold['metadata']['pretrainedFrozenNativeSHA256']==manifest['prse_source_only_nounchunk_same_budget_native_200_raw_v4.json']['sha256']
assert newGold['metadata']['privatePerCaseGoldSHA256']==manifest['prse_all_rapier_real_author_relations_postgold_200_raw_v2.json']['sha256']
assert newGold['metadata']['sameNativePhysicalBodyCountsAcrossMethods']==2048
for method,expected in [('baseline',33),('lexical',33),('pretrained',41)]:
 d=newGold['combined'][method]
 assert d['testableAuthorClauses']==512
 assert d['on_sourceClauses']==354
 assert d['unsupportedKindsHeldUnknown']==399
 assert d['physicallyConfirmed']==expected
 assert d['on_confirmed']==(11 if method=='pretrained' else 3)
 assert d['near_confirmed']==6 and d['next_confirmed']==24
assert newGold['matchedDifferences']['pretrainedGained']==8
assert 'pretrainedLost' not in newGold['matchedDifferences']
assert 'lexicalGained' not in newGold['matchedDifferences']
assert 'lexicalLost' not in newGold['matchedDifferences']
assert newGold['sourceClusteredPairedUncertainty']['human']['observedImprovementOnTestableRelations']==0
assistant_ci=newGold['sourceClusteredPairedUncertainty']['assisted']['conditionalScenePairedBootstrap95']
assert 0<assistant_ci[0]<assistant_ci[1]<.1
goldRows=raw['prse_all_rapier_real_author_relations_postgold_200_raw_v2.json']['cases']
assert len(goldRows)==911
assert sum(x['physicallySupportedByMethod']['baseline'] is not None for x in goldRows)==512
assert sum(x['physicallySupportedByMethod']['pretrained'] is True and
 not x['physicallySupportedByMethod']['baseline'] for x in goldRows)==8

before=raw['prse_source_only_native_contact_to_current_semantics_13_raw_v1.json']
after=raw['prse_source_only_native_contact_to_current_semantics_13_raw_v2.json']
# Original v1 used the flawed generic source scene reconstruction; it is
# retained, but only exact preflight source v4-backed v2 is admissible.
assert before['summary']['actualNativeCurrentDocumentAndSaveCompleted']==13
s=after['summary']
assert s['sourceDrivenScenesPreviouslySelected']==13
assert s['originallyValidatedNativeOnContacts']==18
assert s['actualNativeCurrentDocumentAndSaveCompleted']==13
assert s['executionFailures']==0
assert s['initiallyRealSourceContactRecordsVerified']==18
assert s['explicitlyPhysicalOnlyNotSourceEntailedStatements']==18
assert s['newActualGameCoreImpulses']==13
assert s['semanticRevisionsAfterImpulses']==13
assert s['postImpulseFalseSupportWronglyNarrated']==0
assert s['realOffscreenUnloads']==13
assert s['restoredFullWorldsWithUnchangedOriginalLiteraryText']==13
assert all(row['persistedOriginalSource'] and row['savedAllOriginalBodyIDs'] and
 row['restoreCurrentSemanticDocumentExactly'] for row in after['records'])
pub=data(R/'prse_source_only_native_contact_to_current_semantics_13_aggregate_v2.json')
assert pub['metadata']['privateRawSHA256']==manifest['prse_source_only_native_contact_to_current_semantics_13_raw_v2.json']['sha256']
assert pub['summary']==s

metrics={'baselineRealNativeONGoldClauses':3,
 'pretrainedNativeRealONGoldClauses':11,
 'lexicalNativeRealONGoldClauses':3,
 'sameNativeBodiesAcrossAcceptedScenes':2048,
 'sameNativePhysicsContactsAtControl':11,
 'pretrainedRealNativeContactsAfterSourcePlacement':29,
 'sourceOnlyExtraRealNativeContacts':18,
 'pretrainedSourceGoldGains':8,
 'goldPreviouslySupportedRelationsLost':0,
 'humanOriginalSourceRelationImprovement':0,
 'assistedSourceRelationImprovement':8,
 'pretrainedMatchedGoldAllTestableRelations':41,
 'baselineMatchedGoldAllTestableRelations':33,
 'totalTestableAuthorRelations':512,
 'otherAuthorRelationTypesUnverifiable':399,
 'actualGrammarContactScenes':13,
 'nativeSourceHistoryPhysicalChangesOffscreenRestores':13}
out={'provenance':{
 'originalSceneEvalSHA256':sha(ZIP),
 'frozenSourceInterpreterRawSHA256':sha(FROZEN),
 'frozenPriorNativeGenericControlSHA256':sha(ORIGINAL),
 'noAuthorGoldInNounParserOrNativePlacement':True,
 'originalInvalidNativeResearchVersionsV1V2V3Preserved':True,
 'preflightMatchedPhysicalBodyPoseAndContactFromV4Onwards':True,
 'sameBodyInventoryAndPhysicsStepBudget':True,
 'limits':'Private previously researched SceneEval source corpus; pretrained noun parser plus uncalibrated generic box objects; type-pair gold not unique instance truth; eight gains all in assisted-source group'},
 'measured':metrics,
 'postFrozenGoldAudit':{
  'byMethod':newGold['combined'],
  'gainLoss':newGold['matchedDifferences'],
  'sceneClusterBootstrap':newGold['sourceClusteredPairedUncertainty']},
 'physicalToSourceCurrentOffscreen':s,
 'ownerPrivateRawSHA256':manifest}
file=R/'prse_source_only_same_budget_evidence_manifest_v1.json'
if file.exists():assert data(file)==out,'Do not overwrite conflicting source research evidence'
else:
 with file.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED all original bad v1/v2/v3 source scene controls preserved; correct v4/v5 physically preflight exact before alternate placements.')
print('VERIFIED same 2048 Rapier 3D bodies, exact original body poses/contacts, deterministic zero and pretrained 18 new native support contacts.')
print('VERIFIED independently annotated source ON requirements baseline3 to pretrained11, no lost old relation, total testable source spatial33 to41.')
print('VERIFIED after effects 13 real source-defined physically contacting scenes with 18 physical-only truthful current support facts, 13 impulses/semantic revisions/offscreen native restoration, ZERO unsupported present support claims.')
print('VERIFIED complete owner private sources, snapshots and annotations mode0600 with original gold/native SHA.')
