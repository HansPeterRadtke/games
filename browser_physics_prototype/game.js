import RAPIER from './vendor/rapier.es.js';
const canvas=document.querySelector('#scene'),ctx=canvas.getContext('2d'),status=document.querySelector('#status'),message=document.querySelector('#message'),details=document.querySelector('#details');
const W=1152,H=648;canvas.width=W;canvas.height=H;
const images={};for(const [name,file] of Object.entries({player:'player.png',table:'table.png',sideboard:'sideboard.png',walk:'walk.png',hills:'kenney/background_color_hills.png',clouds:'kenney/background_clouds.png'})){const img=new Image();img.src='./assets/'+file;images[name]=img;}
let world,player,crate,fence,goal=false,moveLeft=false,moveRight=false,desiredJump=false,wasGrounded=false,lastTime=0,accumulator=0,ticks=0,cam=0,lastSave=null,active=true;
const R=()=>Math.round(player.translation().x*100)/100;
function say(v){message.textContent=v;}
function createWorld(){world=new RAPIER.World({x:0,y:-19.6,z:0});world.timestep=1/60;
 const fixed=(x,y,hx,hy,hz=0.8)=>{const b=world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(x,y,0));world.createCollider(RAPIER.ColliderDesc.cuboid(hx,hy,hz).setFriction(0.85),b);return b;};
 fixed(0,-0.35,90,0.35,1.2);fixed(-5.2,1.5,0.5,1.5);
 fence=fixed(5.2,0.75,0.12,0.75,0.8);
 const p=world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(-4.1,0.48,0).setCanSleep(false));p.lockRotations(true,true);world.createCollider(RAPIER.ColliderDesc.ball(.42).setFriction(.6).setRestitution(0),p);player=p;
 crate=world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(-0.7,0.6,0).setLinearDamping(.4).setAngularDamping(.5));crate.lockRotations(true,true);world.createCollider(RAPIER.ColliderDesc.cuboid(.57,.57,.58).setDensity(.55).setFriction(.8),crate);
 goal=false;accumulator=0;ticks=0;cam=0;wasGrounded=false;say('Push the crate, then jump over the fence.');}
const groundCheck=()=>{const p=player.translation();const q=world.castRay(new RAPIER.Ray({x:p.x,y:p.y-.34,z:0},{x:0,y:-1,z:0}),.18,true,undefined,undefined,undefined,player);return !!q;};
function tick(){const p=player.translation(),v=player.linvel();let dir=(moveRight?1:0)-(moveLeft?1:0);
 if(goal && dir===0){if(p.x>6.1){goal=false;say('You crossed the fence.');}else{dir=1;if(p.x>3.4 && p.x<5.7 && groundCheck())desiredJump=true;}}
 const grounded=groundCheck();const target=dir*5.1;player.setLinvel({x:target,y:v.y,z:0},true);
 if(desiredJump&&grounded){player.applyImpulse({x:0,y:8.5,z:0},true);say('Jump!');}desiredJump=false;
 world.step();ticks++;wasGrounded=grounded;const now=player.translation();if(now.y < -5){player.setTranslation({x:-4.1,y:1,z:0},true);player.setLinvel({x:0,y:0,z:0},true);say('Back to the clearing.');}
 if(now.x>6.1 && !goal) say('Across the fence! You can continue exploring.');}
function imageDraw(name,x,y,w,h){const im=images[name];if(!im?.complete||!im.naturalWidth)return false;ctx.drawImage(im,x,y,w,h);return true;}
function draw(){ctx.clearRect(0,0,W,H);const x=player.translation().x,px=(u)=>W*.48+(u-cam)*91;cam+=(x+1-cam)*.085;
 const sky=ctx.createLinearGradient(0,0,0,H);sky.addColorStop(0,'#8eb6c6');sky.addColorStop(.66,'#e0d5b7');sky.addColorStop(1,'#73846a');ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);
 if(images.hills.complete&&images.hills.naturalWidth){ctx.globalAlpha=.28;ctx.drawImage(images.hills,0,90,W,425);ctx.globalAlpha=1;}if(images.clouds.complete&&images.clouds.naturalWidth){ctx.globalAlpha=.2;ctx.drawImage(images.clouds,0,50,W,260);ctx.globalAlpha=1;}ctx.fillStyle='#98a9a0';for(let i=-3;i<11;i++){const center=px(i*4-7)*.45+W*.25;ctx.beginPath();ctx.ellipse(center,420,230,70,0,0,Math.PI*2);ctx.fill();}
 ctx.fillStyle='#748874';ctx.fillRect(0,512,W,136);ctx.fillStyle='#536956';ctx.fillRect(0,510,W,7);
 for(let i=-18;i<48;i++){const screen=px(i*2.9);if(screen<-90||screen>W+90)continue;ctx.fillStyle='#334d36';ctx.beginPath();ctx.moveTo(screen-17,510);ctx.lineTo(screen+7,478);ctx.lineTo(screen+22,510);ctx.fill();}
 const ground=512; const cx=px(crate.translation().x),cy=ground-crate.translation().y*91;
 ctx.fillStyle='#6c4d34';ctx.fillRect(cx-51,cy-52,102,104);ctx.strokeStyle='#d3b185';ctx.lineWidth=6;ctx.strokeRect(cx-49,cy-50,98,100);ctx.beginPath();ctx.moveTo(cx-44,cy-45);ctx.lineTo(cx+44,cy+45);ctx.moveTo(cx+44,cy-45);ctx.lineTo(cx-44,cy+45);ctx.stroke();
 const fenceX=px(5.2);ctx.fillStyle='#5b6260';ctx.fillRect(fenceX-12,375,24,142);ctx.fillStyle='#89928e';for(let j=0;j<3;j++)ctx.fillRect(fenceX-64,397+j*47,128,12);
 const p=player.translation(),sx=px(p.x),sy=ground-p.y*91;ctx.save();ctx.translate(sx,sy-2);if(player.linvel().x<-.2)ctx.scale(-1,1);if(!imageDraw('player',-36,-111,72,111)){ctx.fillStyle='#2e3a4b';ctx.fillRect(-23,-93,46,90);ctx.fillStyle='#cfad88';ctx.beginPath();ctx.arc(0,-105,20,0,7);ctx.fill();}ctx.restore();
 ctx.fillStyle='#dcead8';ctx.font='bold 17px system-ui';ctx.textAlign='center';ctx.fillText('CRATE',cx,cy-64);ctx.fillText('FENCE',fenceX,362);
 ctx.fillStyle='#263c32';ctx.fillRect(0,H-32,W,32);ctx.fillStyle='#d4ebd8';ctx.font='15px system-ui';ctx.textAlign='left';ctx.fillText('Position '+p.x.toFixed(1)+' m    Height '+Math.max(0,p.y-.42).toFixed(1)+' m',20,H-11);
}
function frame(time){if(!active)return;const elapsed=Math.min(.12,(time-lastTime)/1000||0);lastTime=time;accumulator+=elapsed;let count=0;while(accumulator>=1/60&&count++<7){tick();accumulator-=1/60;}draw();requestAnimationFrame(frame);}
function stopGoal(){if(goal){goal=false;say('Automatic movement cancelled.');}}
function hold(id,flag){const el=document.getElementById(id);el.addEventListener('pointerdown',ev=>{ev.preventDefault();el.setPointerCapture(ev.pointerId);stopGoal();if(flag==='left')moveLeft=true;else moveRight=true;});const release=()=>{if(flag==='left')moveLeft=false;else moveRight=false;};el.addEventListener('pointerup',release);el.addEventListener('pointercancel',release);el.addEventListener('lostpointercapture',release);}
hold('left','left');hold('right','right');
function jump(){desiredJump=true;}document.querySelector('#jump').addEventListener('click',jump);document.querySelector('#goal').addEventListener('click',()=>{goal=true;say('Crossing the fence — manual movement interrupts.');});document.querySelector('#cancel').addEventListener('click',stopGoal);
const keyEvent=(e,down)=>{if(e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement)return;const k=e.key.toLowerCase();if(['arrowleft','arrowright',' ','a','d','g','escape'].includes(k))e.preventDefault();if(k==='a'||k==='arrowleft'){moveLeft=down;if(down)stopGoal();}if(k==='d'||k==='arrowright'){moveRight=down;if(down)stopGoal();}if(k===' '&&down&&!e.repeat)jump();if(k==='g'&&down){goal=true;say('Crossing the fence…');}if(k==='escape'&&down)stopGoal();};window.addEventListener('keydown',e=>keyEvent(e,true));window.addEventListener('keyup',e=>keyEvent(e,false));window.addEventListener('blur',()=>{moveLeft=false;moveRight=false;});
function savedState(){return{version:1,ticks,player:{p:player.translation(),v:player.linvel()},crate:{p:crate.translation(),v:crate.linvel()},goal};}
function applyState(s){if(s?.version!==1||!s.player?.p||!s.crate?.p||!Number.isFinite(s.player.p.x)||!Number.isFinite(s.crate.p.x))throw Error('Invalid save');for(const [body,data] of [[player,s.player],[crate,s.crate]]){body.setTranslation(data.p,true);body.setLinvel(data.v,true);}ticks=s.ticks||0;goal=!!s.goal;}
document.querySelector('#save').addEventListener('click',()=>{lastSave=JSON.stringify(savedState());try{localStorage.setItem('world-physics-prototype-save-v1',lastSave);say('Game saved on this device.');}catch{say('Saved for this browser session.');}});
document.querySelector('#load').addEventListener('click',()=>{try{const s=lastSave||localStorage.getItem('world-physics-prototype-save-v1');if(!s){say('No save yet.');return;}applyState(JSON.parse(s));say('Saved game restored.');}catch{say('Saved game could not be loaded.');}});
document.querySelector('#restart').addEventListener('click',()=>{createWorld();say('New game started.');});
try{await RAPIER.init();createWorld();status.textContent='Physics ready · Local simulation';details.textContent='Rapier 3D physics · Canvas 2D · no network needed during play';requestAnimationFrame(frame);}catch(err){status.textContent='Physics failed';say('Could not initialize physics: '+err.message);console.error(err);}
