#!/usr/bin/env python3
"""READ-ONLY round-three evidence verification, run safely repeatedly.
Uses earlier frozen genuine GameCore/Rapier output and this round's distinct
native impulse/offscreen original-human-source stress, checks source version
and protected private bytes. Never runs or repeats an original placement.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
import json,math
HERE=Path(__file__).resolve().parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-hard-negatives-r3')
EXIST=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
GOLD=EXIST/'lego_full_data_public_human_gold.json'
SRC=EXIST/'lego_source_only_frozen_130_raw_v1.json'
INPUT=FROZEN/'lego_extended_source_only_130_raw_v1.json'
OLD=FROZEN/'lego_extended_actual_native_matched_130_raw_v1.json'
NATIVE=FROZEN/'lego_extended_actual_native_matched_130_raw_v2.json'
HARD=PRIV/'round3_hard_original_human_native_causal_observer_raw_v1.json'
AUDIT=PRIV/'round3_human_source_claims_and_native_gold_audit_v1.json'
SA=HERE/'round3_independent_human_source_hard_negative_gold_aggregate_v1.json'
SN=HERE/'prse_round3_hard_human_native_causal_observer_aggregate_v1.json'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert S_IMODE(PRIV.stat().st_mode)==0o700
for path in (GOLD,SRC,INPUT,OLD,NATIVE,HARD,AUDIT):
 assert path.is_file() and S_IMODE(path.stat().st_mode)==0o600, (path,'private source protection')
source=load(SRC);native=load(NATIVE);legacy=load(OLD);gold=load(GOLD)
a=load(SA);n=load(SN);raw=load(HARD);audit=load(AUDIT)
assert len(source['scenes'])==len(native['rows'])==len(gold)==130
assert legacy['summary']['accepted']==82 and legacy['summary']['experimentFailures']==48
assert native['summary']['accepted']==130 and native['summary']['experimentFailures']==0
assert native['summary']['samePhysicalBodiesInEachArm']==678
assert native['summary']['extraSourceLinkedActualNativeBodies']==103
assert native['summary']['trueNewNativeSourceContacts']==6
assert native['summary']['originalNativeContactsLost']==0
assert sha(GOLD)==a['metadata']['frozenIndependentHumanSourceSHA256']
assert sha(INPUT)==a['metadata']['frozenSourceOnlyExpandedSHA256']
assert sha(NATIVE)==a['metadata']['frozenNewActualNativeGameCoreSHA256']==raw['metadata']['originalFrozenRealRapierV2SHA256']
assert sha(OLD)==a['metadata']['invalidResearchV1PreservedSHA256']
assert sha(AUDIT)==a['metadata']['privateDetailedAuditSHA256']
assert sha(HARD)==n['metadata']['privateRawSHA256']
assert sha(SRC)==raw['metadata']['originalHumanLEGOTextSHA256']
assert n['summary']==raw['summary']
m=a['measured']
for name,count in {
 'old16_machine_claims':16,'original_machine_gold_nonvertical':11,
 'original_machine_gold_direct_vertical':4,'original_machine_gold_composite_unknown':1,
 'source_nonvertical_negative_controls':11,
 'nonvertical_source_new_contact_unsupported':1,
 'conditional_selected_explicit_vertical_gold':10,
 'conditional_selected_explicit_vertical_supported_control':3,
 'conditional_selected_explicit_vertical_supported_candidate':9,
 'conditional_selected_explicit_vertical_missed_new':1,
 'posthoc_six_direct_human_positive_added':6,
 'posthoc_six_new_physical_support_gains':6,
 'source_original_nontop_preposition_instances':54,
 'source_top_false_proposals_on_natural_nontop_prepositions':0,
 'all_reference_object_entries':6844,
 'reference_missing_object_name_but_id_usable':2950,
 'reference_id_contains_child_parent_link':2938,
 'reference_duplicate_room_objectname_entries':51,
 'reference_repeated_object_ids':6,
 'reference_object_id_vs_object_name_prefix_mismatches':50,
 'documented_two_room_bed_instance_collapse_example':1
 }.items():assert m[name]==count,(name,m.get(name),count)
assert len(audit['perCase'])==22
assert sum(x['posthocHumanPhraseAdjudication']=='nonvertical' for x in audit['perCase'])==11
assert sum(x['posthocHumanPhraseAdjudication']=='direct_vertical' for x in audit['perCase'])==6
assert all(x['notOriginalHumanNegativeAnnotations'] for x in audit['perCase'] if x['posthocHumanPhraseAdjudication']=='nonvertical')
r=n['summary']
assert r['humanOriginalSourceCases']==7
assert r['realNativePhysicalWorldsAndSemanticPersistenceCompleted']==7
assert r['runtimeFailures']==0
assert r['trueNewImpulseCases']==r['physicallyMovedImpulseSubjects']==r['currentSemanticChangedAfterActualMotion']==6
assert r['actualPhysicsOffscreenUnloads']==r['originalSourceAndBodyIDsAllRestored']==7
ids=[17,28,32,53,54,120,121]
assert [p['id'] for p in raw['records']]==ids
for test in raw['records']:
 i=test['id']
 assert test['originalSourceHash']==source['scenes'][i]['sourceHash']
 assert test['status']=='real_rapier_causal_semantic_offscreen_saved'
 assert test['originalSourcePreserved'] and test['postRestoreOriginalSourcePreserved']
 assert test['postRestoreAllIDsPresent'] and test['postRestoreCurrentDocumentExact']
 assert test['offscreenActuallyUnloaded']
 if test['dynamicChildPresent']:
  assert test['impulseProducedActualMovement']
  assert test['impulseActualMotionMeters']>.03
  assert test['afterImpulseCurrentDocumentChanged'] and test['afterImpulseSourceStillOriginal']
print('VERIFIED ROUND 3: exact earlier v1-invalid/v2-valid/source SHA versions and private permissions;')
print('16 posthoc adjudicated human authored source clauses, 54 natural nonvertical preposition controls,')
print('6 additional author-positive real Rapier top contacts and 11 unsupported-source risk checks,')
print('independent reference scene object naming/ID caveats, 7 genuine native causal/offscreen stress worlds,')
print('6 measured physical impulses, 7 exact source/object-ID restores. No denied placebo executed.')
