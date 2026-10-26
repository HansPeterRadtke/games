#!/usr/bin/env python3
"""INDEPENDENT POST-FROZEN annotation scorer for Nr3D/ScanEnts3D.
This is the first script allowed to read original CSV target_id,
instance_type, correct_guess and independent phrase-3D object-id annotations.
All source-only outputs and pre-registration are immutable (SHA-checked).
Measures cross-genre instance-class transfer, not 3D mesh accuracy.
"""
import ast,csv,hashlib,json,math,re,statistics,time,random
from pathlib import Path
from collections import Counter,defaultdict
from stat import S_IMODE
from scipy.stats import binomtest
ROOT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7')
HERE=Path(__file__).resolve().parent
PRE=ROOT/'PREREG_ORIGINAL_FROZEN_BEFORE_GOLD.md'
S=ROOT/'ScanEnts3D_Nr3D_official_raw.csv'
SRC=ROOT/'nr3d_one_per_scene_480_sourceonly_frozen_v1.json'
FROZEN=ROOT/'nr3d_source_only_predictions_480_frozen_v1.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert S_IMODE(ROOT.stat().st_mode)==0o700
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (PRE,S,SRC,FROZEN))
assert sha(PRE)=='688fc6d8199b30617a481460386de87a329f8ceeea1f255d2774b7416d06076f'
assert sha(S)=='f6b437e2bfc15c69c2b497c755e9a5b42eec110dccc25deb29594e3734a31f5b'
p=read(FROZEN)
assert p['metadata']['preregSHA256']==sha(PRE)
assert p['metadata']['sourceOnlyFrozenCohortSHA256']==sha(SRC)
assert p['metadata']['noHumanGroundTruthFieldsOpened']
cohort=read(SRC)['sourceCohort']
assert len(p['records'])==len(cohort)==480
mapindex={r['datasetIndex']:r for r in p['records']}
assert len(mapindex)==480
for a,b in zip(cohort,p['records']):
 assert a['datasetIndex']==b['datasetIndex'] and a['scanId']==b['scanId']
 assert a['sourceHash']==b['sourceHash']==hashlib.sha256(a['text'].encode()).hexdigest()
 assert a['text']==b['text']
def canon(x):
 return re.sub('[^a-z0-9]+','_',x.casefold()).strip('_')
def wilson(k,n,z=1.959963984540054):
 if n==0:return [None,None]
 d=1+z*z/n
 mu=(k/n+z*z/(2*n))/d
 hw=z*math.sqrt((k/n)*(1-k/n)/n+z*z/(4*n*n))/d
 return [round(mu-hw,6),round(mu+hw,6)]
counts=Counter();rows=[];t=time.perf_counter()
with S.open(newline='',encoding='utf-8') as f:
 reader=csv.DictReader(f)
 for r in reader:
  i=int(r['index'])
  if i not in mapindex:continue
  frozen=mapindex[i]
  assert r['scan_id']==frozen['scanId'] and r['utterance']==frozen['text']
  target=canon(r['instance_type'])
  # scan referential target identity annotations from independent human
  # phrase-to-3D object IDs. Never infer a body position or mesh from these.
  try:
   anns=ast.literal_eval(r['entities'])
  except Exception:
   anns=[]
  aid=r['target_id']
  targets=[]
  for chunk in anns:
   if not isinstance(chunk,(tuple,list)) or len(chunk)!=2:continue
   ts,names=chunk
   if not isinstance(names,(tuple,list)):continue
   for ent in names:
    if not isinstance(ent,str) or '_' not in ent:continue
    number,kind=ent.split('_',1)
    if number==aid:
     targets.append({'type':canon(kind),'tokenIndexes':ts,
                     'officialTargetClassFromDataset':target})
  # Some entity annotation instances have no target phrase indexed; DON'T
  # falsify that into a model extraction mistake, score target class separately.
  baseline=frozen['baselineTargetType']
  proposed=frozen['sourceOnlyPretrainedTargetType']
  b=canon(baseline['kind']) if baseline else None
  c=canon(proposed['kind']) if proposed else None
  success_b=int(b==target) if b is not None else 0
  success_c=int(c==target) if c is not None else 0
  flags={k:r[k] for k in ('correct_guess','uses_spatial_lang','uses_object_lang','uses_color_lang','uses_shape_lang')}
  row={'sourceId':i,'scanId':r['scan_id'],'sourceSHA256':frozen['sourceHash'],
       'officialTargetClass':target,'officialTarget3DInstanceId':aid,
       'officialTargetMentionFoundInIndependentEntitySpans':bool(targets),
       'independentGoldTargetPhraseSpans':targets,
       'baselinePredictedKind':b,'pretrainedPredictedKind':c,
       'baselineExactKindCorrect':bool(success_b),
       'pretrainedExactKindCorrect':bool(success_c),
       'sourceOnlyProposedPhysicalSupportCount':len(frozen['sourceOnlyOnTopProposal']),
       'hardNaturalTopNegations':len(frozen['explicitNaturalNontopCases']),
       'physicallyUnjustifiedOnProposalInNegatedOrSidePhrase':len(frozen['badSupportProposalOverlap']),
       'humanDatasetFlags':flags}
  rows.append(row)
  counts['scenes']+=1;counts['baseline_predicted']+=bool(b)
  counts['pretrained_predicted']+=bool(c)
  counts['baseline_exact_target_class']+=success_b
  counts['pretrained_exact_target_class']+=success_c
  counts['paired_candidate_gain']+=bool(success_c and not success_b)
  counts['paired_candidate_loss']+=bool(success_b and not success_c)
  counts['independent_human_entity_span_of_target_ID']+=bool(targets)
  counts['listener_correct']+=r['correct_guess']=='True'
  counts['uses_spatial_language']+=r['uses_spatial_lang']=='True'
  counts['natural_nontop_control_cases']+=bool(frozen['explicitNaturalNontopCases'])
  counts['nontop_overlap_errors']+=bool(frozen['badSupportProposalOverlap'])
  counts['source_only_proposed_on_relations']+=len(frozen['sourceOnlyOnTopProposal'])
assert len(rows)==480 and len({r['scanId'] for r in rows})==480
baseline=counts['baseline_exact_target_class']/480
cand=counts['pretrained_exact_target_class']/480
improvement=cand-baseline
b01=counts['paired_candidate_gain'];b10=counts['paired_candidate_loss']
pvalue=binomtest(min(b01,b10),b01+b10,0.5).pvalue if (b01+b10)>0 else 1.
rng=random.Random(20261026)
delta=[]
for b in range(10000):
 group=[rows[rng.randrange(480)] for _ in range(480)]
 delta.append(sum(r['pretrainedExactKindCorrect']-r['baselineExactKindCorrect'] for r in group)/480)
delta.sort()
lower,upper=delta[249],delta[9749]
m={
 'independent3DScanScenes':480,
 'originalHumanFreeformReferringExpressions':480,
 'humanCorrectGuessCases':counts['listener_correct'],
 'humanTargetPhrase3DObjectIdGoldAvailable':counts['independent_human_entity_span_of_target_ID'],
 'baselineSourceLexiconProposed':counts['baseline_predicted'],
 'baselineAllSourceExactTargetKind':counts['baseline_exact_target_class'],
 'baselineAllInputCorrectRate':round(baseline,6),
 'baselineAllInputWilson95':wilson(counts['baseline_exact_target_class'],480),
 'pretrainedSourceNounProposed':counts['pretrained_predicted'],
 'pretrainedAllSourceExactTargetKind':counts['pretrained_exact_target_class'],
 'pretrainedAllInputCorrectRate':round(cand,6),
 'pretrainedAllInputWilson95':wilson(counts['pretrained_exact_target_class'],480),
 'pretrainedConditionalExactPrecision':round(counts['pretrained_exact_target_class']/counts['pretrained_predicted'],6),
 'pretrainedConditionalPrecisionWilson95':wilson(counts['pretrained_exact_target_class'],counts['pretrained_predicted']),
 'pretrainedProposalCoverageWilson95':wilson(counts['pretrained_predicted'],480),
 'pretrainedMinusLexiconAllInputExactTargetGain':round(improvement,6),
 'pairedBySceneGain':b01,
 'pairedBySceneLoss':b10,
 'pairedExactMcNemarP':round(pvalue,10),
 'pairedBootstrap95Gain':[round(lower,6),round(upper,6)],
 'naturalNontopCaseCount':counts['natural_nontop_control_cases'],
 'naturalNontopFalseTopPromotionCount':counts['nontop_overlap_errors'],
 'naturalNontopFalseTopPromotionWilson95':wilson(counts['nontop_overlap_errors'],counts['natural_nontop_control_cases']),
 'unverifiedSourceOnlyOnProposalsCount':counts['source_only_proposed_on_relations'],
 'actualUnique3DInstanceIDsPredictedByEitherSourceOnlyMethod':0,
 'actualScanNetMeshDimensionsAndPhysicalSupportGold':'not available',
 'originalAuthorRoomScaleAndObserverProseFidelity':'not tested',
 'preregisteredSourceTransferAccepted':bool(cand>=.75 and improvement>=.10 and lower>0),
 'preregisteredFullPRSELiteraryWorldGeneralizationAccepted':False,
 'scoreWallSeconds':round(time.perf_counter()-t,3)
}
PRIVATE=ROOT/'nr3d_postfrozen_independent_human_3d_gold_percase_v1.json'
with PRIVATE.open('x') as f:
 json.dump({'rows':rows,'method':'original Nr3D official target type and annotated 3D phrase-to-object-id, gold accessed only postfrozen'},f,indent=2);f.write('\n')
PRIVATE.chmod(0o600)
out=HERE/'prse_round7_nr3d_independent_real3d_reference_aggregate_v1.json'
with out.open('x') as f:
 json.dump({'metadata':{
  'officialNr3dAnnotationCSVSourceSHA256':sha(S),
  'originalFrozenPreRegistrationSHA256':sha(PRE),
  'sourceOnlyFrozenPredictionSHA256':sha(FROZEN),
  'frozenHumanInputCohortSHA256':sha(SRC),
  'postFrozenIndependentAnnotationPerCaseSHA256':sha(PRIVATE),
  'noInstanceGeometryLoadedOrInvented':True,
  'independentHumanLabel':True,
  'unseenOutsideSceneEvalLEGO':True,
  'criticalLimitation':'Referring-expression target kind class accuracy is NOT 3D object instance identity or physical support/contact fidelity',
  'preRegisteredAcceptOrFailEnforcedWithoutLabelTuning':True},'metrics':m},f,indent=2);f.write('\n')
print('NR3D_INDEPENDENT_POSTFROZEN_EVALUATION',json.dumps(m,sort_keys=True),flush=True)
