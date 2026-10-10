// Browser presentation/input adapter ONLY. No GameCore, physics or world-state authority.
// 60Hz simulation, rules, autosaves, structured logs and optional LLM inspection live in
// ../prse_runtime/server.mjs on Nitro; this is one of several possible thin adapters.
import {SideViewRenderer} from './side-view-renderer.js';
const $=id=>document.getElementById(id),renderer=new SideViewRenderer($('scene'));
let ws=null,world=null,lastGameTime=0,eventCursor=0,ready=false,moveLeft=false,moveRight=false;
let requestId=1,backoff=500,closed=false,lastUI='',lastJournal='',displayFrame=0,frameId=0,lastPong=Date.now();
let lastStateAt=0,sessionToken=null;
const TOKEN_KEY='prse-remote-session-v1';
function say(text){if(text)$('message').textContent=text;}
function notice(text){$('status').textContent=text;}
function send(packet){if(ws?.readyState!==WebSocket.OPEN)return false;try{ws.send(JSON.stringify(packet));return true;}catch{return false;}}
function control(command){return send({type:'command',requestId:requestId++,command});}
function movement(){return control({type:'Move',direction:Number(moveRight)-Number(moveLeft)});}
function locationName(x){if(x< -4.5)return 'Old beech grove';if(x<5.2)return 'The clearing';if(x<14)return 'Beyond the fence';if(x<22.2)return 'Stream approach';if(x<33)return 'Far bank';if(x<42)return 'Riverside shelter';return 'Valley path';}
function missionText(c){if(c.farBankReached)return 'Explore the abandoned shelter further east →';if(c.bridgeRepaired)return 'Cross the repaired footbridge →';return c.inventory.plank<2?'Find two timber planks near the old beech ←':'Take timber past the fence to the bridge repairs →';}
function updateUI(state){const c=state.character;
 const key=JSON.stringify([c.inventory.plank,Math.round(c.fatigue/5),Math.round(c.hydration/10),c.bridgeRepaired,c.farBankReached,state.nearby?.label,Math.round(state.player.x/5)]);
 if(key!==lastUI){lastUI=key;$('location').textContent=locationName(state.player.x);$('mission').textContent=missionText(c);$('condition').textContent=`Timber ${c.inventory.plank}/2 · ${c.inventory.plank*6} kg carried · ${c.fatigue<25?'Rested':c.fatigue<60?'Tiring':'Exhausted'}`;$('nearby-prompt').textContent=state.nearby?`E · ${state.nearby.label}`:'';}
 const j=`${c.notes.length}:${(c.knowledge||[]).length}`;if(j!==lastJournal){lastJournal=j;const el=$('field-notes');el.replaceChildren();const items=[...c.notes.slice(-16).map(n=>`Time ${n.time.toFixed(1)} s — needle ${n.intensity}, ${n.trend}`),...(c.knowledge||[]).slice(-16).map(k=>`Observed: ${k.text}`)];if(!items.length)el.textContent='No field observations yet.';else{const ul=document.createElement('ul');for(const text of items.reverse()){const li=document.createElement('li');li.textContent=text;ul.append(li);}el.append(ul);}}
}
function acceptState(s){if(!s||!s.player||!s.character||!s.visibleEntities)return;world=s;lastGameTime=s.time;lastStateAt=performance.now();updateUI(s);}
function acceptEvents(events){if(!Array.isArray(events))return;for(const e of events){if((e.sequence||0)<=eventCursor)continue;eventCursor=Math.max(eventCursor,e.sequence||0);if(e.visibility==='offscreen'||e.type==='limb_contact'&&!$('physical-experiment').open)continue;say(e.message);}}
function processPacket(packet){switch(packet.type){
 case 'welcome':{ready=true;sessionToken=packet.token;try{localStorage.setItem(TOKEN_KEY,packet.token)}catch{};$('session-info').textContent=`Authoritative host: ${packet.host}. Physics: ${packet.physicsHz}Hz. Display updates: ${packet.displayHz}Hz. Saving: ${packet.saveLocation}.`;
   notice('Nitro simulation connected');acceptState(packet.state);backoff=500;say('Connected to the authoritative PRSE simulation.');break;}
 case 'state':acceptState(packet.state);break;case 'world_reset':eventCursor=packet.eventSequence||0;lastJournal='';lastUI='';break;
 case 'events':acceptEvents(packet.events);break;
 case 'text_result':say(packet.text);break;
 case 'message':say(packet.text);break;
 case 'error':case 'rejected':say(packet.message);break;
 case 'command_result':if(!packet.accepted)say('That action was rejected by the authoritative game core.');break;
 case 'llm_status':$('llm-status').textContent=packet.message||packet.status;break;
 case 'llm_result':{const a=packet.answer;$('llm-status').textContent=`Jetson model responded in ${packet.durationSeconds.toFixed(1)}s. The physics core remains authoritative.`;
  const result=$('llm-result');result.replaceChildren();const desc=document.createElement('p');desc.textContent=a.description;result.append(desc);
  for(const item of a.observations.slice(0,12)){const p=document.createElement('p');p.textContent='Observed: '+item;result.append(p);}
  const uncertainty=document.createElement('p');uncertainty.textContent='Uncertainty: '+a.uncertainty;result.append(uncertainty);break;}
 case 'pong':lastPong=Date.now();break;
 }}
function connect(){if(closed)return;const origin=location.protocol==='https:'?'wss:':'ws:';const url=`${origin}//${location.host}/llm_game_runtime/ws`;
 notice('Connecting to Nitro game core…');try{ws=new WebSocket(url);}catch{scheduleRetry();return;}
 ws.onopen=()=>{let token=null;try{token=localStorage.getItem(TOKEN_KEY)}catch{}send({type:'hello',token});};
 ws.onmessage=e=>{try{processPacket(JSON.parse(e.data));}catch(err){console.warn('Remote protocol response rejected',err)}};
 ws.onclose=()=>{ready=false;moveLeft=false;moveRight=false;notice('Connection interrupted · reconnecting');scheduleRetry();};
 ws.onerror=()=>{notice('Remote simulation unavailable');};
}
let retryTimer=null;function scheduleRetry(){if(closed||retryTimer)return;retryTimer=setTimeout(()=>{retryTimer=null;connect();},backoff);backoff=Math.min(10000,Math.floor(backoff*1.6));}
function render(t){if(world)renderer.draw(world);frameId=requestAnimationFrame(render);}frameId=requestAnimationFrame(render);
function hold(id,direction){const el=$(id),down=()=>{if(direction<0)moveLeft=true;else moveRight=true;movement();},up=()=>{if(direction<0)moveLeft=false;else moveRight=false;movement();};el.addEventListener('pointerdown',ev=>{ev.preventDefault();el.setPointerCapture(ev.pointerId);down();});for(const type of ['pointerup','pointercancel','lostpointercapture'])el.addEventListener(type,up);}
hold('left',-1);hold('right',1);
const bindings={jump:()=>control({type:'Jump'}),interact:()=>control({type:'Interact'}),tune:()=>control({type:'Experiment'}),goal:()=>control({type:'Goal',intent:'crossFence'}),cancel:()=>control({type:'CancelGoal'}),ragdoll:()=>control({type:'PushRagdoll'}),'ragdoll-balance':()=>control({type:'SetRagdollMode',mode:'balance'}),'ragdoll-walk':()=>control({type:'SetRagdollMode',mode:'walk'}),'ragdoll-relax':()=>control({type:'SetRagdollMode',mode:'relax'}),'ragdoll-injure':()=>control({type:'InjureRagdoll',part:'leftKnee',injury:'sprain',severity:.85}),'ragdoll-heal':()=>control({type:'HealRagdoll'})};
for(const [id,fn] of Object.entries(bindings))$(id).addEventListener('click',fn);
$('view-lab').addEventListener('click',()=>renderer.setView('lab'));$('view-world').addEventListener('click',()=>renderer.setView('world'));
function onKey(e,pressed){if(e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement){if(pressed&&e.key==='Escape')e.target.blur();return;}
 const k=e.key.toLowerCase();if(['arrowleft','arrowright',' ','a','d','e','f','g','escape','enter'].includes(k))e.preventDefault();if(k==='enter'&&pressed&&!e.repeat&&!e.isComposing){$('semantic-input').focus();return;}
 if(k==='a'||k==='arrowleft'){moveLeft=pressed;movement();}else if(k==='d'||k==='arrowright'){moveRight=pressed;movement();}else if(pressed&&!e.repeat){if(k===' ')control({type:'Jump'});if(k==='e')control({type:'Interact'});if(k==='f')control({type:'Experiment'});if(k==='g')control({type:'Goal',intent:'crossFence'});if(k==='escape')control({type:'CancelGoal'});}}
window.addEventListener('keydown',e=>onKey(e,true));window.addEventListener('keyup',e=>onKey(e,false));window.addEventListener('blur',()=>{moveLeft=false;moveRight=false;movement();});
$('semantic-form').addEventListener('submit',event=>{event.preventDefault();const el=$('semantic-input'),text=el.value.trim();if(!text)return;if(!send({type:'text',requestId:requestId++,text})){say('Not connected to the simulation. Please retry after reconnection.');return;}el.value='';el.blur();});
$('save').addEventListener('click',()=>send({type:'save'}));$('load').addEventListener('click',()=>send({type:'load'}));$('restart').addEventListener('click',()=>{send({type:'restart'});eventCursor=0;lastJournal='';lastUI='';});
$('ask-llm').addEventListener('click',()=>send({type:'ask_llm'}));
$('import-local').addEventListener('click',()=>{try{let source=null;for(const key of ['prse-world-save-v5','prse-world-save-v4','world-physics-prototype-save-v3','world-physics-prototype-save-v2']){source=localStorage.getItem(key);if(source)break;}if(!source){say('There is no old browser-local save on this device.');return;}const snapshot=JSON.parse(source);if(!send({type:'import_legacy',snapshot}))say('Connect to Nitro first, then import the old save.');}catch{say('The old browser-local save is damaged or unavailable.');}});
const heartbeat=setInterval(()=>{if(ws?.readyState===WebSocket.OPEN){if(Date.now()-lastPong>60000){ws.close();return;}send({type:'ping'});}},15000);
$('runtime-info').textContent='Simulation, physics, semantic world, events, saves and the LLM gateway are running on Nitro. Browser displays snapshots and sends commands. The LLM receives current visible facts only when explicitly requested.';
window.__prseView={get state(){return world},get connected(){return ready},get gameTime(){return lastGameTime},get eventSequence(){return eventCursor},get socket(){return ws}};
connect();
window.addEventListener('beforeunload',()=>{closed=true;clearTimeout(retryTimer);cancelAnimationFrame(frameId);clearInterval(heartbeat);ws?.close();});
