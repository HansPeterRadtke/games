// Isolated, loopback-only human teaching experiment in the EXISTING PRSE GameCore.
// No public service, live-session mutation or synthetic teacher data.
// Each human-labeled trial is ONLY self-attested: browser provenance is not proof.
import http from 'node:http';
import os from 'node:os';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {GameCore,initializePhysics} from '../../physics-core.js';
import {features,trainSmallMLP,trainKnn,infer,countParameters} from './human_skill_policy.mjs';

const require=createRequire(import.meta.url);
const {WebSocketServer}=require('ws');
const here=path.dirname(fileURLToPath(import.meta.url));
const sources=path.resolve(here,'../..');
const dataDir=path.resolve(process.env.PRSE_HABIT_DATA_DIR||'/data/var/llm_game/human_habit_trials');
const port=Number(process.env.PRSE_HABIT_PORT||0);
const AUTOMATED_TEST=process.env.PRSE_HABIT_TEST_MODE==='1';
const GOAL_X=12.1, BAND=.38, MAX_DEMOS=30, MAX_FRAMES=1200;
const configs={
 demo:[{px:7.1,cx:9.0},{px:7.35,cx:9.1},{px:7.0,cx:8.9},{px:7.2,cx:9.15}],
 holdout:[{px:7.18,cx:9.35},{px:6.9,cx:9.05},{px:7.3,cx:8.72},{px:7.05,cx:9.45}]
};
function makeCore(initial){
 const game=new GameCore();
 game.player.setTranslation({x:initial.px,y:1,z:0},true);
 game.player.setLinvel({x:0,y:0,z:0},true);
 game.crate.setTranslation({x:initial.cx,y:.57,z:0},true);
 game.crate.setLinvel({x:0,y:0,z:0},true);
 game.world.updateSceneQueries();
 return game;
}
function sample(game){
 const player=game.player.translation(),pv=game.player.linvel();
 const crate=game.crate.translation(),cv=game.crate.linvel();
 let contact=false;
 game.world.contactPair(game.player.collider(0),game.crate.collider(0),pair=>{
  if(pair.numContacts()>0)contact=true;
 });
 return {tick:game.stepCount,time:game.time,
  player:{x:player.x,y:player.y,z:player.z,vx:pv.x,vy:pv.y,vz:pv.z},
  crate:{x:crate.x,y:crate.y,z:crate.z,vx:cv.x,vy:cv.y,vz:cv.z},
  grounded:game.grounded(),contact,goalX:GOAL_X,
  speedFactor:game.character.locomotion().speedFactor};
}
function success(state,contacts,still){
 return state.crate.x>=GOAL_X-BAND&&state.crate.x<=GOAL_X+BAND
  &&Math.abs(state.crate.vx)<.17&&contacts>=12&&still>=18;
}
function ext(name){return path.extname(name).toLowerCase();}
function send(ws,packet){if(ws.readyState!==1||ws.bufferedAmount>250000)return false;ws.send(JSON.stringify(packet));return true;}
function safeRecord(name,data){
 fs.mkdirSync(dataDir,{recursive:true,mode:0o700});
 const dest=path.join(dataDir,name);
 fs.writeFileSync(dest,JSON.stringify(data,null,2)+'\n',{encoding:'utf8',flag:'wx',mode:0o600});
 return name;
}
class Lab{
 constructor(){
  this.game=makeCore(configs.demo[0]);this.phase='manual';this.io={left:false,right:false,jump:false,pendingJump:false};
  this.ws=null;this.trial=null;this.demos=[];this.results=[];this.candidate=null;this.accepted=null;
  this.revision=0;this.evalCount=0;this.totalFrames=0;this.still=0;
  this.restoreModel();
  this.loadDemos();
 }
 loadDemos(){
  try{
   for(const name of fs.readdirSync(dataDir).filter(n=>/^manual_[0-9a-f-]{36}\.json$/.test(n)).sort().slice(-MAX_DEMOS)){
    const file=path.join(dataDir,name);
    if(fs.statSync(file).size>8e6)continue;
    const demo=JSON.parse(fs.readFileSync(file,'utf8'));
    if(!['self_attested_direct_browser_inputs_NOT_verified_human','automated_test_fixture_NOT_HUMAN'].includes(demo?.provenance)
      ||typeof demo.success!=='boolean'||!Array.isArray(demo.frames)||demo.frames.length>MAX_FRAMES
      ||!demo.frames.every(x=>x.before?.player&&x.before?.crate&&[-1,0,1].includes(x.action?.move)
           &&typeof x.action?.jump==='boolean'))continue;
    if(AUTOMATED_TEST!== (demo.provenance==='automated_test_fixture_NOT_HUMAN'))continue;
    this.demos.push(demo);
   }
  }catch{/* No existing opt-in practice is a normal initial state. */}
 }
 restoreModel(){
  const file=path.join(dataDir,'accepted_model.json');
  try{
   if(fs.statSync(file).size>2e6)throw Error('oversized');
   const obj=JSON.parse(fs.readFileSync(file,'utf8'));
   if(obj?.version===1 && ['knn','tiny_mlp'].includes(obj.model?.kind)){
    const test=infer(obj.model,Array(12).fill(0));
    if([-1,0,1].includes(test.move)&&typeof test.jump==='boolean')this.accepted=obj.model;
   }
  }catch{/* Absence or malformed persistent model never triggers automation. */}
 }
 state(){
  const s=sample(this.game),full=this.game.state();
  return {phase:this.phase,trainingExamples:this.demos.filter(d=>d.success).length,
    rejectedExamples:this.demos.filter(d=>!d.success).length,candidate:this.candidate?.kind||null,
    accepted:this.accepted?.kind||null,
    trainingLoss:this.candidate?.fitLoss??null,game:full,skill:s,
    task:{target:GOAL_X,tolerance:BAND,goal:'Physically push the existing crate into the marked bay and let it settle.'},
    trial:this.trial?{steps:this.trial.frames.length,contactFrames:this.trial.contacts}:null,
    lastResult:this.results.at(-1)||null};
 }
 tell(kind,message){send(this.ws,{type:'notice',kind,message,state:this.state()});}
 reset(configuration){const old=this.game;this.game=makeCore(configuration);old.world.free();
  this.io={left:false,right:false,jump:false,pendingJump:false};this.still=0;}
 beginDemo(attestation){
  if(this.phase!=='manual'||!attestation ||this.demos.length>=MAX_DEMOS)
   return this.tell('error','Manual mode, a self-attested human-input checkbox and room for a new trial are required.');
  const config=configs.demo[this.demos.length%configs.demo.length];
  this.reset(config);this.revision++;
  this.trial={id:crypto.randomUUID(),provenance:AUTOMATED_TEST?'automated_test_fixture_NOT_HUMAN':'self_attested_direct_browser_inputs_NOT_verified_human',
    participantIdentity:null,source:AUTOMATED_TEST?'automated_ws_client':'local_browser',startedAt:new Date().toISOString(),
    initial:this.game.snapshot(),configuration:config,task:'physical_crate_position',
    frames:[],events:[],contacts:0,stable:0,revision:this.revision};
  this.phase='recording';this.tell('training','Recording physical actions and authoritative world states. Stop when done.');
 }
 stopDemo(reason='user_finished'){
  if(this.phase!=='recording')return this.tell('error','There is no demonstration being recorded.');
  const state=sample(this.game),ok=success(state,this.trial.contacts,this.still);
  const record={...this.trial,frames:this.trial.frames,success:ok,reason,
    finishedAt:new Date().toISOString(),final:state};
  const stored=safeRecord('manual_'+this.trial.id+'.json',record);
  this.demos.push(record);
  this.results.push({kind:'demonstration',success:ok,steps:record.frames.length,
    contactFrames:record.contacts,crateX:state.crate.x,stored});
  this.trial=null;this.phase='manual';this.io={left:false,right:false,jump:false,pendingJump:false};
  this.tell('trial',ok?'Completed demonstration saved.':'Unsuccessful demonstration saved as negative evidence.');
 }
 trainingRows(){
  const rows=[];
  for(const trial of this.demos.filter(t=>t.success)){
   let previous=null;
   for(const frame of trial.frames){
    rows.push({f:features(frame.before,previous),move:frame.action.move,jump:frame.action.jump});
    previous=frame.before;
   }
  }
  return rows;
 }
 train(method){
  if(this.phase!=='manual')return this.tell('error','Stop or interrupt the previous task first.');
  if(this.demos.filter(d=>d.success).length<2)return this.tell('error','At least two successful, self-attested manual demonstrations are required.');
  try{
   const rows=this.trainingRows();
   this.candidate=method==='tiny_mlp'?trainSmallMLP(rows):method==='knn'?trainKnn(rows):null;
   if(!this.candidate)throw Error('Unknown policy');
   this.candidate.trainingSource=AUTOMATED_TEST?'automated_fixture_NO_HUMAN':'self_attested_browser_demonstrations_NOT_independently_verified';
   this.candidate.candidateId=crypto.randomUUID();
   this.candidate.trainingTrials=this.demos.filter(d=>d.success).map(d=>d.id);
   this.tell('trained','A candidate was fitted. Training loss is NOT physical competence; run the held-out preview before accepting.');
  }catch(e){this.tell('error','Candidate training failed: '+String(e.message).slice(0,120));}
 }
 beginAuto(kind){
  if(this.phase!=='manual')return this.tell('error','Stop existing task before starting a preview or an accepted habit.');
  const policy=kind==='preview'?this.candidate:this.accepted;
  if(!policy)return this.tell('error','No '+kind+' controller exists.');
  const config=configs.holdout[this.evalCount%configs.holdout.length];this.evalCount++;
  this.reset(config);this.revision++;this.phase=kind;this.trial={id:crypto.randomUUID(),
    provenance:'automated_controller_evaluation',humanParticipant:false,
    model:policy.kind,candidateId:policy.candidateId||null,initial:this.game.snapshot(),configuration:config,
    frames:[],contacts:0,stable:0,revision:this.revision};
  this.tell('control',kind==='preview'?'Candidate preview: manual input interrupts immediately.':'Accepted habit active: manual input interrupts immediately.');
 }
 accept(){
  if(this.phase!=='manual'||!this.candidate)return this.tell('error','Stop the preview and train a candidate first.');
  const preview=this.results.some(r=>r.kind==='preview'&&r.candidateId===this.candidate.candidateId);
  if(!preview)return this.tell('error','Run a preview before accepting this candidate.');
  this.accepted=structuredClone(this.candidate);
  const payload={version:1,acceptedAt:new Date().toISOString(),model:this.accepted};
  try{
   fs.mkdirSync(dataDir,{recursive:true,mode:0o700});
   const tmp=path.join(dataDir,'.accepted_model_'+crypto.randomUUID()+'.json');
   fs.writeFileSync(tmp,JSON.stringify(payload),{mode:0o600,flag:'wx'});
   fs.renameSync(tmp,path.join(dataDir,'accepted_model.json'));
  }catch(e){this.accepted=null;return this.tell('error','Could not save accepted controller: '+String(e.message).slice(0,90));}
  this.tell('control','Candidate accepted and saved. Enable it explicitly to run.');
 }
 forget(){
  if(this.phase!=='manual')this.interrupt('Accepted habit disabled by player');
  this.accepted=null;
  try{fs.unlinkSync(path.join(dataDir,'accepted_model.json'));}catch(e){if(e.code!=='ENOENT')return this.tell('error','Could not forget the saved habit.');}
  this.tell('control','Accepted habit disabled and its saved controller removed. Raw demonstrations are kept for retraining.');
 }
 reject(){
  if(this.phase==='preview')this.interrupt('Rejected preview');
  this.candidate=null;this.tell('control','Candidate rejected. Original demonstrations retained, manual control restored.');
 }
 interrupt(reason='Manual override'){
  if(this.phase==='recording')return this.stopDemo('interrupted');
  if(this.phase==='manual')return this.tell('control','Already in manual mode.');
  this.revision++; // invalidates all outputs from earlier controller generation.
  if(this.trial)this.finishAuto('interrupted',reason);
  this.phase='manual';this.trial=null;
  this.game.command({type:'TakeManualControl'});
  this.game.command({type:'Move',direction:0});
  this.tell('control','Autonomous commands stopped; manual control owns subsequent ticks.');
 }
 finishAuto(reason='finished',detail=''){
  const t=this.trial;if(!t)return;
  const state=sample(this.game),ok=reason==='finished'&&success(state,t.contacts,this.still);
  const report={kind:this.phase,model:t.model,candidateId:t.candidateId,source:t.provenance,
    success:ok,reason,detail,steps:t.frames.length,contactFrames:t.contacts,
    crateX:state.crate.x,configuration:t.configuration,
    trajectoryChecksum:crypto.createHash('sha256').update(JSON.stringify(t.frames)).digest('hex')};
  safeRecord('evaluation_'+t.id+'.json',{...t,success:ok,reason,detail,final:state});
  this.results.push(report);
  this.trial=null;this.phase='manual';
 }
 key(key,down){
  if(!['left','right','jump'].includes(key)||typeof down!=='boolean')return;
  if((this.phase==='preview'||this.phase==='enabled')&&down)this.interrupt('Direct user control');
  if(this.phase==='manual'||this.phase==='recording'){
   if(key==='jump'){
    if(down&&!this.io.jump)this.io.pendingJump=true;
    this.io.jump=down;
   }else this.io[key]=down;
   if(this.phase==='recording')this.trial.events.push({tick:this.game.stepCount,key,down,
     source:AUTOMATED_TEST?'scripted_test_command_not_human':'browser_command_self_attested_not_verifiable'});
  }
 }
 tick(){
  if(!this.ws||this.ws.readyState!==1)return;
  const before=sample(this.game),previous=this.trial?.frames.at(-1)?.before||null;
  let move=Number(this.io.right)-Number(this.io.left),jump=this.io.pendingJump;
  if(this.phase==='preview'||this.phase==='enabled'){
   const model=this.phase==='preview'?this.candidate:this.accepted;
   try{
    const a=infer(model,features(before,previous));move=a.move;jump=a.jump;
   }catch(e){this.interrupt('Invalid controller: '+String(e.message));move=0;jump=false;}
  }
  this.io.pendingJump=false;
  if(![-1,0,1].includes(move)||typeof jump!=='boolean'){this.interrupt('Invalid action');return;}
  this.game.command({type:'Move',direction:move});
  if(jump)this.game.command({type:'Jump'});
  this.game.step();this.totalFrames++;
  const after=sample(this.game);
  if(after.contact&&this.trial)this.trial.contacts++;
  this.still=(Math.abs(after.crate.vx)<.17&&after.crate.x>=GOAL_X-BAND&&after.crate.x<=GOAL_X+BAND)?this.still+1:0;
  if(this.trial){
   this.trial.frames.push({before,action:{move,jump},after,
     verifiedPhysicalContact:after.contact});
   if(this.trial.frames.length>=MAX_FRAMES){
    if(this.phase==='recording')this.stopDemo('time_limit');
    else {this.finishAuto('time_limit');this.tell('outcome','Preview reached the maximum trial length without meeting the objective.');}
   }else if((this.phase==='preview'||this.phase==='enabled')&&success(after,this.trial.contacts,this.still)){
    this.finishAuto('finished');this.tell('outcome','Controller finished a physically verified crate placement.');
   }
  }
  if(this.totalFrames%6===0)send(this.ws,{type:'state',state:this.state()});
 }
 handle(ws,message){
  if(!message||typeof message!=='object'||Array.isArray(message))return;
  switch(message.type){
   case 'key':this.key(message.key,message.down);break;
   case 'start_demo':this.beginDemo(message.selfAttested===true);break;
   case 'finish_demo':this.stopDemo();break;
   case 'train':this.train(message.method);break;
   case 'try':this.beginAuto('preview');break;
   case 'accept':this.accept();break;
   case 'reject':this.reject();break;
   case 'forget':this.forget();break;
   case 'enable':this.beginAuto('enabled');break;
   case 'interrupt':this.interrupt();break;
   case 'reset':
    if(this.phase==='recording')this.stopDemo('discarded_by_reset');
    if(this.phase!=='manual')this.interrupt('reset');
    this.reset(configs.demo[0]);this.tell('control','Physics reset to manual start.');
    break;
   default:this.tell('error','Unknown instruction');
  }
 }
 close(){this.game.world.free();}
}
await initializePhysics();
const lab=new Lab();
const server=http.createServer((req,res)=>{
 const u=new URL(req.url,'http://localhost');
 let filepath;
 if(u.pathname==='/')filepath=path.join(here,'human_skill_lab.html');
 else if(u.pathname==='/client.mjs')filepath=path.join(here,'human_skill_client.mjs');
 else if(u.pathname.startsWith('/source/')){
  const part=u.pathname.slice('/source/'.length);
  filepath=path.resolve(sources,part);
  if(!filepath.startsWith(sources+path.sep)){res.writeHead(403);res.end();return;}
 }else{res.writeHead(404);res.end();return;}
 const contentType={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
 '.mjs':'text/javascript; charset=utf-8','.png':'image/png','.webp':'image/webp','.json':'application/json'}[ext(path.basename(filepath))]||'application/octet-stream';
 fs.readFile(filepath,(err,buf)=>{
  if(err){res.writeHead(404);res.end('not found');return;}
  res.writeHead(200,{'Content-Type':contentType,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
    'Content-Security-Policy':"default-src 'self'; connect-src 'self' ws://127.0.0.1:* ws://localhost:*; img-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; base-uri 'none'"});
  res.end(buf);
 });
});
const wss=new WebSocketServer({noServer:true});
server.on('upgrade',(req,socket,head)=>{
 const ip=req.socket.remoteAddress||'';
 if(!['127.0.0.1','::1','::ffff:127.0.0.1'].includes(ip)
  ||new URL(req.url,'http://localhost').pathname!=='/ws'
  ||(req.headers.origin&&!/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(req.headers.origin))){
  socket.destroy();return;
 }
 wss.handleUpgrade(req,socket,head,ws=>wss.emit('connection',ws));
});
wss.on('connection',ws=>{
 if(lab.ws&&lab.ws.readyState===1){ws.close(1008,'Only one local user per lab');return;}
 lab.ws=ws;send(ws,{type:'hello',state:lab.state(),warning:'No human training data collected until a person explicitly records.'});
 ws.on('message',raw=>{
  if(raw.length>4096){ws.close(1009);return;}
  try{lab.handle(ws,JSON.parse(raw.toString()));}catch(e){lab.tell('error',String(e.message).slice(0,100));}
 });
 ws.on('close',()=>{if(lab.ws===ws){if(lab.phase==='recording')lab.stopDemo('disconnect');else if(lab.phase!=='manual')lab.interrupt('disconnect');lab.ws=null;}});
});
const timer=setInterval(()=>lab.tick(),1000/60);timer.unref();
server.listen(port,'127.0.0.1',()=>{
 const addr=server.address();
 process.stdout.write(JSON.stringify({status:'ready',url:'http://127.0.0.1:'+addr.port+'/',bind:'loopback',
  liveProductionUnaffected:true,dataDir,existingGameCore:true})+'\n');
});
function stop(){clearInterval(timer);for(const client of wss.clients)client.close();wss.close();server.close();lab.close();}
process.once('SIGTERM',stop);process.once('SIGINT',stop);
