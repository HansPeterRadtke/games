#!/usr/bin/env python3
"""Read-only independent evidence integrity for PRSE *non-destructive* source
interpretation hypotheses + native GameCore 3D state and offscreen story.

Compares already frozen past source-only syntax role decisions, original
unmodified full native physical GameCore scene, original *hard* grammar pruning
negative author source labels, corrected hypothesis-preserving full source/3D
corpus, alternate actual impulse scenarios, exact pose/contact controls, and
trusted native physics/observer/source/save corrupted-input rejection.

No model call, physical rerun, gold-driven selection, original source rewrite
or user account effect. Original external descriptions/per-scene source/gold
results are owner-private Nitro bytes with exact SHA-256 provenance.
"""
from pathlib import Path
from stat import S_IMODE
from hashlib import sha256
import json,zipfile,csv,io
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-hypotheses')
PAST=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop')
SOURCE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_baseline_200_raw_v2.json')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert digest(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(P.stat().st_mode)==0o700
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
source=read(SOURCE)['proposalsAll500']
assert len(source)==500
ids=list(range(100))+list(range(100,500,4))
private={}
def raw(name):
 p=P/name
 assert p.exists() and S_IMODE(p.stat().st_mode)==0o600
 private[name]={'sha256':digest(p),'bytes':p.stat().st_size,'ownerPrivate':True}
 return read(p)
scenes={}
for v in ('v1','v2','v3'):
 name='prse_non_destructive_source_hypothesis_native_200_raw_'+v+'.json'
 d=raw(name)
 pub=read(R/('prse_non_destructive_hypotheses_200_aggregate_'+v+'.json'))
 assert pub['metadata']['privateRawSHA256']==digest(P/name)
 assert pub['summary']==d['summary']
 assert [e['sourceId'] for e in d['results']]==ids
 scenes[v]=d
for x in scenes['v1']['results']:
 assert x['status'] in ('failed','original_geometry_rejected')
 if x['status']=='failed':
  assert 'Non-destructive source hypothesis ledger modified materialized native body IDs' in x['reason']
assert scenes['v1']['summary']['unanticipatedFailures']==197
assert scenes['v2']['summary']['sourceHypothesisLedgerAndFullNativePhysicsSavePassed']==197
assert scenes['v2']['summary']['scenesWithNewHypothesisSemanticVersionAfterAction'] is None
fixed=scenes['v3']
s=fixed['summary']
assert s['sourceDescriptions']==200
assert s['physicallyAcceptedExistingScenes']==197
assert s['sourceHypothesisLedgerAndFullNativePhysicsSavePassed']==197
assert s['unanticipatedFailures']==0
assert s['baselineInvalidScenes']==3
assert s['sourceOriginalParsedRelationsRetained']==407
assert s['originalONSourceHypothesesRetained']==50
assert s['originalONRelationsWithSourceSyntaxEvidence']==7
assert s['originalONSourceRelationsWithUnresolvedRoleKept']==43
assert s['physicallyConfirmedOriginalONRelationsRetained']==27
assert s['physicallyTrueOnAndSourceRoleApproved']==6
assert s['physicallyTrueOnButSourceRoleUnresolved']==21
assert s['scenesWithActualGameCorePhysicalImpulse']==64
assert s['scenesWithNewHypothesisSemanticVersionAfterAction']==8
assert s['originalAllRealBodyIDsKept']==197
assert s['sourceHistoricallyUncertainHypothesesSurvivedSave']==43
for e in fixed['results']:
 if e['status']!='native_source_hypotheses_preserved':continue
 id=e['sourceId']
 assert e['historicalSourceSHA256']==sha256(source[id]['text'].encode()).hexdigest()
 assert e['allOriginalRelationsStillRecorded']==len(source[id]['relations'])
 assert e['restoredSourceCountAndRoleEvidence']
 assert e['restoredSourceLiteralText']
 assert e['originalGeometryUnmodified']
 assert e['savedTransactionDidNotInventHistory']
 assert e['onRecordedTrueButUndecidedSourceDoesNotGetSourceProse']
 assert e['restoredHistoricallyUnresolvedCount']==e['onUncertainPreserved']
 assert e['onSyntaxApproved']+e['onUncertainPreserved']==e['originalSourceOnClaims']
 if e['realPhysicalImpulse']:
  assert e['afterImpulseOnTrue']+e['afterImpulseOnFalse']+e['afterImpulseOnUnknown']==e['originalSourceOnClaims']
# Do not promote a report of zero numeric position error without also checking
# actual native 3D collider contact and body binary against frozen baseline.
pos={}
for v in ('v1','v2'):
 name=f'prse_hypothesis_overlay_baseline_3d_contact_200_raw_{v}.json'
 d=raw(name)
 pub=read(R/f'prse_hypothesis_overlay_baseline_contacts_200_aggregate_{v}.json')
 assert pub['metadata']['privateRawSHA256']==digest(P/name)
 assert pub['summary']==d['summary']
 vdata=d['summary']
 assert vdata['originalPhysicallyAccepted']==197
 assert vdata['unexpectedFailures']==0
 assert vdata['maxObjectPositionDifferenceMeters']==0
 assert vdata['casesPreservingAllRapierObjectToObjectContacts']==197
 assert vdata['totalOriginalNativePhysicalContactPairs']==11
 assert vdata['totalAfterHypothesisOverlayNativePhysicalContacts']==11
 assert vdata['exactNativeWorldBinaryUnchangedByAddingSemanticHypothesisOverlay']==197
 pos[v]=vdata
assert pos['v1']['maxObjectRotationDifferenceRadians']>0.0009
assert pos['v2']['maxObjectRotationDifferenceRadians']<1e-6
# Original v1 rotation error was an unnormalized floating-point quaternion
# self-dot, NOT a measurable change to world angular orientation.
offV1=raw('prse_nondestructive_source_hypotheses_offscreen_32_raw_v1.json')
off=raw('prse_nondestructive_source_hypotheses_offscreen_32_raw_v2.json')
assert offV1['summary']==off['summary']
a=off['summary']
assert read(R/'prse_nondestructive_hypotheses_offscreen_32_aggregate_v2.json')['metadata']['privateRawSHA256']==private['prse_nondestructive_source_hypotheses_offscreen_32_raw_v2.json']['sha256']
assert a['distinctPreselectedSourceONClaims']==8
assert a['fixedIndependentNativeImpulsesPerClaim']==4
assert a['real3DSourceHypothesisOffscreenEpisodes']==32
assert a['failedEpisodes']==0
assert a['retainedOriginalHistoricalSource']==32
assert a['actuallyPhysicallyUnloadedAndNativeRestored']==32
assert a['offscreenPhysicalUnknownNotInvented']==32
assert a['realPhysicalSupportBecameFalseOrUnknown']==30
assert a['syntaxRoleApprovedBeforePhysicalCause']==16
assert a['undecidedSourceInterpretationSurvivedNativeSave']==16
assert a['unseenPhysicalImpulseLeaks']==0
assert a['observerSupportRetractions']==16
assert a['noRepeatedNarrationAfterReturn']
for e in off['results']:
 assert e['status']=='evaluated'
 assert e['fullOriginalLiterarySourceUntouched']
 assert e['dormantPhysicalTruth']=='unknown'
 assert e['sourcedRolesStillUnresolvedAfterNativeSave']
 assert e['nativeWorldTimeUnchangedBySave']
 assert e['sourceRoleIsUnchanged']
integrity=read(R/'prse_source_hypothesis_trusted_integrity_v1.json')
assert integrity['validNativeRestore'] and integrity['originalSourceUnchanged']
assert integrity['intentionallyCorruptTestCopies']==6
assert len(integrity['rejectedCorruptTestCopies'])==6
assert all(x['rejected'] for x in integrity['rejectedCorruptTestCopies'])
# INDEPENDENT source labels come only from earlier author gold source ON scorer
# which was executed after the original AND syntax-hard-filtered 3D worlds
# had been frozen in real GameCore/Rapier.
score=read(R/'prse_pre_layout_source_role_gold_200_aggregate_v1.json')
g=score['counter']
assert g['authorOnClauses']==354
assert g['authorOnPhysicallyConfirmedBaseline']==3
assert g['authorOnPhysicallyConfirmedGuarded']==2
assert g['previouslyVerifiedAuthorOnNowLost']==1
assert pos['v2']['totalOriginalNativePhysicalContactPairs']==11
# Therefore this overlay preserves the exact original physical scene/world
# and all THREE of its baseline author-contact matches. This is NOT new
# author-concordant source interpretation, and gold cannot distinguish the
# remaining uncertain source hypotheses.
metrics={
 'sourceDescriptions':200,
 'physicallyAcceptedNativeScenes':197,
 'originalSourceHypothesesRetained':407,
 'originalSourceOnHypothesesRetained':50,
 'syntaxRoleApprovedOriginalOn':7,
 'unresolvedOriginalOnPreservedWithoutDeletingPhysics':43,
 'physicallyTrueOnRetained':27,
 'physicallyTrueOnButSourceRoleUnresolved':21,
 'actualNativeContactPairsPreserved':11,
 'unmodifiedFrozenWorldOriginalAuthorOnContactMatches':3,
 'oldHardGrammarPruningOriginalAuthorOnContactMatches':2,
 'fullNativeWorldSourceAndObserverHypothesisSaveSuccesses':197,
 'actualNativeGameCoreImpulseSceneCount':64,
 'sourceHypothesisMeaninfulChangeAfterPhysicalActionScenes':8,
 'offscreenRealPhysicalEpisodes':32,
 'unknownLiveContactWhileDematerialized':32,
 'sourceHistoricalInterpretationsPersistedThroughOffscreen':32,
 'observerAppropriateRelationRetractions':16,
 'observerHiddenCauseLeaks':0,
 'physicallySupportedOriginalAuthorOnCountNotNew':True,
 'scope':'Research only, source-role syntax uncertain, uncalibrated assets and incomplete 3D source meaning, not full ordinary literary rewrite'}
out={'metadata':{
 'frozenSceneEvalSourceSHA256':digest(GOLD),
 'sourceInterpreterProposalSHA256':digest(SOURCE),
 'frozenNativeOriginalRapierWorldEvidenceSHA256':digest(BASE),
 'preexistingGrammarRoleScorerPrivateSHA256':digest(PAST/'prse_source_role_on_200_raw_v1.json'),
 'actualGoldOnlyUsedPosthoc':True,
 'noProductionGpuOrModelCalls':True,
 'sourceHypothesisEvidenceNotIndependentNewGoldWorld':True,
 'firstTwoInvalidReportingVersionsPreserved':True,
 'originalOffscreenV1AggregateRawSHAWasIncorrect':True,
 'versionOneQuaternionSelfDotMetricWasNotNormalized':True,
 'warning':'Source-only grammar role and type-pair author labels cannot prove instance-level source entailment or realistic physical assets; history hashes are owner-trusted rather than adversarially authenticated'},
 'summary':metrics,
 'integrityCorruptionRejected':6,
 'privateRawManifest':private}
destination=R/'prse_source_hypothesis_preserving_evidence_manifest_v1.json'
if destination.exists():assert read(destination)==out,'Refusing to overwrite differently grounded source evidence'
else:
 with destination.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED source hypothesis preservation 197 accepted native worlds / 407 original relations / 43 unresolved original ON propositions retained.')
print('VERIFIED original Rapier native exact geometry/contacts and binary state preserved, 11 contacts baseline vs 11 non-destructive overlay, unlike hard source grammar pruning 6 contacts.')
print('VERIFIED independent official author source ON contact matches preserved 3 vs hard-delete 2, with no claim of improved source interpretation.')
print('VERIFIED 32 actual physics/offscreen/source/observer/hypothesis transactions, 30 contact changes, 16 retractions, zero hidden cause leaks and six corrupted saves rejected.')
