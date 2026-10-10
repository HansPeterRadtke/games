import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';import {createRequire} from 'node:module';
const WS=createRequire(import.meta.url)('ws');const port=18830+Math.floor(Math.random()*300),dir=await mkdtemp(path.join(os.tmpdir(),'prse-cap-test-'));
const child=spawn(process.execPath,[path.resolve('server.mjs')],{cwd:path.resolve('.'),env:{...process.env,PRSE_PORT:String(port),PRSE_STATE_DIR:dir,PRSE_MAX_ACTIVE:'3',PRSE_LOG_LEVEL:'quiet'},stdio:['ignore','pipe','pipe']});
let stderr='';child.stderr.on('data',d=>stderr+=d);const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function wait(fn){for(let i=0;i<100;i++){let a=await fn();if(a)return a;await sleep(70)}throw Error('timed out '+stderr.slice(-550));}
async function connect(token=null){const ws=new WS(`ws://127.0.0.1:${port}/ws`,{origin:'https://nitro.jonnyontherun.org'}),received=[];ws.on('message',buf=>received.push(JSON.parse(buf.toString())));await new Promise((res,rej)=>{ws.once('open',res);ws.once('error',rej)});ws.send(JSON.stringify({type:'hello',token}));await wait(()=>received.some(p=>p.type==='welcome'||p.type==='error'));return{ws,received,first:received.find(p=>p.type==='welcome'||p.type==='error')};}
try{
 await wait(async()=>{try{return (await fetch(`http://127.0.0.1:${port}/health`)).ok}catch{return false}});
 const three=[];for(let i=0;i<3;i++){let c=await connect();assert.equal(c.first.type,'welcome');three.push(c);}const full=await connect();assert.equal(full.first.type,'error','server must return useful capacity error');assert.ok(full.first.message.includes('capacity'));
 if(full.ws.readyState!==WS.CLOSED)await Promise.race([new Promise(res=>full.ws.once('close',res)),sleep(1000)]);
 console.log('CAPACITY_ERROR_OK');const firstToken=three[0].first.token;const resumed=await connect(firstToken);assert.equal(resumed.first.type,'welcome','connecting same world must not consume a new simulation slot');resumed.ws.close();console.log('RESUME_OK');
 three[0].ws.close();await sleep(120);console.log('INACTIVE_READY');const newcomer=await connect();assert.equal(newcomer.first.type,'welcome','server must reclaim disconnected sessions');
 newcomer.ws.close();three.forEach(c=>c.ws.close());
 console.log(JSON.stringify({passed:true,maxActive:3,limitHasClearError:true,joinExistingWorld:true,evictIdle:true}));
}finally{child.kill('SIGTERM');await sleep(200)}
