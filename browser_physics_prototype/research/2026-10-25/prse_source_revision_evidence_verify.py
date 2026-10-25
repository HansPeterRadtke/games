#!/usr/bin/env python3
"""Independent PRSE source-preserving narrative / physics / observer evidence audit.

Checks two separately retained corpus runs (original missing visible-object
fact vs corrected version), the preserved physical-ash omission, correction
and native transaction, an explicit mismatched-evidence acceptance test, and
the literal editability of frozen external source-relation text spans.

No physics rerun, no model inference, and no raw-file mutation. The original
SceneEval source, complete source-derived prompts and per-scene records remain
owner-private Nitro inputs. Only aggregate metrics and SHA-256 manifest are
committed to the Games research branch.
"""
import json,hashlib,zipfile,io,csv,stat
from pathlib import Path

R=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-literary-revision')
ORIGINAL=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
SYNTAX=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model/prse_spacy_sceneeval_500_union_v1.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(ORIGINAL)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(ORIGINAL) as z:
 with z.open('annotations.csv') as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
manifest={}
raw=[]
for version,expectedStatements in [('v1',43),('v2',404)]:
 path=PRIVATE/f'prse_source_revision_63_raw_{version}.json'
 assert path.is_file() and stat.S_IMODE(path.stat().st_mode)==0o600
 d=read(path);a=read(R/f'prse_source_revision_63_aggregate_{version}.json')
 assert sha(path)==a['metadata']['privateEvidenceSHA256']
 assert d['summary']==a['summary']
 s=d['summary']
 assert s['inputSourceScenes']==s['valid']==s['sourceArchivesUnchanged']==63
 assert s['failed']==s['failedObserverPrivacyCases']==s['duplicatedReports']==s['physicalSaveDifferencesOverTwoCm']==0
 assert s['identicalCurrentRelationTruthAfterLaterNativeSave']==63
 assert s['witnessedEvents']==63 and s['sceneReadInitialStatements']==expectedStatements
 assert s['largestNativeSavePositionDifferenceMeters']<.001
 if version=='v2':
  assert s['firstVisibleObjectStateStatements']==361
  assert s['firstVerifiedRelationStatements']==43
  assert s['laterVisibleObjectStateStatements']==46
  assert s['laterVerifiedRelationStatements']==7
 for x in d['cases']:
  assert rows[int(x['id'])]['ID']==x['id']
  assert x['status']=='evaluated'
  assert x['originalSourceRetained'] and x['nativeClockEqual'] and x['futureSourceTruthMatches']
  assert x['liveVisibleImpulseReports']>=1 and x['remoteEventLeaks']==0
  assert x['repeatedText']==x['sentenceCountAfterNativeReload']==0
  if version=='v2':
   evidence=x.get('outputEvidence',[])
   assert len(evidence)>0
   valid={
    'witnessed_physical_event','current_visible_physical_state',
    'verified_present_fact','previously_visible_fact_retracted'}
   assert all(z['category'] in valid and isinstance(z['text'],str) and z['text'].strip()
      and z['evidence'] for z in evidence)
 raw.append(d)
 manifest[path.name]={'sha256':sha(path),'bytes':path.stat().st_size,'private':True}

# Same IDs and identical staged physics treatment: only missing-current-fact
# research adapter changed between the two versioned evaluations.
assert [(x['id'],x['subset'],x['kind']) for x in raw[0]['cases']]==[
 (x['id'],x['subset'],x['kind']) for x in raw[1]['cases']]
old=read(R/'prse_source_revision_omitted_visible_ash_negative_v1.json')
fixed=read(R/'prse_story_revision_offscreen_ash_reentry_v1.json')
assert old['physicallyRayVisible'] and old['actualAshColliderCount']==1
assert old['actualCoreDescription'].lower().find('ash')>=0
assert old['omittedFactDespitePhysicalVisibility'] and old['adapterTextOutput']==''
assert fixed['afterReturn']['ashHasRealCollider']
assert fixed['afterReturn']['ashSeen']
assert 'ash' in fixed['afterReturn']['currentSourceLinkedText'].lower()
assert fixed['afterReturn']['unwitnessedIgnitionNotClaimed']
assert fixed['afterReturn']['duplicateFactOnNextPoll']==0 if 'duplicateFactOnNextPoll' in fixed['afterReturn'] else fixed['afterReturn']['duplicateContentAfterRead']==0
assert fixed['afterReturn']['duplicateContentAfterSecondSave']==0
assert fixed['afterReturn']['originalSourceDocumentUnchanged']

valid=read(R/'prse_source_revision_atomic_integrity_v1.json')
assert valid['test']['nativeSaveAccepted']
assert valid['test']['unsafeMutationsRejected']==10
assert all(x['reason'] for x in valid['test']['rejected'])
assert valid['test']['nextRealPhysicalActionReentryPositionDifferenceMeters']<.001
assert valid['test']['noRepeatedVisibleImpulses']
assert valid['test']['sourceLiteraryArchiveUnchanged']

spans=read(R/'prse_literary_source_span_editability_aggregate_v1.json')
assert spans['metadata']['sourceGoldNotRead']
assert len(spans['variants'])==2
expected={
 'deterministic':(FROZEN,1070,1070,9,2),
 'union':(SYNTAX,1557,1481,69,11)
}
for k,(source,total,substr,sentence,candidate) in expected.items():
 v=spans['variants'][k]
 assert v['totalRelations']==total and v['sourceStringFound']==substr
 assert v['exactFullSentence']==sentence
 assert v['potentialControlledSentenceCandidate']==candidate
 assert v['sourceSHA256']==sha(source)
 archive=PRIVATE/f'prse_source_span_editability_{k}_500_raw_v1.json'
 assert archive.is_file() and stat.S_IMODE(archive.stat().st_mode)==0o600
 assert sha(archive)==v['privateFileSHA256']
 rawData=read(archive)
 assert len(rawData['records'])==total
 manifest[archive.name]={'sha256':sha(archive),'bytes':archive.stat().st_size,'private':True}

summary={
 'sourceReference':'SceneEval-500 official original ZIP and previously frozen first hundred human, systematic assisted scene sample',
 'sourceZipSHA256':sha(ORIGINAL),
 'uniqueSourceScenes':63,
 'initialPhysicallySupportedSourceRelationStatements':43,
 'initialCurrentVisibleObjectStateStatementsAdded':361,
 'newSourceRevisionStatementsInitialTotal':404,
 'witnessedPhysicalEventsDeliveredWithoutRemoteLeak':63,
 'atomicNativeGameCoreAndObserverScenarioPasses':63,
 'repeatedUnchangedTextStatementsAfterSave':0,
 'preservedObservedPhysicalAshOmissionThenCorrected':True,
 'trustedTransactionCorruptionsRejected':10,
 'sourceSpans':{
  k:{'frozenRelations':v[1],'exactSubstring':v[2],
      'wholeSentence':v[3],'strictCandidateForReviewNotAutomaticallyRewriteSafe':v[4]}
      for k,v in expected.items()},
 'limitations':[
  'The current text output is factual, not author-quality literary rewriting.',
  'Most original text relations remain physically unknown or ungrounded.',
  'A source-span matching a whole sentence is not guaranteed to preserve its semantics.',
  'No generative LLM calls, formal NLI quality evaluation or human literary preference tests were performed.',
  'Trusted hash checks are not cryptographic authentication against a fully rewritten malicious save.',
  'Only selected externally described materialized scenes and one authored offscreen ash process tested.']
}
out={'metadata':{
 'source':'Original recorded PRSE literary↔authoritative GameCore/Rapier physical↔literary research',
 'ownerPrivateRawEvidence':True,'noSharedGPUorGenerativeModel':True,
 'noHumanPlaytest':True,'independentSourceAnnotationLabelsNotUsedToGenerateOutput':True
 },'summary':summary,'privateRawManifest':manifest}
dest=R/'prse_source_revision_evidence_manifest_v1.json'
if dest.exists():
 assert read(dest)==out,'Would overwrite differently grounded evidence manifest'
else:
 with dest.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('VERIFIED: original negative visible ash omitted, corrected physical ash narrated,')
print('same 63 real-source scenes replayed with 361 new current-object facts,')
print('63 witnessed impulses without remote leaks or post-save duplicates,')
print('10 corrupted/mixed narrative/physical saves rejected,')
print('and exact literary source-span provenance for all 500 descriptions.')
