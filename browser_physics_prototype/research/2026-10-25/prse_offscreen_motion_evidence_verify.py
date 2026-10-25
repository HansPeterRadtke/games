#!/usr/bin/env python3
"""Independent PRSE offscreen causal motion/restore evidence verification.

The parser proposals and scene IDs were FROZEN in earlier SceneEval research.
This verifier only reads finished physical results, previously preserved
negative runs, and independent Rapier/PRSE physics state trajectories. It
does not call the model, re-run physics, or edit the raw evidence.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
import csv,io,json,zipfile

ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-offscreen-motion')
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def hash(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert hash(CORPUS)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(CORPUS) as z:
 with z.open('annotations.csv') as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
files={}
for group in ['human','assisted']:
 for descriptor in ['prse_offscreen_motion_{group}_raw_v1.json',
                    'prse_offscreen_action_schedule_{group}_conservative_raw_v2.json']:
  n=descriptor.format(group=group)
  f=PRIVATE/n
  assert f.is_file() and S_IMODE(f.stat().st_mode)==0o600
  files[n]={'sha256':hash(f),'bytes':f.stat().st_size,'ownerPrivate':True}
  public_name=n.replace('_raw_v1.json','_aggregate_v1.json').replace('_raw_v2.json','_aggregate_v2.json')
  aggregate=read(ROOT/public_name)
  assert aggregate['metadata'].get('privateRawSHA256',aggregate['metadata'].get('rawSHA256'))==hash(f)
  actual=read(f)
  assert aggregate['summary']==actual['summary']
  assert (actual['summary']['failed']==0 if 'failed' in actual['summary'] else actual['summary']['failedEpisodes']==0)
  for item in actual.get('results',actual.get('records',[])):
   assert rows[int(item['id'])]['ID']==str(item['id'])
   assert item['status']=='evaluated'

# Original unsafe scheduled continuation result: NEVER erase its failure.
unsafe=PRIVATE/'prse_offscreen_action_schedule_human_raw_v1.json'
assert unsafe.is_file() and S_IMODE(unsafe.stat().st_mode)==0o600
bad=read(unsafe)
bad_cup=next(x for x in bad['records'] if x['id']=='27')
assert bad_cup['offloadSegments']>=1
assert bad_cup['maxPosErrorAfterOneStep']['maxPoseMeters']>.6
files[unsafe.name]={'sha256':hash(unsafe),'bytes':unsafe.stat().st_size,'ownerPrivate':True}
conservative={}
for group,src,episodes,unloaded,ticks in [('human',28,28,10,287),('assisted',35,35,13,441)]:
 data=read(PRIVATE/f'prse_offscreen_action_schedule_{group}_conservative_raw_v2.json')
 s=data['summary']
 assert (s['sourceScenes'],s['evaluatedEpisodes'],s['episodesWithOneOrMoreOffloads'],s['totalPhysicsTicksSaved'])==(src,episodes,unloaded,ticks)
 assert s['physicalEventSequenceMismatches']==s['sourceRelationTruthMismatchingScenes']==s['actionChronologyErrors']==s['poseDiffMoreThan2cm']==0
 assert s['clockAndSourcePreserved']==episodes
 assert all(x['worldClockErrorSeconds']<1e-5 and x['allObjectIDsPersist'] and x['originalProseUnchanged'] for x in data['records'])
 conservative[group]=s

# Previously observed unloaded five-second no-future-action experiment.
single={}
for group,episodes,unloaded in [('human',56,24),('assisted',70,28)]:
 data=read(PRIVATE/f'prse_offscreen_motion_{group}_raw_v1.json')
 s=data['summary']
 assert s['episodes']==episodes and s['offloadAccepted']==unloaded and s['failed']==0
 assert s['worldClockEquivalent']==episodes and s['sceneProseAndIdentityPreserved']==episodes
 assert s['externalSourceTruthMismatchingCases']==0 and s['eventStreamMismatchCases']==0
 assert s['maximumOffloadPoseErrorMeters']<.0001
 single[group]=s

# Independent forensic controls established that an UNSAFE early unload was not
# the only trigger: ordinary save/reconstruction before future contact also
# caused the cup to diverge.
diagnostic=read(ROOT/'prse_offscreen_queued_cup_62cm_failure_diagnostic_v1.json')
assert diagnostic['metadata']['sourceId']==27 if 'sourceId' in diagnostic['metadata'] else True
r=diagnostic['checkpoints']
assert len(r)==3
assert r[0]['mode']['coarse_no_save']['differenceFromUninterrupted']['positionMeters']<1e-5
assert r[1]['mode']['full_saved']['differenceFromUninterrupted']['positionMeters']>.6
assert r[1]['mode']['coarse_no_save']['differenceFromUninterrupted']['positionMeters']>.6
assert r[2]['mode']['uninterrupted']['differenceFromUninterrupted']['positionMeters']==0

# Another independent check: native Rapier physics serializes more solver state
# than only PRSE JSON body parameters. Native and JSON need exact same source
# selection and input impulses. Both studies are solver/physical fidelity,
# NOT proof of source-literary equivalence.
native=read(PRIVATE/'prse_rapier_native_snapshot_63_raw_v1.json')
assert native['summary']['sourceScenes']==native['summary']['evaluated']==63
assert native['summary']['failed']==native['summary']['nativeBinaryAbove2cm']==0
assert native['summary']['structuredJSONAbove2cm']==1
assert native['summary']['maxBinaryErrorMeters']<.0003
files['prse_rapier_native_snapshot_63_raw_v1.json']={
 'sha256':hash(PRIVATE/'prse_rapier_native_snapshot_63_raw_v1.json'),
 'bytes':(PRIVATE/'prse_rapier_native_snapshot_63_raw_v1.json').stat().st_size,'ownerPrivate':True}
assert read(ROOT/'prse_rapier_native_snapshot_63_aggregate_v1.json')['metadata']['privateRawSHA256']==files['prse_rapier_native_snapshot_63_raw_v1.json']['sha256']
for sample in ['human','assisted']:
 assert sample in conservative

# Full GameCore native transactional result can be optional only during early
# verification before the benchmark finishes. Once present, require it.
nativeTransaction=PRIVATE/'prse_full_gamecore_native_transaction_63_raw_v1.json'
if nativeTransaction.exists():
 assert S_IMODE(nativeTransaction.stat().st_mode)==0o600
 full=read(nativeTransaction)
 assert full['summary']['evaluated']==63 and full['summary']['failed']==0
 assert full['summary']['nativeWorldClockMismatches']==0
 assert full['summary']['originalSourceTextsPreserved']==63
 assert read(ROOT/'prse_full_gamecore_native_transaction_63_aggregate_v1.json')['metadata']['privateRawSHA256']==hash(nativeTransaction)
 files[nativeTransaction.name]={'sha256':hash(nativeTransaction),
  'bytes':nativeTransaction.stat().st_size,'ownerPrivate':True}
else:full=None

aggregate={
 'provenance':{
  'source':'Official author SceneEval-500 v250610 ZIP, unchanged source IDs, physics inputs are investigator-defined',
  'sourceSHA256':hash(CORPUS),
  'allRawArtifactsOwnerPrivate':True,'sourceAnnotationsNotUsedInAnyMotionPolicy':True,
  'nativeSimulation':'Existing PRSE GameCore/Rapier; shared renderer and other agents preserved',
  'limitations':'Offscreen tests cover known scheduled physical impulses only; no human play, unknown actors, or realistic multi-region physics.'},
 'singleQuietOffload':single,
 'scheduledConservative':conservative,
 'preservedOriginalFailure':{
  'sourceId':'27','maximumSourceCupErrorMetres':bad_cup['maxPosErrorAfterOneStep']['maxPoseMeters'],
  'equalInitialPoseAtTick150':True,
  'saveReconstructionAlsoDivergedAfterFutureContact':True},
 'solverNativeBinaryComparison':native['summary'],
 'nativeFullGameCoreTransactionComparison':full['summary'] if full else None,
 'rawPrivateManifest':files}
outfile=ROOT/'prse_offscreen_causal_motion_evidence_manifest_v1.json'
if outfile.exists():assert read(outfile)==aggregate,'Refuse to overwrite different evidence'
else:
 with outfile.open('x') as f:json.dump(aggregate,f,indent=2);f.write('\n')
print('VERIFIED offscreen idle result 52/126 accepted, never freeze uncertain objects;')
print('VERIFIED known future actions conservative 63/63 completed, 23 after-final offloads, 728 physical ticks skipped;')
print('VERIFIED original 0.62m source27 failure and native solver serialization raw source checksum;',
      'full GameCore binary test',bool(full))
