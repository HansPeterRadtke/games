#!/usr/bin/env python3
"""Independent PRSE source↔native Rapier↔semantics↔observer/offscreen 4-vector
evidence audit. Frozen original text, physical eligibility and source-only
grammar decisions were finalized BEFORE source-gold audit; original author
annotations are only a post hoc category-pair diagnostic.

The eight source-derived physically eligible relations are a SELECTED narrow
subset. Four perturbations each are repeated conditions, NOT 32 independent
literary source worlds. No human literary-quality scores, unscripted actors
or general unrestricted source entailment are claimed.
"""
import json,zipfile,io,csv
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter
DIR=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop')
SOURCE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert sha(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert S_IMODE(P.stat().st_mode)==0o700
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:authors=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(authors)==500
originals=load(SOURCE)['proposalsAll500']
assert len(originals)==500
manifest={}
def raw(name):
 p=P/name
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600
 manifest[name]={'sha256':sha(p),'bytes':p.stat().st_size,'ownerPrivate':True}
 return load(p)
roles=raw('prse_source_role_on_200_raw_v1.json')
physical=raw('prse_source_blind_support_eligibility_v1.json')
sourceGold=raw('prse_source_role_independent_on_gold_v1.json')
assert roles['summary']['extractedOnSourceClaims']==54
assert roles['summary']['syntaxRoleCandidates']==9
assert roles['summary']['roleNotSourceConfirmedAbstentions']==45
assert physical['tally']['parsedOnRelations']==53
assert physical['tally']['baselineTrue']==27
assert physical['tally']['eligibleForPotentialUnambiguousDynamicPhysicalRepair']==8
assert physical['tally']['eligibleButNotPhysicallyTrue']==0
assert sourceGold['metrics']['originalParsedOnClaims']==54
assert sourceGold['metrics']['originalParsedOnPhysicallyTrue']==27
assert sourceGold['metrics']['originalParsedOnAnnotationConcordant']==11
assert sourceGold['metrics']['originalParsedOnPhysicallyTrueAndGoldConcordant']==7
assert sourceGold['metrics']['syntaxRoleAccept']==9
assert sourceGold['metrics']['syntaxRoleAnnotationConcordant']==6
assert sourceGold['metrics']['syntaxRolePhysicallyTrue']==6
assert sourceGold['metrics']['syntaxRolePhysicalAndGoldConcordant']==5
assert sourceGold['metrics']['syntaxAbstainedButAnnotationConcordant']==5
assert sourceGold['metrics']['sourceRolePhysicallyTrueButNotInAuthorAnnotations']==1
originalRole={(r['sourceId'],r['sourceRelationIndex']):r for r in roles['records']}
eligible=[r for r in physical['records'] if r.get('eligible')]
assert len(eligible)==8
expectedIds=sorted((r['id'],r['relA'],r['relB']) for r in eligible)
independentGold={(r['sourceId'],r['child'],r['support']):r
 for r in sourceGold['rows']}
measured,versions=[],[]
for version,impulse in [('v1',(4,1.1,.5)),('v2',(-4,1.1,.5)),
                        ('v3',(.5,1.1,4)),('v4',(1.2,.9,-3.5))]:
 d=raw('prse_source_role_full_loop_8_raw_'+version+'.json')
 pub=load(DIR/('prse_source_role_full_loop_8_aggregate_'+version+'.json'))
 assert pub['metadata']['privateRawSHA256']==manifest['prse_source_role_full_loop_8_raw_'+version+'.json']['sha256']
 assert pub['summary']==d['summary']
 assert d['metadata']['sourceGoldNeverLoaded']
 if version=='v1':
  # Original consumed result predates the versioned v2-v4 extension; infer
  # its one recorded fixed physical vector from the immutable metadata.
  assert 'x4 y1.1 z0.5' in d['metadata']['fixedNativeInput']
 else:
  assert d['metadata']['experimentVersion']==version
  assert tuple(d['metadata']['predeclaredImpulseVector'][k] for k in ('x','y','z'))==impulse
 s=d['summary']
 for k in ['sourceBlindPredefinedEligiblePhysicalRelations','successfullyEvaluated',
           'originalPhysicalTrue','realPhysicalImpulsesApplied','actualSafeOffscreenRegionUnloads',
           'unknownUnloadedSemanticsQualified','nativeSavedAndRematerialized',
           'initialPhysicallyVisibleSourceCases','sourceTextsUnchanged']:
  assert s[k]==8,(version,k,s[k])
 for k in ['executionFailures','physicallyDisprovedSourceClaimsStillPrinted',
           'remoteHiddenPhysicalEventLeaks','repeatedUnchangedReturnNarrative']:
  assert s[k]==0,(version,k,s[k])
 assert s['sourceSyntaxAccepted']==s['initialSourceSupportedRelationsActuallyNarrated']==4
 assert s['successfulObserverPhysicalRelationRetractions']==4
 assert s['realImpulsesLedToFalseOrUnknownSupport']==(7 if version in ('v1','v2') else 8)
 assert s['reentryPhysicallyVisibleBothObjects']==(7 if version=='v4' else 8)
 r=d['results']
 assert sorted((x['sourceId'],x['sourceChild'],x['sourceSupport']) for x in r)==expectedIds
 approved=0
 for x in r:
  original=originals[x['sourceId']]
  assert sha256(original['text'].encode()).hexdigest()==x['expectedOriginalHistoricalSourceSHA256']
  matching=[(i,r) for i,r in enumerate(original['relations']) if r['kind']=='object' and
   r['type']=='on' and r['a']==x['sourceChild'] and r['b']==x['sourceSupport']]
  assert len(matching)==1 and matching[0][0]==x['sourceRelationIndex']
  predicate=originalRole[(x['sourceId'],x['sourceRelationIndex'])]
  assert x['sourceSyntaxAccepted']==(predicate['status']=='source_syntax_role_candidate')
  assert x['status']=='evaluated' and x['initialRolePhysicalState']=='true'
  assert x['initialSourceRoleRelationPrinted']==x['sourceSyntaxAccepted']
  assert x['initialPhysicalOnlySupportPrinted']!=x['sourceSyntaxAccepted']
  assert x['actualPhysicsEvents']>=1 and x['elapsedPhysicsSeconds']>2.5
  assert x['wasPhysicallyUnloaded'] and x['unloadedQualifiedCurrentWorld']
  assert x['restoredHistoricalSourceAndIds'] and x['currentSourceStillHistorical']
  assert x['initialContactObservableToReader']
  assert x['remotelyLeakedPhysicalEventCount']==0
  assert x.get('reentryWitnessedHiddenEvents',0)==0
  assert x.get('duplicateCurrentFactMessages',0)==0
  if x['afterRealPhysicalImpulse']=='false':
   assert not x['currentDocumentSourceClaimStillAsserted']
   assert x['finalNativePhysicalOnStatus']=='false'
  gold=independentGold[(x['sourceId'],x['sourceChild'],x['sourceSupport'])]
  approved+=bool(x['sourceSyntaxAccepted'] and gold['annotationOnCategoryConcordant'])
  measured.append({'sourceId':x['sourceId'],'child':x['sourceChild'],
   'support':x['sourceSupport'],'authorSourceTypePairOnConcordant':gold['annotationOnCategoryConcordant'],
   'grammarGate':x['sourceSyntaxAccepted'],'impulseVersion':version,
   'afterPhysical':x['afterRealPhysicalImpulse'],'afterReentry':x['finalNativePhysicalOnStatus'],
   'witnessedUnseenEventCount':x.get('reentryWitnessedHiddenEvents',0)+x['remotelyLeakedPhysicalEventCount'],
   'nativeSavedUnloaded':x['wasPhysicallyUnloaded']})
 assert approved==3
 versions.append({'name':version,'summary':s})
assert len(measured)==32
root=sum((d['summary']['realImpulsesLedToFalseOrUnknownSupport'] for d in
       (load(P/f'prse_source_role_full_loop_8_raw_{k}.json') for k in ['v1','v2','v3','v4'])))
assert root==30,(root,'expected 30 physical false or unknown across 32')
# Note: 7+7+8+8=30, not 31. Preserve raw measurements, never round up.
out={'metadata':{
 'source':'Frozen original SceneEval 200 sample source, CPU-pretrained syntax PP role gate, actual native GameCore/Rapier full save and observer histories',
 'sourceSHA256':sha(SOURCE),
 'authorSceneEvalOriginalSHA256':sha(GOLD),
 'noAuthorGoldLoadedUntilAfterSceneSelectionAndPhysics':True,
 'sourceRoleCaution':'Syntactic PP attachment is a selective heuristic and not source entailment or coreference resolution',
 'repeatedSourceDesign':'8 selected native physically eligible source claims x 4 fixed impulses =32 repeated physical conditions, NOT 32 independent stories',
 'noNewGPUorLLMorHumanStudy':True,
 'privateOriginalProseAndPerCaseEvidence':True},
 'sourceRoleVsIndependentAuthorCategoryLabels':sourceGold['metrics'],
 'physicalEligibility':physical['tally'],
 'independentGoldEightSelected':{
  'eligibleSourceUniqueOnClaims':8,
  'syntaxAcceptedClaimsPerVector':4,
  'syntaxAcceptedAlsoAuthorAnnotated':3,
  'syntaxAbstainedAlsoAuthorAnnotated':1,
  'annotationUncertainOrMissingShouldNotBeAssumedFalse':True},
 'nativeFullLoops':{
  'physicalEpisodes':32,
  'distinctEligibleSourceRelationships':8,
  'successfulSourcePhysicalSemanticOffscreenNativeReentryEpisodes':32,
  'physicalContactBecameFalseOrUnknownAfterImpulse':root,
  'sourceSyntacticApprovedRelationshipRetractions':16,
  'actualNativeUnloadedAreaWithSemanticTimeAndReentry':32,
  'unseenImpulseEyewitnessLeaks':0,
  'repeatedUnchangedNarration':0,
  'sceneSourceArchiveAndOriginalEntityIdsPreserved':32,
  'oneCaseReturnedOutsideJointLineOfSight':True},
 'perVersion':versions,
 'privateRawManifest':manifest}
dest=DIR/'prse_support_full_loop_evidence_manifest_v1.json'
if dest.exists():assert load(dest)==out,'Refusing to silently overwrite existing scientific manifest'
else:
 with dest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('INDEPENDENT_EVIDENCE VERIFIED parser 54 candidate ON, 27 physics true, 9 source syntax accepted, 6 author annotated.')
print('INDEPENDENT_EVIDENCE VERIFIED original source/physics category agreement on 8 preselected eligible source claims, 4 syntax accepted and 3 author on type-pair labels.')
print('INDEPENDENT_EVIDENCE VERIFIED 32 physical impulses, 30 support loss/unknown, 16 correct observer retractions, 32 real unloads/native saved rematerializations, zero unseen event leaks.')
print('INDEPENDENT_EVIDENCE original v1/v2/v3/v4 private RAW SHA256 and source labels not used to choose conditions.')
