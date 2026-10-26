#!/usr/bin/env python3
"""Read-only final user-facing PRSE product/browser acceptance verifier.

Verifies private isolated real Chrome screenshots, captured rendered DOM text,
authoritative GameCore session snapshots, save/reconnect, mobile touch sizing,
and actual human-source import refusal. Does NOT repeat network/browser/model
effects or invent a literary asset importer.
"""
from pathlib import Path
from hashlib import sha256
from stat import S_IMODE
from collections import Counter
from PIL import Image,ImageStat
import json,io

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[2]
RUN=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-round4-user-facing')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert S_IMODE(RUN.stat().st_mode)==0o700
v1=RUN/'browser_user_visible_acceptance_raw_v1.json'
v3=RUN/'literary_user_entry_browser_raw_v3.json'
for p in (v1,v3):
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600
old,new=read(v1),read(v3)
assert old['failure'] is None and new['failure'] is None
assert old['metadata']['productionPort18764Untouched']
assert old['metadata']['noJetsonGPURequests']
assert new['metadata']['noExternalProductionEffects']
assert new['metadata']['noLocalOrJetsonLLMRequests']
assert old['metadata']['viewerCodeSHA256']==sha(GAME/'browser_physics_prototype/viewer.js')
assert new['metadata']['viewerSourceCodeSHA256']==sha(GAME/'browser_physics_prototype/viewer.js')
assert new['metadata']['gameCoreSourceCodeSHA256']==sha(GAME/'browser_physics_prototype/physics-core.js')
for stem,report in [('browser_user_visible_acceptance_aggregate_v1.json',old),
                   ('literary_user_entry_actual_browser_aggregate_v3.json',new)]:
 agg=read(HERE/stem)
 assert agg['metadata']['privateRawSHA256']==sha(v1 if report is old else v3)
 assert not agg.get('failed',False)
a=old['measurements']
assert a['privateBrowserContext'] and a['unmodifiedProductionViewerLoaded'] and a['isolatedGameCoreBackend']
assert a['userFacingTextReadFromRenderedDOM']
assert a['playerMovedMeters']>2.0
assert a['browserSaveAcknowledged'] and a['samePrivateSessionAfterReloadAndReconnect']
assert abs(a['reloadedPositionDeltaMeters'])<.3
assert abs(a['reconnectionDisplacementMeters'])<.85
assert a['mobileDOM']['viewport']==360 and a['mobileDOM']['documentWidth']==360
assert a['mobileHorizontalOverflowPx']==0
assert not a['mobileDOM']['shortButtons'] and a['mobileButtonsOver44Px']
assert a['passesUIBasic'] and a['privateServerProcessesStopped']
assert a['privateSavedSessionCount']==a['privateEventLogCount']==1
assert a['privateServerFilesOwnerOnly'] and a['productionPortNotUsed']
assert a['backendHealth']['physicsHz']==60 and a['backendHealth']['displayHz']==10
assert 'forest path' in a['userVisibleLookText'].lower()
assert a['userVisibleLookText'].count('A solid timber plank')==4

b=new['measurements']
assert b['sourceBelowInputAndTransportLimit'] and b['humanSourceInputLength']==51
literal='A projector in the conference room is on the table.'
assert b['sourceRequestHashSHA256']==sha256(literal.encode()).hexdigest()
assert b['visibleResponseWasCommandHelpInsteadOfSceneCreation']
assert b['playerSawRejectionInRealBrowserDOM']
assert b['noInventedSourceProjectorOrTable'] and b['physicalInventoryInVisibleRegionUnchanged']
assert b['beforeVisibleEntityCount']==6
assert 'No supported action for bench' in b['visibleResponseText']
assert 'Try: look' in b['visibleResponseText']
assert b['isolatedProcessesTerminated'] and b['safeProductionIsolation']
assert b['realBackendHealth']['sessions']==1
assert b['realBackendHealth']['physicsHz']==60
assert b['localGameSnapshotFilesSaved']==1

images={}
for entry in (a['actualDesktopScreenshot'],a['actualMobileScreenshot'],b['screenshot']):
 path=RUN/entry['path']
 assert path.is_file() and S_IMODE(path.stat().st_mode)==0o600
 assert sha(path)==entry['sha256'] and len(path.read_bytes())==entry['bytes']
 with Image.open(path) as im:
  assert im.format=='PNG'
  w,h=im.size
  img=im.convert('RGB')
  contrast=sum(ImageStat.Stat(img).stddev)/3
  assert w>=350 and h>=350 and contrast>25
  images[entry['path']]={'width':w,'height':h,'contrast':round(contrast,2),'bytes':entry['bytes']}
assert images[a['actualDesktopScreenshot']['path']]['width']==780
assert images[a['actualMobileScreenshot']['path']]['width']==720
s0=RUN/'private-gamecore-sessions-v1'
s3=RUN/'private-gamecore-sessions-v3'
for data in (s0,s3):
 assert data.is_dir() and S_IMODE(data.stat().st_mode)==0o700
 files=list(data.glob('*.snapshot.json'))
 logs=list(data.glob('*.events.ndjson'))
 assert len(files)==len(logs)==1
 assert all(S_IMODE(p.stat().st_mode)==0o600 for p in files+logs)
 snap=read(files[0])
 assert snap['version']==5
 assert len(snap['semantic']['entities'])==11
 if data==s3:
  assert all(e['kind'] not in ('projector','table') for e in snap['semantic']['entities'])
  assert '"kind":"text_command"' in logs[0].read_text()
  assert 'Try: look' in logs[0].read_text()
# The original human-authored projector/table requirement is a positive
# in external official source, not a hallucinated synthetic test command.
gold=read(Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent/lego_full_data_public_human_gold.json'))
assert any('projector' in ' '.join(x['instructions']).lower()
       and 'on the table' in ' '.join(x['instructions']).lower()
       for x in gold[31]['labels'])
# Separate CURRENT CANONICAL checkout (dirty main) artifact, evaluated only
# inside NEW private server + isolated Chromium context. The prior research
# test is NOT misreported as the current deployed browser version.
CANON=Path('/data/src/github/games')
v4=RUN/'canonical_current_browser_acceptance_raw_v4.json'
v4agg=HERE/'canonical_current_browser_acceptance_aggregate_v4.json'
assert v4.is_file() and S_IMODE(v4.stat().st_mode)==0o600
latest=read(v4);agg=read(v4agg);cur=latest['measurements']
assert latest['failure'] is None and agg['failure'] is None
assert agg['metadata']['privateRawSHA256']==sha(v4)
assert latest['sourceSHA256AtStart']==latest['sourceSHA256AtEnd']
assert agg['metadata']['exactCanonicalSourceHashes']==latest['sourceSHA256AtStart']
assert agg['metadata']['isolatedCanonicalSourceBranchDirtyAndUncommitted']
assert agg['metadata']['notClaimedLiveServiceBinaryVersion']
assert agg['metadata']['noExternalProductionEffects'] and agg['metadata']['noRealJetsonModelCalls']
assert cur['canonicalLandingLoaded'] and cur['actualCanonicalViewerJSLoaded'] and cur['canonicalStudyButtonInBrowser']
assert cur['browserPlayerMovementMeters']>1.0
assert cur['studyResultReceivedAsRealWorkerPhysics'] and cur['studyPhysicsPassed']
assert cur['afterAbsenceNote']=='ashes' and cur['afterReturnPhysicalNote'] is True
assert cur['actualContactProofInStudy'] and cur['actualContactProofInStudy']['tiltRadians']>1.0
assert 'PASS: An independent Nitro world' in cur['studyResultDisplayedToUser']
assert 'actual Rapier 3D candle-paper contact detected' in cur['studyResultDisplayedToUser']
assert 'bench scorched' in cur['studyResultDisplayedToUser']
assert 'physical note object recreated' in cur['studyResultDisplayedToUser']
assert 'not been generated yet' in cur['actualUserFacingInspectorText']
assert cur['literalOriginalHumanSceneRequestSHA256']==sha256(literal.encode()).hexdigest()
assert 'No supported action for bench' in cur['humanSceneInputVisibleResponse']
assert cur['projectorSceneNotCreated']
assert cur['canonicalDurableSaveAcknowledged'] and cur['sameAuthoritativeSessionAfterReload']
assert abs(cur['reloadPositionDeltaMeters'])<.4
assert cur['mobileSizing']['width']==cur['mobileSizing']['scroll']==360
assert cur['mobileOverflowPx']==0 and not cur['mobileSizing']['tooShort']
assert cur['canonicalBrowserPass'] and cur['canonicalSourceFilesUnchangedDuringTest']
assert cur['privateBackendAndUIProcessesStopped'] and cur['productionPortUnused']
assert cur['privateContextNoProductionTabsModified']
assert cur['productionLLMDisabledByInvalidLocalEndpoint']
assert cur['privateCanonicalSnapshotCount']==cur['privateCanonicalLogCount']==1
assert cur['canonicalPrivateBackendHealth']['physicsHz']==60
assert cur['canonicalPrivateBackendHealth']['displayHz']==10
for screen in (cur['desktopCausalityStudyScreenshot'],cur['canonicalLiteraryNegativeScreenshot'],
               cur['mobileStudyPanelScreenshot']):
 p=RUN/screen['path']
 assert p.is_file() and S_IMODE(p.stat().st_mode)==0o600 and sha(p)==screen['sha256']
 assert p.stat().st_size==screen['bytes'] and screen['meanChannelStddev']>25
 with Image.open(p) as img:
  assert img.format=='PNG'
  assert img.width==screen['width'] and img.height==screen['height']
 privateScreens=images
 privateScreens[p.name]={'width':img.width,'height':img.height,'contrast':screen['meanChannelStddev'],'bytes':screen['bytes']}
session=RUN/'private-canonical-uncommitted-session-v4'
assert session.is_dir() and S_IMODE(session.stat().st_mode)==0o700
saved=list(session.glob('*.snapshot.json'))
logs=list(session.glob('*.events.ndjson'))
assert len(saved)==len(logs)==1
assert S_IMODE(saved[0].stat().st_mode)==S_IMODE(logs[0].stat().st_mode)==0o600
snapshot=read(saved[0]);assert snapshot['version']==5
assert len(snapshot['semantic']['entities'])==11
assert not any(e['kind'] in ('projector','table') for e in snapshot['semantic']['entities'])
assert not any('shelter-' in e['id'] for e in snapshot['semantic']['entities'])
trace=[json.loads(line) for line in logs[0].read_text().splitlines() if line.strip()]
assert sum(e['kind']=='study_started' for e in trace)==1
assert sum(e['kind']=='study_completed' and e.get('passed') for e in trace)==1
assert not any(e['kind'].startswith('llm_') for e in trace)
assert not any(e['kind']=='event' and e.get('eventType')=='note_ignited' for e in trace), 'Worker changed user session'
assert not any(e['kind']=='command' and e.get('command',{}).get('type')=='Interact' for e in trace), 'Worker interacted with user game'
print('VERIFIED CANONICAL DIRTY SOURCE SNAPSHOT: exact file hashes unchanged during test;')
print('real user-facing native GameCore candle causality worker PASS, physical contact, offscreen ashes,')
print('real returned note in on-screen browser text; user session never mutated by independent worker;')
print('separate human source text command rejected with unsupported bench label; current room still not generated;')
print('private persistent server save, 360px mobile no overflow, and real rendered desktop/mobile screenshots.')

print('VERIFIED FINAL PRSE PRODUCT VIEWER: unmodified Chrome UI, actual private native GameCore WebSocket,')
print('player movement, on-screen forest prose, save/reload/reconnect, real desktop and mobile pixels;')
print('mobile 360px no overflow, all button targets >=44px, physics 60Hz/display 10Hz;')
print('separate human source scene command visibly rejected with spurious bench referent,')
print('authoritative private persisted entity inventory unchanged at 11, zero projector/table.')
print('Screenshots:',json.dumps(images,sort_keys=True))
