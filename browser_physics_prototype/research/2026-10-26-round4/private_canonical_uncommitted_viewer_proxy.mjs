// Isolated real Chromium test proxy for the CURRENT CANONICAL (dirty) Nitro
// Games checkout. Read only current production-adjacent JS/HTML: no writes
// to canonical checkout, Apache alias, host systemd, production port or
// other agents' sessions. Point WS at a distinct new isolated GameCore.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {createRequire}from'node:module';
const require=createRequire(import.meta.url);
const WS=require('ws');
const ROOT='/data/src/github/games';
const PORT=Number(process.env.PRSE_ROUND4_UI_PORT);
const UPSTREAM=Number(process.env.PRSE_ROUND4_BACKEND_PORT);
if(!Number.isInteger(PORT)||!Number.isInteger(UPSTREAM)||
  PORT===UPSTREAM||[PORT,UPSTREAM].some(x=>x<1025||x===18764||x>65535))
 throw Error('Canonical browser test must be isolated and avoid production port');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
 '.css':'text/css; charset=utf-8','.json':'application/json','.png':'image/png',
 '.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml'};
const webroot=path.join(ROOT,'browser_physics_prototype');
const server=http.createServer(async(req,res)=>{
 const u=(req.url||'/').split('?')[0];
 if(u==='/llm_game_runtime/health'){
  try{const r=await fetch('http://127.0.0.1:'+UPSTREAM+'/health');
   res.writeHead(r.status,{'content-type':'application/json'});res.end(await r.text());
  }catch{res.writeHead(502);res.end('isolated GameCore unavailable')}
  return;
 }
 const landing=u==='/'||u==='/llm_game/'||u==='/llm_game';
 let file=path.join(ROOT,'LLM_Game/web/index.html');
 if(!landing){
  if(!u.startsWith('/llm_game/physics-prototype/')){res.writeHead(404);res.end();return}
  let sub=u.slice('/llm_game/physics-prototype/'.length);
  try{sub=decodeURIComponent(sub)}catch{res.writeHead(400);res.end();return}
  file=path.resolve(webroot,sub);
  if(!file.startsWith(webroot+path.sep)){res.writeHead(404);res.end();return}
 }
 const kind=types[path.extname(file)];
 if(!kind){res.writeHead(404);res.end();return}
 try{const body=await readFile(file);
  res.writeHead(200,{'content-type':kind,'cache-control':'no-store',
    'x-private-canonical-ui':'read-only-uncommitted-snapshot'});
  res.end(body);
 }catch{res.writeHead(404);res.end()}
});
const wss=new WS.WebSocketServer({noServer:true});
server.on('upgrade',(req,socket,head)=>{
 if(req.url!=='/llm_game_runtime/ws'){socket.destroy();return}
 wss.handleUpgrade(req,socket,head,down=>{
  const up=new WS('ws://127.0.0.1:'+UPSTREAM+'/ws'),buffer=[];
  let ready=false;
  down.on('message',(data,binary)=>{
   if(up.readyState===WS.OPEN)up.send(data,{binary});
   else if(buffer.length<8)buffer.push([data,binary]);
  });
  up.on('open',()=>{
   ready=true;
   for(const [data,binary]of buffer)up.send(data,{binary});
   buffer.length=0;
  });
  up.on('message',(data,binary)=>{
   if(down.readyState===WS.OPEN)down.send(data,{binary});
  });
  up.on('close',code=>{if(down.readyState===WS.OPEN)down.close(code===1006?1000:code)});
  down.on('close',()=>{if(up.readyState===WS.OPEN)up.close();else up.terminate()});
  up.on('error',()=>{if(down.readyState===WS.OPEN)down.close(1011,'test upstream error')});
 });
});
server.listen(PORT,'127.0.0.1',()=>{
 console.log(JSON.stringify({privateCanonicalUITest:true,port:PORT,backendPort:UPSTREAM,
   productionPortUnchanged:true,canonicalCheckoutReadOnly:true}));
});
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));
