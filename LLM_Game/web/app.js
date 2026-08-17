'use strict';

const BUILD='20260817-umzug-stable-v34';
const MODEL_CONTEXT_LABEL='context 8192';
const ROOM={w:1400,h:860};
const WORLD_ROOM_CAP=10;
const ROOM_CONTENT_CAP=12;
const SAVE_KEY='prse-umzug-v29';
const COMMAND_HISTORY_KEY='prse-command-history-v1';

const canvas=document.getElementById('game');
const ctx=canvas.getContext('2d');
const mapCanvas=document.getElementById('minimap');
const mapCtx=mapCanvas.getContext('2d');
const storyEl=document.getElementById('story');
const eventsEl=document.getElementById('events');
const stateEl=document.getElementById('state');
const statsEl=document.getElementById('stats');
const resultEl=document.getElementById('result');
const actionEl=document.getElementById('action');
const roomLabelEl=document.getElementById('room-label');
const debugEl=document.getElementById('debug');
const transcriptScrollEl=document.getElementById('transcript-scroll');
const healthTextEl=document.getElementById('health-text'),healthFillEl=document.getElementById('health-fill');

const roleColors={
  player:'#e8d65c', prop:'#8e8172', item:'#d7b84d', npc:'#70bfd0',
  hazard:'#cd5555', treasure:'#df9d48', mechanism:'#7996bd', door:'#71b27a'
};

let W=innerWidth,H=innerHeight,DPR=1,lastFrame=performance.now(),lastUserActionAt=Date.now();
let world=null,scenarioRecord=null,gameMinute=0,eventSeq=0,llmBusy=false,backgroundBusy=false,storyBusy=false;
let visitedRooms=new Set(),refinedRooms=new Set(),backgroundTimer=null,storyEventTimer=null;
let exploredCells={};
let commandHistory=[],commandHistoryIndex=0,commandHistoryDraft='';
const EXP_COLS=14,EXP_ROWS=9;
const keys=new Set();

const player={
  room:'roomA',x:300,y:430,lastX:300,lastY:430,vx:0,vy:0,
  facingX:1,facingY:0,
  shape:{type:'cross',width:44,height:44,thickness:14},
  speed:185,interactionReach:26,speechReach:165,
  state:{health:100}
};

const stick={active:false,id:null,dx:0,dy:0,max:38};

function clamp(v,a,b){v=Number(v);return Number.isFinite(v)?Math.max(a,Math.min(b,v)):(a+b)/2}
function safeText(v,n=500){return String(v??'').slice(0,n)}
function loadCommandHistory(){try{const v=JSON.parse(localStorage.getItem(COMMAND_HISTORY_KEY)||'[]');commandHistory=Array.isArray(v)?v.map(x=>safeText(x,500)).filter(Boolean).slice(-300):[]}catch{commandHistory=[]}commandHistoryIndex=commandHistory.length;commandHistoryDraft=''}
function saveCommandHistory(){try{localStorage.setItem(COMMAND_HISTORY_KEY,JSON.stringify(commandHistory.slice(-300)))}catch{}}
function rememberCommand(text){const v=safeText(text,500).trim();if(!v)return;if(commandHistory[commandHistory.length-1]!==v)commandHistory.push(v);commandHistory=commandHistory.slice(-300);commandHistoryIndex=commandHistory.length;commandHistoryDraft='';saveCommandHistory()}
function navigateCommandHistory(dir){if(!commandHistory.length&&dir<0)return;if(commandHistoryIndex===commandHistory.length)commandHistoryDraft=actionEl.value;commandHistoryIndex=clamp(commandHistoryIndex+dir,0,commandHistory.length);actionEl.value=commandHistoryIndex===commandHistory.length?commandHistoryDraft:commandHistory[commandHistoryIndex];requestAnimationFrame(()=>actionEl.setSelectionRange(actionEl.value.length,actionEl.value.length))}
function directionName(dx,dy){
  const a=Math.atan2(dy,dx)*180/Math.PI;
  if(a>=-22.5&&a<22.5)return'east/right'; if(a<67.5&&a>=22.5)return'southeast/down-right';
  if(a<112.5&&a>=67.5)return'south/down'; if(a<157.5&&a>=112.5)return'southwest/down-left';
  if(a>=157.5||a<-157.5)return'west/left'; if(a<-112.5)return'northwest/up-left';
  if(a<-67.5)return'north/up'; return'northeast/up-right';
}

function normalizeShape(raw,role='prop'){
  const s=raw&&typeof raw==='object'?{...raw}:{};
  const type=['rect','circle','capsule','polygon','cross'].includes(String(s.type))?String(s.type):(role==='npc'?'circle':'rect');
  if(type==='circle')return{type,radius:clamp(s.radius??24,6,90)};
  if(type==='capsule')return{type,width:clamp(s.width??40,10,160),height:clamp(s.height??56,10,180)};
  if(type==='cross')return{type,width:clamp(s.width??44,12,160),height:clamp(s.height??44,12,160),thickness:clamp(s.thickness??14,4,80)};
  if(type==='polygon'){
    const pts=Array.isArray(s.points)?s.points.slice(0,12).map(p=>[clamp(p?.[0],-100,100),clamp(p?.[1],-100,100)]):[];
    if(pts.length>=3)return{type,points:pts};
  }
  return{type:'rect',width:clamp(s.width??48,8,180),height:clamp(s.height??48,8,180)};
}

function rectPoly(cx,cy,w,h){return[[cx-w/2,cy-h/2],[cx+w/2,cy-h/2],[cx+w/2,cy+h/2],[cx-w/2,cy+h/2]]}
function circlePoly(cx,cy,r,n=16){return Array.from({length:n},(_,i)=>{const a=i*Math.PI*2/n;return[cx+Math.cos(a)*r,cy+Math.sin(a)*r]})}
function capsulePoly(cx,cy,w,h){
  if(Math.abs(w-h)<1)return circlePoly(cx,cy,w/2,18);
  const pts=[];
  if(h>=w){const r=w/2,half=(h-w)/2;for(let i=0;i<=8;i++){const a=Math.PI+i*Math.PI/8;pts.push([cx+Math.cos(a)*r,cy-half+Math.sin(a)*r])}for(let i=0;i<=8;i++){const a=i*Math.PI/8;pts.push([cx+Math.cos(a)*r,cy+half+Math.sin(a)*r])}}
  else{const r=h/2,half=(w-h)/2;for(let i=0;i<=8;i++){const a=Math.PI/2+i*Math.PI/8;pts.push([cx-half+Math.cos(a)*r,cy+Math.sin(a)*r])}for(let i=0;i<=8;i++){const a=-Math.PI/2+i*Math.PI/8;pts.push([cx+half+Math.cos(a)*r,cy+Math.sin(a)*r])}}
  return pts;
}
function shapeParts(shape,cx,cy){
  const s=normalizeShape(shape);
  if(s.type==='rect')return[rectPoly(cx,cy,s.width,s.height)];
  if(s.type==='circle')return[circlePoly(cx,cy,s.radius)];
  if(s.type==='capsule')return[capsulePoly(cx,cy,s.width,s.height)];
  if(s.type==='polygon')return[s.points.map(([x,y])=>[cx+x,cy+y])];
  if(s.type==='cross'){
    const t=Math.min(s.thickness,s.width,s.height);
    return[rectPoly(cx,cy,t,s.height),rectPoly(cx,cy,s.width,t)];
  }
  return[rectPoly(cx,cy,48,48)];
}
function polyAxes(poly){const a=[];for(let i=0;i<poly.length;i++){const p=poly[i],q=poly[(i+1)%poly.length],dx=q[0]-p[0],dy=q[1]-p[1],n=Math.hypot(dx,dy)||1;a.push([-dy/n,dx/n])}return a}
function project(poly,axis){let lo=Infinity,hi=-Infinity;for(const p of poly){const v=p[0]*axis[0]+p[1]*axis[1];lo=Math.min(lo,v);hi=Math.max(hi,v)}return[lo,hi]}
function polysCollide(a,b){for(const axis of [...polyAxes(a),...polyAxes(b)]){const A=project(a,axis),B=project(b,axis);if(A[1]<B[0]||B[1]<A[0])return false}return true}
function polyCenter(poly){let x=0,y=0;for(const p of poly){x+=p[0];y+=p[1]}return{x:x/poly.length,y:y/poly.length}}
function polyCollisionNormal(a,b){let best=null,bestOverlap=Infinity;for(const axis0 of [...polyAxes(a),...polyAxes(b)]){let axis=[axis0[0],axis0[1]],A=project(a,axis),B=project(b,axis),overlap=Math.min(A[1],B[1])-Math.max(A[0],B[0]);if(overlap<=0)return null;if(overlap<bestOverlap){const ca=polyCenter(a),cb=polyCenter(b);if((ca.x-cb.x)*axis[0]+(ca.y-cb.y)*axis[1]<0)axis=[-axis[0],-axis[1]];best=axis;bestOverlap=overlap}}return best}
function shapeCollisionNormal(sa,ax,ay,sb,bx,by){let best=null,bestOverlap=Infinity;for(const a of shapeParts(sa,ax,ay))for(const b of shapeParts(sb,bx,by)){let overlapMin=Infinity,normal=null,colliding=true;for(const axis0 of [...polyAxes(a),...polyAxes(b)]){let axis=[axis0[0],axis0[1]],A=project(a,axis),B=project(b,axis),overlap=Math.min(A[1],B[1])-Math.max(A[0],B[0]);if(overlap<=0){colliding=false;break}if(overlap<overlapMin){const ca=polyCenter(a),cb=polyCenter(b);if((ca.x-cb.x)*axis[0]+(ca.y-cb.y)*axis[1]<0)axis=[-axis[0],-axis[1]];overlapMin=overlap;normal=axis}}if(colliding&&overlapMin<bestOverlap){bestOverlap=overlapMin;best=normal}}return best}
function shapesCollide(sa,ax,ay,sb,bx,by){for(const a of shapeParts(sa,ax,ay))for(const b of shapeParts(sb,bx,by))if(polysCollide(a,b))return true;return false}
function pointSegDistance(px,py,a,b){const vx=b[0]-a[0],vy=b[1]-a[1],l=vx*vx+vy*vy;if(!l)return Math.hypot(px-a[0],py-a[1]);const t=clamp(((px-a[0])*vx+(py-a[1])*vy)/l,0,1);return Math.hypot(px-(a[0]+t*vx),py-(a[1]+t*vy))}
function polyDistance(a,b){if(polysCollide(a,b))return 0;let d=Infinity;for(const p of a)for(let i=0;i<b.length;i++)d=Math.min(d,pointSegDistance(p[0],p[1],b[i],b[(i+1)%b.length]));for(const p of b)for(let i=0;i<a.length;i++)d=Math.min(d,pointSegDistance(p[0],p[1],a[i],a[(i+1)%a.length]));return d}
function shapeDistance(sa,ax,ay,sb,bx,by){let d=Infinity;for(const a of shapeParts(sa,ax,ay))for(const b of shapeParts(sb,bx,by))d=Math.min(d,polyDistance(a,b));return d}
function shapeBounds(shape,cx,cy){const pts=shapeParts(shape,cx,cy).flat();return{x0:Math.min(...pts.map(p=>p[0])),x1:Math.max(...pts.map(p=>p[0])),y0:Math.min(...pts.map(p=>p[1])),y1:Math.max(...pts.map(p=>p[1]))}}

function normalizeActor(raw){if(!raw||typeof raw!=='object')return null;return{goal:safeText(raw.goal||'',300),plan:Array.isArray(raw.plan)?raw.plan.slice(0,16).map(x=>x&&typeof x==='object'?{...x}:{}):Array.isArray(raw.steps)?raw.steps.slice(0,16).map(x=>x&&typeof x==='object'?{...x}:{}):[],index:clamp(raw.index??0,0,16),awaitingReply:!!raw.awaitingReply,replyDeadline:Number(raw.replyDeadline)||0,lastReply:safeText(raw.lastReply||'',500),memory:Array.isArray(raw.memory)?raw.memory.map(x=>safeText(x,240)).slice(-12):[],stepStartedAt:Number(raw.stepStartedAt)||0,lastEventAt:Number(raw.lastEventAt)||0}}
function normalizeObject(raw,index=0){
  const role=['prop','item','npc','hazard','treasure','mechanism'].includes(String(raw?.role))?String(raw.role):'prop';
  const interaction=raw?.interaction&&typeof raw.interaction==='object'?raw.interaction:{};
  const motion=raw?.motion&&typeof raw.motion==='object'?raw.motion:{};
  return{
    id:safeText(raw?.id||`obj_${index}`,50),name:safeText(raw?.name||`Objekt ${index}`,80),role,
    description:safeText(raw?.description||'',700),affordances:Array.isArray(raw?.affordances)?raw.affordances.map(x=>safeText(x,80)).slice(0,12):[],
    state:raw?.state&&typeof raw.state==='object'?{...raw.state}:{},
    shape:normalizeShape(raw?.shape,role),solid:!!raw?.solid,pushable:!!raw?.pushable,
    interactionReach:clamp(raw?.interaction_reach??interaction.reach??24,0,180),
    speechReach:clamp(raw?.speech_reach??interaction.speech_reach??160,0,500),
    semantic:{x:clamp(raw?.x,30,ROOM.w-30),y:clamp(raw?.y,30,ROOM.h-30),vx:Number(raw?.vx)||0,vy:Number(raw?.vy)||0,active:raw?.active!==false},
    physical:{x:clamp(raw?.x,30,ROOM.w-30),y:clamp(raw?.y,30,ROOM.h-30),vx:Number(raw?.vx)||0,vy:Number(raw?.vy)||0,materialized:false},
    motion:{type:safeText(motion.type||'idle',30),speed:clamp(motion.speed??0,0,260),radius:clamp(motion.radius??120,0,500),damage:clamp(motion.damage??0,0,100),target:safeText(motion.target||'player',50)},
    actor:normalizeActor(raw?.actor||raw?.state?.actor),
    doorTo:raw?.door_to||null,spawn:raw?.spawn||null
  };
}
function normalizeDoor(raw,fromRoom,roomsById){
  const to=safeText(raw?.to,50),target=roomsById.get(to);
  return normalizeObject({
    id:raw?.id||`door_${fromRoom}_${to}`,name:raw?.name||`Durchgang zu ${target?.name||to}`,role:'mechanism',
    description:raw?.description||'',x:raw?.x??1320,y:raw?.y??430,solid:false,pushable:false,
    shape:raw?.shape||{type:'rect',width:58,height:72},interaction_reach:raw?.interaction_reach??30,
    affordances:['enter'],state:{door:true},door_to:to,
    spawn:null
  });
}
function applyPlayerDefinition(raw){
  if(!raw||typeof raw!=='object')return;
  player.shape=normalizeShape(raw.shape||player.shape,'player');
  player.speed=clamp(raw.speed??player.speed,50,320);
  player.interactionReach=clamp(raw.interaction_reach??player.interactionReach,0,180);
  player.speechReach=clamp(raw.speech_reach??player.speechReach,20,500);
  if(raw.state&&typeof raw.state==='object')player.state={...player.state,...raw.state};
}
function buildWorld(scenario){
  const rooms={},rawRooms=Array.isArray(scenario?.rooms)?scenario.rooms:[];
  const map=new Map(rawRooms.map(r=>[String(r.id),r]));
  for(const rr of rawRooms){rooms[String(rr.id)]={id:String(rr.id),name:safeText(rr.name||rr.id,100),description:safeText(rr.description||'',1000),objects:(rr.objects||[]).slice(0,ROOM_CONTENT_CAP).map(normalizeObject),topologyExpansions:Number(rr.topology_expansions)||0,topologyClosed:!!rr.topology_closed}}
  for(const rr of rawRooms){const r=rooms[String(rr.id)];for(const d of rr.doors||[]){if(!rooms[String(d.to)])continue;const o=normalizeDoor(d,String(rr.id),map);const back=(map.get(String(d.to))?.doors||[]).find(x=>String(x.to)===String(rr.id));if(back){const bx=clamp(back.x,50,ROOM.w-50),by=clamp(back.y,50,ROOM.h-50),edge=Math.min(bx,ROOM.w-bx,by,ROOM.h-by);o.spawn=edge===bx?{x:bx+90,y:by}:edge===ROOM.w-bx?{x:bx-90,y:by}:edge===by?{x:bx,y:by+90}:{x:bx,y:by-90}}else o.spawn={x:120,y:430};r.objects.push(o)}}
  applyPlayerDefinition(scenario?.player);
  const first=rawRooms[0]?.id||'roomA';player.room=rooms[player.room]?player.room:String(first);
  return{scenario,rooms,inventory:[],events:[],scheduledEvents:[],goal:safeText(scenario?.goal||'Erkunde die Umgebung.',500),goalComplete:false,created:0};
}

function room(){return world.rooms[player.room]}
function obj(id){for(const r of Object.values(world.rooms)){const o=r.objects.find(x=>x.id===id);if(o)return o}return null}
function activeRoomObjects(){return room().objects.filter(o=>o.semantic.active)}
function materialize(o){o.physical.x=o.semantic.x;o.physical.y=o.semantic.y;o.physical.vx=o.semantic.vx;o.physical.vy=o.semantic.vy;o.physical.materialized=true}
function dematerialize(o){o.semantic.x=o.physical.x;o.semantic.y=o.physical.y;o.semantic.vx=o.physical.vx;o.semantic.vy=o.physical.vy;o.physical.materialized=false}
function centerDistance(o){return Math.hypot(o.semantic.x-player.x,o.semantic.y-player.y)}
function perceptionRadius(){return clamp(world?.scenario?.player?.perception_radius??330,160,700)}
function inPerception(o){return o.semantic.active&&centerDistance(o)<=perceptionRadius()}
function syncPerception(){for(const [rid,r] of Object.entries(world.rooms))for(const o of r.objects){if(rid===player.room&&inPerception(o)){if(!o.physical.materialized)materialize(o)}else if(o.physical.materialized)dematerialize(o)}}
function edgeDistanceToPlayer(o){const x=o.physical.materialized?o.physical.x:o.semantic.x,y=o.physical.materialized?o.physical.y:o.semantic.y;return shapeDistance(player.shape,player.x,player.y,o.shape,x,y)}
function touching(o){return edgeDistanceToPlayer(o)<=1.5}
function interactionReach(o){return Math.max(player.interactionReach,o.interactionReach)}
function canInteract(o){return o.semantic.active&&edgeDistanceToPlayer(o)<=interactionReach(o)}
function canHear(o){return o.role==='npc'&&o.semantic.active&&edgeDistanceToPlayer(o)<=Math.max(player.speechReach,o.speechReach)}

function playerCollisionAt(x,y,ignore=null){for(const o of activeRoomObjects()){if(o===ignore||!o.physical.materialized||!o.solid)continue;if(shapesCollide(player.shape,x,y,o.shape,o.physical.x,o.physical.y))return o}return null}
function objectCollisionAt(o,x,y){const b=shapeBounds(o.shape,x,y);if(b.x0<18||b.x1>ROOM.w-18||b.y0<18||b.y1>ROOM.h-18)return{kind:'wall',normal:b.x0<18?[1,0]:b.x1>ROOM.w-18?[-1,0]:b.y0<18?[0,1]:[0,-1]};if(shapesCollide(o.shape,x,y,player.shape,player.x,player.y))return{kind:'player',shape:player.shape,x:player.x,y:player.y};for(const q of activeRoomObjects()){if(q===o||!q.physical.materialized||!q.solid)continue;if(shapesCollide(o.shape,x,y,q.shape,q.physical.x,q.physical.y))return{kind:'object',object:q,shape:q.shape,x:q.physical.x,y:q.physical.y}}return null}
function objectBlockedAt(o,x,y){return!!objectCollisionAt(o,x,y)}
function projectSlide(dx,dy,n){const into=dx*n[0]+dy*n[1];if(into>=0)return[dx,dy];return[dx-n[0]*into,dy-n[1]*into]}
function rotatedStep(dx,dy,deg){const a=deg*Math.PI/180,c=Math.cos(a),sn=Math.sin(a);return[dx*c-dy*sn,dx*sn+dy*c]}
function tryPlayerSubstep(dx,dy){let nx=clamp(player.x+dx,20,ROOM.w-20),ny=clamp(player.y+dy,20,ROOM.h-20),hit=playerCollisionAt(nx,ny);if(!hit){player.x=nx;player.y=ny;return true}if(hit.pushable){const tx=hit.physical.x+dx,ty=hit.physical.y+dy;if(!objectBlockedAt(hit,tx,ty)){hit.physical.x=tx;hit.physical.y=ty;hit.semantic.x=tx;hit.semantic.y=ty;player.x=nx;player.y=ny;return true}}
  const n=shapeCollisionNormal(player.shape,nx,ny,hit.shape,hit.physical.x,hit.physical.y)||(()=>{const vx=player.x-hit.physical.x,vy=player.y-hit.physical.y,m=Math.hypot(vx,vy)||1;return[vx/m,vy/m]})();const [sx,sy]=projectSlide(dx,dy,n);if(Math.hypot(sx,sy)>.001){nx=clamp(player.x+sx,20,ROOM.w-20);ny=clamp(player.y+sy,20,ROOM.h-20);if(!playerCollisionAt(nx,ny)){player.x=nx;player.y=ny;return true}}
  // Slippery-contact fallback: find the smallest angular deflection that remains collision-free.
  for(const deg of [15,-15,30,-30,45,-45,60,-60,75,-75,90,-90]){const [ax,ay]=rotatedStep(dx,dy,deg);nx=clamp(player.x+ax,20,ROOM.w-20);ny=clamp(player.y+ay,20,ROOM.h-20);if(!playerCollisionAt(nx,ny)){player.x=nx;player.y=ny;return true}}const opts=[[dx,0],[0,dy]].sort((a,b)=>Math.hypot(b[0],b[1])-Math.hypot(a[0],a[1]));for(const [ax,ay] of opts){if(Math.hypot(ax,ay)<.001)continue;nx=clamp(player.x+ax,20,ROOM.w-20);ny=clamp(player.y+ay,20,ROOM.h-20);if(!playerCollisionAt(nx,ny)){player.x=nx;player.y=ny;return true}}return false}
function tryMove(dx,dy){player.lastX=player.x;player.lastY=player.y;player.vx=dx;player.vy=dy;if(Math.hypot(dx,dy)>.01){const n=Math.hypot(dx,dy);player.facingX=dx/n;player.facingY=dy/n}const steps=Math.max(1,Math.ceil(Math.hypot(dx,dy)/4)),sx=dx/steps,sy=dy/steps;for(let i=0;i<steps;i++)tryPlayerSubstep(sx,sy)}
function tryObjectSubstep(o,dx,dy){let nx=o.physical.x+dx,ny=o.physical.y+dy,hit=objectCollisionAt(o,nx,ny);if(!hit){o.physical.x=nx;o.physical.y=ny;o.semantic.x=nx;o.semantic.y=ny;return true}let n=hit.normal;if(!n&&hit.shape)n=shapeCollisionNormal(o.shape,nx,ny,hit.shape,hit.x,hit.y);if(!n){const vx=o.physical.x-(hit.x??o.physical.x),vy=o.physical.y-(hit.y??o.physical.y),m=Math.hypot(vx,vy)||1;n=[vx/m,vy/m]}const [sx,sy]=projectSlide(dx,dy,n);if(Math.hypot(sx,sy)>.001){nx=o.physical.x+sx;ny=o.physical.y+sy;if(!objectCollisionAt(o,nx,ny)){o.physical.x=nx;o.physical.y=ny;o.semantic.x=nx;o.semantic.y=ny;return true}}return false}
function moveObjectSliding(o,dx,dy){const steps=Math.max(1,Math.ceil(Math.hypot(dx,dy)/4)),sx=dx/steps,sy=dy/steps;let moved=false;for(let i=0;i<steps;i++)moved=tryObjectSubstep(o,sx,sy)||moved;return moved}
function inputVec(){let x=0,y=0;if(keys.has('a')||keys.has('arrowleft'))x--;if(keys.has('d')||keys.has('arrowright'))x++;if(keys.has('w')||keys.has('arrowup'))y--;if(keys.has('s')||keys.has('arrowdown'))y++;if(stick.active){x+=stick.dx/stick.max;y+=stick.dy/stick.max}const n=Math.hypot(x,y)||1;return{x:x/n,y:y/n}}

function moveToward(o,tx,ty,speed,dt,away=false,stopDistance=0){let dx=tx-o.physical.x,dy=ty-o.physical.y,n=Math.hypot(dx,dy)||1;if(!away&&n<=stopDistance)return false;if(away){dx=-dx;dy=-dy}return moveObjectSliding(o,dx/n*speed*dt,dy/n*speed*dt)}
function actorState(o){if(!o.actor)o.actor=normalizeActor({goal:'',steps:[]});return o.actor}
function advanceActor(o){const a=actorState(o);a.index=Math.min(a.plan.length,a.index+1);a.stepStartedAt=0;a.awaitingReply=false;a.replyDeadline=0}
function actorTarget(step){if(step.target_id==='player'||step.target==='player')return{kind:'player',x:player.x,y:player.y,shape:player.shape};const t=obj(step.target_id||step.target);if(t&&t.semantic.active&&t.physical.materialized)return{kind:'object',object:t,x:t.physical.x,y:t.physical.y,shape:t.shape};if(Number.isFinite(Number(step.x))&&Number.isFinite(Number(step.y)))return{kind:'point',x:clamp(step.x,20,ROOM.w-20),y:clamp(step.y,20,ROOM.h-20),shape:null};return null}
function actorCanPerceivePlayer(o){return o.physical.materialized&&shapeDistance(o.shape,o.physical.x,o.physical.y,player.shape,player.x,player.y)<=Math.max(o.speechReach,240)}
function runActorPlan(o,dt){const a=o.actor;if(!a||!Array.isArray(a.plan)||a.index>=a.plan.length)return false;const step=a.plan[a.index]||{},type=safeText(step.type,30),now=Date.now();
  if(a.awaitingReply){if(a.replyDeadline&&now>=a.replyDeadline){a.awaitingReply=false;a.replyDeadline=0;advanceActor(o)}return true}
  if(type==='move_to'){const t=actorTarget(step);if(!t){advanceActor(o);return true}const desired=clamp(step.distance??(t.kind==='player'?Math.max(24,o.speechReach*.55):Math.max(12,o.interactionReach)),0,300),gap=t.kind==='point'?Math.hypot(o.physical.x-t.x,o.physical.y-t.y):shapeDistance(o.shape,o.physical.x,o.physical.y,t.shape,t.x,t.y);if(gap<=desired){advanceActor(o);return true}moveToward(o,t.x,t.y,clamp(step.speed??o.motion.speed??70,15,200),dt,false,0);return true}
  if(type==='say'){const text=safeText(step.text,600).trim();if(!text){advanceActor(o);return true}if(!canHear(o))return true;addTranscript('npc',`${o.name}: ${text}`);eventLog(`${o.name}: ${text}`);a.lastEventAt=now;if(step.wait_for_reply){a.awaitingReply=true;a.replyDeadline=now+clamp(step.timeout_seconds??25,3,180)*1000}else advanceActor(o);saveGame();return true}
  if(type==='interact'){const t=obj(step.target_id);if(!t||!t.semantic.active){advanceActor(o);return true}const gap=shapeDistance(o.shape,o.physical.x,o.physical.y,t.shape,t.physical.x,t.physical.y),reach=Math.max(18,o.interactionReach,t.interactionReach);if(gap>reach){moveToward(o,t.physical.x,t.physical.y,clamp(step.speed??70,15,180),dt,false,0);return true}if(step.target_patch&&typeof step.target_patch==='object')sanitizeObjectPatch(t,step.target_patch);if(step.target_move&&typeof step.target_move==='object'){const mv=step.target_move;if('x'in mv||'y'in mv){const nx=clamp(mv.x??t.physical.x,20,ROOM.w-20),ny=clamp(mv.y??t.physical.y,20,ROOM.h-20),dx=nx-t.physical.x,dy=ny-t.physical.y;moveObjectSliding(t,dx,dy)}else moveObjectSliding(t,Number(mv.dx)||0,Number(mv.dy)||0);t.semantic.x=t.physical.x;t.semantic.y=t.physical.y}const verb=safeText(step.verb||'interagiert mit',100),msg=safeText(step.text||`${o.name} ${verb} ${t.name}.`,500);if(msg&&((o.physical.materialized&&edgeDistanceToPlayer(o)<perceptionRadius())||(t.physical.materialized&&edgeDistanceToPlayer(t)<perceptionRadius()))){addTranscript('world',msg);eventLog(msg)}advanceActor(o);saveGame();return true}
  if(type==='wait'){if(!a.stepStartedAt)a.stepStartedAt=now;if(now-a.stepStartedAt>=clamp(step.seconds??2,.1,300)*1000)advanceActor(o);return true}
  if(type==='set_state'){if(step.patch&&typeof step.patch==='object')o.state={...o.state,...step.patch};advanceActor(o);saveGame();return true}
  advanceActor(o);return true}
function notifyActorsOfPlayerCommand(text){for(const o of activeRoomObjects()){if(o.role!=='npc'||!o.actor?.awaitingReply||!canHear(o))continue;o.actor.lastReply=safeText(text,500);o.actor.memory=[...(o.actor.memory||[]),`Spieler: ${safeText(text,220)}`].slice(-12);advanceActor(o)}}
function runScheduledEvents(){if(!world?.scheduledEvents?.length)return;const now=Date.now(),keep=[];for(const e of world.scheduledEvents){if(Number(e.at)>now){keep.push(e);continue}const actor=e.actor_id?obj(e.actor_id):null;if(actor&&(!actor.physical.materialized||(!canHear(actor)&&edgeDistanceToPlayer(actor)>perceptionRadius()))){if((e.defer_count||0)<12){e.defer_count=(e.defer_count||0)+1;e.at=now+5000;keep.push(e)}continue}const text=safeText(e.text,600).trim();if(text){const speaker=safeText(e.speaker||(actor?.name||''),100);addTranscript(speaker?'npc':'world',speaker?`${speaker}: ${text}`:text);eventLog(speaker?`${speaker}: ${text}`:text)}}world.scheduledEvents=keep}
function behaviorStep(dt){
  for(const o of activeRoomObjects()){
    if(!o.physical.materialized||o.doorTo)continue;const m=o.motion||{type:'idle'};
    if(runActorPlan(o,dt))continue;
    if(m.type==='approach_player'){const desiredGap=Math.max(18,Number(m.radius)||0),gap=shapeDistance(o.shape,o.physical.x,o.physical.y,player.shape,player.x,player.y);if(gap>desiredGap)moveToward(o,player.x,player.y,m.speed||60,dt,false,0);}
    else if(m.type==='chase_player')moveToward(o,player.x,player.y,m.speed||60,dt,false,0);
    else if(m.type==='flee_player')moveToward(o,player.x,player.y,m.speed||70,dt,true,0);
    else if(m.type==='wander'){o.state.wander_angle=Number(o.state.wander_angle)||Math.random()*Math.PI*2;o.state.wander_angle+=(Math.random()-.5)*dt*2;const ok=moveObjectSliding(o,Math.cos(o.state.wander_angle)*(m.speed||30)*dt,Math.sin(o.state.wander_angle)*(m.speed||30)*dt);if(!ok)o.state.wander_angle+=Math.PI*.7}
    if(m.type==='attack_contact'&&touching(o)&&m.damage>0){const now=performance.now();if(!o.state.last_attack_ms||now-o.state.last_attack_ms>800){player.state.health=clamp((player.state.health??100)-m.damage,0,100);o.state.last_attack_ms=now;addTranscript('world',`${o.name} hits you for ${m.damage}.`)}}
  }
}
function physicalStep(dt){const v=inputVec();tryMove(v.x*player.speed*dt,v.y*player.speed*dt);behaviorStep(dt);runScheduledEvents()}

function eventLog(text){world.events.unshift({id:++eventSeq,t:gameMinute,text:safeText(text,500)});world.events=world.events.slice(0,30)}
function addTranscript(kind,text){const v=safeText(text,1200).trim();if(!v)return;const row=document.createElement('div');row.className=`turn ${kind||'world'}`;row.textContent=v;transcriptScrollEl.appendChild(row);while(transcriptScrollEl.children.length>100)transcriptScrollEl.firstChild.remove();transcriptScrollEl.scrollTop=transcriptScrollEl.scrollHeight;return row}
function setResult(text,kind='world'){resultEl.textContent=safeText(text,240);if(text){eventLog(text);addTranscript(kind,text)}refresh()}

function objectView(o){
  const x=o.physical.materialized?o.physical.x:o.semantic.x,y=o.physical.materialized?o.physical.y:o.semantic.y;
  const dx=x-player.x,dy=y-player.y,center=Math.hypot(dx,dy),gap=edgeDistanceToPlayer(o),dot=center?dx/center*player.facingX+dy/center*player.facingY:1;
  return{id:o.id,name:o.name,role:o.role,description:o.description,state:o.state,affordances:o.affordances,
    shape:o.shape,solid:o.solid,pushable:o.pushable,interaction_reach:o.interactionReach,speech_reach:o.speechReach,motion:o.motion,actor:o.actor?{goal:o.actor.goal,plan:o.actor.plan,index:o.actor.index,awaiting_reply:o.actor.awaitingReply,last_reply:o.actor.lastReply,memory:o.actor.memory}:null,
    absolute:{x:Math.round(x),y:Math.round(y)},relative:{dx:Math.round(dx),dy:Math.round(dy),center_distance:Math.round(center),edge_distance:+gap.toFixed(1),direction:directionName(dx,dy),bearing_degrees:Math.round(Math.atan2(dy,dx)*180/Math.PI)},
    touching:gap<=1.5,interaction_reachable:gap<=interactionReach(o),speech_reachable:canHear(o),in_front:dot>.45,facing_alignment:+dot.toFixed(2),door_to:o.doorTo||null};
}
function llmState(){
  const visible=activeRoomObjects().filter(o=>o.physical.materialized).map(objectView).sort((a,b)=>a.relative.edge_distance-b.relative.edge_distance);
  const contacts=visible.filter(o=>o.touching),interact=visible.filter(o=>o.interaction_reachable),speech=visible.filter(o=>o.speech_reachable),front=visible.filter(o=>o.in_front).sort((a,b)=>b.facing_alignment-a.facing_alignment||a.relative.edge_distance-b.relative.edge_distance);
  return{
    game_description:world.scenario.game_description||world.scenario.premise||'',title:world.scenario.title,premise:world.scenario.premise||'',goal:world.goal,goal_complete:world.goalComplete,
    world_summary:{generated_rooms:Object.keys(world.rooms).length,visited_rooms:[...visitedRooms],room_cap:WORLD_ROOM_CAP},
    coordinate_system:'2D top-down coordinates. x increases right/east; y increases down/south. Shapes below are the exact visible/collision geometry.',
    current_room:{id:player.room,name:room().name,description:room().description,bounds:{x_min:0,y_min:0,x_max:ROOM.w,y_max:ROOM.h}},
    player:{position:{x:+player.x.toFixed(1),y:+player.y.toFixed(1)},previous_position:{x:+player.lastX.toFixed(1),y:+player.lastY.toFixed(1)},movement_delta:{dx:+player.vx.toFixed(1),dy:+player.vy.toFixed(1)},facing:{dx:+player.facingX.toFixed(2),dy:+player.facingY.toFixed(2),direction:directionName(player.facingX,player.facingY)},shape:player.shape,speed:player.speed,interaction_reach:player.interactionReach,speech_reach:player.speechReach,state:player.state},
    perception:{radius:perceptionRadius(),meaning:'visible_environment is every materialized entity in perception; edge_distance uses exact shape geometry'},inventory:world.inventory.slice(),
    visible_environment:visible,physical_contacts:contacts.map(o=>o.id),interaction_reachable:interact.map(o=>o.id),speech_reachable:speech.map(o=>o.id),
    nearest_visible:visible[0]?.id||null,nearest_interactable:interact[0]?.id||null,best_facing_candidate:front[0]?.id||null,
    conversation:[...transcriptScrollEl.children].slice(-12).map(x=>({kind:x.className.replace('turn ','').trim(),text:x.textContent})),recent_events:world.events.slice(0,8).map(e=>e.text)
  };
}

function sanitizeObjectPatch(o,patch){
  if('name'in patch)o.name=safeText(patch.name,80);if('description'in patch)o.description=safeText(patch.description,700);if('state'in patch&&patch.state&&typeof patch.state==='object')o.state={...o.state,...patch.state};
  if(Array.isArray(patch.affordances))o.affordances=patch.affordances.map(x=>safeText(x,80)).slice(0,12);if(patch.shape)o.shape=normalizeShape(patch.shape,o.role);
  if(typeof patch.solid==='boolean')o.solid=patch.solid;if(typeof patch.pushable==='boolean')o.pushable=patch.pushable;
  if('interaction_reach'in patch)o.interactionReach=clamp(patch.interaction_reach,0,180);if('speech_reach'in patch)o.speechReach=clamp(patch.speech_reach,0,500);
}
function applyToolCalls(calls){
  for(const c of Array.isArray(calls)?calls.slice(0,16):[]){if(!c||typeof c!=='object')continue;const tool=safeText(c.tool,50),a=c.args&&typeof c.args==='object'?c.args:{};
    if(tool==='set_object'){const o=obj(a.id);if(o)sanitizeObjectPatch(o,a.patch||a)}
    else if(tool==='move_object'){const o=obj(a.id);if(o){o.semantic.x=clamp(a.x??(o.semantic.x+Number(a.dx||0)),20,ROOM.w-20);o.semantic.y=clamp(a.y??(o.semantic.y+Number(a.dy||0)),20,ROOM.h-20);if(o.physical.materialized){o.physical.x=o.semantic.x;o.physical.y=o.semantic.y}}}
    else if(tool==='set_motion'){const o=obj(a.id);if(o)o.motion={type:safeText(a.type||'idle',30),speed:clamp(a.speed??0,0,260),radius:clamp(a.radius??120,0,500),damage:clamp(a.damage??0,0,100),target:safeText(a.target||'player',50)}}
    else if(tool==='remove_object'){const o=obj(a.id);if(o&&!o.doorTo){o.semantic.active=false;o.physical.materialized=false}}
    else if(tool==='create_object'){const rid=world.rooms[a.room_id]?a.room_id:player.room,r=world.rooms[rid];if(r&&r.objects.filter(o=>!o.doorTo&&o.semantic.active).length<ROOM_CONTENT_CAP){const raw={...(a.object||a),id:(a.object||a).id||`llm_${Date.now()}_${++world.created}`};r.objects.push(normalizeObject(raw,r.objects.length+1))}}
    else if(tool==='inventory_add'){const n=safeText(a.name,80).trim();if(n&&!world.inventory.includes(n))world.inventory.push(n)}
    else if(tool==='inventory_remove'){const n=safeText(a.name,80).trim().toLowerCase();world.inventory=world.inventory.filter(x=>x.toLowerCase()!==n)}
    else if(tool==='set_goal'){world.goal=safeText(a.text,500)}
    else if(tool==='set_room'){const r=world.rooms[a.room_id||player.room];if(r){if(a.name)r.name=safeText(a.name,100);if(a.description)r.description=safeText(a.description,1000)}}
    else if(tool==='set_player'){if(a.state&&typeof a.state==='object')player.state={...player.state,...a.state};if('speed'in a)player.speed=clamp(a.speed,50,320);if('interaction_reach'in a)player.interactionReach=clamp(a.interaction_reach,0,180);if('speech_reach'in a)player.speechReach=clamp(a.speech_reach,20,500)}
    else if(tool==='create_room'){if(Object.keys(world.rooms).length<WORLD_ROOM_CAP){const spec=a.room&&typeof a.room==='object'?a.room:a;let id=safeText(spec.id||`room${String.fromCharCode(65+Object.keys(world.rooms).length)}`,50);if(world.rooms[id])id=`room_${Date.now()}`;world.rooms[id]={id,name:safeText(spec.name||id,100),description:safeText(spec.description||'',1000),objects:(spec.objects||[]).slice(0,ROOM_CONTENT_CAP).map(normalizeObject)};world.scenario.rooms.push({id,name:world.rooms[id].name,description:world.rooms[id].description,objects:[],doors:[]})}}
    else if(tool==='create_door'){const from=world.rooms[a.from_room_id]?a.from_room_id:player.room,to=safeText(a.to_room_id,50);if(world.rooms[from]&&world.rooms[to]){const raw={id:`door_${from}_${to}_${Date.now()}`,name:a.name||`Durchgang zu ${world.rooms[to].name}`,to,x:clamp(a.x,50,ROOM.w-50),y:clamp(a.y,50,ROOM.h-50),description:a.description||'',shape:a.shape||{type:'rect',width:58,height:72},interaction_reach:a.interaction_reach??30};const map=new Map(Object.entries(world.rooms).map(([id,r])=>[id,{id,name:r.name,doors:[]} ]));world.rooms[from].objects.push(normalizeDoor(raw,from,map))}}
    else if(tool==='set_actor_plan'){const o=obj(a.id);if(o&&o.role==='npc'){o.actor=normalizeActor({goal:a.goal||o.actor?.goal||'',steps:Array.isArray(a.steps)?a.steps:[],index:0,memory:o.actor?.memory||[],lastReply:o.actor?.lastReply||''});o.motion={...o.motion,type:'idle'}}}
    else if(tool==='emit_event'){const text=safeText(a.text,600).trim(),speaker=safeText(a.speaker,100).trim();if(text){addTranscript(speaker?'npc':'world',speaker?`${speaker}: ${text}`:text);eventLog(speaker?`${speaker}: ${text}`:text)}}
    else if(tool==='schedule_event'){const text=safeText(a.text,600).trim();if(text){world.scheduledEvents=Array.isArray(world.scheduledEvents)?world.scheduledEvents:[];world.scheduledEvents.push({at:Date.now()+clamp(a.delay_seconds??5,.2,3600)*1000,text,speaker:safeText(a.speaker,100),actor_id:safeText(a.actor_id,50),defer_count:0});world.scheduledEvents=world.scheduledEvents.slice(-40)}}
  }
  syncPerception();saveGame();
}

function partialJsonString(raw,key){
  const re=new RegExp(`"${key}"\\s*:\\s*"`),m=re.exec(raw);if(!m)return'';let i=m.index+m[0].length,out='';
  while(i<raw.length){const c=raw[i++];if(c==='"')break;if(c!=='\\'){out+=c;continue}if(i>=raw.length)break;const e=raw[i++];
    if(e==='n')out+='\n';else if(e==='r')out+='\r';else if(e==='t')out+='\t';else if(e==='b')out+='\b';else if(e==='f')out+='\f';else if(e==='"')out+='"';else if(e==='\\')out+='\\';else if(e==='/')out+='/';else if(e==='u'){if(i+4>raw.length)break;const hex=raw.slice(i,i+4);if(!/^[0-9a-fA-F]{4}$/.test(hex))break;out+=String.fromCharCode(parseInt(hex,16));i+=4}else out+=e;
  }return out
}
function renderModelStream(pending,raw){const n=partialJsonString(raw,'n'),sp=partialJsonString(raw,'s'),d=partialJsonString(raw,'d'),dialogue=d?(sp?`${sp}: ${d}`:d):'',shown=[n,dialogue].filter(Boolean).join(n&&dialogue?'\n':'');if(shown&&pending){pending.textContent=shown;pending.className='turn pending streaming';transcriptScrollEl.scrollTop=transcriptScrollEl.scrollHeight;resultEl.textContent=safeText(shown,240)}return shown}
async function runLlmAttempt(text,pending,attempt,requestId,mode='action',onVisible=null){
  let modelRaw='',finalEvent=null,streamed='',timer=null,reader=null;
  try{
    const ctrl=new AbortController();timer=setTimeout(()=>ctrl.abort(),45000);
    const r=await fetch('/llm_game_stt/http/game/action',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/x-ndjson'},body:JSON.stringify({action:text,state:llmState(),request_id:requestId,attempt,mode}),signal:ctrl.signal});
    if(!r.ok)throw new Error(`HTTP ${r.status}`);if(!r.body)throw new Error('Streaming-Antwort ohne Datenstrom');
    reader=r.body.getReader();const decoder=new TextDecoder(),lines={buf:''};
    while(true){let packet;try{packet=await reader.read()}catch(e){if(finalEvent?.ok)break;throw e}const {value,done}=packet;if(done)break;lines.buf+=decoder.decode(value,{stream:true});let nl;
      while((nl=lines.buf.indexOf('\n'))>=0){const line=lines.buf.slice(0,nl).trim();lines.buf=lines.buf.slice(nl+1);if(!line)continue;let evt;try{evt=JSON.parse(line)}catch{continue}
        if(evt.type==='delta'&&typeof evt.delta==='string'){modelRaw+=evt.delta;streamed=renderModelStream(pending,modelRaw)||streamed;if(onVisible)onVisible(streamed,modelRaw)}
        else if(evt.type==='final'){finalEvent=evt}
        else if(evt.type==='error')throw new Error(evt.error||'Streaming-Fehler');
      }
    }
    if(!finalEvent?.ok)throw new Error('Keine vollständige KI-Antwort');return{finalEvent,streamed}
  }finally{if(timer)clearTimeout(timer);try{reader?.releaseLock()}catch{}}
}
function retryDelay(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
async function llmAction(text){
  if(llmBusy){setResult('Die Spiel-KI denkt bereits.','system');return false}
  llmBusy=true;statsEl.textContent='KI antwortet…';const pending=addTranscript('pending','…'),requestId=(crypto.randomUUID?.()||`${Date.now()}-${Math.random()}`);let success=false,lastError=null;
  try{
    for(let attempt=1;attempt<=3;attempt++){
      if(attempt>1){pending.textContent=`Erneuter KI-Versuch ${attempt}/3 …`;pending.className='turn pending';addTranscript('system',`KI-Aufruf fehlgeschlagen. Automatischer Wiederholungsversuch ${attempt}/3 …`);await retryDelay(500*(attempt-1))}
      try{
        const {finalEvent,streamed}=await runLlmAttempt(text,pending,attempt,requestId),out=finalEvent.result||{};
        if(out.allowed!==false)applyToolCalls(out.tool_calls||out.mutations||[]);if(out.goal_complete)world.goalComplete=true;
        pending?.remove();if(out.narration)addTranscript('world',out.narration);if(out.speaker&&out.dialogue)addTranscript('npc',`${out.speaker}: ${out.dialogue}`);
        const shown=out.speaker&&out.dialogue?`${out.speaker}: ${out.dialogue}`:(out.narration||streamed||'Nichts geschieht.');resultEl.textContent=safeText(shown,240);eventLog(shown);saveGame();refresh();success=true;return true
      }catch(e){lastError=e;if(attempt<3){pending.textContent=`KI-Fehler: ${safeText(e.message,120)} — erneuter Versuch folgt …`;continue}throw e}
    }
  }catch(e){lastError=e;pending?.remove();actionEl.value=text;commandHistoryIndex=commandHistory.length;commandHistoryDraft=text;setResult(`${e.name==='AbortError'?'Die Spiel-KI hat zu lange gebraucht.':`KI-Fehler: ${e.message}`} Der Befehl bleibt im Eingabefeld und kann erneut gesendet werden.`,'error');actionEl.focus();requestAnimationFrame(()=>actionEl.setSelectionRange(actionEl.value.length,actionEl.value.length));return false}
  finally{llmBusy=false;refresh();if(!success&&lastError)console.warn('llm final failure',lastError)}
}
async function executeAction(raw){const text=safeText(raw,500).trim();if(!text)return false;lastUserActionAt=Date.now();notifyActorsOfPlayerCommand(text);addTranscript('user',text);const t=text.toLowerCase();if(/^(warte|wait)\b/.test(t)){const m=clamp(parseInt(t.match(/\d+/)?.[0]||'10',10),1,120);gameMinute+=m;setResult(`Du wartest ${m} Minuten.`);return true}return await llmAction(text)}

function contextInteract(){const st=llmState(),id=st.physical_contacts[0]||st.nearest_interactable||st.best_facing_candidate,t=id?st.visible_environment.find(o=>o.id===id):null;if(t?.door_to&&t.relative.edge_distance<=Math.max(player.interactionReach,t.interaction_reach)){return useDoor(t.id)}executeAction('interact');return true}
function useDoor(id=null){lastUserActionAt=Date.now();const candidates=activeRoomObjects().filter(o=>o.doorTo&&o.physical.materialized&&canInteract(o)).sort((a,b)=>edgeDistanceToPlayer(a)-edgeDistanceToPlayer(b));const d=id?obj(id):candidates[0];if(!d||!d.doorTo||!canInteract(d)){setResult('Kein erreichbarer Durchgang.');return false}player.room=d.doorTo;player.x=d.spawn?.x??120;player.y=d.spawn?.y??430;player.lastX=player.x;player.lastY=player.y;visitedRooms.add(player.room);syncPerception();markExplored();setResult(`Du betrittst ${room().name}.`);scheduleBackgroundExpansion(60000);saveGame();return true}

function saveGame(){try{if(!world)return;localStorage.setItem(SAVE_KEY,JSON.stringify({title:world.scenario.title,world,player:{...player},gameMinute,visited:[...visitedRooms],refined:[...refinedRooms],explored:exploredCells,transcript:[...transcriptScrollEl.children].slice(-100).map(x=>({kind:x.className.replace('turn ','').trim(),text:x.textContent}))}))}catch(e){console.warn('save',e)}}
function restoreGame(scenario){try{const raw=localStorage.getItem(SAVE_KEY);if(!raw)return false;const s=JSON.parse(raw);if(!s||s.title!==scenario.title||!s.world)return false;world=s.world;world.scheduledEvents=Array.isArray(world.scheduledEvents)?world.scheduledEvents:[];for(const rr of Object.values(world.rooms||{}))for(const o of rr.objects||[]){if(o.role==='npc'&&!('actor'in o))o.actor=null}Object.assign(player,s.player||{});player.shape=normalizeShape(player.shape,'player');gameMinute=Number(s.gameMinute)||0;visitedRooms=new Set(s.visited||[player.room]);refinedRooms=new Set(s.refined||[]);exploredCells=s.explored||{};transcriptScrollEl.replaceChildren();for(const t of s.transcript||[])addTranscript(t.kind,t.text);syncPerception();refresh();return true}catch(e){console.warn('restore',e);return false}}

function observedFacts(){const out=[];for(const id of visitedRooms){const r=world.rooms[id];if(!r)continue;out.push({room:id,name:r.name,description:r.description,objects:r.objects.filter(o=>o.semantic.active).map(o=>({id:o.id,name:o.name,role:o.role,description:o.description,state:o.state,shape:o.shape,solid:o.solid,pushable:o.pushable,interaction_reach:o.interactionReach,speech_reach:o.speechReach,position:{x:o.semantic.x,y:o.semantic.y},motion:o.motion,door_to:o.doorTo}))})}return out}
function rawRoom(id){return (world.scenario.rooms||[]).find(r=>String(r.id)===String(id))||null}
function setDoorSpawn(o,fromId,rawMap){const target=rawMap.get(String(o.doorTo)),back=(target?.doors||[]).find(x=>String(x.to)===String(fromId));if(back){const bx=clamp(back.x,50,ROOM.w-50),by=clamp(back.y,50,ROOM.h-50),edge=Math.min(bx,ROOM.w-bx,by,ROOM.h-by);o.spawn=edge===bx?{x:bx+90,y:by}:edge===ROOM.w-bx?{x:bx-90,y:by}:edge===by?{x:bx,y:by+90}:{x:bx,y:by-90}}else o.spawn={x:120,y:430}}
function materializeScenarioDoor(fromId,d){const r=world.rooms[fromId];if(!r||r.objects.some(o=>o.id===d.id))return;const map=new Map((world.scenario.rooms||[]).map(x=>[String(x.id),x]));const o=normalizeDoor(d,fromId,map);setDoorSpawn(o,fromId,map);r.objects.push(o)}
function topologyCandidate(){if(Object.keys(world.rooms).length>=WORLD_ROOM_CAP)return null;return Object.keys(world.rooms).find(id=>!visitedRooms.has(id)&&!world.rooms[id].topologyClosed&&(Number(world.rooms[id].topologyExpansions)||0)<3)||null}
function integrateTopology(targetId,out){const target=world.rooms[targetId];if(!target)return false;target.topologyExpansions=Number(out.target_topology_expansions)||target.topologyExpansions||0;target.topologyClosed=!!out.target_topology_closed;const targetRaw=rawRoom(targetId);if(targetRaw){targetRaw.topology_expansions=target.topologyExpansions;targetRaw.topology_closed=target.topologyClosed}if(!out.create||!out.room)return false;const rr=out.room,newId=String(rr.id||'');if(!newId||world.rooms[newId])return false;rr.topology_expansions=Number(rr.topology_expansions)||0;rr.topology_closed=!!rr.topology_closed;world.scenario.rooms.push(rr);world.rooms[newId]={id:newId,name:safeText(rr.name||newId,100),description:safeText(rr.description||'',1000),objects:(rr.objects||[]).slice(0,ROOM_CONTENT_CAP).map(normalizeObject),topologyExpansions:rr.topology_expansions,topologyClosed:rr.topology_closed};if(targetRaw){targetRaw.doors=Array.isArray(targetRaw.doors)?targetRaw.doors:[];if(out.door_from&&!targetRaw.doors.some(d=>d.id===out.door_from.id))targetRaw.doors.push(out.door_from)}if(out.door_from)materializeScenarioDoor(targetId,out.door_from);for(const d of rr.doors||[])materializeScenarioDoor(newId,d);saveGame();return true}
async function expandTopology(targetId){const target=world.rooms[targetId];if(!target||visitedRooms.has(targetId)||Object.keys(world.rooms).length>=WORLD_ROOM_CAP)return false;const payload={premise:world.scenario.premise||'',goal:world.goal,target_room_id:targetId,target_room:{id:targetId,name:target.name,description:target.description,objects:target.objects.filter(o=>!o.doorTo&&o.semantic.active).map(o=>({id:o.id,name:o.name,role:o.role,description:o.description,state:o.state,shape:o.shape,solid:o.solid,pushable:o.pushable,interaction_reach:o.interactionReach,speech_reach:o.speechReach,x:o.semantic.x,y:o.semantic.y,motion:o.motion})),doors:target.objects.filter(o=>o.doorTo).map(o=>({id:o.id,name:o.name,to:o.doorTo,x:o.semantic.x,y:o.semantic.y,description:o.description,shape:o.shape,interaction_reach:o.interactionReach}))},target_observed:false,target_topology_expansions:Number(target.topologyExpansions)||0,target_topology_closed:!!target.topologyClosed,existing_room_ids:Object.keys(world.rooms),world_room_count:Object.keys(world.rooms).length,observed_facts:observedFacts()};const res=await fetch('/llm_game_stt/http/game/topology',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await res.json();if(!res.ok||!j.ok)throw new Error(j.error||`HTTP ${res.status}`);if(visitedRooms.has(targetId))return false;return integrateTopology(targetId,j.result||{})}
function scheduleBackgroundExpansion(delay=60000){clearTimeout(backgroundTimer);backgroundTimer=setTimeout(()=>backgroundTick(),delay)}
async function backgroundTick(){if(backgroundBusy||llmBusy||Date.now()-lastUserActionAt<60000)return scheduleBackgroundExpansion(15000);const topo=topologyCandidate();if(topo){backgroundBusy=true;try{await expandTopology(topo)}catch(e){console.warn('background topology',e)}finally{backgroundBusy=false;refresh();scheduleBackgroundExpansion(60000)}return}const unseen=Object.keys(world.rooms).find(id=>!visitedRooms.has(id));if(!unseen)return;const r=world.rooms[unseen];backgroundBusy=true;try{const free=Math.max(0,ROOM_CONTENT_CAP-r.objects.filter(o=>!o.doorTo&&o.semantic.active).length);if(free>0){const res=await fetch('/llm_game_stt/http/game/expand',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({premise:world.scenario.premise||'',goal:world.goal,observed:false,allow_updates:true,observed_facts:observedFacts(),free_slots:Math.min(1,free),room:{id:r.id,name:r.name,description:r.description,objects:r.objects.filter(o=>!o.doorTo).map(o=>({id:o.id,name:o.name,role:o.role,description:o.description,state:o.state,shape:o.shape,solid:o.solid,pushable:o.pushable,interaction_reach:o.interactionReach,speech_reach:o.speechReach,x:o.semantic.x,y:o.semantic.y,motion:o.motion}))}})});const j=await res.json();if(j.ok&&!visitedRooms.has(unseen)){const d=j.result||{};if(d.room_description)r.description=safeText(d.room_description,1000);for(const u of d.updates||[]){const o=r.objects.find(x=>x.id===u.id);if(o)sanitizeObjectPatch(o,u)}for(const a of d.additions||[]){if(r.objects.filter(o=>!o.doorTo).length>=ROOM_CONTENT_CAP)break;r.objects.push(normalizeObject(a,r.objects.length+1))}saveGame()}}}catch(e){console.warn('background content',e)}finally{backgroundBusy=false;scheduleBackgroundExpansion(60000)}}
function scheduleStoryEvent(delay=45000+Math.random()*45000){clearTimeout(storyEventTimer);storyEventTimer=null}
async function backgroundStoryEvent(){
  if(!world)return scheduleStoryEvent();
  if(storyBusy||llmBusy||backgroundBusy||Date.now()-lastUserActionAt<15000)return scheduleStoryEvent(10000+Math.random()*10000);
  storyBusy=true;const requestId=(crypto.randomUUID?.()||`bg-${Date.now()}`);let pending=null,lastShown='';
  const onVisible=shown=>{if(!shown||shown===lastShown)return;lastShown=shown;if(!pending)pending=addTranscript('pending',shown);else{pending.textContent=shown;pending.className='turn pending streaming'}transcriptScrollEl.scrollTop=transcriptScrollEl.scrollHeight};
  try{
    let answer=null,lastError=null;
    for(let attempt=1;attempt<=2;attempt++){try{answer=await runLlmAttempt('__HINTERGRUNDEREIGNIS__',null,attempt,requestId,'background',onVisible);break}catch(e){lastError=e;if(attempt<2)await retryDelay(700)}}
    if(!answer)throw lastError||new Error('Hintergrund-KI ohne Antwort');const out=answer.finalEvent.result||{};
    if(out.allowed!==false)applyToolCalls(out.tool_calls||[]);if(out.goal_complete)world.goalComplete=true;
    pending?.remove();if(out.narration)addTranscript('world',out.narration);if(out.speaker&&out.dialogue)addTranscript('npc',`${out.speaker}: ${out.dialogue}`);
    const shown=out.speaker&&out.dialogue?`${out.speaker}: ${out.dialogue}`:out.narration;if(shown){resultEl.textContent=safeText(shown,240);eventLog(shown);saveGame()}
  }catch(e){pending?.remove();console.warn('background story event',e)}finally{storyBusy=false;refresh();scheduleStoryEvent()}
}


function exploredSet(id){return new Set(exploredCells[id]||[])}
function markExplored(){const set=exploredSet(player.room),cw=ROOM.w/EXP_COLS,ch=ROOM.h/EXP_ROWS,R=perceptionRadius();for(let y=0;y<EXP_ROWS;y++)for(let x=0;x<EXP_COLS;x++){const cx=(x+.5)*cw,cy=(y+.5)*ch;if(Math.hypot(cx-player.x,cy-player.y)<=R+Math.max(cw,ch)*.5)set.add(`${x},${y}`)}exploredCells[player.room]=[...set]}
function isExplored(id,x,y){return exploredSet(id).has(`${x},${y}`)}

function drawShape(g,shape,cx,cy,fill,stroke='#171a17'){
  g.save();g.fillStyle=fill;g.strokeStyle=stroke;g.lineWidth=2;
  for(const poly of shapeParts(shape,cx,cy)){g.beginPath();g.moveTo(poly[0][0],poly[0][1]);for(let i=1;i<poly.length;i++)g.lineTo(poly[i][0],poly[i][1]);g.closePath();g.fill();g.stroke()}
  g.restore();
}
function camera(){return{x:W/2-player.x,y:H/2-player.y}}
function screen(x,y){const c=camera();return{x:x+c.x,y:y+c.y}}
function drawFog(c){const cw=ROOM.w/EXP_COLS,ch=ROOM.h/EXP_ROWS;ctx.save();ctx.fillStyle='rgba(5,7,6,.60)';for(let y=0;y<EXP_ROWS;y++)for(let x=0;x<EXP_COLS;x++)if(!isExplored(player.room,x,y))ctx.fillRect(c.x+x*cw,c.y+y*ch,cw+.5,ch+.5);ctx.restore()}
function labelLines(g,text,maxWidth=210){const words=String(text||'').split(/\s+/).filter(Boolean),lines=[];let line='';for(const word of words){const test=line?`${line} ${word}`:word;if(line&&g.measureText(test).width>maxWidth){lines.push(line);line=word}else line=test}if(line)lines.push(line);return lines.length?lines:['']}
function drawObjectLabel(g,text,x,y){g.save();g.font='11px sans-serif';g.textAlign='center';g.textBaseline='middle';const lines=labelLines(g,text,210),lineH=14,pad=5,w=Math.min(220,Math.max(...lines.map(line=>g.measureText(line).width))+pad*2),h=lines.length*lineH+4;g.fillStyle='#111e';g.fillRect(x-w/2,y-h,w,h);g.fillStyle='#f1ead4';lines.forEach((line,i)=>g.fillText(line,x,y-h/2+2+lineH*(i+.5)));g.restore()}
function drawMinimap(){const mw=mapCanvas.width,mh=mapCanvas.height;mapCtx.clearRect(0,0,mw,mh);mapCtx.fillStyle='#090c09';mapCtx.fillRect(0,0,mw,mh);const ids=Object.keys(world.rooms),sw=(mw-12)/WORLD_ROOM_CAP;for(let i=0;i<WORLD_ROOM_CAP;i++){const id=ids[i],x=6+i*sw;mapCtx.fillStyle=id?(visitedRooms.has(id)?'#c9bd72':'#656a66'):'#202520';mapCtx.fillRect(x,6,Math.max(4,sw-3),12);if(id===player.room){mapCtx.strokeStyle='#f2e49b';mapCtx.strokeRect(x-.5,5.5,Math.max(4,sw-3)+1,13)}}const top=24,gw=mw-12,gh=mh-top-6,cw=gw/EXP_COLS,ch=gh/EXP_ROWS;for(let y=0;y<EXP_ROWS;y++)for(let x=0;x<EXP_COLS;x++){mapCtx.fillStyle=isExplored(player.room,x,y)?'#58645a':'#272b28';mapCtx.fillRect(6+x*cw,top+y*ch,cw-.6,ch-.6)}mapCtx.fillStyle='#f0df72';mapCtx.beginPath();mapCtx.arc(6+player.x/ROOM.w*gw,top+player.y/ROOM.h*gh,2.8,0,Math.PI*2);mapCtx.fill()}
function draw(){
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#151a16';ctx.fillRect(0,0,W,H);const c=camera();ctx.fillStyle='#4d5149';ctx.fillRect(c.x,c.y,ROOM.w,ROOM.h);ctx.strokeStyle='#1d211d';ctx.lineWidth=16;ctx.strokeRect(c.x,c.y,ROOM.w,ROOM.h);
  for(const o of activeRoomObjects()){if(!o.physical.materialized)continue;const p=screen(o.physical.x,o.physical.y);drawShape(ctx,o.shape,p.x,p.y,roleColors[o.doorTo?'door':o.role]||'#aaa');if(edgeDistanceToPlayer(o)<150){drawObjectLabel(ctx,o.name,p.x,p.y-36)}}
  drawShape(ctx,player.shape,W/2,H/2,roleColors.player);drawFog(c);drawMinimap();
}
function refresh(){if(!world)return;const ids=Object.keys(world.rooms),hp=clamp(player.state.health??100,0,100);roomLabelEl.textContent=String(ids.indexOf(player.room)+1);healthTextEl.textContent=`HP ${Math.round(hp)}`;healthFillEl.style.width=`${hp}%`;statsEl.textContent=llmBusy?'KI denkt…':`${room().name} · ${world.inventory.length} Gegenstand${world.inventory.length===1?'':'e'}`;storyEl.textContent=`${world.scenario.title}\nAuftrag: ${world.goal}\n${room().description}`;eventsEl.innerHTML=world.events.slice(0,10).map(e=>`<div>${e.t}m — ${e.text}</div>`).join('');stateEl.textContent=JSON.stringify(llmState(),null,2);drawMinimap()}
function resize(){DPR=Math.min(devicePixelRatio||1,2);const r=document.getElementById('game-pane').getBoundingClientRect();W=Math.max(1,Math.round(r.width));H=Math.max(1,Math.round(r.height));canvas.width=Math.round(W*DPR);canvas.height=Math.round(H*DPR);ctx.setTransform(DPR,0,0,DPR,0,0)}
function tick(now){const dt=Math.min(.04,(now-lastFrame)/1000);lastFrame=now;if(world){physicalStep(dt);syncPerception();markExplored();draw()}requestAnimationFrame(tick)}

async function loadScenario(regenerate=false){if(regenerate)setResult('Eine neue Spielwelt wird erzeugt…','system');try{const r=await fetch('/llm_game_stt/http/game/scenario',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({regenerate,theme:'Erzeuge ein neues, realistisches und leicht komisches Spiel in einer verständlichen Gegenwartssituation. Klare Rolle, konkreter Auftrag, überprüfbares Ziel und konkrete Informationsquellen. Humor aus glaubwürdigem Chaos oder Peinlichkeit. Keine Fantasy, keine Magie, keine Kristallenergie, keine kosmischen oder nicht-euklidischen Regeln. Alle spielersichtbaren Texte auf Deutsch.'})});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||`HTTP ${r.status}`);scenarioRecord=j.record;const scenario=scenarioRecord.scenario||scenarioRecord;if(!restoreGame(scenario)){world=buildWorld(scenario);const first=Object.keys(world.rooms)[0];player.room=first;player.x=Number(scenario.player?.x)||300;player.y=Number(scenario.player?.y)||430;player.lastX=player.x;player.lastY=player.y;visitedRooms=new Set([first]);refinedRooms=new Set();exploredCells={};transcriptScrollEl.replaceChildren();syncPerception();markExplored();addTranscript('system',scenario.title);addTranscript('world',scenario.opening||room().description);addTranscript('system',`Auftrag: ${scenario.goal}`);saveGame();refresh()}scheduleBackgroundExpansion(60000)}catch(e){setResult(`Spielwelt konnte nicht geladen werden: ${e.message}`,'error')}}

function submitCommand(){const text=actionEl.value.trim();if(!text)return;rememberCommand(text);actionEl.value='';actionEl.blur();keys.clear();executeAction(text)}
document.addEventListener('selectstart',e=>{if(e.target!==actionEl&&e.target!==debugEl&&!transcriptScrollEl.contains(e.target))e.preventDefault()});
window.addEventListener('resize',resize);
window.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(k==='enter'){if(document.activeElement!==actionEl){keys.clear();actionEl.focus();e.preventDefault()}return}if(document.activeElement===actionEl)return;keys.add(k);if(k==='e'){contextInteract();e.preventDefault()}if(k.startsWith('arrow'))e.preventDefault()});
window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
actionEl.addEventListener('keydown',e=>{if(e.key==='ArrowUp'){e.preventDefault();navigateCommandHistory(-1);return}if(e.key==='ArrowDown'){e.preventDefault();navigateCommandHistory(1);return}if(e.key==='Enter'){e.preventDefault();e.stopPropagation();submitCommand()}});
document.getElementById('action-form').addEventListener('submit',e=>{e.preventDefault();submitCommand()});
document.getElementById('goal').onclick=()=>setResult(world.goal,'system');
document.getElementById('new-world').onclick=()=>{localStorage.removeItem(SAVE_KEY);loadScenario(true)};
document.getElementById('reset').onclick=()=>{localStorage.removeItem(SAVE_KEY);loadScenario(false)};
document.getElementById('fullscreen').onclick=()=>document.documentElement.requestFullscreen?.();
document.getElementById('debug-toggle').onclick=()=>{debugEl.hidden=!debugEl.hidden};

const sb=document.getElementById('stick-base'),st=document.getElementById('stick-thumb');
function setStick(e){const r=sb.getBoundingClientRect();let dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2),n=Math.hypot(dx,dy);if(n>stick.max){dx*=stick.max/n;dy*=stick.max/n}stick.dx=dx;stick.dy=dy;st.style.transform=`translate(${dx}px,${dy}px)`}
sb.addEventListener('pointerdown',e=>{stick.active=true;stick.id=e.pointerId;sb.setPointerCapture(e.pointerId);setStick(e)});
sb.addEventListener('pointermove',e=>{if(stick.active&&e.pointerId===stick.id)setStick(e)});
function endStick(e){if(e.pointerId!==stick.id)return;stick.active=false;stick.dx=stick.dy=0;st.style.transform='translate(0,0)'}
sb.addEventListener('pointerup',endStick);sb.addEventListener('pointercancel',endStick);

const micStatus=document.getElementById('mic-status'),micText=document.getElementById('mic-text'),micToggle=document.getElementById('mic-toggle');
let mic={active:false,ws:null,stream:null,ctx:null,processor:null};
function browserSttLanguage(){return'de'}
function sttUrl(){return`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/llm_game_stt/ws/`}
function downsampleTo16k(input,sr){if(sr===16000)return input;const ratio=sr/16000,out=new Int16Array(Math.floor(input.length/ratio));for(let i=0;i<out.length;i++)out[i]=Math.max(-1,Math.min(1,input[Math.floor(i*ratio)]))*32767;return out}
function onStt(m){if(m.type==='stt_processing'){micStatus.textContent='stt_processing…';return}if(m.type==='stt'&&m.text){micText.textContent=m.text;executeAction(m.text)}}
async function startMic(){mic.stream=await navigator.mediaDevices.getUserMedia({audio:true});mic.ctx=new(window.AudioContext||window.webkitAudioContext)();const src=mic.ctx.createMediaStreamSource(mic.stream);mic.processor=mic.ctx.createScriptProcessor(4096,1,1);const g=mic.ctx.createGain();g.gain.value=0;src.connect(mic.processor);mic.processor.connect(g);g.connect(mic.ctx.destination);mic.ws=new WebSocket(sttUrl());mic.ws.binaryType='arraybuffer';mic.ws.onopen=()=>{mic.ws.send(JSON.stringify({type:'hello',sample_rate:16000,format:'pcm16le',language:browserSttLanguage()}));micStatus.textContent='Sprache bereit'};mic.ws.onmessage=e=>{try{onStt(JSON.parse(e.data))}catch{}};mic.processor.onaudioprocess=e=>{if(mic.ws?.readyState===WebSocket.OPEN)mic.ws.send(downsampleTo16k(e.inputBuffer.getChannelData(0),mic.ctx.sampleRate).buffer)};mic.active=true;micToggle.textContent='stopp'}
async function stopMic(){mic.active=false;try{mic.ws?.close()}catch{};try{mic.processor?.disconnect()}catch{};try{mic.stream?.getTracks().forEach(t=>t.stop())}catch{};try{await mic.ctx?.close()}catch{};mic.ws=mic.stream=mic.ctx=mic.processor=null;micToggle.textContent='mic';micStatus.textContent='Sprache aus'}
micToggle.onclick=async()=>{try{mic.active?await stopMic():await startMic()}catch(e){micStatus.textContent=`Sprachfehler: ${e.message}`}};

resize();requestAnimationFrame(tick);loadCommandHistory();loadScenario(false);
