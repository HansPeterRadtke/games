import {SideViewRenderer} from '/source/side-view-renderer.js';
const el=id=>document.getElementById(id);
const renderer=new SideViewRenderer(el('scene'));
const status=el('status'),metrics=el('metrics');
let socket=null,latest=null,ready=false;
let held=new Set(),lastNotice='';
function send(packet){
 if(socket?.readyState!==WebSocket.OPEN){status.textContent='No private local connection.';return false;}
 socket.send(JSON.stringify(packet));return true;
}
function key(name,down){
 if(down===held.has(name))return;
 if(down)held.add(name);else held.delete(name);
 send({type:'key',key:name,down});
}
function release(){
 for(const keyName of [...held])key(keyName,false);
}
function updateUI(s){
 latest=s;
 const r=s.lastResult||null,sk=s.skill,model=s.candidate||'none';
 metrics.textContent='Mode: '+s.phase+'   Successful demonstrations: '+s.trainingExamples
 + '   Failed demonstrations: '+s.rejectedExamples
 + '\nPlayer position: '+sk.player.x.toFixed(2)+'m'
 + '   Crate position: '+sk.crate.x.toFixed(2)+'m'
 + '   Crate velocity: '+sk.crate.vx.toFixed(2)+'m/s'
 + '   Physical contact: '+String(sk.contact)
 + '\nCandidate: '+model+'   Accepted: '+(s.accepted||'none')
 + '   Fit loss (not success): '+(s.trainingLoss===null?'unavailable':s.trainingLoss.toFixed(4))
 + '\nLast recorded result: '+(r?JSON.stringify(r):'none');
 const buttons={
  'start-demo':s.phase==='manual',
  'finish-demo':s.phase==='recording',
  train:s.phase==='manual',
  try:s.phase==='manual'&&!!s.candidate,
  accept:s.phase==='manual'&&!!s.candidate,
  reject:!!s.candidate,
  enable:s.phase==='manual'&&!!s.accepted,
  forget:!!s.accepted
 };
 for(const [id,allowed]of Object.entries(buttons))el(id).disabled=!allowed;
}
function draw(){
 if(latest){
  renderer.draw(latest.game);
  const c=renderer.ctx,left=renderer.screen(latest.task.target-latest.task.tolerance),
        right=renderer.screen(latest.task.target+latest.task.tolerance),
        h=renderer.height;
  c.save();
  c.fillStyle='#2ca89b55';c.fillRect(left,420,right-left,95);
  c.strokeStyle='#0b7165';c.lineWidth=3;c.strokeRect(left,420,right-left,95);
  renderer.label('PHYSICAL CRATE TARGET',Math.max(150,Math.min(renderer.width-150,(left+right)/2)),405,'#ffffff');
  c.restore();
 }
 requestAnimationFrame(draw);
}
draw();
function connect(){
 socket=new WebSocket('ws://'+location.host+'/ws');
 socket.onopen=()=>{ready=true;status.textContent='Connected to private physics core. No recording until you opt in.';};
 socket.onmessage=event=>{
  let packet;try{packet=JSON.parse(event.data)}catch{return;}
  if(packet.state)updateUI(packet.state);
  if(packet.type==='notice'){lastNotice=packet.message;status.textContent=packet.message;}
  if(packet.type==='hello')status.textContent='Ready: manual control of the existing PRSE physical world.';
 };
 socket.onclose=()=>{ready=false;release();status.textContent='Local lab disconnected. Restart the private server to continue.';};
 socket.onerror=()=>{status.textContent='Cannot reach the private lab. Start the loopback lab server on Nitro.';};
}
connect();
const bind=(id,action)=>el(id).addEventListener('click',action);
for(const name of ['left','right','jump']){
 const button=el(name);
 button.addEventListener('pointerdown',event=>{event.preventDefault();button.setPointerCapture(event.pointerId);key(name,true);});
 button.addEventListener('pointerup',()=>key(name,false));
 button.addEventListener('pointercancel',()=>key(name,false));
 button.addEventListener('lostpointercapture',()=>key(name,false));
}
window.addEventListener('keydown',event=>{
 if(event.repeat||['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;
 const name={'a':'left','ArrowLeft':'left','d':'right','ArrowRight':'right',' ':'jump'}[event.key];
 if(name){event.preventDefault();key(name,true);}
});
window.addEventListener('keyup',event=>{
 const name={'a':'left','ArrowLeft':'left','d':'right','ArrowRight':'right',' ':'jump'}[event.key];
 if(name){event.preventDefault();key(name,false);}
});
window.addEventListener('blur',()=>{release();send({type:'interrupt'});});
document.addEventListener('visibilitychange',()=>{if(document.hidden){release();send({type:'interrupt'});}});
bind('start-demo',()=>send({type:'start_demo',selfAttested:el('attestation').checked}));
bind('finish-demo',()=>{release();send({type:'finish_demo'});});
bind('train',()=>send({type:'train',method:el('algorithm').value}));
bind('try',()=>send({type:'try'}));
bind('accept',()=>send({type:'accept'}));
bind('reject',()=>{release();send({type:'reject'});});
bind('enable',()=>send({type:'enable'}));
bind('forget',()=>{release();send({type:'forget'});});
bind('interrupt',()=>{release();send({type:'interrupt'});});
bind('reset',()=>{release();send({type:'reset'});});
