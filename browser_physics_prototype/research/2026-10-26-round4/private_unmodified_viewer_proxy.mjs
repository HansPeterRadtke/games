// Research-only loopback adapter for real PRSE viewer end-to-end acceptance.
// Serves the UNCHANGED project viewer assets (no copied/reimplemented UI)
// and proxies WSS input to a NEW isolated Nitro GameCore instance.
// NEVER connects to existing localhost:18764 or public production API.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const WS=require('ws');
const frontendPort=Number(process.env.PRSE_ROUND4_UI_PORT);
const backendPort=Number(process.env.PRSE_ROUND4_BACKEND_PORT);
const root=path.resolve(fileURLToPath(new URL('../../',import.meta.url)));
if(!Number.isInteger(frontendPort)||!Number.isInteger(backendPort)||
 frontendPort===backendPort||[frontendPort,backendPort].some(x=>x<1025||x>65535||x===18764))
 throw Error('Round4 test must use two different dedicated unprivileged ports, never production');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
 '.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8',
 '.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.webp':'image/webp',
 '.json':'application/json'};
const server=http.createServer(async(req,res)=>{
 const raw=(req.url||'/').split('?')[0];
 if(raw==='/llm_game_runtime/health'){
  try{
   const response=await fetch('http://127.0.0.1:'+backendPort+'/health');
   res.writeHead(response.status,{'content-type':'application/json','cache-control':'no-store'});
   res.end(await response.text());
  }catch{res.writeHead(502);res.end('isolated backend unavailable')}
  return;
 }
 const url=raw==='/'?'/viewer.html':raw;
 let requested;
 try{requested=decodeURIComponent(url)}catch{res.writeHead(400);res.end();return}
 const file=path.resolve(root,'.'+requested);
 if(!file.startsWith(root+path.sep) || !mime[path.extname(file)]){
  res.writeHead(404);res.end();return;
 }
 try{
  const data=await readFile(file);
  res.writeHead(200,{'content-type':mime[path.extname(file)],'cache-control':'no-store',
   'x-prse-round4':'isolated-real-viewer'});
  res.end(data);
 }catch{res.writeHead(404);res.end()}
});
const upgrade=new WS.WebSocketServer({noServer:true});
server.on('upgrade',(req,socket,head)=>{
 if(req.url!=='/llm_game_runtime/ws'){socket.destroy();return;}
 upgrade.handleUpgrade(req,socket,head,client=>{
  const upstream=new WS('ws://127.0.0.1:'+backendPort+'/ws');
  const pending=[];
  let opened=false;
  client.on('message',(bytes,binary)=>{
   if(opened&&upstream.readyState===WS.OPEN)upstream.send(bytes,{binary});
   else if(pending.length<8)pending.push([bytes,binary]);
  });
  upstream.on('open',()=>{
   opened=true;
   for(const [bytes,binary] of pending)upstream.send(bytes,{binary});
   pending.length=0;
  });
  upstream.on('message',(bytes,binary)=>{
   if(client.readyState===WS.OPEN)client.send(bytes,{binary});
  });
  upstream.on('close',(code)=>{if(client.readyState===WS.OPEN)client.close(code===1006?1000:code)});
  client.on('close',()=>{if(upstream.readyState===WS.OPEN)upstream.close();else upstream.terminate()});
  upstream.on('error',()=>{if(client.readyState===WS.OPEN)client.close(1011,'isolated backend unavailable')});
 });
});
server.listen(frontendPort,'127.0.0.1',()=>{
 process.stdout.write(JSON.stringify({event:'private_round4_viewer_ready',port:frontendPort,
 backendPort,root,productionUntouched:true})+'\n');
});
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));
