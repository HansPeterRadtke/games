import {GameCore,initializePhysics,SETTINGS} from './physics-core.js';
import {rigDefinition} from './active-ragdoll.js';
const canvas=document.querySelector('#scene'),ctx=canvas.getContext('2d'),status=document.querySelector('#status'),message=document.querySelector('#message'),details=document.querySelector('#details');
const W=1152,H=648;canvas.width=W;canvas.height=H;
const images={};for(const [name,file] of Object.entries({idle:'kenney/character/idle.png',walkA:'kenney/character/walk_a.png',walkB:'kenney/character/walk_b.png',jump:'kenney/character/jump.png',npcIdle:'kenney/character/character_green_idle.png',npcWalkA:'kenney/character/character_green_walk_a.png',npcWalkB:'kenney/character/character_green_walk_b.png',hills:'kenney/background_color_hills.png',clouds:'kenney/background_clouds.png'})){const img=new Image();img.src='./assets/'+file;images[name]=img;}
let core,moveLeft=false,moveRight=false,lastTime=0,accumulator=0,camera=-2,eventCount=0,frameIndex=0,lastSave=null,paused=false;
const say=(text)=>{message.textContent=text;};
const keyMove=()=>{if(core)core.command({type:'Move',direction:Number(moveRight)-Number(moveLeft)});};
function drawSprite(name,dx,dy,dw,dh){const im=images[name];if(!im?.complete||!im.naturalWidth)return false;ctx.drawImage(im,dx,dy,dw,dh);return true;}
function render(){if(!core)return;const state=core.state(),pos=state.player,px=u=>W*.48+(u-camera)*91;camera+=(pos.x-1.2-camera)*.07;
 const sky=ctx.createLinearGradient(0,0,0,H);sky.addColorStop(0,'#8eb6c6');sky.addColorStop(.66,'#e0d5b7');sky.addColorStop(1,'#73846a');ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);
 for(const [name,y,h,alpha] of [['clouds',45,300,.23],['hills',105,420,.35]]){if(images[name].complete&&images[name].naturalWidth){ctx.globalAlpha=alpha;ctx.drawImage(images[name],0,y,W,h);ctx.globalAlpha=1;}}
 ctx.fillStyle='#98a9a0';for(let i=-3;i<12;i++){const x=px(i*4-7)*.45+W*.25;ctx.beginPath();ctx.ellipse(x,420,230,70,0,0,Math.PI*2);ctx.fill();}
 ctx.fillStyle='#748874';ctx.fillRect(0,512,W,136);ctx.fillStyle='#536956';ctx.fillRect(0,510,W,7);
 for(let i=-18;i<48;i++){const screen=px(i*2.9);if(screen<-90||screen>W+90)continue;ctx.fillStyle='#334d36';ctx.beginPath();ctx.moveTo(screen-17,510);ctx.lineTo(screen+7,478);ctx.lineTo(screen+22,510);ctx.fill();}
 const ground=512,cx=px(state.crate.x),cy=ground-state.crate.y*91;ctx.fillStyle='#6c4d34';ctx.fillRect(cx-47,cy-47,94,94);ctx.strokeStyle='#d3b185';ctx.lineWidth=5;ctx.strokeRect(cx-46,cy-46,92,92);ctx.beginPath();ctx.moveTo(cx-41,cy-40);ctx.lineTo(cx+41,cy+40);ctx.moveTo(cx+41,cy-40);ctx.lineTo(cx-41,cy+40);ctx.stroke();
 const fx=px(SETTINGS.fenceX),fTop=ground-SETTINGS.fenceHeight*91;ctx.fillStyle='#606a62';ctx.fillRect(fx-9,fTop,18,ground-fTop+4);ctx.fillStyle='#8c9b91';for(let j=0;j<2;j++)ctx.fillRect(fx-34,fTop+10+j*24,68,9);
 for(const e of state.visibleEntities){const ex=px(e.position.x),feet=ground-(e.position.y-.8)*91;ctx.save();ctx.translate(ex,feet);const npcFrame=e.physical?(Math.floor(state.time*6)%2===0?'npcWalkA':'npcWalkB'):'npcIdle';if(!drawSprite(npcFrame,-50,-118,100,118)){ctx.fillStyle='#384b40';ctx.fillRect(-15,-63,30,63);}ctx.restore();ctx.fillStyle='#f6f4df';ctx.font='bold 14px system-ui';ctx.textAlign='center';ctx.fillText(e.name,ex,feet-126);}
 // Physics rig: graphical bodies follow the authoritative 3D segment transforms.
 const rig=state.ragdoll,parts=rig.parts;
 for(const name of ['leftThigh','leftShin','rightThigh','rightShin','leftUpperArm','leftForearm','rightUpperArm','rightForearm','torso','head']){
  const data=parts[name],p=data.position,q=data.rotation,geometry=rigDefinition.parts[name];
  const x=px(p.x),y=ground-p.y*91,angle=-2*Math.atan2(q.z,q.w);
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.lineCap='round';ctx.strokeStyle=name==='head'?'#dfc69f':name==='torso'?'#3f667d':name.includes('Arm')?'#9d7157':'#65796c';ctx.lineWidth=geometry.radius*2*91;
  ctx.beginPath();ctx.moveTo(0,-geometry.length/2*91);ctx.lineTo(0,geometry.length/2*91);ctx.stroke();ctx.restore();
 }
 const head=parts.head.position;ctx.font='bold 15px system-ui';ctx.fillStyle='#f1f7f2';ctx.textAlign='center';ctx.fillText('MANNEQUIN',px(head.x),ground-head.y*91-34);
 if(rig.health.leftKnee.severity>.05){const k=parts.leftShin.position;ctx.beginPath();ctx.fillStyle='#c77758';ctx.arc(px(k.x),ground-(k.y+.25)*91,7,0,Math.PI*2);ctx.fill();}
 const st=SETTINGS.stoneX;ctx.fillStyle='#5c645d';ctx.beginPath();ctx.ellipse(px(st),ground-10,20,14,-.1,Math.PI,Math.PI*2);ctx.fill();
 const sx=px(pos.x),foot=ground-(pos.y-(SETTINGS.playerRadius+SETTINGS.playerHalfHeight))*91;ctx.save();ctx.translate(sx,foot);if(core.direction===-1)ctx.scale(-1,1);
 const moving=Math.abs(state.velocity.x)>.3,pose=!state.grounded?'jump':moving?(Math.floor(state.time*7)%2===0?'walkA':'walkB'):'idle';
 if(!drawSprite(pose,-57,-143,114,143)){ctx.fillStyle='#2e3a4b';ctx.fillRect(-22,-110,44,108);ctx.fillStyle='#cfad88';ctx.beginPath();ctx.arc(0,-120,18,0,7);ctx.fill();}ctx.restore();
 ctx.fillStyle='#fffbe6';ctx.textAlign='center';ctx.font='bold 16px system-ui';ctx.fillText('FENCE',fx,fTop-13);ctx.fillText('CRATE',cx,cy-58);
 ctx.fillStyle='#263c32';ctx.fillRect(0,H-34,W,34);ctx.fillStyle='#e5f0dc';ctx.font='15px system-ui';ctx.textAlign='left';ctx.fillText(`X ${pos.x.toFixed(2)} m    Z ${pos.z.toFixed(2)} m    Jump ${(Math.max(0,pos.y-SETTINGS.playerRadius-SETTINGS.playerHalfHeight)).toFixed(2)} m    ${state.grounded?'Grounded':'Airborne'}    ${state.goal?'Automatic: '+state.goal:''}`,20,H-12);
 if(core.events.length>eventCount){say(core.events.at(-1).message);eventCount=core.events.length;}
}
function frame(now){if(!core||paused)return;const delta=lastTime?Math.min(.12,(now-lastTime)/1000):0;lastTime=now;accumulator+=delta;let n=0;while(accumulator>=SETTINGS.step&&n++<7){core.step();accumulator-=SETTINGS.step;}render();requestAnimationFrame(frame);}
function bindHold(id,flag){const el=document.getElementById(id),on=()=>{if(flag==='left')moveLeft=true;else moveRight=true;keyMove();},off=()=>{if(flag==='left')moveLeft=false;else moveRight=false;keyMove();};el.addEventListener('pointerdown',e=>{e.preventDefault();el.setPointerCapture(e.pointerId);on();});el.addEventListener('pointerup',off);el.addEventListener('pointercancel',off);el.addEventListener('lostpointercapture',off);}
bindHold('left','left');bindHold('right','right');
document.querySelector('#ragdoll').addEventListener('click',()=>core.command({type:'PushRagdoll'}));
document.querySelector('#ragdoll-balance').addEventListener('click',()=>core.command({type:'SetRagdollMode',mode:'balance'}));
document.querySelector('#ragdoll-walk').addEventListener('click',()=>core.command({type:'SetRagdollMode',mode:'walk'}));
document.querySelector('#ragdoll-relax').addEventListener('click',()=>core.command({type:'SetRagdollMode',mode:'relax'}));
document.querySelector('#ragdoll-injure').addEventListener('click',()=>core.command({type:'InjureRagdoll',part:'leftKnee',injury:'sprain',severity:.85}));
document.querySelector('#ragdoll-heal').addEventListener('click',()=>core.command({type:'HealRagdoll'}));
document.querySelector('#jump').addEventListener('click',()=>core.command({type:'Jump'}));document.querySelector('#goal').addEventListener('click',()=>core.command({type:'Goal',intent:'crossFence'}));document.querySelector('#cancel').addEventListener('click',()=>core.command({type:'CancelGoal'}));
const setKey=(e,pressed)=>{if(e.key==='Enter'&&pressed&&!e.repeat&&!e.isComposing&&!(e.target instanceof HTMLInputElement)&&!(e.target instanceof HTMLTextAreaElement)){e.preventDefault();document.querySelector('#semantic-input').focus();return;}if(e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement)return;const k=e.key.toLowerCase();if(['arrowleft','arrowright',' ','a','d','g','escape'].includes(k))e.preventDefault();if(k==='a'||k==='arrowleft'){moveLeft=pressed;keyMove();}else if(k==='d'||k==='arrowright'){moveRight=pressed;keyMove();}else if(k===' '&&pressed&&!e.repeat)core.command({type:'Jump'});else if(k==='g'&&pressed&&!e.repeat)core.command({type:'Goal',intent:'crossFence'});else if(k==='escape'&&pressed)core.command({type:'CancelGoal'});};
window.addEventListener('keydown',e=>setKey(e,true));window.addEventListener('keyup',e=>setKey(e,false));window.addEventListener('blur',()=>{moveLeft=false;moveRight=false;keyMove();});
document.querySelector('#semantic-form').addEventListener('submit',event=>{event.preventDefault();const input=document.querySelector('#semantic-input'),text=input.value.trim().toLowerCase();if(!text)return;const result=core.textCommand(text);say(result);input.value='';input.blur();});
document.querySelector('#save').addEventListener('click',()=>{lastSave=JSON.stringify(core.snapshot());try{localStorage.setItem('world-physics-prototype-save-v3',lastSave);say('Game saved on this device.');}catch{say('Saved for this browser session.');}});
document.querySelector('#load').addEventListener('click',()=>{try{const s=lastSave||localStorage.getItem('world-physics-prototype-save-v3')||localStorage.getItem('world-physics-prototype-save-v2');if(!s){say('No saved game found.');return;}if(!core.restore(JSON.parse(s)))throw Error('Invalid state');eventCount=core.events.length;say(JSON.parse(s).version===2?'Older save restored; mannequin reset to its new rig.':'Game restored.');}catch{say('Save is invalid or unavailable.');}});
document.querySelector('#restart').addEventListener('click',()=>{core.create();eventCount=0;camera=-2;say('New game started.');});
try{await initializePhysics();core=new GameCore();status.textContent='Rapier 3D physics ready';details.textContent='3D physical world · 2D graphics · local simulation';say('Move, jump the fence, and push the crate.');window.__gameDebug={core,snapshot:()=>core.snapshot(),settings:SETTINGS};requestAnimationFrame(frame);}catch(e){status.textContent='Physics initialization failed';say(String(e.message));console.error(e);}
