#!/usr/bin/env python3
"""Checks remote authoritative runtime through real Chromium, isolated context."""
import base64, itertools, json, os, pathlib, requests, sys, time, websocket
URL=os.environ.get('PRSE_BROWSER_URL','https://nitro.jonnyontherun.org/llm_game/physics-prototype/viewer.html')
MOBILE=os.environ.get('MOBILE','0')=='1'
class Chrome:
 def __init__(self):
  url=requests.get('http://127.0.0.1:40297/json/version',timeout=5).json()['webSocketDebuggerUrl'];self.ws=websocket.create_connection(url,timeout=20,origin='http://127.0.0.1');self.ids=itertools.count(1);self.context=None;self.target=None;self.session=None
 def call(self,method,params=None,session=False):
  ident=next(self.ids);packet={'id':ident,'method':method,'params':params or {}}
  if session:packet['sessionId']=self.session
  self.ws.send(json.dumps(packet));end=time.monotonic()+22
  while time.monotonic()<end:
   result=json.loads(self.ws.recv())
   if result.get('id')==ident:
    if 'error'in result:raise RuntimeError(f'{method}: {result["error"]}')
    return result.get('result',{})
  raise TimeoutError(method)
 def eval(self,js):
  result=self.call('Runtime.evaluate',{'expression':js,'returnByValue':True,'awaitPromise':True},True)
  if result.get('exceptionDetails'):raise RuntimeError(str(result['exceptionDetails']))
  return result.get('result',{}).get('value')
 def open(self):
  self.context=self.call('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId'];self.target=self.call('Target.createTarget',{'url':'about:blank','browserContextId':self.context})['targetId'];self.session=self.call('Target.attachToTarget',{'targetId':self.target,'flatten':True})['sessionId']
  self.call('Page.enable',session=True);self.call('Runtime.enable',session=True)
  if MOBILE:self.call('Emulation.setDeviceMetricsOverride',{'width':320,'height':740,'deviceScaleFactor':2,'mobile':True},True)
  self.call('Page.navigate',{'url':URL},True)
 def wait(self,script,seconds=20):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   r=self.eval(script)
   if r:return r
   time.sleep(.15)
  raise AssertionError(f'timeout waiting: {script}; URL={self.eval("location.href")}; status={self.eval("document.getElementById(\"status\")?.textContent")}')
 def close(self):
  try:
   if self.target:self.call('Target.closeTarget',{'targetId':self.target})
   if self.context:self.call('Target.disposeBrowserContext',{'browserContextId':self.context})
  finally:self.ws.close()

c=Chrome()
try:
 c.open();c.wait('window.__prseView?.connected===true',22)
 assert c.eval('![...document.scripts].some(s=>s.src.endsWith("/game.js"))'),'Legacy simulation script must not load';assert c.eval('[...document.scripts].some(s=>s.src.endsWith("/viewer.js"))'),'Thin viewer missing'
 layout=json.loads(c.eval('JSON.stringify({overflow:document.documentElement.scrollWidth-window.innerWidth,short:[...document.querySelectorAll("button")].filter(b=>b.getBoundingClientRect().height<44).map(b=>b.id)})'))
 assert layout['overflow']<3 and not layout['short'],f'Invalid mobile UI: {layout}'
 token=c.eval('localStorage.getItem("prse-remote-session-v1")');assert len(token)==32
 health=requests.get('http://127.0.0.1:18764/health',timeout=5).json();assert health['connected']>=1
 old=c.eval('window.__prseView.state.player.x')
 c.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'d','code':'KeyD','windowsVirtualKeyCode':68},True);time.sleep(.8);c.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'d','code':'KeyD','windowsVirtualKeyCode':68},True)
 c.wait(f'window.__prseView.state.player.x > {old+1.1}',6)
 new=c.eval('window.__prseView.state.player.x')
 c.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Enter','code':'Enter','windowsVirtualKeyCode':13},True)
 c.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Enter','code':'Enter','windowsVirtualKeyCode':13},True)
 assert c.eval('document.activeElement.id')=='semantic-input','Enter must focus command field'
 c.eval('document.getElementById("semantic-input").value="look"')
 c.eval('document.getElementById("semantic-form").requestSubmit()')
 c.wait('document.getElementById("message").textContent.includes("forest")',8)
 c.eval('document.getElementById("save").click()');c.wait('document.getElementById("message").textContent.includes("saved")',7)
 c.call('Page.reload',{'ignoreCache':True},True);time.sleep(.55);c.wait('window.__prseView?.connected===true && !!window.__prseView?.state?.player',18)
 assert c.eval('localStorage.getItem("prse-remote-session-v1")')==token,'must retain session identity after reload'
 after=c.eval('window.__prseView.state.player.x');assert after>=new-.25,f'Headless simulation did not resume: {new} -> {after}'
 # Force a transport interruption without destroying the actual server world.
 oldCount=c.eval('window.__prseView.disconnectCount')
 c.eval('window.__prseView.socket.close()')
 c.wait(f'window.__prseView?.disconnectCount>{oldCount}',8)
 c.wait('window.__prseView?.connected===true',12)
 assert c.eval('localStorage.getItem("prse-remote-session-v1")')==token,'transport reconnect changed world identity'
 recovered=c.eval('window.__prseView.state.player.x');assert abs(recovered-after)<.85,f'World reset after reconnect: {after} -> {recovered}'
 for cycle in range(int(os.environ.get('RECONNECT_CYCLES','0'))):
  old=c.eval('window.__prseView.disconnectCount')
  current=c.eval('window.__prseView.state.player.x')
  c.eval('window.__prseView.socket.close()')
  c.wait(f'window.__prseView.disconnectCount>{old}',9)
  c.wait('window.__prseView.connected===true',15)
  restored=c.eval('window.__prseView.state.player.x')
  assert abs(restored-current)<.9,'Server-side world reset during link interruption'
  assert c.eval('localStorage.getItem("prse-remote-session-v1")')==token
 if os.environ.get('SLOW_LINK')=='1':
  previous=c.eval('window.__prseView.gameTime')
  c.call('Network.enable',session=True)
  c.call('Network.emulateNetworkConditions',{'offline':False,'latency':450,'downloadThroughput':16000,'uploadThroughput':3000},True)
  time.sleep(6)
  c.call('Network.emulateNetworkConditions',{'offline':False,'latency':0,'downloadThroughput':-1,'uploadThroughput':-1},True)
  c.wait(f'window.__prseView.gameTime>{previous+2}',10)
  print('SLOW_LINK_OK',json.dumps({'timeBefore':previous,'timeAfter':c.eval('window.__prseView.gameTime'),'disconnects':c.eval('window.__prseView.disconnectCount')}),flush=True)
 c.eval('window.scrollTo(0,0)');time.sleep(.25)
 screenshot=c.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False},True)['data'];dest=pathlib.Path('/data/tmp/prse-headless-mobile.png' if MOBILE else '/data/tmp/prse-headless-desktop.png');dest.write_bytes(base64.b64decode(screenshot))
 print(json.dumps({'passed':True,'url':URL,'mobile':MOBILE,'connected':True,'backend':'Nitro authoritative headless','tokenPersisted':True,'initialX':old,'newX':new,'reloadedX':after,'reconnectedX':recovered,'health':health,'layout':layout,'screenshot':str(dest)}),flush=True)
finally:c.close()
