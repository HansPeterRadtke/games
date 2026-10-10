// Headless authoritative PRSE engine host. Neither Canvas, DOM nor a browser is involved.
// The webpage is one replaceable remote viewer/controller; CLI/tests can be other adapters.
import http from 'node:http';
import fs from 'node:fs';
import {promises as fsp} from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {GameCore, initializePhysics, SETTINGS} from '../browser_physics_prototype/physics-core.js';
import {narrateWorld} from '../browser_physics_prototype/narrative-view.js';
import {projectViewerState} from './view-projection.mjs';
const require=createRequire(import.meta.url),{WebSocketServer}=require('ws');
const PORT=Number(process.env.PRSE_PORT||18764);
const STATE_DIR=process.env.PRSE_STATE_DIR||'/data/var/llm_game/prse_sessions';
const MAX_ACTIVE=Number(process.env.PRSE_MAX_ACTIVE||8),TICK_MS=1000/60,FRAME_EVERY=6; // 60Hz physics, <=10Hz display
const LOG_LEVEL=process.env.PRSE_LOG_LEVEL||'normal';
const now=()=>new Date().toISOString();
const status=(event,data={})=>{process.stdout.write(JSON.stringify({at:now(),service:'prse-headless',event,...data})+'\n');};
const validToken=value=>typeof value==='string'&&/^[0-9a-f]{32}$/.test(value);
const sessions=new Map(),loadingSessions=new Map();let hostTick=0,active=true,interval=null,modelInFlight=false,lastGlobalModelStart=0;
function filePaths(id){return {snapshot:path.join(STATE_DIR,`${id}.snapshot.json`),events:path.join(STATE_DIR,`${id}.events.ndjson`)}};
function send(ws,packet){if(ws.readyState!==1)return false;try{if(ws.bufferedAmount>350000){return false;}ws.send(JSON.stringify(packet));return true;}catch(err){return false;}}
function notify(session,packet){for(const ws of session.clients)send(ws,packet);}
class GameSession {
 constructor(id,snapshot=null){this.id=id;this.core=new GameCore();this.clients=new Set();this.lastSeq=0;this.lastSaved=0;this.lastLogTime=0;this.lastFrame=0;this.isLoading=false;this.pendingSave=Promise.resolve();this.llmBusy=false;this.lastLLMStart=0;this.created=Date.now();this.lastSeen=Date.now();this.droppedFrames=0;this.logErrors=0;
  if(snapshot){if(this.core.restore(snapshot)){this.lastSeq=this.core.eventSequence;status('restored',{snapshotVersion:snapshot.version,sessionSuffix:id.slice(-4)});}else status('invalid_snapshot_new_world',{sessionSuffix:id.slice(-4)});}
  this.logStream=fs.createWriteStream(filePaths(id).events,{flags:'a',mode:0o600});this.logStream.on('error',err=>{this.logErrors++;status('log_error',{kind:err.code,sessionSuffix:id.slice(-4)})});this.log('session_start',{resumed:!!snapshot,version:this.core.snapshot().version});
 }
 log(type,fields={}){const obj={utc:now(),kind:type,gameTime:+this.core.time.toFixed(3),tick:this.core.stepCount,...fields};const row=JSON.stringify(obj)+'\n';if(this.logStream.destroyed||this.logStream.writableLength>65536){this.logErrors++;return;}this.logStream.write(row);}
 events(){const fresh=this.core.events.filter(e=>(e.sequence||0)>this.lastSeq);if(!fresh.length)return [];this.lastSeq=this.core.eventSequence;
  for(const e of fresh){this.log('event',{eventId:e.id,eventType:e.type,entityId:e.entityId||null,cause:e.cause||null,outcome:e.outcome||null,visibility:e.visibility||'visible',text:e.message||'',sequence:e.sequence});}
  return fresh;
 }
 tick(){if(!this.clients.size)return;
  this.core.step();const recent=this.events();if(recent.length)notify(this,{type:'events',events:recent});
  if(this.core.stepCount%60===0&&LOG_LEVEL!=='quiet')this.log('summary',{player:{x:+this.core.player.translation().x.toFixed(2),y:+this.core.player.translation().y.toFixed(2)},worldRevision:this.core.semantic.entities.reduce((a,e)=>a+(e.revision||0),0),physicalEntities:this.core.worldBridge.active.size});
  if(this.core.stepCount%600===0)this.save();
  if(this.core.stepCount%FRAME_EVERY===0){const frame={type:'state',gameTime:this.core.time,tick:this.core.stepCount,state:projectViewerState(this.core.state())};notify(this,frame);}
 }
 cmd(ws,msg){const command=msg.command;if(!command||typeof command!=='object'||Array.isArray(command))return send(ws,{type:'rejected',message:'Invalid command'});
  const allow=new Set(['Move','Jump','Interact','Experiment','Goal','CancelGoal','TakeManualControl','SetRagdollMode','PushRagdoll','InjureRagdoll','HealRagdoll','SetLaboratoryActive']);
  if(!allow.has(command.type)||JSON.stringify(command).length>350)return send(ws,{type:'rejected',message:'Unsupported command'});
  const accepted=this.core.command(command);if(command.type!=='Move'||this.lastMoveDirection!==command.direction||!accepted)this.log('command',{command,accepted});if(command.type==='Move'&&accepted)this.lastMoveDirection=command.direction;const actionEvents=this.events();if(actionEvents.length)notify(this,{type:'events',events:actionEvents});send(ws,{type:'command_result',requestId:msg.requestId||null,accepted});if(command.type!=='Move'){notify(this,{type:'state',gameTime:this.core.time,tick:this.core.stepCount,state:projectViewerState(this.core.state())});this.save();}
 }
 text(ws,msg){if(typeof msg.text!=='string'||msg.text.length>120)return send(ws,{type:'rejected',message:'Invalid text input'});
  const result=this.core.textCommand(msg.text);this.log('text_command',{input:msg.text,result});const textEvents=this.events();if(textEvents.length)notify(this,{type:'events',events:textEvents});send(ws,{type:'text_result',requestId:msg.requestId||null,text:result});notify(this,{type:'state',gameTime:this.core.time,tick:this.core.stepCount,state:projectViewerState(this.core.state())});this.save();
 }
 save(){const data=JSON.stringify(this.core.snapshot());this.lastSaved=Date.now();const file=filePaths(this.id).snapshot;
  this.pendingSave=this.pendingSave.catch(()=>{}).then(async()=>{const tmp=file+'.tmp';await fsp.writeFile(tmp,data,{mode:0o600});await fsp.rename(tmp,file);}).catch(error=>{this.logErrors++;status('save_error',{sessionSuffix:this.id.slice(-4),kind:error.code||error.message});});return this.pendingSave;
 }
 importSnapshot(ws,snapshot){
  if(!snapshot||typeof snapshot!=='object'||JSON.stringify(snapshot).length>350000)return send(ws,{type:'error',message:'Invalid or excessively large imported save.'});
  const candidate=new GameCore();if(!candidate.restore(snapshot)){candidate.world.free();this.log('import_rejected',{version:snapshot.version||null});return send(ws,{type:'error',message:'The old save failed game-world validation.'});}
  const old=this.core;this.core=candidate;old.world.free();this.lastSeq=candidate.eventSequence;this.log('import_legacy_save',{version:snapshot.version,entities:candidate.semantic.entities.length});
  this.save();notify(this,{type:'world_reset',eventSequence:candidate.eventSequence});notify(this,{type:'state',gameTime:candidate.time,tick:candidate.stepCount,state:projectViewerState(candidate.state())});send(ws,{type:'message',text:'Previous browser-local world imported into authoritative Nitro game state.'});
 }
 async load(ws){await this.pendingSave;try{const data=JSON.parse(await fsp.readFile(filePaths(this.id).snapshot,'utf8'));const candidate=new GameCore();if(!candidate.restore(data))throw Error('invalid snapshot');this.core.world.free();this.core=candidate;this.lastSeq=this.core.eventSequence;this.log('load',{version:data.version});notify(this,{type:'world_reset',eventSequence:this.core.eventSequence});notify(this,{type:'state',state:projectViewerState(this.core.state()),tick:this.core.stepCount,gameTime:this.core.time});send(ws,{type:'message',text:'World reloaded from authoritative Nitro storage.'});}catch(e){send(ws,{type:'error',message:'No valid saved world is available.'});this.log('load_error',{kind:e.code||e.message});}}
 restart(){const old=this.core;this.core=new GameCore();old.world.free();this.lastSeq=0;this.log('restart');notify(this,{type:'world_reset',eventSequence:0});notify(this,{type:'state',state:projectViewerState(this.core.state()),tick:0,gameTime:0});this.save();}
 async close(){this.log('session_close');await this.save();await this.pendingSave;await new Promise(resolve=>this.logStream.end(resolve));this.core.world.free();}
}
async function fromStorage(token){const file=filePaths(token).snapshot;try{const bytes=await fsp.readFile(file,'utf8');if(bytes.length>1600000)throw Error('snapshot oversized');return JSON.parse(bytes);}catch(e){if(e.code!=='ENOENT')status('snapshot_read_issue',{sessionSuffix:token.slice(-4),reason:e.code||e.message});return null;}}
function publiclyDescribable(session){const state=session.core.state(),visible=state.visibleEntities.filter(e=>e.physical&&!e.state?.collected).slice(0,10);
 return {position:state.player,character:{inventory:state.character.inventory,bridgeRepaired:state.character.bridgeRepaired,fenceOpened:state.character.fenceOpened,knowledge:state.character.knowledge?.map(k=>k.fact)||[]},visible:visible.map(e=>({id:e.id,kind:e.kind,name:e.name,description:String(e.description||'').slice(0,160),position:e.position,condition:e.state?.condition,lit:e.state?.lit,water:e.state?.water})),recentEvents:session.core.events.filter(e=>e.visibility!=='offscreen').slice(-5).map(e=>({type:e.type,entity:e.entityId||null,result:e.outcome||null,text:String(e.message||'').slice(0,100)}))};
}
async function askLLM(session,ws){
 if(session.llmBusy||modelInFlight)return send(ws,{type:'llm_status',status:'busy',message:'The local model is already interpreting another state.'});
 if(Date.now()-session.lastLLMStart<60000||Date.now()-lastGlobalModelStart<15000)return send(ws,{type:'llm_status',status:'cooldown',message:'The local model is cooling down; try again shortly.'});
 modelInFlight=true;lastGlobalModelStart=Date.now();session.llmBusy=true;session.lastLLMStart=Date.now();const view=publiclyDescribable(session),requestId=crypto.randomBytes(6).toString('hex');
 session.log('llm_request',{requestId,visibleCount:view.visible.length,worldTime:+session.core.time.toFixed(2)});
 send(ws,{type:'llm_status',status:'working',message:'Jetson is interpreting the current authoritative world state.'});const start=Date.now();
 try{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),65000);
  const schema={type:'object',properties:{description:{type:'string'},uncertainty:{type:'string'}},required:['description','uncertainty'],additionalProperties:false};
  const prompt='Summarize only the CURRENT visible game state in at most 55 English words. Do not invent events or physical reactions. A lit candle does not imply burning paper. Put unknowns in a short uncertainty field. JSON only.\n'+JSON.stringify(view);
  let response;try{response=await fetch('http://jetson.lan:14829/completion',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({prompt,n_predict:150,temperature:0,top_k:10,json_schema:schema,stream:false}),signal:controller.signal});}finally{clearTimeout(timer)}
  if(!response.ok)throw Error('model HTTP '+response.status);const result=await response.json();let answer;
  try{answer=JSON.parse(result.content||'{}');}catch(e){session.log('llm_invalid_json',{requestId,modelTokens:result.tokens_predicted||null,rawPrefix:String(result.content||'').slice(0,900),reason:e.message});throw Error('model returned malformed or truncated JSON');}
  if(typeof answer.description!=='string'||answer.description.length>1500||typeof answer.uncertainty!=='string')throw Error('model output invalid');answer.observations=[];
  const duration=+(Date.now()-start)/1000;session.log('llm_response',{requestId,durationSeconds:duration,answer,modelTokens:result.tokens_predicted||null});
  send(ws,{type:'llm_result',requestId,answer,durationSeconds:duration,model:'Qwen3.8-27B',grounding:'unverified model wording; structured world remains authoritative'});
 }catch(err){session.log('llm_error',{requestId,reason:err.name==='AbortError'?'timeout':String(err.message).slice(0,100)});send(ws,{type:'llm_status',status:'failed',message:'The model could not answer in time. The simulation remains fully operational.'});}finally{session.llmBusy=false;modelInFlight=false;}
}
async function getOrCreateSession(token){
 const existing=sessions.get(token);if(existing)return existing;
 if(loadingSessions.has(token))return loadingSessions.get(token);
 const pending=(async()=>{
  // Capacity is reserved synchronously by inserting this promise into loadingSessions.
  // Never recount this very reservation after awaiting an idle session's closure.
  if(sessions.size+loadingSessions.size>=MAX_ACTIVE){
   const inactive=[...sessions.values()].find(s=>s.clients.size===0);
   if(!inactive)return null;
   sessions.delete(inactive.id);
   await inactive.close();
  }
  const snap=await fromStorage(token),instance=new GameSession(token,snap);
  sessions.set(token,instance);
  return instance;
 })();
 loadingSessions.set(token,pending);
 try{return await pending;}finally{loadingSessions.delete(token);}
}
async function attach(ws,msg){
 const token=validToken(msg.token)?msg.token:crypto.randomBytes(16).toString('hex');
 const session=await getOrCreateSession(token);
 if(!session){send(ws,{type:'error',message:'The game is at capacity; retry shortly.'});ws.close(1013,'capacity');return;}
 if(ws.readyState!==1)return;
 session.clients.add(ws);ws.session=session;session.lastSeen=Date.now();ws.connectedAt=Date.now();ws.lastClientPingAt=Date.now();
 send(ws,{type:'welcome',token,host:'nitro',authoritative:true,physicsHz:60,displayHz:10,backend:'Rapier 3D headless',saveLocation:'Nitro (server)',state:projectViewerState(session.core.state()),gameTime:session.core.time});
 session.log('viewer_connected',{viewers:session.clients.size});
}
function handler(req,res){if(req.url==='/health'){res.writeHead(200,{'content-type':'application/json','cache-control':'no-store'});res.end(JSON.stringify({ok:true,headless:true,sessions:sessions.size,connected:[...sessions.values()].filter(s=>s.clients.size).length,physicsHz:60,displayHz:10,transport:'compressed-view-v2',maxSessions:MAX_ACTIVE}));return;}res.writeHead(404);res.end('not found');}
await fsp.mkdir(STATE_DIR,{recursive:true,mode:0o700});await initializePhysics();const server=http.createServer(handler),wss=new WebSocketServer({noServer:true,maxPayload:400000,perMessageDeflate:{threshold:512,concurrencyLimit:4},clientTracking:true});
server.on('upgrade',(req,socket,head)=>{
 if(req.url!=='/ws'){socket.destroy();return;}
 const origin=req.headers.origin;
 if(origin&&!['https://nitro.jonnyontherun.org','http://nitro.jonnyontherun.org','http://127.0.0.1','http://localhost'].includes(origin)){
  socket.write('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n');socket.destroy();return;
 }
 wss.handleUpgrade(req,socket,head,ws=>wss.emit('connection',ws,req));
});
wss.on('connection',ws=>{ws.connectedAt=Date.now();ws.lastClientPingAt=null;let initial=false;const timeout=setTimeout(()=>{if(!initial)ws.close(1008,'hello timeout')},5000);
 ws.on('message',data=>{let msg;try{msg=JSON.parse(data.toString());}catch{return send(ws,{type:'rejected',message:'Invalid JSON'})}
  if(!initial){if(msg?.type!=='hello')return send(ws,{type:'rejected',message:'Send hello first'});initial=true;clearTimeout(timeout);attach(ws,msg).catch(err=>{status('attach_error',{reason:err.message});ws.close(1011);});return;}
  const session=ws.session;if(!session)return;session.lastSeen=Date.now();
  try{switch(msg?.type){case 'command':session.cmd(ws,msg);break;case 'text':session.text(ws,msg);break;case 'save':session.save();send(ws,{type:'message',text:'Authoritative world saved on Nitro.'});break;case 'load':session.load(ws);break;case 'import_legacy':session.importSnapshot(ws,msg.snapshot);break;case 'restart':session.restart();break;case 'describe':send(ws,{type:'text_result',text:narrateWorld(session.core.state())});break;case 'ask_llm':askLLM(session,ws);break;case 'ping':ws.lastClientPingAt=Date.now();send(ws,{type:'pong',time:Date.now()});break;default:send(ws,{type:'rejected',message:'Unknown request'});}}
  catch(err){session.log('command_error',{reason:String(err.message).slice(0,200)});send(ws,{type:'error',message:'The command could not be completed.'});}
 });
 ws.on('close',(code,reason)=>{
  clearTimeout(timeout);
  const session=ws.session;if(!session)return;
  session.clients.delete(ws);session.lastSeen=Date.now();
  if(!session.clients.size){session.core.command({type:'Move',direction:0});session.events();session.save();}
  session.log('viewer_disconnected',{viewers:session.clients.size,closeCode:code,closeReason:String(reason||'').slice(0,100),durationSeconds:Math.round((Date.now()-ws.connectedAt)/1000),secondsSinceClientPing:ws.lastClientPingAt?Math.round((Date.now()-ws.lastClientPingAt)/1000):null});
  if(code===1006||code===1011||code===1013)status('viewer_abnormal_close',{code,durationSeconds:Math.round((Date.now()-ws.connectedAt)/1000),sessionSuffix:session.id.slice(-4)});
 });
 ws.on('error',err=>{status('viewer_error',{kind:err.code||'socket'})});
});
let lastTime=process.hrtime.bigint(),carryMs=0;
interval=setInterval(()=>{if(!active)return;const n=process.hrtime.bigint(),elapsed=Math.min(120,Number(n-lastTime)/1e6);lastTime=n;carryMs+=elapsed;
 let loops=0;while(carryMs>=TICK_MS&&loops++<7){hostTick++;for(const s of sessions.values())try{s.tick()}catch(e){status('tick_error',{sessionSuffix:s.id.slice(-4),error:String(e.message).slice(0,120)});s.log('tick_error',{reason:e.message})}carryMs-=TICK_MS;}if(loops>=7)carryMs=0;
 if(hostTick%3600===0)for(const [id,s] of sessions){if(!s.clients.size&&Date.now()-s.lastSeen>120000){s.close().catch(e=>status('session_close_error',{reason:e.message}));sessions.delete(id);}}
},16);interval.unref();
server.listen(PORT,'127.0.0.1',()=>status('ready',{port:PORT,backend:'Rapier3D',dir:STATE_DIR,protocol:1}));
async function shutdown(signal){if(!active)return;active=false;clearInterval(interval);status('shutdown',{signal});wss.clients.forEach(ws=>ws.close(1001,'server restart'));for(const s of sessions.values())try{await s.close()}catch(err){status('shutdown_save_error',{reason:err.message})}server.close(()=>process.exit(0));setTimeout(()=>process.exit(0),4000).unref();}
process.on('SIGTERM',()=>shutdown('SIGTERM'));process.on('SIGINT',()=>shutdown('SIGINT'));
