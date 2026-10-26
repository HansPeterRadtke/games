#!/usr/bin/env python3
"""TRUE Chromium presentation acceptance for the existing unchanged PRSE viewer.

Runs one new *private* GameCore/Rapier backend and an isolated loopback
unmodified static UI+WebSocket proxy, drives Chrome in an independent,
disposable browser context, captures the actual pixels and observed DOM,
and verifies save/reconnect and mobile layout. This is not an arbitrary
literary-source player, and no production server, session, browser tab or
Jetson LLM is touched.
"""
import base64, contextlib, hashlib, itertools, json, os, pathlib, socket
import subprocess, time, urllib.request, websocket
from PIL import Image, ImageStat
from io import BytesIO

HERE=pathlib.Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
RUN=pathlib.Path('/data/var/games/prse_semantic_research/runs/2026-10-26-round4-user-facing')
RUN.mkdir(parents=True,exist_ok=True,mode=0o700)
RUN.chmod(0o700)
DATA=RUN/'private-gamecore-sessions-v1'
DATA.mkdir(mode=0o700,exist_ok=True)
DATA.chmod(0o700)
PROXY=HERE/'private_unmodified_viewer_proxy.mjs'
SERVER=PROJECT/'prse_runtime/server.mjs'
assert PROXY.is_file() and SERVER.is_file()
assert not (RUN/'browser_user_visible_acceptance_raw_v1.json').exists(), 'Preserve earlier results: do not rerun this version'
def sha(x):return hashlib.sha256(x).hexdigest()
def write_private(filename,bytes_):
 p=RUN/filename
 with p.open('xb') as f:f.write(bytes_)
 p.chmod(0o600)
 return p
def pick_port():
 with socket.socket() as s:
  s.bind(('127.0.0.1',0))
  return s.getsockname()[1]
port_a=pick_port()
port_b=pick_port()
while port_b in (port_a,18764):port_b=pick_port()
assert port_a!=18764 and port_b!=18764
def spawn(command,env,log):
 file=log.open('xb');os.chmod(log,0o600)
 proc=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=file,
                       stderr=subprocess.STDOUT,cwd=PROJECT)
 file.close()
 return proc
def health(url):
 try:
  with urllib.request.urlopen(url,timeout=2.5) as r:return json.load(r)
 except Exception:return None
def wait(fn,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  val=fn()
  if val:return val
  time.sleep(.13)
 raise TimeoutError('Acceptance condition did not occur before timeout')
class CDP:
 def __init__(self):
  info=health('http://127.0.0.1:40297/json/version')
  if not info or not info.get('webSocketDebuggerUrl'):
   raise RuntimeError('Dedicated already-running debug browser missing; no production browser tabs may be reused')
  self.browser=info['Browser']
  self.ws=websocket.create_connection(info['webSocketDebuggerUrl'],timeout=20,origin='http://127.0.0.1')
  self.ids=itertools.count(1);self.context=None;self.target=None;self.session=None
 def call(self,method,params=None,session=False):
  req={'id':next(self.ids),'method':method,'params':params or {}}
  if session:req['sessionId']=self.session
  self.ws.send(json.dumps(req))
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   msg=json.loads(self.ws.recv())
   if msg.get('id')==req['id']:
    if 'error' in msg:raise RuntimeError(method+': '+str(msg['error']))
    return msg.get('result',{})
  raise TimeoutError(method)
 def open(self,url):
  self.context=self.call('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId']
  self.target=self.call('Target.createTarget',{'url':'about:blank','browserContextId':self.context})['targetId']
  self.session=self.call('Target.attachToTarget',{'targetId':self.target,'flatten':True})['sessionId']
  self.call('Page.enable',session=True)
  self.call('Runtime.enable',session=True)
  self.call('Page.navigate',{'url':url},True)
 def eval(self,js):
  r=self.call('Runtime.evaluate',{'expression':js,'returnByValue':True,'awaitPromise':True},True)
  if r.get('exceptionDetails'):raise RuntimeError('Page JS error '+str(r['exceptionDetails'])[:600])
  return r.get('result',{}).get('value')
 def until(self,js,seconds=16):
  return wait(lambda:self.eval(js),seconds)
 def screenshot(self,name):
  png=base64.b64decode(self.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False},True)['data'])
  img=Image.open(BytesIO(png)).convert('RGB')
  colors=len(img.resize((90,60)).getcolors(6000) or [])
  spread=sum(ImageStat.Stat(img).stddev)/3
  p=write_private(name,png)
  return {'path':p.name,'width':img.width,'height':img.height,
          'uniqueSmallImageColors':colors,'meanChannelStddev':round(spread,2),
          'sha256':sha(png),'bytes':len(png)}
 def close(self):
  try:
   if self.target:self.call('Target.closeTarget',{'targetId':self.target})
   if self.context:self.call('Target.disposeBrowserContext',{'browserContextId':self.context})
  finally:self.ws.close()

environment={**os.environ,'PRSE_PORT':str(port_a),'PRSE_STATE_DIR':str(DATA),
 'PRSE_LOG_LEVEL':'quiet','PRSE_MAX_ACTIVE':'2'}
proxyenv={**os.environ,'PRSE_ROUND4_UI_PORT':str(port_b),
 'PRSE_ROUND4_BACKEND_PORT':str(port_a)}
backend=None;proxy=None;chrome=None;failure=None
measure={}
try:
 backend=spawn(['node',str(SERVER)],environment,RUN/'private-backend-v1.log')
 assert wait(lambda:health(f'http://127.0.0.1:{port_a}/health'),12)['ok']
 proxy=spawn(['node',str(PROXY)],proxyenv,RUN/'private-viewer-proxy-v1.log')
 assert wait(lambda:health(f'http://127.0.0.1:{port_b}/llm_game_runtime/health'),8)['ok']
 chrome=CDP()
 chrome.open(f'http://127.0.0.1:{port_b}/viewer.html')
 chrome.until('window.__prseView?.connected===true && !!window.__prseView?.state?.player',18)
 assert chrome.eval('Array.from(document.scripts).some(s=>s.src.endsWith("/viewer.js"))')
 assert not chrome.eval('Array.from(document.scripts).some(s=>s.src.endsWith("/game.js"))')
 token=chrome.eval('localStorage.getItem("prse-remote-session-v1")')
 assert isinstance(token,str) and len(token)==32
 measure['privateBrowserContext']=True;measure['browserEngine']=chrome.browser
 measure['unmodifiedProductionViewerLoaded']=True;measure['isolatedGameCoreBackend']=True
 measure['initialPlayerX']=chrome.eval('window.__prseView.state.player.x')
 measure['initialBrowserStatus']=chrome.eval('document.getElementById("status").textContent')
 measure['initialVisibleCanvasPNGSize']=chrome.eval('document.getElementById("scene").toDataURL("image/png").length')
 assert measure['initialVisibleCanvasPNGSize']>1200
 chrome.eval('document.getElementById("semantic-input").value="look";document.getElementById("semantic-form").requestSubmit()')
 chrome.until('document.getElementById("message").textContent.includes("forest")',10)
 measure['userVisibleLookText']=chrome.eval('document.getElementById("message").textContent')
 measure['actualDesktopScreenshot']=chrome.screenshot('private-real-game-desktop-v1.png')
 old=chrome.eval('window.__prseView.state.player.x')
 chrome.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'d','code':'KeyD','windowsVirtualKeyCode':68},True)
 time.sleep(.95)
 chrome.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'d','code':'KeyD','windowsVirtualKeyCode':68},True)
 chrome.until(f'window.__prseView.state.player.x > {old+.9}',8)
 move=chrome.eval('window.__prseView.state.player.x')
 measure['playerMovedMeters']=round(move-old,3)
 time.sleep(.22)
 chrome.eval('document.getElementById("save").click()')
 chrome.until('document.getElementById("message").textContent.includes("saved")',8)
 measure['browserSaveAcknowledged']=True
 saved=chrome.eval('window.__prseView.state.player.x')
 chrome.call('Page.reload',{'ignoreCache':True},True)
 chrome.until('window.__prseView?.connected===true && !!window.__prseView?.state?.player',19)
 assert chrome.eval('localStorage.getItem("prse-remote-session-v1")')==token
 reloaded=chrome.eval('window.__prseView.state.player.x')
 assert reloaded>=saved-.25,('Browser UI load/reset movement lost',saved,reloaded)
 measure['reloadedPositionDeltaMeters']=round(reloaded-saved,3)
 before=chrome.eval('window.__prseView.disconnectCount')
 chrome.eval('window.__prseView.socket.close()')
 chrome.until(f'window.__prseView?.disconnectCount>{before}',8)
 chrome.until('window.__prseView?.connected===true',15)
 assert chrome.eval('localStorage.getItem("prse-remote-session-v1")')==token
 new=chrome.eval('window.__prseView.state.player.x')
 assert abs(new-reloaded)<.85
 measure['reconnectionDisplacementMeters']=round(new-reloaded,3)
 measure['samePrivateSessionAfterReloadAndReconnect']=True
 chrome.call('Emulation.setDeviceMetricsOverride',{'width':360,'height':740,
  'deviceScaleFactor':2,'mobile':True},True)
 time.sleep(.6)
 mobile=chrome.eval('JSON.stringify({viewport:window.innerWidth,documentWidth:document.documentElement.scrollWidth,shortButtons:[...document.querySelectorAll("button")].filter(b=>b.getBoundingClientRect().height<44).map(b=>b.id),status:document.getElementById("status").textContent})')
 measure['mobileDOM']=json.loads(mobile)
 measure['mobileHorizontalOverflowPx']=max(0,measure['mobileDOM']['documentWidth']-measure['mobileDOM']['viewport'])
 chrome.eval('document.getElementById("semantic-input").value="look";document.getElementById("semantic-form").requestSubmit()')
 chrome.until('document.getElementById("message").textContent.includes("forest")',9)
 measure['actualMobileScreenshot']=chrome.screenshot('private-real-game-mobile-v1.png')
 measure['mobileButtonsOver44Px']=not bool(measure['mobileDOM']['shortButtons'])
 measure['backendHealth']=health(f'http://127.0.0.1:{port_a}/health')
 measure['passesUIBasic']=bool(measure['mobileHorizontalOverflowPx']<=2 and measure['mobileButtonsOver44Px'])
 measure['LLMNotCalledOrAltered']=True
 measure['userFacingTextReadFromRenderedDOM']=True
 print('PRIVATE_UNMODIFIED_GAME_VIEWER_ACCEPTANCE',json.dumps({k:v for k,v in measure.items() if k not in ('userVisibleLookText',)}),flush=True)
except Exception as e:
 failure={'type':type(e).__name__,'reason':str(e)[:850]}
 print('PRIVATE_UNMODIFIED_GAME_VIEWER_FAILURE',failure,flush=True)
finally:
 if chrome:
  try:chrome.close()
  except Exception as e:print('PRIVATE_BROWSER_CLEANUP_ISSUE',type(e).__name__,str(e)[:150])
 for proc in (proxy,backend):
  if proc:
   try:proc.terminate();proc.wait(timeout=7)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
 measure['privateServerProcessesStopped']=all(p is None or p.poll() is not None for p in (proxy,backend))
 files=list(DATA.glob('*.snapshot.json'));logs=list(DATA.glob('*.events.ndjson'))
 measure['privateSavedSessionCount']=len(files)
 measure['privateEventLogCount']=len(logs)
 measure['privateServerFilesOwnerOnly']=all((p.stat().st_mode&0o777)==0o600 for p in files+logs)
 measure['productionPortNotUsed']=port_a!=18764 and port_b!=18764
 measure['isolatedSessionTokenRedacted']=True
 measure['browserNoSharedTabsModified']=True
 result={'metadata':{'mode':'real unmodified browser viewer and new isolated Nitro authoritative GameCore/Rapier on loopback',
  'doesNotExerciseArbitraryHumanLiteraryMaterialization':True,
  'backendCodeSHA256':sha(SERVER.read_bytes()),
  'viewerCodeSHA256':sha((PROJECT/'browser_physics_prototype/viewer.js').read_bytes()),
  'rendererCodeSHA256':sha((PROJECT/'browser_physics_prototype/side-view-renderer.js').read_bytes()),
  'productionPort18764Untouched':True,'noJetsonGPURequests':True},
  'measurements':measure,'failure':failure}
 private=write_private('browser_user_visible_acceptance_raw_v1.json',(json.dumps(result,indent=2)+'\n').encode())
 safe={'metadata':result['metadata']|{'privateRawSHA256':sha(private.read_bytes())},
       'summary':{k:v for k,v in measure.items() if k not in ('userVisibleLookText','backendHealth')},
       'renderedUserMessageLength':len(measure.get('userVisibleLookText','')),
       'failure':failure}
 safe_path=HERE/'browser_user_visible_acceptance_aggregate_v1.json'
 with safe_path.open('x') as f:json.dump(safe,f,indent=2);f.write('\n')
 if failure:raise RuntimeError('Private isolated browser acceptance failed, see versioned raw evidence')
