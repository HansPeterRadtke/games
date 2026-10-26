#!/usr/bin/env python3
"""Round 3 POST-FROZEN source entailment / physical authority / reference
version audit. Runs ONLY after the earlier 130-scene Rapier v2 worlds
and source-only proposals are immutable. This is a POSTHOC error analysis,
not independent human negative annotation or a new language-model test.

Do not substitute reference object_name grouping names for instance IDs,
or convert physical contact into author source entailment.
"""
from pathlib import Path
from stat import S_IMODE
from collections import defaultdict,Counter
import hashlib,json,math,re
ROOT=Path(__file__).resolve().parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-hard-negatives-r3')
PRIV.mkdir(parents=True,exist_ok=True,mode=0o700);PRIV.chmod(0o700)
B=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
V=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-source-extended-v1')
FULL=B/'lego_full_data_public_human_gold.json'
SRC=B/'lego_source_only_frozen_130_raw_v1.json'
SOURCE_EXT=V/'lego_extended_source_only_130_raw_v1.json'
NATIVE=V/'lego_extended_actual_native_matched_130_raw_v2.json'
FAILED=V/'lego_extended_actual_native_matched_130_raw_v1.json'
LEGACY=B/'lego_source_only_matched_native_130_raw_v1.json'
REF=B/'reference-snapshots'
EARLIER=B/'lego_independent_human_gold_source_and_3d_reference_score_v2.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
for p in (FULL,SRC,SOURCE_EXT,NATIVE,FAILED,LEGACY,EARLIER):
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600, p
gold=read(FULL)
original=read(SRC)
proposals=read(SOURCE_EXT)
native=read(NATIVE)
bad=read(FAILED)
legacy=read(LEGACY)
extract=read(EARLIER)['posthocExtractedGoldON']
assert len(gold)==len(original['scenes'])==len(proposals['scenes'])==len(native['rows'])==130
assert native['summary']['accepted']==130 and native['summary']['experimentFailures']==0
assert bad['summary']['accepted']==82 and bad['summary']['experimentFailures']==48
assert native['metadata']['sourceProposalSHA256']==digest(SOURCE_EXT)
assert native['metadata']['originalLegacyFrozenSHA256']==digest(LEGACY)
assert proposals['metadata']['inputFrozenSourceOnlySHA256']==digest(SRC)
assert original['metadata']['rawFullDataSHA256']==digest(FULL)
assert native['metadata']['referenceGoldNeverOpened'] and native['metadata']['previouslyDeniedRandomPlacementNotAttempted']
assert native['summary']['samePhysicalBodiesInEachArm']==678
assert native['summary']['extraSourceLinkedActualNativeBodies']==103

def norm(s):
 s=s.lower().replace(' ','_').replace('-','_')
 return {'television':'tv','refrigerator':'fridge','bedside_lamp':'lamp','bunk_bed':'bed'}.get(s,s)
def tilt(q):
 n=math.hypot(q['x'],q['y'],q['z'],q['w'])
 if n<.5:return math.pi
 y=1-2*(q['x']*q['x']+q['z']*q['z'])/(n*n)
 return math.acos(max(-1,min(1,y)))
def native_supported(state,child,support):
 by=defaultdict(list)
 for e in state['bodyStates']:by[norm(e['kind'])].append(e)
 touching={frozenset((p['a'],p['b'])) for p in state['contactPairs'] if p.get('contactPointCount',0)>0}
 for p in by[support]:
  if p['shape']!='box' or tilt(p['rotation'])>.1:continue
  for e in by[child]:
   if e['id']==p['id'] or tilt(e['rotation'])>.1:continue
   if any(abs(e['position'][k]-p['position'][k])+e['size'][k]/2>p['size'][k]/2+.03 for k in ('x','z')):continue
   dy=(e['position']['y']-e['size']['y']/2)-(p['position']['y']+p['size']['y']/2)
   if abs(dy)>.08:continue
   if frozenset((e['id'],p['id'])) in touching:return True
 return False

# Adjudication of the previous mechanically extracted sixteen "gold ON"
# clauses. Labels are PERSON-written independent positives, but category-pair
# derivation and NEGATIVE classifications here are explicitly auditor-created
# after inspecting the source, not human negative gold or unseen test data.
NONVERTICAL={2,11,12,17,25,51,52,64,67,68,122}
VERTICAL={53,65,120,121}
COMPOSITE={54}
assert len(NONVERTICAL|VERTICAL|COMPOSITE)==16
assert len(extract)==16
assert {r['scene'] for r in extract}==NONVERTICAL|VERTICAL|COMPOSITE
# Human authored direct support positives omitted by the old 16-claim
# automatic scorer, paired with the ORIGINAL human label condition_idx.
NEW_SUPPORT={(28,'blanket','bed','4'),(31,'projector','table','7'),
 (34,'computer','desk','11'),(38,'computer','desk','9'),
 (44,'telephone','desk','7'),(48,'computer','desk','7')}
m=Counter()
case_rows=[]
for row in extract:
 i=row['scene']
 label=next(x for x in gold[i]['labels'] if x['condition_idx']==row['constraintIndex'])
 source_clause=' '.join(label['instructions'])
 assert source_clause
 category='nonvertical' if i in NONVERTICAL else 'vertical' if i in VERTICAL else 'composite_unknown'
 old=native_supported(native['rows'][i]['baseline'],row['derivedChild'],row['derivedParent'])
 new=native_supported(native['rows'][i]['candidate'],row['derivedChild'],row['derivedParent'])
 m['old16_machine_claims']+=1
 m['original_machine_gold_nonvertical']+=category=='nonvertical'
 m['original_machine_gold_composite_unknown']+=category=='composite_unknown'
 m['original_machine_gold_direct_vertical']+=category=='vertical'
 if category=='vertical':
  m['strict_vertical_source_positive_control']+=int(old)
  m['strict_vertical_source_positive_new']+=int(new)
 elif category=='nonvertical':
  m['nonvertical_source_control_contact_unsupported']+=int(old)
  m['nonvertical_source_new_contact_unsupported']+=int(new)
 case_rows.append({'scene':i,'relation':[row['derivedChild'],row['derivedParent']],
   'sourceHumanLabelIdx':row['constraintIndex'],'sourceClaimHash':hashlib.sha256(source_clause.encode()).hexdigest(),
   'posthocHumanPhraseAdjudication':category,
   'realRapierDirectedTopSupportControl':old,'realRapierDirectedTopSupportCandidate':new,
   'notOriginalHumanNegativeAnnotations':True})
for i,child,support,condition_idx in sorted(NEW_SUPPORT):
 label=next(x for x in gold[i]['labels'] if x['condition_idx']==condition_idx)
 claim=' '.join(label['instructions'])
 assert (child in claim.lower() or (child=='blanket' and 'blanket' in claim.lower()))
 assert (support in claim.lower() and ' on ' in ' '+claim.lower()+' ')
 old=native_supported(native['rows'][i]['baseline'],child,support)
 new=native_supported(native['rows'][i]['candidate'],child,support)
 assert not old and new,('Previously claimed physical improvement not supported by real Rapier',i)
 m['posthoc_six_direct_human_positive_added']+=1
 m['posthoc_six_new_physical_support_gains']+=int(new and not old)
 case_rows.append({'scene':i,'relation':[child,support],'sourceHumanLabelIdx':condition_idx,
   'sourceClaimHash':hashlib.sha256(claim.encode()).hexdigest(),
   'posthocHumanPhraseAdjudication':'direct_vertical',
   'realRapierDirectedTopSupportControl':old,'realRapierDirectedTopSupportCandidate':new,
   'mayLackUniqueInstanceAndRoomGrounding':True})
assert m['old16_machine_claims']==16
assert m['original_machine_gold_nonvertical']==11
assert m['original_machine_gold_direct_vertical']==4
assert m['original_machine_gold_composite_unknown']==1
assert m['strict_vertical_source_positive_control']==3
assert m['strict_vertical_source_positive_new']==3
assert m['nonvertical_source_new_contact_unsupported']==1
assert m['posthoc_six_direct_human_positive_added']==6
assert m['posthoc_six_new_physical_support_gains']==6
m['conditional_selected_explicit_vertical_gold']=4+6
m['conditional_selected_explicit_vertical_supported_control']=3
m['conditional_selected_explicit_vertical_supported_candidate']=9
m['conditional_selected_explicit_vertical_missed_new']=1
m['source_nonvertical_negative_controls']=11
m['source_nonvertical_contradictory_support_new']=1

# The natural source's original source versions and every reference query
# must be identical to author instructions. Never infer uniqueness from
# object_name: it can name a composite group containing DIFFERENT true ids.
natural_non_top=re.compile(r'\bon\s+(?:either\s+side|(?:the|one|other|same|each|both|another)\s+side|the\s+(?:left|right|wall|walls|floor|ceiling)|tracks)\b',re.I)
raw_stale=0
all_ref_objs=0;id_group_links=0;no_objname=0;duplicate_obj_ids=0;distinct_name_collision=0;misnamed=0
source_top_false_proposals=[]
for i,(g,src,pr,n) in enumerate(zip(gold,original['scenes'],proposals['scenes'],native['rows'])):
 assert src['sourceIndex']==pr['sourceIndex']==n['id']==i
 assert src['sourceText']==g['instruction']
 assert hashlib.sha256(g['instruction'].encode()).hexdigest()==pr['sourceHash']==n['sourceHash']
 assert n['status']=='matched_native_3d_saved'
 assert isinstance(n['baseline']['bodyStates'],list) and isinstance(n['candidate']['bodyStates'],list)
 ids0={x['id'] for x in n['baseline']['bodyStates']};ids1={x['id'] for x in n['candidate']['bodyStates']}
 assert ids0==ids1
 for x in n['candidate']['bodyStates']:
  y=next(z for z in n['baseline']['bodyStates'] if z['id']==x['id'])
  assert y['kind']==x['kind'] and y['size']==x['size'] and y['shape']==x['shape'] and y['body']==x['body']
 if n['sourcePlacements']==0:
  assert sorted(tuple(sorted((x['a'],x['b']))) for x in n['baseline']['contactPairs'])==sorted(tuple(sorted((x['a'],x['b']))) for x in n['candidate']['contactPairs'])
 rfile=REF/f'data_{i}.json'
 assert rfile.is_file() and S_IMODE(rfile.stat().st_mode)==0o600
 ref=read(rfile)
 assert ref['query']==g['instruction'] and ref['index']==i
 all_ref_objs+=len(ref['objects'])
 id_groups=Counter(z['id'] for z in ref['objects'])
 duplicate_obj_ids+=sum(v-1 for v in id_groups.values() if v>1)
 grouped=defaultdict(list)
 for o in ref['objects']:
  id_group_links+=int('|' in o['id'])
  no_objname+=int(not o.get('object_name'))
  if o.get('object_name'):
   grouped[(o['roomId'],o['object_name'])].append(o)
   idtype=re.sub(r'-\d+.*$','',o['id'].split('|')[0])
   nametype=re.sub(r'-\d+.*$','',o['object_name'])
   misnamed+=int(idtype!=nametype)
 distinct_name_collision+=sum(v.__len__()-1 for v in grouped.values() if len(v)>1)
 for bad_prep in natural_non_top.finditer(g['instruction']):
  m['source_original_nontop_preposition_instances']+=1
  for x in pr['pretrainedOn']:
   offset=x['sourceCharPositions'][2]
   if bad_prep.start()<=offset<bad_prep.end():
    source_top_false_proposals.append({'scene':i,'at':offset,'proposal':[x['a'],x['b']]})
m['all_reference_object_entries']=all_ref_objs
m['reference_id_contains_child_parent_link']=id_group_links
m['reference_missing_object_name_but_id_usable']=no_objname
m['reference_repeated_object_ids']=duplicate_obj_ids
m['reference_duplicate_room_objectname_entries']=distinct_name_collision
m['reference_object_id_vs_object_name_prefix_mismatches']=misnamed
m['source_top_false_proposals_on_natural_nontop_prepositions']=len(source_top_false_proposals)
assert all_ref_objs==6844 and no_objname==2950
assert duplicate_obj_ids>=1 and distinct_name_collision>=1
assert not source_top_false_proposals
# Explicit original human case 28 speaks of a bed in two different rooms,
# whereas the source-only compiler materializes only a single global bed.
t=gold[28]['instruction'].lower()
assert ('study room' in t and 'bathroom' in t and 'bed in the bathroom' in t)
r28=native['rows'][28]
assert sum(x['kind']=='bed' for x in r28['candidate']['bodyStates'])==1
ref28=read(REF/'data_28.json')
assert {'study room','bathroom'}.issubset({x['roomId'] for x in ref28['objects'] if x['id'].startswith('bed-')})
m['documented_two_room_bed_instance_collapse_example']=1

private=PRIV/'round3_human_source_claims_and_native_gold_audit_v1.json'
with private.open('x') as f:
 json.dump({'perCase':case_rows,'naturalNonTopCandidateLeaks':source_top_false_proposals},f,indent=2);f.write('\n')
private.chmod(0o600)
result={'metadata':{
 'basis':'Frozen earlier author original 130 LEGO human instructions and independent human positive constraints; NEW posthoc hard semantic adjudication',
 'frozenIndependentHumanSourceSHA256':digest(FULL),
 'frozenSourceOnlyExpandedSHA256':digest(SOURCE_EXT),
 'frozenNewActualNativeGameCoreSHA256':digest(NATIVE),
 'invalidResearchV1PreservedSHA256':digest(FAILED),
 'priorFrozenNativeSHA256':digest(LEGACY),
 'originalPreexistingGoldExtractorSHA256':digest(EARLIER),
 'privateDetailedAuditSHA256':digest(private),
 'noGenerationOrPhysicsRunHere':True,
 'posthocAuditorNegativeLabelsNotHumanExhaustiveNegatives':True,
 'controlledCategoriesSelectedFromEarlierFalseGoldPlusSixAlreadyObservedGains':True,
 'notAnUnseenDomainEstimate':True,
 'realNativeRapierContactsDistinctFromOriginalAuthorEntailment':True,
 'unidentifiedSourceObjectsAndNoWorldSpecificRoomIDsRemain':True,
 'explicitOriginalNaturalLanguageNotSyntheticGeneratedTexts':True,
 'frozenModelAndAllVersionedInvalidEvidenceUnchanged':True},'measured':dict(m)}
output=ROOT/'round3_independent_human_source_hard_negative_gold_aggregate_v1.json'
with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('ROUND3_STRICT_HUMAN_HARD_GOLD_AUDIT',json.dumps(dict(m),sort_keys=True))
