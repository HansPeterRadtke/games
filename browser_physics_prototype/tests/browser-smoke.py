#!/usr/bin/env python3
"""Isolated CDP browser context; never uses or closes unrelated user tabs."""
import base64,json,time,os,requests,websocket,itertools,sys
from pathlib import Path
HOST=os.environ.get('CDP_HOST','http://127.0.0.1:40297')
URL=os.environ.get('GAME_URL','http://127.0.0.1/llm_game/physics-prototype/')
MOBILE=os.environ.get('MOBILE','0')=='1'
SCENE=os.environ.get('SCENE','0')=='1'
class CDP:
 def __init__(self):
  ws_url=requests.get(HOST+'/json/version',timeout=5).json()['webSocketDebuggerUrl'];self.ws=websocket.create_connection(ws_url,timeout=10,origin='http://127.0.0.1');self.ids=itertools.count(1);self.context=None;self.target=None;self.session=None
 def call(self,method,params=None,session=False):
  no=next(self.ids);q={'id':no,'method':method,'params':params or {}};
  if session:q['sessionId']=self.session
  self.ws.send(json.dumps(q));deadline=time.time()+18
  while time.time()<deadline:
   data=json.loads(self.ws.recv());
   if data.get('id')==no:
    if 'error' in data:raise RuntimeError(f'{method}: {data["error"]}')
    return data.get('result',{})
  raise TimeoutError(method)
 def eval(self,s):
  response=self.call('Runtime.evaluate',{'expression':s,'returnByValue':True,'awaitPromise':True},True)
  if response.get('exceptionDetails'):raise RuntimeError(str(response['exceptionDetails']))
  return response.get('result',{}).get('value')
 def open(self):
  self.context=self.call('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId'];self.target=self.call('Target.createTarget',{'url':'about:blank','browserContextId':self.context})['targetId'];self.session=self.call('Target.attachToTarget',{'targetId':self.target,'flatten':True})['sessionId'];self.call('Page.enable',session=True);self.call('Runtime.enable',session=True);self.call('Page.navigate',{'url':URL},session=True)
 def close(self):
  try:
   if self.target:self.call('Target.closeTarget',{'targetId':self.target})
   if self.context:self.call('Target.disposeBrowserContext',{'browserContextId':self.context})
  finally:self.ws.close()
c=CDP()
try:
 c.open()
 if MOBILE:
  c.call('Emulation.setDeviceMetricsOverride',{'width':320,'height':740,'deviceScaleFactor':2,'mobile':True},True)
  c.call('Page.reload',{'ignoreCache':True},True)
 start=time.monotonic()
 while time.monotonic()-start<18:
  status=c.eval('document.querySelector("#status")?.textContent')
  ready=c.eval('!!window.__gameDebug')
  if ready or (status and ('failed' in status.lower())):break
  time.sleep(.3)
 assert ready,f'Browser game not ready: {status}'
 print('READY',status,'time',round(time.monotonic()-start,2),'title',c.eval('document.title'),flush=True)
 print('INITIAL',c.eval('JSON.stringify(window.__gameDebug.core.state().ragdoll.parts.torso.position)'),flush=True)
 dimensions=c.eval('JSON.stringify({width:document.documentElement.scrollWidth,window:window.innerWidth,buttons:[...document.querySelectorAll("button")].map(x=>Math.floor(x.getBoundingClientRect().height)).filter(x=>x<44)})');print('LAYOUT',dimensions,flush=True)
 d=json.loads(dimensions);assert d['width']<=d['window']+2,'Unexpected horizontal scroll';assert not d['buttons'],'Some tap targets smaller than 44 CSS px'
 
 c.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Enter','code':'Enter','windowsVirtualKeyCode':13},session=True)
 c.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Enter','code':'Enter','windowsVirtualKeyCode':13},session=True)
 focused=c.eval('document.activeElement.id');assert focused=='semantic-input',f'Enter did not focus command input: {focused}'
 print('ENTER_FOCUS',focused,flush=True)
 # Verify the actual game UI, not merely the isolated physics laboratory.
 c.eval('document.getElementById("semantic-input").value="look"')
 c.eval('document.getElementById("semantic-form").requestSubmit()')
 assert 'footbridge' in c.eval('document.getElementById("message").textContent').lower(),'text RPG description missing'
 gathered=0
 for _ in range(10):
  if c.eval('window.__gameDebug.core.state().nearby?.kind')!='plank':
   c.eval('(function(){let g=window.__gameDebug.core;g.command({type:"Move",direction:-1});for(let i=0;i<15;i++)g.step();g.command({type:"Move",direction:0});})()')
  if c.eval('window.__gameDebug.core.state().nearby?.kind')=='plank':c.eval('document.getElementById("interact").click()')
  gathered=c.eval('window.__gameDebug.core.character.inventory.plank')
  if gathered>=2:break
 assert gathered>=2,f'Cannot gather timber by physically walking left and using Interact: {gathered}'
 c.eval('window.__gameDebug.core.command({type:"Goal",intent:"crossFence"})')
 crossed=c.eval('(function(){let g=window.__gameDebug.core;for(let i=0;i<950&&g.goal;i++)g.step();return g.events.some(e=>e.type==="goal_success")})()')
 assert crossed,'high-level fence goal failed in real browser'
 found=c.eval('(function(){let g=window.__gameDebug.core;g.command({type:"Move",direction:1});for(let i=0;i<850&&g.state().nearby?.kind!=="workbench";i++)g.step();g.command({type:"Move",direction:0});for(let i=0;i<7;i++)g.step();return g.state().nearby?.kind})()')
 assert found=='workbench',f'workbench unreachable in browser: {found}'
 c.eval('document.getElementById("interact").click()')
 repaired=c.eval('window.__gameDebug.core.character.bridgeRepaired')
 assert repaired,'bridge repair button failed in browser'
 print('GAMEPLAY_JOURNEY',json.dumps({'gathered':gathered,'fenceGoal':crossed,'bridgeRepaired':repaired}),flush=True)
 c.eval('document.getElementById("restart").click()')
 for id in ['ragdoll-walk','ragdoll','ragdoll-injure','save','load','ragdoll-relax','ragdoll-balance']:
  c.eval(f'document.getElementById({json.dumps(id)}).click()');time.sleep(.18)
  print('CLICK',id,'mode',c.eval('window.__gameDebug.core.state().ragdoll.mode'),'event',c.eval('document.querySelector("#message").textContent'),flush=True)
 c.eval('document.querySelector("#semantic-input").blur()')
 c.eval('document.getElementById("semantic-input").value="jump over fence"');c.eval('document.getElementById("semantic-form").requestSubmit()')
 assert c.eval('window.__gameDebug.core.state().goal') is not None,'text goal missing'
 time.sleep(.6)
 c.call('Network.enable',session=True)
 c.call('Network.emulateNetworkConditions',{'offline':True,'latency':500,'downloadThroughput':20000,'uploadThroughput':2000},session=True)
 t0=c.eval('window.__gameDebug.core.time');time.sleep(1.1);t1=c.eval('window.__gameDebug.core.time')
 assert t1-t0>.5,f'World stopped simulating offline: {t0} -> {t1}'
 print('OFFLINE_SIMULATION',round(t1-t0,2),'seconds of physics',flush=True)
 c.call('Network.emulateNetworkConditions',{'offline':False,'latency':0,'downloadThroughput':-1,'uploadThroughput':-1},session=True)
 c.eval('window.scrollTo(0,0)');time.sleep(.2)
 screenshot=c.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False},True)['data'];path=Path('/data/tmp/game-active-mobile.png' if MOBILE else '/data/tmp/game-active-smoke.png');path.write_bytes(base64.b64decode(screenshot));print('SCREENSHOT',path,path.stat().st_size,flush=True)
 if SCENE:
  # Traverse same renderer/physics path using an isolated browser context to validate generated story objects.
  c.eval('document.getElementById("restart").click()')
  c.eval('(function(){let g=window.__gameDebug.core;g.player.setTranslation({x:37.1,y:.86,z:0},true);g.player.setLinvel({x:0,y:0,z:0},true);for(let i=0;i<65;i++)g.step()})()')
  members=c.eval('JSON.stringify(["shelter-bench","shelter-candle","shelter-jug","shelter-note"].map(id=>({id,exists:!!window.__gameDebug.core.worldBridge.active.get(id)})))')
  assert all(item['exists'] for item in json.loads(members)),'Generated 3D scene not materialized in public browser'
  for textcmd in ['read note','light candle','ignite note']:
   c.eval('document.getElementById("semantic-input").value='+json.dumps(textcmd))
   c.eval('document.getElementById("semantic-form").requestSubmit()')
  assert c.eval('window.__gameDebug.core.character.knows("warning_note")'),'reading note should persist knowledge'
  assert c.eval('window.__gameDebug.core.consequences.pending.length')>0,'no fire cause/effect schedule'
  c.eval('(function(){let g=window.__gameDebug.core;for(let i=0;i<1510;i++)g.step();window.__gameDebug.renderer.draw(g.state())})()')
  c.eval('window.scrollTo(0,0)');time.sleep(.4)
  screenshot=c.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False},True)['data']
  scene_path=Path('/data/tmp/game-scene-mobile.png' if MOBILE else '/data/tmp/game-scene-desktop.png')
  scene_path.write_bytes(base64.b64decode(screenshot))
  print('LLM_SCENE',members,'knowledge',c.eval('window.__gameDebug.core.character.knowledge.length'),'condition',c.eval('window.__gameDebug.core.semantic.entity("shelter-bench").state.condition'),'screenshot',scene_path,flush=True)
 print('SUCCEEDED',flush=True)
finally:
 c.close()
