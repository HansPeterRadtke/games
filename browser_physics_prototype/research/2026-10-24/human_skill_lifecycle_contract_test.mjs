// Bounded programmatic UI-protocol acceptance. This IS NOT HUMAN TEACHING EVIDENCE.
// Every saved demonstration carries explicit automated_test_fixture_NOT_HUMAN provenance.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,readdir,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createRequire} from 'node:module';

const require=createRequire(import.meta.url);
const WS=require('ws');
const tmp=await mkdtemp(path.join(os.tmpdir(),'prse-habit-lifecycle-'));
const proc=spawn(process.execPath,[new URL('human_skill_lab.mjs',import.meta.url).pathname],{
  env:{...process.env,PRSE_HABIT_PORT:'0',PRSE_HABIT_DATA_DIR:tmp,PRSE_HABIT_TEST_MODE:'1'},stdio:['ignore','pipe','pipe']});
let port=null,stdout='',stderr='',socket=null,packets=[];
proc.stdout.on('data',b=>{
 stdout+=b.toString();
 for(const line of stdout.split('\n'))try{const obj=JSON.parse(line);
   if(obj.status==='ready')port=Number(new URL(obj.url).port);}catch{}
});
proc.stderr.on('data',b=>stderr+=b.toString());
const nap=ms=>new Promise(r=>setTimeout(r,ms));
async function until(f,seconds=6){const timeout=Date.now()+seconds*1000;
 while(Date.now()<timeout){const val=f();if(val)return val;await nap(30);}
 throw Error('Timed out; '+stderr.slice(-200)+' last='+JSON.stringify(packets.at(-1)?.state?.skill||{}));
}
const send=msg=>socket.send(JSON.stringify(msg));
async function waitPhase(phase){return until(()=>packets.slice(-5).reverse().find(x=>x.state?.phase===phase));}
try{
 await until(()=>port);
 socket=new WS('ws://127.0.0.1:'+port+'/ws');
 socket.on('message',b=>{try{packets.push(JSON.parse(b.toString()));if(packets.length>1000)packets=packets.slice(-500);}catch{}});
 await new Promise((r,j)=>{socket.once('open',r);socket.once('error',j);});
 await until(()=>packets.find(m=>m.type==='hello'));
 for(let trial=0;trial<2;trial++){
  send({type:'start_demo',selfAttested:true});
  await until(()=>packets.slice(-5).find(x=>x.type==='notice'&&x.state?.phase==='recording'),5);
  send({type:'key',key:'right',down:true});
  await until(()=>packets.at(-1)?.state?.skill?.crate.x>11.64,5);
  send({type:'key',key:'right',down:false});
  await until(()=>{const s=packets.at(-1)?.state?.skill;return s&&Math.abs(s.crate.vx)<.15&&s.crate.x>11.72&&s.crate.x<12.48;},3);
  await nap(410);
  send({type:'finish_demo'});
  const result=await until(()=>packets.slice(-10).reverse().find(x=>x.type==='notice'&&x.state?.lastResult?.kind==='demonstration'&&x.state.trainingExamples===trial+1),4);
  assert.equal(result.state.lastResult.success,true,'scripted validation needs complete physics task');
 }
 send({type:'train',method:'tiny_mlp'});
 const trained=await until(()=>packets.findLast(x=>x.type==='notice'&&x.state?.candidate==='tiny_mlp'),5);
 assert.equal(trained.state.trainingExamples,2);
 send({type:'try'});
 await waitPhase('preview');
 await nap(250);
 send({type:'key',key:'left',down:true});
 const interruption=await until(()=>packets.findLast(x=>x.type==='notice'&&x.state?.lastResult?.reason==='interrupted'),5);
 assert.equal(interruption.state.phase,'manual');
 send({type:'key',key:'left',down:false});
 send({type:'accept'});
 const accepted=await until(()=>packets.findLast(x=>x.type==='notice'&&x.state?.accepted==='tiny_mlp'),5);
 assert.equal(accepted.state.phase,'manual');
 send({type:'enable'});
 await waitPhase('enabled');
 send({type:'interrupt'});
 await waitPhase('manual');
 send({type:'forget'});
 const forgot=await until(()=>packets.findLast(x=>x.type==='notice'&&x.state?.accepted===null&&x.message.includes('disabled')),5);
 const files=await readdir(tmp);
 const raw=files.filter(x=>x.startsWith('manual_')&&x.endsWith('.json'));
 assert.equal(raw.length,2);
 for(const name of raw){const data=JSON.parse(await readFile(path.join(tmp,name),'utf8'));assert.equal(data.provenance,'automated_test_fixture_NOT_HUMAN');assert(data.frames.some(t=>t.verifiedPhysicalContact));}
 const scores=files.filter(f=>f.startsWith('evaluation_')).length;
 assert(scores>=1,'preview or interruption evaluation missing');
 console.log(JSON.stringify({passed:true,kind:'scripted_habit_lifecycle_QA_NOT_human',
  completedScriptedFixtures:2,humanParticipants:0,policyTraining:'tiny_mlp',
  previewInterrupted:true,manualPriority:true,accepted:true,enabled:true,forgotten:true,
  physicallyContactingFixtures:true,evaluations:scores}));
}finally{
 try{socket?.close();}catch{}
 proc.kill('SIGTERM');await nap(280);if(proc.exitCode===null)proc.kill('SIGKILL');
 await rm(tmp,{recursive:true,force:true});
}
