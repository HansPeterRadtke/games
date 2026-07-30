#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,hashlib,io,json,os,signal,socket,subprocess,tempfile,time
from pathlib import Path
import websocket
from PIL import Image

def free_port()->int:
 with socket.socket() as sock:
  sock.bind(('127.0.0.1',0));return int(sock.getsockname()[1])
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--url',default='https://nitro.jonnyontherun.org/llm_game/gif_inspector/');a=ap.parse_args()
 port=free_port();profile=Path(tempfile.mkdtemp(prefix='firefox-gif-loop-',dir='/data/tmp'));log=Path('/data/tmp/firefox-gif-loop.log')
 (profile/'user.js').write_text('''user_pref("remote.active-protocols", 1);\nuser_pref("browser.shell.checkDefaultBrowser", false);\nuser_pref("browser.startup.homepage_override.mstone", "ignore");\nuser_pref("datareporting.policy.dataSubmissionEnabled", false);\nuser_pref("image.animation_mode", "normal");\n''')
 url=a.url.rstrip('/')+'/?browser-loop='+str(time.time_ns())
 env=os.environ.copy();env.update({'NO_PROXY':'127.0.0.1,localhost','no_proxy':'127.0.0.1,localhost','LIBGL_ALWAYS_SOFTWARE':'1','MOZ_WEBRENDER':'1'})
 with log.open('wb') as handle:
  process=subprocess.Popen(['xvfb-run','-a','-s','-screen 0 1280x900x24 +extension GLX +render -noreset','firefox','--no-remote','--profile',str(profile),'--remote-debugging-port',str(port),url],stdout=handle,stderr=subprocess.STDOUT,env=env,preexec_fn=os.setsid)
 try:
  for _ in range(60):
   if process.poll() is not None:raise RuntimeError({'firefox_exited':process.returncode,'log':log.read_text(errors='replace')[-4000:]})
   if 'WebDriver BiDi listening' in log.read_text(errors='replace'):break
   time.sleep(.5)
  else:raise RuntimeError({'bidi_not_ready':log.read_text(errors='replace')[-4000:]})
  ws=websocket.create_connection(f'ws://127.0.0.1:{port}/session',timeout=20,suppress_origin=True);sequence=0;events=[]
  def call(method:str,params:dict,timeout:float=30)->dict:
   nonlocal sequence;sequence+=1;ident=sequence;ws.send(json.dumps({'id':ident,'method':method,'params':params}));deadline=time.time()+timeout
   while time.time()<deadline:
    message=json.loads(ws.recv())
    if message.get('id')==ident:
     if message.get('type')=='error' or 'error' in message:raise RuntimeError(message)
     return message.get('result',message)
    events.append(message)
   raise TimeoutError(method)
  call('session.new',{'capabilities':{'alwaysMatch':{'browserName':'firefox'}}});call('session.subscribe',{'events':['log.entryAdded']})
  context=None
  for _ in range(40):
   contexts=call('browsingContext.getTree',{}).get('contexts',[]);context=next((x['context'] for x in contexts if '/gif_inspector/' in x.get('url','')),None)
   if context:break
   time.sleep(.25)
  if not context:raise RuntimeError({'context_missing':contexts})
  call('browsingContext.activate',{'context':context})
  layout_expression="""(async()=>{const deadline=performance.now()+20000;let img=null;while(performance.now()<deadline){img=document.querySelector('.checker img');if(img&&img.complete&&img.naturalWidth===512&&img.naturalHeight===768&&!document.hidden)break;await new Promise(resolve=>setTimeout(resolve,100));}if(!img)throw new Error('checker image missing');img.scrollIntoView({block:'center',inline:'center'});await new Promise(resolve=>setTimeout(resolve,300));const r=img.getBoundingClientRect();return JSON.stringify({complete:img.complete,naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,left:r.left,top:r.top,width:r.width,height:r.height,dpr:window.devicePixelRatio,hidden:document.hidden,title:document.title,currentSrc:img.currentSrc});})()"""
  result=call('script.evaluate',{'expression':layout_expression,'target':{'context':context},'awaitPromise':True},timeout=25)['result']
  if result.get('type')=='exception':raise RuntimeError(result)
  data=json.loads(result.get('value','{}'))
  if not (data.get('complete') and (data.get('naturalWidth'),data.get('naturalHeight'))==(512,768) and data.get('hidden') is False):raise RuntimeError({'gif_image_not_ready':data,'firefox_log':log.read_text(errors='replace')[-4000:]})
  dpr=float(data['dpr']);box=tuple(int(round(v*dpr)) for v in [data['left'],data['top'],data['left']+data['width'],data['top']+data['height']])
  hashes=[];times=[];started=time.monotonic()
  for _ in range(64):
   sample_started=time.monotonic();shot=call('browsingContext.captureScreenshot',{'context':context,'origin':'viewport'},timeout=10);image=Image.open(io.BytesIO(base64.b64decode(shot['data']))).convert('RGB');crop=image.crop(box);hashes.append(hashlib.sha256(crop.tobytes()).hexdigest());times.append(time.monotonic()-started);delay=.11-(time.monotonic()-sample_started)
   if delay>0:time.sleep(delay)
  blocks=[hashes[i:i+16] for i in range(0,64,16)]
  unique=[len(set(block)) for block in blocks]
  elapsed=times[-1]
  if elapsed<6.4:raise RuntimeError({'browser_sampling_too_short':elapsed})
  if min(unique)<6:raise RuntimeError({'gif_stopped_or_static':{'unique_per_sampling_quarter':unique,'elapsed':elapsed,'hashes':hashes}})
  final=blocks[-1]
  if len(set(final))<8:raise RuntimeError({'gif_stopped_in_final_sampling_quarter':{'unique':len(set(final)),'elapsed':elapsed}})
  overlap=len(set(final).intersection(set(hashes[:48])))
  if overlap<2:raise RuntimeError({'late_animation_not_periodic':{'overlap':overlap,'unique_per_sampling_quarter':unique,'elapsed':elapsed}})
  cycles_observed=elapsed/1.6
  if cycles_observed<4:raise RuntimeError({'fewer_than_four_cycles_observed':cycles_observed})
  bad_logs=[e for e in events if e.get('method')=='log.entryAdded' and e.get('params',{}).get('entry',{}).get('level') in {'error','warn'}]
  print(json.dumps({'ok':True,'url':url,'title':data['title'],'samples':64,'elapsed_ms':round(elapsed*1000,1),'cycle_ms':1600,'cycles_observed':round(cycles_observed,2),'unique_per_sampling_quarter':unique,'final_quarter_unique':len(set(final)),'late_phase_overlap':overlap,'browser_log_errors':bad_logs},sort_keys=True));ws.close();return 0
 finally:
  try:os.killpg(process.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:process.wait(timeout=4)
  except subprocess.TimeoutExpired:
   try:os.killpg(process.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   process.wait(timeout=4)
  subprocess.run(['rm','-rf',str(profile)],check=False)
if __name__=='__main__':raise SystemExit(main())
