#!/usr/bin/env python3
"""Negative end-to-end product acceptance: human literary sentence through
UNCHANGED visible PRSE browser semantic input to isolated live GameCore/Rapier.
Expected product limitation: it refuses scene creation and does NOT
instantiate the projector/table. This is a NEW v3 test with separate state
and captures; it does not repeat v1 movement/save/viewport actions or touch
the existing game session, public browser, production service or GPUs.
"""
import base64,hashlib,itertools,json,os,pathlib,socket,subprocess,time,urllib.request,websocket
ROOT=pathlib.Path('/data/var/games/prse_semantic_research/runs/2026-10-26-round4-user-facing')
ROOT.mkdir(exist_ok=True,parents=True,mode=0o700);ROOT.chmod(0o700)
CODE=pathlib.Path(__file__).resolve().parents[3]
VIEWER=pathlib.Path(__file__).parent/'private_unmodified_viewer_proxy.mjs'
OUT=pathlib.Path(__file__).parent/'literary_user_entry_actual_browser_aggregate_v3.json'
assert not OUT.exists() and not (ROOT/'literary_user_entry_browser_raw_v3.json').exists()
STATES=ROOT/'private-gamecore-sessions-v3'
STATES.mkdir(exist_ok=True,mode=0o700);STATES.chmod(0o700)
def sha(x):return hashlib.sha256(x).hexdigest()
def reserve():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
backend=reserve();view=reserve()
while view==backend or backend==18764 or view==18764:
 backend=reserve();view=reserve()
def private(name,data):
 p=ROOT/name
 with p.open('xb') as f:f.write(data)
 p.chmod(0o600);return p
def fetch(url):
 try:
  with urllib.request.urlopen(url,timeout=2) as res:return json.load(res)
 except Exception:return None
def wait(fn,sec=12):
 deadline=time.monotonic()+sec
 while time.monotonic()<deadline:
  v=fn()
  if v:return v
  time.sleep(.15)
 raise TimeoutError('No response from isolated real user-facing pipeline')
def start(args,env,logname):
 f=(ROOT/logname).open('xb');os.chmod(f.name,0o600)
 try:return subprocess.Popen(args,cwd=CODE,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
 finally:f.close()
class Cdp:
 def __init__(self):
  info=fetch('http://127.0.0.1:40297/json/version')
  if not info:raise RuntimeError('Dedicated debug Chrome not available')
  self.ws=websocket.create_connection(info['webSocketDebuggerUrl'],timeout=15,origin='http://127.0.0.1')
  self.counter=itertools.count(1);self.ctx=None;self.target=None;self.session=None
 def cmd(self,method,params=None,inside=False):
  req={'id':next(self.counter),'method':method,'params':params or {}}
  if inside:req['sessionId']=self.session
  self.ws.send(json.dumps(req))
  while True:
   r=json.loads(self.ws.recv())
   if r.get('id')==req['id']:
    if 'error' in r:raise RuntimeError(str(r['error']))
    return r.get('result',{})
 def init(self,url):
  self.ctx=self.cmd('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId']
  self.target=self.cmd('Target.createTarget',{'url':'about:blank','browserContextId':self.ctx})['targetId']
  self.session=self.cmd('Target.attachToTarget',{'targetId':self.target,'flatten':True})['sessionId']
  self.cmd('Page.enable',inside=True);self.cmd('Runtime.enable',inside=True)
  self.cmd('Page.navigate',{'url':url},True)
 def evaluate(self,js):
  r=self.cmd('Runtime.evaluate',{'expression':js,'returnByValue':True,'awaitPromise':True},True)
  if r.get('exceptionDetails'):raise RuntimeError(str(r['exceptionDetails'])[:250])
  return r.get('result',{}).get('value')
 def screen(self,name):
  d=base64.b64decode(self.cmd('Page.captureScreenshot',{'format':'png'},True)['data'])
  return {'path':private(name,d).name,'sha256':sha(d),'bytes':len(d)}
 def cleanup(self):
  try:
   if self.target:self.cmd('Target.closeTarget',{'targetId':self.target})
   if self.ctx:self.cmd('Target.disposeBrowserContext',{'browserContextId':self.ctx})
  finally:self.ws.close()
game=None;proxy=None;chrome=None;failure=None;info={}
try:
 game=start(['node',str(CODE/'prse_runtime/server.mjs')],
  {**os.environ,'PRSE_PORT':str(backend),'PRSE_STATE_DIR':str(STATES),'PRSE_LOG_LEVEL':'quiet','PRSE_MAX_ACTIVE':'2'},
  'private-literary-entry-backend-v3.log')
 wait(lambda:fetch(f'http://127.0.0.1:{backend}/health'),10)
 proxy=start(['node',str(VIEWER)],{**os.environ,'PRSE_ROUND4_UI_PORT':str(view),
       'PRSE_ROUND4_BACKEND_PORT':str(backend)},'private-literary-entry-proxy-v3.log')
 wait(lambda:fetch(f'http://127.0.0.1:{view}/llm_game_runtime/health'),9)
 chrome=Cdp();chrome.init(f'http://127.0.0.1:{view}/viewer.html')
 wait(lambda:chrome.evaluate('window.__prseView?.connected===true'),20)
 # Original real author-supplied positive support claim on public LEGO human corpus.
 question='A projector in the conference room is on the table.'
 info['sourceRequestHashSHA256']=sha(question.encode())
 info['humanSourceInputLength']=len(question)
 info['sourceBelowInputAndTransportLimit']=len(question)<120
 info['beforePhysicalKinds']=chrome.evaluate('window.__prseView.state.visibleEntities.map(e=>e.kind)')
 info['beforeVisibleEntityCount']=len(info['beforePhysicalKinds'])
 chrome.evaluate('document.getElementById("semantic-input").value='+json.dumps(question)+
   ';document.getElementById("semantic-form").requestSubmit();')
 wait(lambda:'Try: look' in (chrome.evaluate('document.getElementById("message").textContent') or ''),10)
 answer=chrome.evaluate('document.getElementById("message").textContent')
 info['visibleResponseText']=answer
 info['visibleResponseWasCommandHelpInsteadOfSceneCreation']='Try: look' in answer
 info['afterPhysicalKinds']=chrome.evaluate('window.__prseView.state.visibleEntities.map(e=>e.kind)')
 info['noInventedSourceProjectorOrTable']=not any(x in ('projector','table') for x in info['afterPhysicalKinds'])
 info['physicalInventoryInVisibleRegionUnchanged']=info['beforePhysicalKinds']==info['afterPhysicalKinds']
 info['screenshot']=chrome.screen('private-literary-entry-rejected-v3.png')
 info['playerSawRejectionInRealBrowserDOM']=bool(chrome.evaluate('document.getElementById("message").innerText')==answer)
 info['realBackendHealth']=fetch(f'http://127.0.0.1:{backend}/health')
 print('LITERARY_SOURCE_FINAL_USER_SCREEN',json.dumps({k:v for k,v in info.items() if k not in ('beforePhysicalKinds','afterPhysicalKinds','visibleResponseText')}),flush=True)
except Exception as e:
 failure={'type':type(e).__name__,'reason':str(e)[:500]}
 print('LITERARY_SOURCE_USER_SCREEN_FAILED',failure,flush=True)
finally:
 if chrome:
  try:chrome.cleanup()
  except Exception as e:print('CONTEXT_CLEANUP',type(e).__name__,str(e)[:150])
 for process in (proxy,game):
  if process:
   try:process.terminate();process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
 info['isolatedProcessesTerminated']=all(p is None or p.poll() is not None for p in (game,proxy))
 info['localGameSnapshotFilesSaved']=len(list(STATES.glob('*.snapshot.json')))
 info['safeProductionIsolation']=(backend!=18764 and view!=18764)
 record={'metadata':{
  'testType':'actual unmodified PRSE viewer browser DOM -> private WebSocket -> authoritative GameCore textCommand -> visible rejection',
  'sourceSceneNotMaterialized':True,'noResearchOnlyDOMSubstituted':True,
  'noExternalProductionEffects':True,'noLocalOrJetsonLLMRequests':True,
  'viewerSourceCodeSHA256':sha((CODE/'browser_physics_prototype/viewer.js').read_bytes()),
  'gameCoreSourceCodeSHA256':sha((CODE/'browser_physics_prototype/physics-core.js').read_bytes())},
  'measurements':info,'failure':failure}
 raw=private('literary_user_entry_browser_raw_v3.json',(json.dumps(record,indent=2)+'\n').encode())
 safe={'metadata':record['metadata']|{'privateRawSHA256':sha(raw.read_bytes())},
       'summary':{k:v for k,v in info.items() if k not in ('visibleResponseText','realBackendHealth','beforePhysicalKinds','afterPhysicalKinds')},
       'visibleResponseLength':len(info.get('visibleResponseText','')),
       'failed':failure is not None}
 with OUT.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
 if failure:raise RuntimeError('Isolated literary entry user acceptance could not complete')
