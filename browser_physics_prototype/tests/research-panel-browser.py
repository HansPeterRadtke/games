import os,json,time
os.environ.setdefault('GAME_URL','https://nitro.jonnyontherun.org/llm_game/')
import requests,websocket,itertools
host='http://127.0.0.1:40297';ws=websocket.create_connection(requests.get(host+'/json/version',timeout=5).json()['webSocketDebuggerUrl'],timeout=15,origin='http://127.0.0.1');nums=itertools.count(1)
def call(method,params=None,session=None):
 n=next(nums);msg={'id':n,'method':method,'params':params or {}};
 if session:msg['sessionId']=session
 ws.send(json.dumps(msg));
 while True:
  item=json.loads(ws.recv());
  if item.get('id')==n:
   if item.get('error'):raise RuntimeError(item['error'])
   return item.get('result',{})
def evaluate(code):
 result=call('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True},session)
 if result.get('exceptionDetails'):raise RuntimeError(result['exceptionDetails'])
 return result.get('result',{}).get('value')
context=call('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId'];target=call('Target.createTarget',{'browserContextId':context,'url':'about:blank'})['targetId'];session=call('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
try:
 call('Page.enable',session=session);call('Runtime.enable',session=session);call('Page.navigate',{'url':os.environ['GAME_URL']},session);
 for i in range(65):
  if evaluate('!!window.__gameDebug'):break
  time.sleep(.2)
 assert evaluate('!!window.__gameDebug'),'game missing'
 evaluate('document.getElementById("prse-research").open=true')
 def click(id):evaluate('document.getElementById('+json.dumps(id)+').click()')
 click('research-shelter');assert evaluate('document.getElementById("research-result").textContent.includes("Candle: unlit")')
 click('research-light');assert evaluate('document.getElementById("research-result").textContent.includes("Candle: lit")')
 assert evaluate('window.__gameDebug.core.semantic.entity("shelter-note").state.condition')=='intact'
 click('research-ignite');click('research-observe');assert evaluate('window.__gameDebug.core.semantic.entity("shelter-note").state.condition') in ['smoldering','burning']
 click('research-offscreen');assert evaluate('document.getElementById("research-result").textContent.includes("outside perception")')
 evaluate('(function(){for(let i=0;i<1800;i++)window.__gameDebug.core.step()})()')
 click('research-return');assert evaluate('window.__gameDebug.core.semantic.entity("shelter-note").state.condition')=='ashes'
 assert evaluate('document.getElementById("research-raw").textContent.includes("ashes")')
 print('PRSE_BROWSER_EXPERIMENT_PASS: lit candle alone, explicit ignition, delayed consequences offscreen, persisted ash and visible state inspector')
finally:
 call('Target.closeTarget',{'targetId':target});call('Target.disposeBrowserContext',{'browserContextId':context});ws.close()
