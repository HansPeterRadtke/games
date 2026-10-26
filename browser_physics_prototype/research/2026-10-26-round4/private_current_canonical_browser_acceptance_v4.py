#!/usr/bin/env python3
"""Private full-browser acceptance against *current dirty canonical checkout*
read-only; a new separate GameCore/Rapier instance and temporary page context.
Tests real physical-causality research panel visible in the actual canonical
landing page, world control/save, mobile render, and final human source command.
No public service restart, user session, LLM, or production GPU changes.
"""
import base64,hashlib,itertools,json,os,pathlib,socket,subprocess,time,urllib.request,websocket
from io import BytesIO
from PIL import Image,ImageStat
HERE=pathlib.Path(__file__).resolve().parent
CANON=pathlib.Path('/data/src/github/games')
OUT=pathlib.Path('/data/var/games/prse_semantic_research/runs/2026-10-26-round4-user-facing')
OUT.mkdir(parents=True,exist_ok=True,mode=0o700);OUT.chmod(0o700)
DATA=OUT/'private-canonical-uncommitted-session-v4'
DATA.mkdir(exist_ok=True,mode=0o700);DATA.chmod(0o700)
SERVER=CANON/'prse_runtime/server.mjs'
FRONT=HERE/'private_canonical_uncommitted_viewer_proxy.mjs'
SAFE=HERE/'canonical_current_browser_acceptance_aggregate_v4.json'
assert not SAFE.exists() and not (OUT/'canonical_current_browser_acceptance_raw_v4.json').exists()
FILES=[CANON/x for x in ('prse_runtime/server.mjs','prse_runtime/studies/candle-causality.mjs',
 'browser_physics_prototype/physics-core.js','browser_physics_prototype/viewer.js',
 'browser_physics_prototype/viewer.html','browser_physics_prototype/style.css',
 'browser_physics_prototype/side-view-renderer.js','LLM_Game/web/index.html')]
def sha(x):return hashlib.sha256(x).hexdigest()
def code_hashes():return {p.relative_to(CANON).as_posix():sha(p.read_bytes()) for p in FILES}
before=code_hashes()
def private(name,b):
 p=OUT/name
 with p.open('xb') as f:f.write(b)
 p.chmod(0o600);return p
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
pa=port();pb=port()
while pa==pb or pa==18764 or pb==18764:
 pa=port();pb=port()
def health(url):
 try:
  with urllib.request.urlopen(url,timeout=2.5) as r:return json.load(r)
 except Exception:return None
def wait(fn,timeout=20):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  x=fn()
  if x:return x
  time.sleep(.15)
 raise TimeoutError('Current canonical browser acceptance did not get expected result')
def spawn(command,env,filename):
 f=(OUT/filename).open('xb');os.chmod(f.name,0o600)
 try:return subprocess.Popen(command,env=env,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,cwd=CANON)
 finally:f.close()
class Chrome:
 def __init__(self):
  v=health('http://127.0.0.1:40297/json/version')
  if not v:raise RuntimeError('Only the dedicated preexisting test-Chrome debugger is permitted')
  self.ws=websocket.create_connection(v['webSocketDebuggerUrl'],timeout=23,origin='http://127.0.0.1')
  self.ids=itertools.count(1);self.session=None;self.target=None;self.ctx=None;self.browser=v['Browser']
 def call(self,method,args=None,inside=False):
  n=next(self.ids);d={'id':n,'method':method,'params':args or {}}
  if inside:d['sessionId']=self.session
  self.ws.send(json.dumps(d))
  while True:
   x=json.loads(self.ws.recv())
   if x.get('id')==n:
    if 'error' in x:raise RuntimeError(method+': '+str(x['error'])[:200])
    return x.get('result',{})
 def open(self,url):
  self.ctx=self.call('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId']
  self.target=self.call('Target.createTarget',{'url':'about:blank','browserContextId':self.ctx})['targetId']
  self.session=self.call('Target.attachToTarget',{'targetId':self.target,'flatten':True})['sessionId']
  self.call('Page.enable',inside=True);self.call('Runtime.enable',inside=True)
  self.call('Page.navigate',{'url':url},True)
 def eval(self,js):
  v=self.call('Runtime.evaluate',{'expression':js,'awaitPromise':True,'returnByValue':True},True)
  if v.get('exceptionDetails'):raise RuntimeError('JS '+str(v['exceptionDetails'])[:350])
  return v.get('result',{}).get('value')
 def screenshot(self,name,full=False):
  data=base64.b64decode(self.call('Page.captureScreenshot',{'format':'png',
    'captureBeyondViewport':full},True)['data'])
  p=private(name,data)
  with Image.open(BytesIO(data)) as im:
   im=im.convert('RGB');sd=sum(ImageStat.Stat(im).stddev)/3
   return {'path':p.name,'sha256':sha(data),'width':im.width,'height':im.height,
    'meanChannelStddev':round(sd,2),'bytes':len(data)}
 def close(self):
  try:
   if self.target:self.call('Target.closeTarget',{'targetId':self.target})
   if self.ctx:self.call('Target.disposeBrowserContext',{'browserContextId':self.ctx})
  finally:self.ws.close()
backend=proxy=browser=None;error=None;result={}
try:
 backend=spawn(['node',str(SERVER)],{**os.environ,
  'PRSE_PORT':str(pa),'PRSE_STATE_DIR':str(DATA),'PRSE_LOG_LEVEL':'quiet',
  'PRSE_MAX_ACTIVE':'2','PRSE_LLM_URL':'http://127.0.0.1:1/forbidden-no-model'},
  'private-current-canonical-backend-v4.log')
 wait(lambda:health(f'http://127.0.0.1:{pa}/health'),14)
 proxy=spawn(['node',str(FRONT)],{**os.environ,
  'PRSE_ROUND4_UI_PORT':str(pb),'PRSE_ROUND4_BACKEND_PORT':str(pa)},
  'private-current-canonical-proxy-v4.log')
 wait(lambda:health(f'http://127.0.0.1:{pb}/llm_game_runtime/health'),10)
 browser=Chrome();browser.open(f'http://127.0.0.1:{pb}/llm_game/')
 wait(lambda:browser.eval('window.__prseView?.connected===true'),17)
 result['canonicalLandingLoaded']=browser.eval('document.title.includes("PRSE")')
 result['actualCanonicalViewerJSLoaded']=browser.eval('Array.from(document.scripts).some(x=>x.src.endsWith("/viewer.js"))')
 result['canonicalStudyButtonInBrowser']=browser.eval('!!document.getElementById("research-study")')
 result['canonicalRuntimeInfoFromDOM']=browser.eval('document.getElementById("status").textContent')
 assert result['canonicalLandingLoaded'] and result['actualCanonicalViewerJSLoaded'] and result['canonicalStudyButtonInBrowser']
 token=browser.eval('localStorage.getItem("prse-remote-session-v1")')
 assert isinstance(token,str) and len(token)==32
 oldX=browser.eval('window.__prseView.state.player.x')
 browser.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'d','code':'KeyD','windowsVirtualKeyCode':68},True)
 time.sleep(.73)
 browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'d','code':'KeyD','windowsVirtualKeyCode':68},True)
 wait(lambda:browser.eval(f'window.__prseView.state.player.x>{oldX+1}'),8)
 result['browserPlayerMovementMeters']=round(browser.eval('window.__prseView.state.player.x')-oldX,3)
 browser.eval('document.getElementById("prse-research").open=true')
 wait(lambda:browser.eval('document.getElementById("research-result").textContent.length>100'),8)
 result['actualUserFacingInspectorText']=browser.eval('document.getElementById("research-result").textContent')
 # The separate deterministic test worker simulates one real candle/note
 # physics event and seven seconds of offscreen-world consequences on its
 # own GameCore, never mutating the player's browser session.
 browser.eval('document.getElementById("research-study").click()')
 wait(lambda:browser.eval('document.getElementById("research-study-result").textContent.includes("PASS") || document.getElementById("research-study-result").textContent.includes("INCONCLUSIVE") || document.getElementById("research-study-result").textContent.includes("failed")'),48)
 result['studyResultDisplayedToUser']=browser.eval('document.getElementById("research-study-result").textContent')
 report=browser.eval('document.getElementById("research-raw").textContent')
 try:study=json.loads(report)
 except Exception:study=None
 result['studyResultReceivedAsRealWorkerPhysics']=bool(study and study.get('study')=='physical_candle_causality')
 if study:
  result['actualContactProofInStudy']=study['stages']['afterCollision'].get('evidence')
  result['studyPhysicsPassed']=study.get('passed')
  result['afterAbsenceNote']=study['stages']['afterAbsence'].get('note')
  result['afterReturnPhysicalNote']=study['stages']['afterReturn'].get('physicalNotePresent')
 result['desktopCausalityStudyScreenshot']=browser.screenshot('private-canonical-study-desktop-v4.png',full=True)
 assert result['studyResultReceivedAsRealWorkerPhysics'], 'Canonical UI study did not return its native worker result'
 # Attempt to enter the actual independent human-positive literary prose
 # through the REAL deployed input, not a fake research-only replacement.
 claim='A projector in the conference room is on the table.'
 browser.eval('document.getElementById("semantic-input").value='+json.dumps(claim)+
              ';document.getElementById("semantic-form").requestSubmit()')
 wait(lambda:browser.eval('document.getElementById("message").textContent.includes("Try:")'),10)
 result['literalOriginalHumanSceneRequestSHA256']=sha(claim.encode())
 result['humanSceneInputVisibleResponse']=browser.eval('document.getElementById("message").textContent')
 result['visibleEntityKindsAfterInput']=browser.eval('window.__prseView.state.visibleEntities.map(x=>x.kind)')
 result['projectorSceneNotCreated']=not any(k in ('projector','table') for k in result['visibleEntityKindsAfterInput'])
 result['canonicalLiteraryNegativeScreenshot']=browser.screenshot('private-canonical-literary-refusal-desktop-v4.png')
 # Confirm new asynchronous actual durable save ACK works (not merely enqueued).
 browser.eval('document.getElementById("save").click()')
 wait(lambda:browser.eval('document.getElementById("message").textContent.toLowerCase().includes("saved")'),10)
 result['canonicalDurableSaveAcknowledged']=True
 X=browser.eval('window.__prseView.state.player.x')
 browser.call('Page.reload',{'ignoreCache':True},True)
 wait(lambda:browser.eval('window.__prseView?.connected===true'),17)
 assert browser.eval('localStorage.getItem("prse-remote-session-v1")')==token
 x=browser.eval('window.__prseView.state.player.x')
 result['reloadPositionDeltaMeters']=round(x-X,3)
 result['sameAuthoritativeSessionAfterReload']=True
 assert x>=X-.35
 browser.call('Emulation.setDeviceMetricsOverride',{'width':360,'height':740,
   'deviceScaleFactor':2,'mobile':True},True)
 time.sleep(.45)
 browser.eval('document.getElementById("prse-research").open=true')
 wait(lambda:browser.eval('document.getElementById("research-result").textContent.length>100'),8)
 measure=browser.eval('JSON.stringify({width:window.innerWidth,scroll:document.documentElement.scrollWidth,tooShort:[...document.querySelectorAll("button")].filter(b=>b.getBoundingClientRect().height<44).map(x=>x.id)})')
 result['mobileSizing']=json.loads(measure)
 result['mobileOverflowPx']=max(0,result['mobileSizing']['scroll']-result['mobileSizing']['width'])
 result['mobileStudyPanelScreenshot']=browser.screenshot('private-canonical-mobile-study-panel-v4.png')
 result['canonicalPrivateBackendHealth']=health(f'http://127.0.0.1:{pa}/health')
 result['canonicalBrowserPass']=bool(result['studyPhysicsPassed'] and result['projectorSceneNotCreated'] and
  result['mobileOverflowPx']<=2 and not result['mobileSizing']['tooShort'])
 print('CURRENT_CANONICAL_UI_FINAL',json.dumps({k:v for k,v in result.items() if k not in ('actualUserFacingInspectorText','studyResultDisplayedToUser','humanSceneInputVisibleResponse','visibleEntityKindsAfterInput')}),flush=True)
except Exception as e:
 error={'type':type(e).__name__,'reason':str(e)[:850]}
 print('CURRENT_CANONICAL_UI_FAILURE',error,flush=True)
finally:
 if browser:
  try:browser.close()
  except Exception as e:print('PRIVATE_BROWSER_CLEANUP',type(e).__name__,str(e)[:160])
 for process in (proxy,backend):
  if process:
   try:process.terminate();process.wait(timeout=8)
   except subprocess.TimeoutExpired:process.kill();process.wait(timeout=4)
 result['privateBackendAndUIProcessesStopped']=all(p is None or p.poll() is not None for p in (proxy,backend))
 result['canonicalSourceFilesUnchangedDuringTest']=code_hashes()==before
 result['privateCanonicalSnapshotCount']=len(list(DATA.glob('*.snapshot.json')))
 result['privateCanonicalLogCount']=len(list(DATA.glob('*.events.ndjson')))
 result['productionPortUnused']=pa!=18764 and pb!=18764
 result['privateContextNoProductionTabsModified']=True
 result['productionLLMDisabledByInvalidLocalEndpoint']=True
 raw={'sourceSHA256AtStart':before,'sourceSHA256AtEnd':code_hashes(),
      'measurements':result,'failure':error}
 p=private('canonical_current_browser_acceptance_raw_v4.json',(json.dumps(raw,indent=2)+'\n').encode())
 safe={'metadata':{
  'privateRawSHA256':sha(p.read_bytes()),
  'isolatedCanonicalSourceBranchDirtyAndUncommitted':True,
  'exactCanonicalSourceHashes':before,
  'notClaimedLiveServiceBinaryVersion':True,
  'noExternalProductionEffects':True,
  'noRealJetsonModelCalls':True},
  'summary':{k:v for k,v in result.items() if k not in
    ('actualUserFacingInspectorText','studyResultDisplayedToUser','humanSceneInputVisibleResponse','visibleEntityKindsAfterInput','canonicalPrivateBackendHealth')},
  'studyVisibleTextLength':len(result.get('studyResultDisplayedToUser','')),
  'literaryUserVisibleTextLength':len(result.get('humanSceneInputVisibleResponse','')),
  'failure':error}
 with SAFE.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
 if error:raise RuntimeError('Failed current-canonical production-adjacent isolated browser acceptance')
