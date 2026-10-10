#!/usr/bin/env python3
"""Isolated-CDP test for generated PRSE scene branches and licensed sprite loading."""
import base64,json,os,pathlib,time,requests,websocket,itertools,sys
BROWSER='http://127.0.0.1:40297';SITE='https://nitro.jonnyontherun.org/llm_game/'
class Session:
 def __init__(self):
  self.ws=websocket.create_connection(requests.get(BROWSER+'/json/version',timeout=5).json()['webSocketDebuggerUrl'],timeout=12,origin='http://127.0.0.1');self.ids=itertools.count(1);self.context=None;self.target=None;self.session=None
 def call(self,method,params=None,attach=True):
  i=next(self.ids);req={'id':i,'method':method,'params':params or {}};
  if attach:req['sessionId']=self.session
  self.ws.send(json.dumps(req));deadline=time.time()+25
  while time.time()<deadline:
   data=json.loads(self.ws.recv());
   if data.get('id')==i:
    if 'error'in data:raise RuntimeError(data['error'])
    return data.get('result',{})
  raise TimeoutError(method)
 def eval(self,expr):
  r=self.call('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True});
  if r.get('exceptionDetails'):raise RuntimeError(str(r['exceptionDetails']))
  return r['result'].get('value')
 def launch(self):
  self.context=self.call('Target.createBrowserContext',{'disposeOnDetach':True},False)['browserContextId'];self.target=self.call('Target.createTarget',{'url':'about:blank','browserContextId':self.context},False)['targetId'];self.session=self.call('Target.attachToTarget',{'targetId':self.target,'flatten':True},False)['sessionId'];self.call('Page.enable');self.call('Runtime.enable');self.call('Emulation.setDeviceMetricsOverride',{'width':1152,'height':920,'deviceScaleFactor':1,'mobile':False});self.call('Page.navigate',{'url':SITE});
  for i in range(75):
   if self.eval('!!window.__gameDebug'):return
   time.sleep(.2)
  raise RuntimeError('Game not ready')
 def close(self):
  try:
   if self.target:self.call('Target.closeTarget',{'targetId':self.target},False)
   if self.context:self.call('Target.disposeBrowserContext',{'browserContextId':self.context},False)
  finally:self.ws.close()
c=Session();
try:
 c.launch()
 for repaired in [False,True]:
  js='''(()=>{const g=window.__gameDebug.core;g.create();g.character.bridgeRepaired=%s;g.player.setTranslation({x:40.5,y:.87,z:0},true);g.player.setLinvel({x:0,y:0,z:0},true);for(let n=0;n<60;n++)g.step();return g.semantic.entity('region-1-landmark')?.description;})()'''%('true'if repaired else 'false')
  desc=c.eval(js);assert desc, 'Scene not generated'
  time.sleep(1.1)
  data=c.eval('''(()=>{const g=window.__gameDebug.core,entities=g.state().visibleEntities.filter(e=>e.id.startsWith('region-1-'));return {branch:g.character.bridgeRepaired,entityCount:entities.length,desc:g.semantic.entity('region-1-landmark')?.description,renderAssetKeys:entities.map(e=>e.artwork?.relativePath||null),loaded:entities.map(e=>e.artwork?.relativePath ? !!window.__gameDebug.renderer.images[e.artwork.relativePath]?.naturalWidth : null),physical:entities.map(e=>[e.id,e.position.x,e.position.y,e.position.z])};})()''')
  print('SCENE',json.dumps(data,ensure_ascii=False),flush=True);assert data['entityCount']>=3 and all(x for x in data['loaded'] if x is not None),'Missing generated textures'
  name='bridge-repaired' if repaired else 'bridge-unrepaired';raw=c.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})['data'];path=pathlib.Path('/data/tmp/prse-llm-'+name+'.png');path.write_bytes(base64.b64decode(raw));print('SCREENSHOT',path,path.stat().st_size,flush=True)
 print('SUCCESS',flush=True)
finally:c.close()
