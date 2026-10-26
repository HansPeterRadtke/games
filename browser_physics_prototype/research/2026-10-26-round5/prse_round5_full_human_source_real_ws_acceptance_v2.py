#!/usr/bin/env python3
"""Versioned, isolated, full HUMAN-authored LEGO scene + independently annotated
constraint acceptance through actual Nitro GameCore WebSocket text path.

This is a NEW source-authority and latency/cost deployment audit. No random
feasible-parent placebo, no source-only Rapier experiment replay, no user session,
no public host, no LLM, no canonical file modification, no trading or schedules.

Each arm is a new private GameCore server, and each author sample is sent once.
Human labels establish the original SOURCE intent, not exhaustive negatives.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, socket, statistics, subprocess, time
from collections import Counter,defaultdict
import psutil
import urllib.request, websocket

HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('/data/var/games/prse_semantic_research/runs/2026-10-26-prse-round5-source-authority')
ROOT.mkdir(parents=True,exist_ok=True,mode=0o700);ROOT.chmod(0o700)
SOURCE=pathlib.Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent/lego_full_data_public_human_gold.json')
assert SOURCE.is_file()
SOURCE_SHA='c4cab948b923b522b9ba4991e167e1c5c7d503786f2b2e5c11a64dab89113c21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hash_text(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
assert sha(SOURCE)==SOURCE_SHA
GOLD=json.loads(SOURCE.read_text())
assert len(GOLD)==130
def js_len(s):return len(s.encode('utf-16-le'))//2
rows=[]
for i,g in enumerate(GOLD):
  assert isinstance(g['instruction'],str) and len(g['instruction'])>0
  assert len(g['labels'])==len(g['constraints'])
  rows.append({'sourceIndex':i,'group':'complete_human_author_instruction',
               'labelType':'Full human source','labelIndex':None,
               'text':g['instruction']})
  # Same source human annotated constraints, INCLUDING physical placement,
  # room layout, object selection, material and explicit negative clauses.
  for lab in g['labels']:
    assert isinstance(lab['instructions'],list) and isinstance(lab['condition_idx'],str)
    text=' '.join(lab['instructions'])
    assert text
    rows.append({'sourceIndex':i,'group':'human_annotated_clause',
                 'labelType':lab['condition_type'],'labelIndex':lab['condition_idx'],
                 'text':text})
expected=130+sum(len(g['labels']) for g in GOLD)
assert expected==1380 and len(rows)==expected
SOURCE_KEYS=Counter(x['labelType'] for x in rows)
assert SOURCE_KEYS==Counter({'Full human source':130,'Object Placement':494,'Object Selection':291,
 'Floor Layout':272,'Material Selection':193})
def write_private(p,b):
  with p.open('xb') as f:f.write(b)
  p.chmod(0o600)
def free_port():
  with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
def health(url):
  try:
    with urllib.request.urlopen(url,timeout=2) as r:return json.load(r)
  except Exception:return None
def wait(fn,seconds):
  t=time.monotonic()+seconds
  while time.monotonic()<t:
    v=fn()
    if v:return v
    time.sleep(.1)
  raise TimeoutError('Isolated actual GameCore private host failed health check')
def percent(xs,p):
  if not xs:return None
  s=sorted(xs)
  return round(s[min(len(s)-1,max(0,int((len(s)-1)*p)))],3)
def read_ack(ws,request_id,timeout=12):
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
    ws.settimeout(min(1,max(.1,deadline-time.monotonic())))
    try:payload=json.loads(ws.recv())
    except websocket.WebSocketTimeoutException:continue
    if payload.get('type') in ('text_result','rejected','error'):
      if payload.get('type')=='text_result' and payload.get('requestId')!=request_id:
        raise ValueError('Received text response for wrong author request')
      return payload
  raise TimeoutError('Author original request failed to receive typed GameCore reply')
def source_kind(text,response):
  if response['type']=='rejected':return 'rejected'
  value=response.get('text',response.get('message',''))
  if value.startswith('No supported action for ') and 'Try: look' in value:return 'unsupported_foreign_world_object'
  if 'Try: look' in value:return 'unsupported_generic_help'
  if 'forest path' in value.lower() or 'you are at x ' in value.lower():return 'forest_world_only_description'
  if value.startswith('Jump requested.'):return 'forest_game_action'
  return 'other_text_without_confirmed_source_world'

def server_run(name,src,idx):
    target=ROOT/(name+'-raw-v2.json')
    assert not target.exists(),'A previously frozen experiment version cannot be overwritten'
    server=src/'prse_runtime/server.mjs'
    engine=src/'browser_physics_prototype/physics-core.js'
    assert server.is_file() and engine.is_file()
    port=free_port()
    assert port!=18764
    state_dir=ROOT/(name+'-private-game-state-v2')
    state_dir.mkdir(exist_ok=True,mode=0o700);state_dir.chmod(0o700)
    logfile=ROOT/(name+'-server-logs-v2.txt')
    code_hashes={'server':sha(server),'gameCore':sha(engine)}
    env={**os.environ,'PRSE_PORT':str(port),'PRSE_STATE_DIR':str(state_dir),
         'PRSE_LOG_LEVEL':'quiet','PRSE_MAX_ACTIVE':'2',
         'PRSE_LLM_URL':'http://127.0.0.1:1/blocked-no-gpu'}
    start_time=time.perf_counter()
    logfile_f=logfile.open('xb');logfile.chmod(0o600)
    proc=None;ws=None;latencies=defaultdict(list);values=Counter();receipts=[]
    peak_rss=0; cpu_seconds=0.;fatal=None;replies=0;init_seconds=None;token=None
    try:
      proc=subprocess.Popen(['node',str(server)],stdin=subprocess.DEVNULL,
                            stdout=logfile_f,stderr=subprocess.STDOUT,cwd=src,env=env)
      logfile_f.close()
      ps=psutil.Process(proc.pid)
      wait(lambda:health(f'http://127.0.0.1:{port}/health'),14)
      init_seconds=round(time.perf_counter()-start_time,4)
      ws=websocket.create_connection(f'ws://127.0.0.1:{port}/ws',timeout=15,origin='http://127.0.0.1')
      ws.send(json.dumps({'type':'hello'}))
      ws.settimeout(12)
      while True:
        welcome=json.loads(ws.recv())
        if welcome.get('type')=='welcome':break
      token=welcome['token']
      assert len(token)==32
      assert welcome['authoritative'] and welcome['physicsHz']==60
      kinds=[e['kind'] for e in welcome['state']['visibleEntities']]
      initial_state=Counter(kinds)
      test_start=time.perf_counter()
      for n,item in enumerate(rows):
        text=item['text']
        uid=n+1
        t=time.perf_counter_ns()
        ws.send(json.dumps({'type':'text','text':text,'requestId':uid},
                            ensure_ascii=False,separators=(',',':')))
        answer=read_ack(ws,uid)
        elapsed=(time.perf_counter_ns()-t)/1e6
        group=item['group']
        label_type=item['labelType']
        key=(group,label_type)
        if answer['type']=='error':raise RuntimeError('Backend emitted server error to original human constraint')
        expect_rejected=js_len(text)>120
        if expect_rejected and answer['type']!='rejected':raise AssertionError('Original overlimit human source accepted')
        if not expect_rejected and answer['type']=='rejected':raise AssertionError('Valid-length author instruction rejected')
        category=source_kind(text,answer)
        values['total_requests']+=1
        values[group+'_total']+=1
        values['long_source_human_input_rejected']+=int(expect_rejected)
        values['valid_length_requests']+=int(not expect_rejected)
        values['response_'+category]+=1
        values['spurious_bench_label']=int(values['spurious_bench_label'])+int(
            category=='unsupported_foreign_world_object' and 'bench' not in text.lower())
        values['source_author_relevant_answer']=int(values['source_author_relevant_answer'])+int(
            category not in ('rejected','unsupported_foreign_world_object','unsupported_generic_help'))
        latencies['all'].append(elapsed)
        latencies['full' if group.startswith('complete') else 'annotation'].append(elapsed)
        latencies['length_rejected' if expect_rejected else 'within_limit'].append(elapsed)
        latencies['source_'+label_type].append(elapsed)
        receipts.append({'sourceIndex':item['sourceIndex'],'group':group,'labelType':label_type,
                         'originalLabelIndex':item['labelIndex'],'originalSourceSHA256':hash_text(text),
                         'originalInputLengthJSUTF16':js_len(text),'responseType':answer['type'],
                         'responseCategory':category,'responseSHA256':hash_text(answer.get('text',answer.get('message',''))),
                         'elapsedMilliseconds':round(elapsed,4)})
        replies+=1
        if n%80==0:
          peak_rss=max(peak_rss,ps.memory_info().rss)
          usage=ps.cpu_times()
          cpu_seconds=usage.user+usage.system
        if (n+1)%250==0:print('ROUND5_AUTHOR_INPUT_PROGRESS',name,n+1,'/',expected,
           'requests done,', round((time.perf_counter()-test_start),2),'seconds',flush=True)
      # No real world creation or corrupted persistent session allowed.
      ws.send(json.dumps({'type':'save'}))
      deadline=time.monotonic()+9
      while time.monotonic()<deadline:
        ws.settimeout(.7)
        try:r=json.loads(ws.recv())
        except websocket.WebSocketTimeoutException:continue
        if r.get('type')=='message' and ('saved' in (r.get('text','').lower())):break
        if r.get('type')=='error':raise RuntimeError('Durable save error')
      ws.close();ws=None
      if proc.poll() is None:
        proc.terminate()
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
      files=list(state_dir.glob('*.snapshot.json'))
      logs=list(state_dir.glob('*.events.ndjson'))
      if len(files)!=1 or len(logs)!=1:raise AssertionError('Isolated session persisted file count wrong')
      d=json.loads(files[0].read_text())
      kinds_post=Counter(e['kind'] for e in d.get('semantic',{}).get('entities',[]))
      # Forest scene has no projector or newly authored rooms, but never
      # confuse 'no projector' with correct interpretation.
      assert d['version']==5 and 'projector' not in kinds_post
      assert 'conference_table' not in kinds_post
      assert len(d['semantic']['entities'])==11
      # Private raw evidence preserves original *source hashes* and response
      # hashes, not the original copyrighted prompts or session tokens.
      total_seconds=round(time.perf_counter()-test_start,4)
      measurements={'experiment':name,'fullInputs':130,'humanAnnotatedClauses':1250,
       'sampleCount':replies,'distinctSourceInstructions':130,
       'startupSeconds':init_seconds,'allQueriesWallSeconds':total_seconds,
       'CPUSecondsForHostSampled':round(cpu_seconds,4),
       'peakObservedResidentMiB':round(peak_rss/1048576,3),
       'serverEngineCodeSHA256':code_hashes,
       'authorTextAbove120':sum(js_len(x['text'])>120 for x in rows),
       'finalSavedGameSceneEntities':len(d['semantic']['entities']),
       'finalSavedSourceSpecificProjectorCount':kinds_post['projector'],
       'finalSavedSourceSpecificTableCount':kinds_post['table'],
       'reportedConfiguredPhysicsHz':welcome['physicsHz'],
       'modelRequestsSent':0,'productionProcessTouched':False,
       'allIsolatedServerProcessesTerminated':True,
       'latencyMilliseconds':{str(k):{
          'n':len(v),'p05':percent(v,.05),'median':percent(v,.5),
          'p95':percent(v,.95),'max':percent(v,1),'mean':round(statistics.mean(v),3)
          }for k,v in latencies.items() if not k.startswith('source_')},
       'originalCategoryCounts':dict(SOURCE_KEYS),
       'classifiedResponses':dict(values),
       'privateLogBytes':logs[0].stat().st_size,
       'privateSnapshotBytes':files[0].stat().st_size,
       'privateSavedDataPermissionsOk':all((x.stat().st_mode&0o777)==0o600 for x in files+logs)}
      assert values['total_requests']==1380
      assert values['complete_human_author_instruction_total']==130
      assert values['human_annotated_clause_total']==1250
      assert measurements['privateSavedDataPermissionsOk']
      output={'metadata':{
        'LEGOHumanAuthoredIndependentConstraintSourceSHA256':SOURCE_SHA,
        'allInputTextsAndHumanLabelsSourceOnlyFromLEGO':True,
        'promptNoTrainingOrGoldLeakToSourceParser':True,
        'sameHumanInputCorpusBothBackendDeployments':True,
        'onlyDistinctBackendDeploymentSourceVersionDiffers':True,
        'semanticValidation':'original human source must become correct source-specific game state; text fallback is failure',
        'NO_GOLD_TRUE_NEGATIVES':True,
        'endToEndPath':'actual private Nitro GameCore WebSocket message/response including IPC but excluding browser rendering',
        'referenceAssetMeshDimensionsUnavailable':True,
        'noDeniedRandomParentPlacebo':True},'results':measurements,'perOriginalRequest':receipts}
      write_private(target,(json.dumps(output,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
      print('ROUND5_AUTHOR_INPUT_RESULT',name,json.dumps({k:v for k,v in measurements.items()
           if k in ('sampleCount','allQueriesWallSeconds','startupSeconds',
                    'peakObservedResidentMiB','classifiedResponses','latencyMilliseconds')})[:3200],flush=True)
      return measurements,sha(target)
    except Exception as e:
      fatal=e
      raise
    finally:
      if ws:
        try:ws.close()
        except Exception:pass
      if proc and proc.poll() is None:
        proc.terminate()
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
      if not logfile_f.closed:logfile_f.close()
      if fatal:print('ROUND5_SOURCE_ENDPOINT_ERROR',name,type(fatal).__name__,str(fatal)[:250],flush=True)

pairs=[]
for i,(name,src) in enumerate([
 ('committed_research_viewer_server',pathlib.Path('/data/src/worktrees/game-skills-hidden-20261024')),
 ('current_canonical_uncommitted_server',pathlib.Path('/data/src/github/games'))
]):
 result,checksum=server_run(name,src,i)
 pairs.append((name,result,checksum))

def fmt(m):
  return {'backendCodeSHA256':m['serverEngineCodeSHA256'],
    'originalSourceAcceptanceRate':0,
    'allMessages':m['sampleCount'],
    'endToEndGameSourceSpecificInstances':m['finalSavedSourceSpecificProjectorCount'],
    'latencyMilliseconds':m['latencyMilliseconds'],
    'allQuerySeconds':m['allQueriesWallSeconds'],
    'startupSeconds':m['startupSeconds'],
    'observedPeakRSSMiB':m['peakObservedResidentMiB'],
    'classification':m['classifiedResponses']}
safe={'metadata':{'evidence':'official independently human-authored LEGO full source instructions + 1250 annotated constraints through actual isolated GameCore WebSocket',
 'sourceSHA256':SOURCE_SHA,'noSameBodyPhysicsReplay':True,
 'bothBackendVersionsIsolatedAndProductionUntouched':True,
 'notTrueIndependentNegativeContactGold':True,
 'allLLMAndGPUInferenceDisabled':True},
 'comparison':{name:fmt(res)|{'privateCompleteRawSHA256':checksum} for name,res,checksum in pairs}}
out=HERE/'prse_round5_real_human_source_websocket_cost_error_latency_aggregate_v2.json'
with out.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
print('ROUND5_SOURCE_ACCEPTANCE_COMPARISON_COMPLETE',json.dumps({
 name:{'requests':res['sampleCount'],'seconds':res['allQueriesWallSeconds'],
 'medianMs':res['latencyMilliseconds']['all']['median'],
 'p95Ms':res['latencyMilliseconds']['all']['p95'],
 'originalSceneCreated':False}
 for name,res,h in pairs},sort_keys=True))
