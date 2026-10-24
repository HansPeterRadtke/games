// End-to-end *plumbing* test, NOT a participant or skill-learning experiment.
// Starts a NEW loopback-only PRSE human habit lab with temporary isolated storage.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,readdir,readFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createRequire} from 'node:module';
import {trainSmallMLP,trainKnn,infer} from './human_skill_policy.mjs';

const require=createRequire(import.meta.url);
const WS=require('ws');
const tmp=await mkdtemp(path.join(os.tmpdir(),'prse-human-lab-fixture-'));
const node=spawn(process.execPath,[new URL('./human_skill_lab.mjs',import.meta.url).pathname],{
 env:{...process.env,PRSE_HABIT_PORT:'0',PRSE_HABIT_TEST_MODE:'1',PRSE_HABIT_DATA_DIR:tmp},
 stdio:['ignore','pipe','pipe']
});
let buffer='',err='',port=null;const packets=[];
node.stdout.on('data',chunk=>{
 buffer+=chunk.toString();
 for(const line of buffer.split('\n').slice(0,-1)){
  try{const value=JSON.parse(line);if(value.status==='ready')port=Number(new URL(value.url).port);}catch{}
 }
 buffer=buffer.slice(buffer.lastIndexOf('\n')+1);
});
node.stderr.on('data',chunk=>err+=chunk.toString());
const nap=ms=>new Promise(r=>setTimeout(r,ms));
async function until(f,seconds=7){const deadline=Date.now()+seconds*1000;
 while(Date.now()<deadline){const v=f();if(v)return v;await nap(30);}
 throw Error('wait exceeded: '+err.slice(-500));
}
let ws=null;
try{
 await until(()=>port);
 const url='http://127.0.0.1:'+port;
 const pages=['/','/client.mjs','/source/side-view-renderer.js',
  '/source/generated/semantic-asset-manifest.js'];
 for(const target of pages){
  const res=await fetch(url+target,{signal:AbortSignal.timeout(3500)});
  assert(res.ok,'missing browser dependency '+target+': '+res.status);
  assert((await res.text()).length>100);
 }
 const invalid=await fetch(url+'/../../../../../etc/passwd');
 assert.equal(invalid.status,404,'path traversal should never expose a file');
 ws=new WS('ws://127.0.0.1:'+port+'/ws');
 ws.on('message',b=>{try{packets.push(JSON.parse(b.toString()));}catch{}});
 await new Promise((resolve,reject)=>{ws.once('open',resolve);ws.once('error',reject);});
 await until(()=>packets.find(p=>p.type==='hello'));
 assert.equal(packets[0].state.phase,'manual');
 const send=object=>ws.send(JSON.stringify(object));
 send({type:'train',method:'knn'});
 await until(()=>packets.find(p=>p.type==='notice'&&p.message.includes('At least two')));
 send({type:'start_demo',selfAttested:false});
 await until(()=>packets.find(p=>p.type==='notice'&&p.message.includes('checkbox')));
 assert.equal(packets.at(-1).state.phase,'manual');
 send({type:'start_demo',selfAttested:true});
 await until(()=>packets.find(p=>p.type==='notice'&&p.state?.phase==='recording'));
 send({type:'key',key:'right',down:true});
 await nap(1200);
 send({type:'key',key:'right',down:false});
 await nap(350);
 send({type:'finish_demo'});
 const completed=await until(()=>packets.find(p=>p.type==='notice'&&p.state?.lastResult?.kind==='demonstration'),5);
 assert.equal(completed.state.phase,'manual');
 const names=await readdir(tmp);
 const records=names.filter(n=>n.startsWith('manual_')&&n.endsWith('.json'));
 assert.equal(records.length,1,'trial must save exactly once');
 const saved=JSON.parse(await readFile(path.join(tmp,records[0]),'utf8'));
 assert.equal(saved.provenance,'automated_test_fixture_NOT_HUMAN');
 assert.equal(saved.source,'automated_ws_client');
 assert(saved.frames.length>30);
 assert(saved.events.some(e=>e.source==='scripted_test_command_not_human'));
 assert(saved.frames.some(f=>f.action.move===1));
 assert(saved.frames.at(-1).after.player.x>saved.frames[0].before.player.x+.5);
 assert(saved.frames.some(f=>typeof f.verifiedPhysicalContact==='boolean'));
 assert(saved.frames.every(f=>f.before.player.z===0&&f.after.player.z===0));
 assert(!names.some(n=>n.startsWith('evaluation_')),'no automatic test may be mistaken for learned evaluation');
 // Separate fixed synthetic rows verify bounded training plumbing only.
 const synthetic=Array.from({length:90},(_,i)=>{
  const f=Array(12).fill(0);f[0]=(i-45)/9;f[1]=Math.sin(i/10);
  return {f,move:i<20?-1:i<50?0:1,jump:i%7===0};
 });
 for(const model of [trainSmallMLP(synthetic,{epochs:2}),trainKnn(synthetic)]){
  const action=infer(model,synthetic[10].f);
  assert([-1,0,1].includes(action.move)&&typeof action.jump==='boolean');
 }
 console.log(JSON.stringify({passed:true,kind:'automated_interface_validation_NOT_human_study',
   authoritativeFrames:saved.frames.length,keyEvents:saved.events.length,
   physicalContactFrames:saved.frames.filter(f=>f.verifiedPhysicalContact).length,
   recordedOutcome:saved.success,unverifiedHumanClaims:0,trainingRefusedWithNoSuccess:true,
   localHostOnly:true,independentStaticBrowserAssetsAccessible:true}));
}finally{
 try{ws?.close();}catch{}
 node.kill('SIGTERM');
 await nap(300);
 if(node.exitCode===null)node.kill('SIGKILL');
 await rm(tmp,{recursive:true,force:true});
}
