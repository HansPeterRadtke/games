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
print('VERIFIED FINAL PRSE PRODUCT VIEWER: unmodified Chrome UI, actual private native GameCore WebSocket,')
print('player movement, on-screen forest prose, save/reload/reconnect, real desktop and mobile pixels;')
print('mobile 360px no overflow, all button targets >=44px, physics 60Hz/display 10Hz;')
print('separate human source scene command visibly rejected with spurious bench referent,')
print('authoritative private persisted entity inventory unchanged at 11, zero projector/table.')
print('Screenshots:',json.dumps(images,sort_keys=True))
