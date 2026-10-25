#!/usr/bin/env python3
"""Independent PRSE open-vocabulary semantic noun → real native 3D outcome
verification. Checks exact source/GPU/model provenance, author labels only at
independent scoring, formerly missed types, extra unannotated candidate risk,
real Rapier placement and native full save, and paired scene-bootstrap counts.

ALL complete SceneEval source prose, spans, raw dynamic scene outcomes and gold
per-case labels stay owner-private on Nitro. Reuse already written evidence;
no inference or physical effects are replayed.
"""
import json,zipfile,io,csv,stat
from collections import Counter
from hashlib import sha256
from pathlib import Path
from stat import S_IMODE
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery')
MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl')
INPUT=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
ORIGINAL=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance/prse_source_quantity_physics_200_raw_v1.json')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert sha(MODEL)=='1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85'
assert stat.S_IMODE(P.stat().st_mode)==0o700
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as f:scenes=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(scenes)==500
original=read(INPUT)['proposalsAll500']
assert len(original)==500
name=[
 'prse_spacy_open_vocab_500_proposals_raw_v1.json',
 'prse_spacy_open_vocab_independent_gold_per_case_v1.json',
 'prse_spacy_open_vocab_native_200_raw_v1.json',
 'prse_spacy_open_vocab_native_independent_gold_cases_v1.json']
private={}
for n in name:
 p=P/n
 assert p.exists() and stat.S_IMODE(p.stat().st_mode)==0o600
 private[n]={'sha256':sha(p),'bytes':p.stat().st_size}
grammar=read(P/name[0])
assert grammar['summary']['sourceSHA256']==sha(INPUT)
assert grammar['summary']['goldAnnotationsNotReadOrImported']
assert len(grammar['records'])==500
for i,entry in enumerate(grammar['records']):
 assert entry['sourceText']==original[i]['text']==scenes[i]['Description']
 assert int(entry['id'])==i
 for n in entry['candidates']:
  assert entry['sourceText'][n['sourceOffsets'][0]:n['sourceOffsets'][1]]==n['sourceText']
  assert n['type'] and isinstance(n['count'],int) and n['count']>=0
textScore=read(R/'prse_spacy_open_vocab_gold_200_aggregate_v1.json')
assert textScore['meta']['frozenSourceProposalSHA256']==sha(P/name[0])
assert textScore['meta']['privateGoldAuditSHA256']==sha(P/name[1])
assert textScore['combined']['goldRequirements']==1237
assert textScore['combined']['matchedGoldByExisting3D']==565
assert textScore['combined']['matchedGoldBySourceNounCandidateOnly']==989
assert textScore['combined']['goldCorrectionsSuggestedBySyntax']==424
assert textScore['combined']['additionalPositiveTypeProposals']==922
assert textScore['combined']['additionalTypesNotInAuthorLabels']==491
actual=read(P/name[2]); physical=actual['summary']
assert physical['originalFrozenSourceScenes']==200
assert physical['originalPhysicallyAccepted']==physical['augmentedPhysicallyAcceptedAndRestored']==197
assert physical['rejectedByOriginalGeometry']==3
assert physical['rejectedAfterExtraGeometry']==physical['runtimeSaveFailures']==0
assert physical['addedActualGenericRapierBodies']==1110
assert physical['addedNewTypes']==889
assert physical['originalIDsAndTextPreserved']==197
assert physical['unknownGeometryAndPhysicalScaleForEveryNewNoun'] is True
ids=list(range(100))+list(range(100,500,4))
assert [x['sourceID'] for x in actual['records']]==ids
for row in actual['records']:
 if row['status']=='native_saved_and_reentered':
  assert row['addedActuallyNativePhysicalBodies']==row['added']
  assert row['sourceHistoricTextUnchanged'] and row['originalIDsUnaffected']
  assert all(e['provisionalShape'].startswith('generic_actual_Rapier_box')
   for e in row['addedProvenance'])
  assert all(x['sourceSpan'] and original[row['sourceID']]['text'][x['sourceSpan'][0]:x['sourceSpan'][1]]
   for x in row['addedProvenance'])
assert sum(r['status']=='native_saved_and_reentered' for r in actual['records'])==197
gold=read(R/'prse_spacy_open_vocab_native_gold_200_aggregate_v1.json')
assert gold['meta']['authorSceneEvalSHA256']==sha(CORPUS)
assert gold['meta']['frozenNativeAugmentedWorldSHA256']==sha(P/name[2])
assert gold['meta']['privateFullGoldAuditSHA256']==sha(P/name[3])
s=gold['total']
assert s['annotationCountClauses']==1237
assert s['baselineGoldClausesMatched']==565
assert s['augmentedGoldClausesMatched']==972
assert s['formerlyIncorrectNowCorrect']==407
assert s['formerlyCorrectNowBroken']==0
assert s['extraTypeInstances']==889
assert s['extraCandidateTypesNotAuthorAnnotated']==467
assert s['nativeGenericExtraBodies']==1110
assert s['unverifiedPhysicalDimensionsAndAppearance']==1110
assert s['goldStillUnsatisfied']==265
assert s['stillUndercounted']==263
assert s['physicalSceneUnacceptedOrFailure']==3
bootstrap=read(R/'prse_spacy_open_vocab_paired_uncertainty_v1.json')
for name,baseCount,augCount in [('human',310,437),('assisted',255,535)]:
 split=bootstrap['byGroup'][name]
 assert split['baselinePhysicallySatisfied']==baseCount
 assert split['augmentedPhysicallySatisfied']==augCount
 assert 0<split['sceneBootstrap95Difference'][0]<=split['recallDifference']<=split['sceneBootstrap95Difference'][1]
errorRaw=read(Path('/data/var/games/prse_semantic_research/runs/2026-10-25-quantity-provenance/prse_source_quantity_official_gold_per_case_v1.json'))['cases']
errors=Counter()
for row in errorRaw:
 if 'countClaims' not in row:continue
 for c in row['countClaims']:
  if c['physicalSatisfied']:continue
  if c['parserCount'] is None:errors['original_type_not_extracted']+=1
  elif c['physicalNum']==0:errors['recognized_but_zero']+=1
  elif c['physicalNum']<c['goldNum']:errors['recognized_but_undercounted']+=1
  else:errors['other']+=1
assert sum(errors.values())==672
assert errors['original_type_not_extracted']==620
assert errors['recognized_but_undercounted']==50
assert errors['other']==2
# RESEARCH CORRECTION: real native 3D categories need known physical size,
# collider and material/asset parameters. Assess second, strictly catalog-
# gated physical GameCore path separately from all-generic fallback.
catalogFile=P/'prse_spacy_open_vocab_catalog_native_200_raw_v1.json'
catalogGoldPrivate=P/'prse_spacy_open_vocab_catalog_postgold_cases_v1.json'
for n in [catalogFile,catalogGoldPrivate]:
 assert n.exists() and S_IMODE(n.stat().st_mode)==0o600
 private[n.name]={'sha256':sha(n),'bytes':n.stat().st_size}
catalog=read(catalogFile)
cat=catalog['metrics']
assert cat['originalSourceScenes']==200
assert cat['baselineAccepted']==cat['acceptedWithCatalogGate']==197
assert cat['addedApproxCategorySizeRealRapierBodies']==17
assert cat['addedSourceTypeInstances']==13
assert cat['runtimeFailures']==cat['moreRejectedThanBaseline']==cat['placementRefusals']==0
assert cat['candidateCategoriesRefusedForNoKnownGeometry']==916
assert [r['sourceId'] for r in catalog['results']]==ids
for r in catalog['results']:
 if r['status']=='accepted_native_3d_reentered':
  assert r['addedActualNativeBodies']==len(r['retainedCategories'])
  for entity in r['retainedCategories']:
   a,b=entity['sourceSpan']
   assert 0<=a<b<=len(original[r['sourceId']]['text'])
   assert entity['approxCategoryDimensions'] and entity['explicitUncertainty']
catAggregate=read(R/'prse_spacy_open_vocab_catalog_native_200_aggregate_v1.json')
assert catAggregate['metadata']['privateRawSHA256']==sha(catalogFile)
assert catAggregate['metrics']==cat
catGold=read(R/'prse_spacy_open_vocab_catalog_gold_200_aggregate_v1.json')
assert catGold['metadata']['frozenCatalogNativeResultSha256']==sha(catalogFile)
assert catGold['metadata']['privatePostGoldCaseSha256']==sha(catalogGoldPrivate)
assert catGold['total']['baselineMatches']==565
assert catGold['total']['catalogMatches']==571
assert catGold['total']['newlyMatchedAuthorCountClauses']==6
assert catGold['total']['previouslyCorrectNowWrong']==0
assert catGold['total']['actualNewCatalogBodies']==17
assert catGold['total']['newCategories']==13
assert catGold['total']['accepted']==197
out={
 'provenance':{
  'source':'Official author SceneEval-500 v250610 source text and independent annotation labels; same fixed sample as previous Games research',
  'SceneEvalZIPsha256':sha(CORPUS),
  'baselineSourceSHA256':sha(INPUT),
  'baselineNativePhysicalSHA256':sha(ORIGINAL),
  'pretrainedSpaCyModelWheelSha256':sha(MODEL),
  'sourceOnlyNounCandidateGenerationBeforeGoldScoring':True,
  'noTrainingOrGoldTuningInThisExperiment':True,
  'priorDatasetExposure':'Prior agents examined some gold labels/results. This is an exploratory, NOT pristine blind evaluation.',
  'hardware':'Nitro CPU, low-priority fixed pretrained parser; no additional GPU/production inference calls',
  'visualPhysicalFidelityWarning':'Generic uncalibrated native collision boxes represent additional types. This validates type-count grounding and actual native saving ONLY, not 3D shape, identity/coreference, appearances, physical affordances or literary quality'},
 'originalErrorMechanisms':dict(errors),
 'frozenPretrainedNounCandidates':grammar['summary'],
 'textOnlyPotentialAgainstIndependentGold':textScore['combined'],
 'actualNativeGameCoreAcceptance':physical,
 'independentAuthorNativeCountResult':s,
 'sceneLevelBootstrap':bootstrap['byGroup'],
 'calibratedCategoryCatalogGateNativeResult':cat,
 'independentAuthorCatalogOnlyCountResult':catGold['total'],
 'privateRawManifest':private}
dest=R/'prse_spacy_open_vocab_evidence_manifest_v2.json'
if dest.exists():assert read(dest)==out,'Refusing to overwrite different consumed research evidence'
else:
 with dest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED 620/672 original count failures from absent recognized noun types.')
print('VERIFIED 500 CPU pretrained parse proposals frozen BEFORE independent author annotation scorer.')
print('VERIFIED 197/197 native GameCore + Rapier source-linked augmented scenes save/reload without extra geometric rejection.')
print('VERIFIED 1110 added generic 3D bodies and 407 additional satisfied source count claims, 467 extra unannotated type proposals.')
print('VERIFIED 17 catalog-size native bodies and only six more independent author count requirements, vs 407 generic-box matches.')
print('VERIFIED paired scene resample intervals and source/private/model SHA evidence, no ungrounded visual/scale claims.')
