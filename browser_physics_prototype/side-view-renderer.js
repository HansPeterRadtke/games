// 2D presentation adapter. It is not allowed to mutate game-world state.
const SPRITES={
 idle:'kenney/character/idle.png',walkA:'kenney/character/walk_a.png',walkB:'kenney/character/walk_b.png',jump:'kenney/character/jump.png',
 npcIdle:'kenney/character/character_green_idle.png',npcWalkA:'kenney/character/character_green_walk_a.png',npcWalkB:'kenney/character/character_green_walk_b.png',
 plank:'kenney/scenery/block_plank.png',lever:'kenney/scenery/lever.png',bush:'kenney/scenery/bush.png',rock:'kenney/scenery/rock.png',water:'kenney/scenery/water.png',bridge:'kenney/scenery/bridge_logs.png',sign:'kenney/scenery/sign.png',hills:'kenney/background_color_hills.png',clouds:'kenney/background_clouds.png'
};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export class SideViewRenderer {
 constructor(canvas){this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:false});this.images={};this.camera=-2;this.viewMode='world';
  this.mobile=matchMedia('(max-width:670px)').matches;this.width=this.mobile?640:1152;this.height=this.mobile?640:648;canvas.width=this.width;canvas.height=this.height;
  for(const [key,path] of Object.entries(SPRITES)){const image=new Image();image.src=new URL('./assets/'+path,import.meta.url).href;this.images[key]=image;}}
 setView(mode){if(!['world','lab'].includes(mode))return false;this.viewMode=mode;return true;}
 image(name,x,y,w,h){const img=this.images[name];if(!img?.complete||!img.naturalWidth)return false;this.ctx.drawImage(img,x,y,w,h);return true;}
 screen(x){return this.width*.48+(x-this.camera)*91;}
 label(text,x,y,fill='#fffdf4',font='bold 16px system-ui'){const c=this.ctx;c.font=font;c.textAlign='center';c.fillStyle='#233b39';c.fillText(text,x+1,y+2);c.fillStyle=fill;c.fillText(text,x,y);}
 ground(){const c=this.ctx,W=this.width,H=this.height,level=512,left=this.screen(22.4),right=this.screen(24.8);
  c.fillStyle='#708b70';c.fillRect(0,level,W,H-level);
  const start=clamp(left,0,W),end=clamp(right,0,W);if(end>start){c.fillStyle='#355f81';c.fillRect(start,level,end-start,H-level);c.fillStyle='#69a7be';for(let y=level+15;y<H;y+=26){c.fillRect(start,y,end-start,5);}}
  c.fillStyle='#456b4c';c.fillRect(0,level-4,Math.max(0,start),7);if(end<W)c.fillRect(end,level-4,W-end,7);
  for(let i=-40;i<75;i++){const screen=this.screen(i*3.15);if(screen<-55||screen>W+55||i*3.15>=22.4&&i*3.15<=24.8)continue;
   c.fillStyle='#3b6042';c.beginPath();c.moveTo(screen-15,level);c.lineTo(screen+7,level-26);c.lineTo(screen+18,level);c.fill();}}
 landscape(){const c=this.ctx,W=this.width,H=this.height;
  const sky=c.createLinearGradient(0,0,0,H);sky.addColorStop(0,'#94bed1');sky.addColorStop(.65,'#ded9bd');sky.addColorStop(1,'#8baa8b');c.fillStyle=sky;c.fillRect(0,0,W,H);
  for(const [name,y,h,opacity] of [['clouds',20,275,.23],['hills',90,380,.27]]){const img=this.images[name];if(img.complete&&img.naturalWidth){c.globalAlpha=opacity;c.drawImage(img,0,y,W,h);c.globalAlpha=1;}}
  c.fillStyle='#96aaa1';for(let i=-4;i<13;i++){const x=this.screen(i*4-9)*.47+W*.27;c.beginPath();c.ellipse(x,421,255,67,0,0,Math.PI*2);c.fill();}}
 landmark(e,state){const c=this.ctx,x=this.screen(e.position.x),y=512-e.position.y*91;
  switch(e.kind){
   case 'tree':{c.fillStyle='#654932';c.fillRect(x-17,278,34,235);for(const [dx,dy,r] of [[-45,305,72],[40,298,75],[0,252,82]]){c.beginPath();c.fillStyle='#496c52';c.arc(x+dx,dy,r,0,7);c.fill();}this.label(e.name,x,228,'#ebf7da');break;}
   case 'rock':{this.image('rock',x-38,512-55,76,55);this.label(e.name,x,439);break;}
   case 'plank':{const img=this.images.plank,rot=2*Math.atan2(e.rotation?.z||0,e.rotation?.w||1);c.save();c.translate(x,y);c.rotate(-rot);if(!this.image('plank',-33,-17,66,34)){c.fillStyle='#a57d49';c.fillRect(-31,-16,62,32);}c.restore();break;}
   case 'resonator':{c.fillStyle='#6d7867';c.fillRect(x-18,450,36,65);this.image('lever',x-36,430,72,72);this.label('MECHANISM',x,419);break;}
   case 'spring':{c.fillStyle='#3d88b1';c.beginPath();c.ellipse(x,510,53,12,0,0,7);c.fill();this.label('SPRING',x,477);break;}
   case 'workbench':{c.fillStyle='#927359';c.fillRect(x-45,446,90,62);c.fillStyle='#c9aa76';c.fillRect(x-55,436,110,12);this.image('sign',x+13,393,43,43);this.label(state.character.bridgeRepaired?'BRIDGE REPAIRED':'BRIDGE REPAIRS',x,384);break;}
   case 'bridge':{const l=this.screen(22.4),r=this.screen(24.8);c.fillStyle='#4c5547';c.fillRect(l-8,452,14,70);c.fillRect(r-8,452,14,70);if(e.state.repaired){c.fillStyle='#a27b50';c.fillRect(l-8,492,r-l+16,20);for(let i=0;i<6;i++){c.strokeStyle='#68472c';c.strokeRect(l+i*(r-l)/6,492,(r-l)/6,20);}}else{c.strokeStyle='#b49a78';c.lineWidth=4;c.setLineDash([17,10]);c.beginPath();c.moveTo(l+15,500);c.lineTo(r-15,500);c.stroke();c.setLineDash([]);}break;}
   case 'destination':{c.fillStyle='#9c865e';c.fillRect(x-3,448,8,66);c.fillStyle='#d2ca8c';c.fillRect(x,448,78,25);this.label('FAR BANK',x+41,440);break;}
   case 'wanderer':{const pose=e.physical?(Math.floor(state.time*7)%2?'npcWalkA':'npcWalkB'):'npcIdle';this.image(pose,x-44,512-(e.position.y-.8)*91-121,88,121);this.label('TRAVELER',x,512-(e.position.y-.8)*91-129);break;}
   default:break;
  }}
 drawRagdoll(rag){const c=this.ctx,ground=512;const lengths={torso:.76,head:.18,leftUpperArm:.48,leftForearm:.44,rightUpperArm:.48,rightForearm:.44,leftThigh:.54,leftShin:.54,rightThigh:.54,rightShin:.54};
  for(const [name,geometry] of Object.entries(lengths)){const d=rag.parts[name],p=d.position,q=d.rotation,x=this.screen(p.x),y=ground-p.y*91,angle=-2*Math.atan2(q.z,q.w);c.save();c.translate(x,y);c.rotate(angle);c.lineCap='round';c.lineWidth=(name==='torso'?.36:name==='head'?.38:name.includes('Thigh')?.27:.2)*91;c.strokeStyle=name==='head'?'#d4ad83':name==='torso'?'#3e6579':name.includes('Arm')?'#a27a60':'#647767';c.beginPath();c.moveTo(0,-geometry*91/2);c.lineTo(0,geometry*91/2);c.stroke();c.restore();}
  const x=this.screen(rag.parts.head.position.x),y=ground-rag.parts.head.position.y*91;this.label('PHYSICS LAB',x,y-31);}
 draw(state){const c=this.ctx,W=this.width,H=this.height;const p=state.player;
  const target=this.viewMode==='lab'?state.ragdoll.parts.torso.position.x+1.2:p.x-1.2;this.camera+=(target-this.camera)*.12;
  this.landscape();this.ground();
  for(const e of state.visibleEntities)this.landmark(e,state);
  const stone=this.screen(-14.12);if(stone>-60&&stone<W+60){this.image('rock',stone-26,472,52,44);}
  this.drawRagdoll(state.ragdoll);
  // The fence's drawn position comes from the simulated kinematic 3D body.
  const fx=this.screen(5.2),fy=512-(state.fence.y+.69/2)*91;
  c.fillStyle='#64736b';c.fillRect(fx-10,fy,20,63);c.fillStyle='#a8b3a4';for(let row=0;row<2;row++)c.fillRect(fx-32,fy+10+row*24,64,9);this.label('FENCE',fx,fy-13);
  const boxX=this.screen(state.crate.x),boxY=512-state.crate.y*91;
  c.fillStyle='#815c3e';c.fillRect(boxX-46,boxY-46,92,92);c.strokeStyle='#bc9468';c.lineWidth=5;c.strokeRect(boxX-44,boxY-44,88,88);c.beginPath();c.moveTo(boxX-40,boxY-40);c.lineTo(boxX+40,boxY+40);c.moveTo(boxX-40,boxY+40);c.lineTo(boxX+40,boxY-40);c.stroke();
  // A fixed photographic-style side-view sprite; 3D player position/velocity remain authoritative.
  const foot=512-(p.y-(state.playerDimensions.radius+state.playerDimensions.halfHeight))*91;c.save();c.translate(this.screen(p.x),foot);if(state.direction<0)c.scale(-1,1);
  const moving=Math.abs(state.velocity.x)>.35,pose=!state.grounded?'jump':moving?(Math.floor(state.time*7)%2?'walkA':'walkB'):'idle';if(!this.image(pose,-57,-143,114,143)){c.fillStyle='#354b5e';c.fillRect(-25,-119,50,119);}c.restore();
  c.fillStyle='#243f34';c.fillRect(0,H-32,W,32);c.fillStyle='#d8eddf';c.font='15px system-ui';c.textAlign='left';c.fillText(`Position ${p.x.toFixed(1)} m     Height ${Math.max(0,p.y-state.playerDimensions.radius-state.playerDimensions.halfHeight).toFixed(1)} m     ${state.grounded?'Grounded':'Airborne'}`,16,H-11);
 }
}
