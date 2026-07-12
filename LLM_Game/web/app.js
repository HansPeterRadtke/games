'use strict';
const canvas = document.getElementById('game');
if(window.CanvasRenderingContext2D && !CanvasRenderingContext2D.prototype.roundRect){ CanvasRenderingContext2D.prototype.roundRect=function(x,y,w,h,r){ r=Math.min(r,Math.abs(w)/2,Math.abs(h)/2); this.beginPath(); this.moveTo(x+r,y); this.arcTo(x+w,y,x+w,y+h,r); this.arcTo(x+w,y+h,x,y+h,r); this.arcTo(x,y+h,x,y,r); this.arcTo(x,y,x+w,y,r); this.closePath(); return this; }; }
const ctx = canvas.getContext('2d');
const stats = document.getElementById('stats');
const log = document.getElementById('log');
const keys = new Set();
const spriteIds = ['player','spark','void','echo','gate','wisp','stone','glyph'];
const sprites = {};
const topicGifImages = {}; const REAL_IMAGE_BACKEND=false;
for (const id of spriteIds) { const img = new Image(); img.src = `assets/sprites/${id}.png?v=20260711-1254-utterance-vad-no-tiny-whisper-slices`; sprites[id] = img; }

const animDefs = {
  player_idle: {src:'assets/animations/player_idle.png', frames:2, fps:2},
  player_walk: {src:'assets/animations/player_walk.png', frames:4, fps:8},
  spark_spin: {src:'assets/animations/spark_spin.png', frames:3, fps:7},
  void_pulse: {src:'assets/animations/void_pulse.png', frames:2, fps:4},
  gate_shimmer: {src:'assets/animations/gate_shimmer.png', frames:2, fps:3}
};
const anims = {};
for (const [id,def] of Object.entries(animDefs)) { const img = new Image(); img.src = `${def.src}?v=20260711-1254-utterance-vad-no-tiny-whisper-slices`; anims[id] = img; }

let DPR = 1, W = 0, H = 0, last = performance.now();
let camera = {x:0,y:0,shake:0};
let stick = {active:false, id:null, cx:0, cy:0, dx:0, dy:0, max:44};
const state = { score:0, insight:0, level:1, time:0, player:{x:0,y:0,r:14,speed:170,vx:0,vy:0,pulse:0}, sparks:[], voids:[], echoes:[], gates:[], wisps:[], stones:[], glyphs:[], speechObjects:[] };
const speechWorld = {queue:[], seen:{}, spawned:0, lastTopics:[], maxObjects:36, copiesPerTopic:1};
const stickBase = document.getElementById('stick-base');
const stickThumb = document.getElementById('stick-thumb');
function rand(seed){ let t = seed += 0x6D2B79F5; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function resize(){ DPR=Math.min(devicePixelRatio||1,2); W=innerWidth; H=innerHeight; canvas.width=Math.floor(W*DPR); canvas.height=Math.floor(H*DPR); canvas.style.width=W+'px'; canvas.style.height=H+'px'; ctx.setTransform(DPR,0,0,DPR,0,0); }
function say(text){ log.textContent=text; }
function reset(){ state.score=0; state.insight=0; state.level=1; state.time=0; state.player.x=0; state.player.y=0; state.player.pulse=0; spawnField(); say('Field reset. Use the thumb-stick. Collect sparks and glyphs. Avoid voids.'); }
function spawnNear(list,count,base,spread,make){ list.length=0; for(let i=0;i<count;i++){ let a=rand(base+i*17+state.level)*Math.PI*2, d=80+rand(base+i*31)*spread; list.push(make(Math.cos(a)*d, Math.sin(a)*d, i)); } }
function spawnField(){ spawnNear(state.sparks,28,100,900,(x,y,i)=>({x,y,z:rand(i+7),r:8,got:false})); spawnNear(state.voids,10,700,920,(x,y,i)=>({x,y,r:32+rand(i+91)*34,phase:rand(i+19)*6})); spawnNear(state.echoes,12,220,900,(x,y,i)=>({x,y,phase:rand(i+6)*8})); spawnNear(state.wisps,8,340,870,(x,y,i)=>({x,y,got:false,phase:rand(i+66)*8})); spawnNear(state.stones,18,440,980,(x,y,i)=>({x,y,phase:rand(i+23)*6})); spawnNear(state.glyphs,7,540,900,(x,y,i)=>({x,y,got:false,phase:rand(i+47)*6})); spawnNear(state.gates,3,640,1000,(x,y,i)=>({x,y,phase:rand(i+11)*6})); }
function updateStickVisual(){ stickThumb.style.transform = `translate(${stick.dx}px, ${stick.dy}px)`; }
function setStickFromEvent(e){ const r=stickBase.getBoundingClientRect(); stick.cx=r.left+r.width/2; stick.cy=r.top+r.height/2; let dx=e.clientX-stick.cx, dy=e.clientY-stick.cy; const len=Math.hypot(dx,dy); if(len>stick.max){ dx=dx/len*stick.max; dy=dy/len*stick.max; } stick.dx=dx; stick.dy=dy; updateStickVisual(); }
function bindStick(){ stickBase.addEventListener('pointerdown',e=>{ e.preventDefault(); stick.active=true; stick.id=e.pointerId; stickBase.setPointerCapture(e.pointerId); setStickFromEvent(e); }, {passive:false}); stickBase.addEventListener('pointermove',e=>{ if(stick.active && e.pointerId===stick.id){ e.preventDefault(); setStickFromEvent(e); } }, {passive:false}); const end=e=>{ if(e.pointerId===stick.id){ e.preventDefault(); stick.active=false; stick.id=null; stick.dx=0; stick.dy=0; updateStickVisual(); } }; stickBase.addEventListener('pointerup',end,{passive:false}); stickBase.addEventListener('pointercancel',end,{passive:false}); }
function input(){ let x=0,y=0; if(stick.active){ x=stick.dx/stick.max; y=stick.dy/stick.max; } if(keys.has('ArrowLeft')||keys.has('a')) x--; if(keys.has('ArrowRight')||keys.has('d')) x++; if(keys.has('ArrowUp')||keys.has('w')) y--; if(keys.has('ArrowDown')||keys.has('s')) y++; const len=Math.hypot(x,y); state.player.vx=len?x/Math.max(1,len):0; state.player.vy=len?y/Math.max(1,len):0; }
function tick(dt){ state.time+=dt; input(); const p=state.player; p.x+=p.vx*p.speed*dt; p.y+=p.vy*p.speed*dt; if(p.pulse>0) p.pulse=Math.max(0,p.pulse-dt*1.6); camera.x+=(p.x-camera.x)*Math.min(1,dt*4); camera.y+=(p.y-camera.y)*Math.min(1,dt*4); for(const s of state.sparks){ if(!s.got && Math.hypot(p.x-s.x,p.y-s.y)<28){ s.got=true; state.score++; state.insight+=3; say('Semantic spark collected.'); } } for(const g of state.glyphs){ if(!g.got && Math.hypot(p.x-g.x,p.y-g.y)<30){ g.got=true; state.score+=3; state.insight+=8; say('Glyph captured. The field becomes more readable.'); } } for(const w of state.wisps){ if(!w.got && Math.hypot(p.x-w.x,p.y-w.y)<28){ w.got=true; state.insight+=5; say('A wisp joins your perception trail.'); } } for(const v of state.voids){ if(Math.hypot(p.x-v.x,p.y-v.y)<p.r+v.r*.75){ state.insight=Math.max(0,state.insight-18*dt); camera.shake=.25; say('The void pulls at your perception. Move away.'); } } if(state.score>0 && state.score % 14 === 0){ state.level++; state.score++; spawnField(); say('A new perception layer unfolds.'); } updateSpeechSpawns(); camera.shake=Math.max(0,camera.shake-dt); stats.textContent=`score ${state.score}  insight ${Math.floor(state.insight)}  sprites ${spriteIds.length} anims 5  speech ${state.speechObjects.length} topics ${Object.keys(speechWorld.seen).length} cards ${state.speechObjects.length}  context 8192  model ~6.43 tok/s`; }
function worldToScreen(x,y,z=0){
  const dx=x-camera.x, dy=y-camera.y;
  const sx=W/2 + dx - dy*0.18;
  const sy=H/2 + dy*0.58 - (z||0)*34;
  const depth=Math.max(-1, Math.min(1, dy/900));
  const scale=0.88 + depth*0.16 + Math.max(0, Math.min(1, z||0))*0.08;
  return {x:sx,y:sy,scale};
}

function drawSprite(id,x,y,size,z=0){ const p=worldToScreen(x,y,z), img=sprites[id]; if(img && img.complete && img.naturalWidth){ const s=size*p.scale; ctx.imageSmoothingEnabled=false; ctx.drawImage(img,p.x-s/2,p.y-s/2,s,s); return true; } return false; }

function drawAnim(id,x,y,size,z=0,offset=0){ const def=animDefs[id], img=anims[id], p=worldToScreen(x,y,z); if(def && img && img.complete && img.naturalWidth){ const frame=Math.floor((state.time+offset)*def.fps)%def.frames; const s=size*p.scale; ctx.imageSmoothingEnabled=false; ctx.drawImage(img, frame*64, 0, 64, 64, p.x-s/2, p.y-s/2, s, s); return true; } return false; }

function hashString(text){ let h=2166136261; for(let i=0;i<text.length;i++){ h^=text.charCodeAt(i); h=Math.imul(h,16777619); } return h>>>0; }
function topicGifSlug(text){ return String(text||'object').toLowerCase().replace(/[^a-z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,64) || 'object'; }
function topicGifSrc(name, category, prompt='', motion='idle'){
  const n=String(name||'object'); const c=String(category||'object'); const p=String(prompt||n); const m=String(motion||'idle');
  return `https://nitro.jonnyontherun.org/llm_game_topic_gif/${topicGifSlug('real-'+c+'-'+n)}.gif?name=${encodeURIComponent(n)}&category=${encodeURIComponent(c)}&prompt=${encodeURIComponent(p)}&motion=${encodeURIComponent(m)}&v=20260711-1254-utterance-vad-no-tiny-whisper-slices`;
}

function topicIcon(name, category){
  const n=String(name||'').toLowerCase(); const c=String(category||'').toLowerCase();
  if(/poop|shit|crap|kacke|feces|faeces/.test(n)) return '💩';
  if(/bone/.test(n)) return '🦴';
  if(/bicycle|bike|fahrrad|mountainbike|rennrad|racing/.test(n)) return '🚲';
  if(/flower|blume|flauer/.test(n)) return '🌸';
  if(/tree|baum/.test(n)) return '🌳';
  if(/toothbrush/.test(n)) return '🪥';
  if(/teeth|tooth/.test(n)) return '🦷';
  if(/toilet/.test(n)) return '🚽';
  if(/juice|drink|milkshake/.test(n)) return '🥤';
  if(/jew|people|person|portrait|doctor|child|baby/.test(n)||c==='person') return '👤';
  if(/dance|dancing/.test(n)) return '💃';
  if(/dog|hund/.test(n)) return '🐶';
  if(/cat|katze/.test(n)) return '🐱';
  if(/house|haus/.test(n)) return '🏠';
  if(/street|city/.test(n)) return '🛣️';
  if(/trash/.test(n)) return '🗑️';
  if(/music/.test(n)) return '🎵';
  if(/ticket/.test(n)) return '🎫';
  if(/document|scroll|letter/.test(n)) return '📜';
  if(c==='food') return '🍽️';
  if(c==='animal') return '🐾';
  if(c==='plant') return '🌿';
  return '●';
}

function ensureTopicGif(o){
  const key=String(o.gifSrc||''); if(!key) return null;
  let rec=topicGifImages[key];
  const now=performance.now();
  function startLoad(rec){
    rec.state='loading'; rec.last=now; rec.retryCount=(rec.retryCount||0)+1;
    const img=new Image(); rec.img=img;
    img.onload=()=>{rec.state='ready'; rec.last=performance.now(); rec.naturalWidth=img.naturalWidth||0;};
    img.onerror=()=>{
      rec.state='pending'; rec.last=performance.now();
      const wait=Math.min(30000, 1500*Math.pow(1.45, Math.min(8, rec.retryCount||1)));
      rec.retryAt=performance.now()+wait;
      if((rec.retryCount||0)<=3 || (rec.retryCount||0)%5===0) appendMicDebug(`IMAGE PENDING/RETRY: ${String(o.name||'object')} retry=${rec.retryCount} wait=${Math.round(wait/1000)}s`);
    };
    const sep=key.includes('?')?'&':'?';
    img.src=`${key}${sep}retry=${rec.retryCount}&ts=${Math.floor(Date.now()/1000)}`;
  }
  if(!rec){ rec={img:null,state:'new',last:now,src:key,retryCount:0,retryAt:0,naturalWidth:0}; topicGifImages[key]=rec; startLoad(rec); return rec; }
  if((rec.state==='pending' || rec.state==='error') && now >= (rec.retryAt||0)) startLoad(rec);
  return rec;
}

function pruneOldTopics(){ for(const [k,v] of Object.entries(speechWorld.seen)){ if(state.time-(v.last||0)>55) delete speechWorld.seen[k]; } state.speechObjects=state.speechObjects.filter(o=>state.time-(o.born||0)<70); }
function handleTopics(items, engine){
  pruneOldTopics();
  if(!items.length){ setMicStatus('no direct objects yet; building scene context'); setTopicStatus([]); sendClientDebug({event:'topics_empty', engine}); return; }
  const accepted=[];
  let spawnedNow=0;
  const seenThisBatch=new Set();
  for(const item of items){
    const name=String(item.name||'').toLowerCase().trim();
    if(!name || name.length<3 || seenThisBatch.has(name)) continue;
    seenThisBatch.add(name);
    const existing=speechWorld.seen[name] || {name, category:item.category||'object', weight:0, last:0};
    existing.weight += Math.max(1, Math.min(5, Number(item.weight)||1));
    existing.last = state.time;
    existing.animation = item.animation || item.motion || 'idle';
    existing.prompt = item.prompt || item.name || existing.name;
    existing.x = Number.isFinite(item.x) ? item.x : existing.x; existing.y = Number.isFinite(item.y) ? item.y : existing.y; existing.z = Number.isFinite(item.z) ? item.z : existing.z; existing.scale = Number.isFinite(item.scale) ? item.scale : existing.scale; existing.count = item.count || existing.count;
    existing.gifSrc = topicGifSrc(existing.name, existing.category||'object', existing.prompt, existing.animation);
    speechWorld.seen[name]=existing;
    accepted.push(existing);
    const count = Math.max(1, Math.min(4, Number(item.count)||speechWorld.copiesPerTopic));
    for(let i=0;i<count;i++){ if(spawnSpeechObject(existing, i, accepted.length-1)) spawnedNow++; }
  }
  speechWorld.lastTopics = accepted.slice(0,16);
  setTopicStatus(accepted);
  setMicStatus(`world topics ${accepted.length}, spawned ${spawnedNow} scene graphics`);
  sendClientDebug({event:'topics_received', engine, accepted:accepted.map(x=>x.name), spawnedNow, copiesPerTopic:speechWorld.copiesPerTopic, totalObjects:state.speechObjects.length, totalTopics:Object.keys(speechWorld.seen).length});
}
function screenToWorldEdge(sx, sy){
  let wy = camera.y + (sy - H/2);
  for(let i=0;i<5;i++){
    const sc = 1 + Math.max(-.25, Math.min(.35, (wy-camera.y)/900));
    wy = camera.y + (sy - H/2) / sc;
  }
  const scale = 1 + Math.max(-.25, Math.min(.35, (wy-camera.y)/900));
  return {x: camera.x + (sx - W/2) / scale, y: wy};
}
function eventHorizonPosition(index){
  const margin = 64;
  const side = index % 4;
  const laneSeed = hashString(String(index) + ':' + Math.round(camera.x) + ':' + Math.round(camera.y));
  const t = 0.12 + ((laneSeed % 760) / 1000);
  if(side === 0) return screenToWorldEdge(W + margin, t * H);
  if(side === 1) return screenToWorldEdge(-margin, t * H);
  if(side === 2) return screenToWorldEdge(t * W, -margin);
  return screenToWorldEdge(t * W, H + margin);
}
function visiblePlayerSpawnPosition(copyIndex=0, topicIndex=0, topic=null){
  if(topic && Number.isFinite(topic.x) && Number.isFinite(topic.y)){
    const radius=260 + (copyIndex%3)*42;
    return {x:state.player.x + topic.x*radius + (copyIndex-1)*28, y:state.player.y + topic.y*radius};
  }
  const n = Math.max(1, speechWorld.copiesPerTopic || 1);
  const angle = ((copyIndex % n) / n) * Math.PI * 2 + topicIndex * 0.82 + speechWorld.spawned * 0.09;
  const dist = 118 + (topicIndex % 6) * 46 + Math.floor(copyIndex / n) * 38;
  return {x:state.player.x + Math.cos(angle)*dist, y:state.player.y + Math.sin(angle)*dist};
}

function tooDenseAt(x,y){ let near=0; for(const o of state.speechObjects){ if(Math.hypot(o.x-x,o.y-y)<86) near++; if(near>=1) return true; } return false; }
function spawnSpeechObject(topic, copyIndex=0, topicIndex=0){
  if(state.speechObjects.length>=speechWorld.maxObjects) state.speechObjects.splice(0, Math.ceil(state.speechObjects.length-speechWorld.maxObjects+1));
  for(let i=0;i<20;i++){
    const pos=visiblePlayerSpawnPosition(copyIndex+i, topicIndex, topic);
    if(!tooDenseAt(pos.x,pos.y) || i>8){
      const seed=hashString(topic.name+topic.category+speechWorld.spawned+':'+copyIndex+':'+topicIndex);
      state.speechObjects.push({x:pos.x,y:pos.y,z:Number(topic.z)||0,objectScale:Number(topic.scale)||1,name:topic.name,category:topic.category||'object',gifSrc:topic.gifSrc||'',seed,phase:(seed%1000)/100,weight:Math.max(3,topic.weight||1),motion:topic.animation||topic.motion||'idle',prompt:topic.prompt||topic.name,born:state.time});
      speechWorld.spawned++;
      sendClientDebug({event:'spawn_object', name:topic.name, category:topic.category||'object', gifSrc:topic.gifSrc||'', x:Math.round(pos.x), y:Math.round(pos.y), px:Math.round(pos.x-state.player.x), py:Math.round(pos.y-state.player.y), copyIndex, topicIndex, totalObjects:state.speechObjects.length});
      return true;
    }
  }
  return false;
}
function updateSpeechSpawns(){ let budget=1; while(budget-- > 0 && speechWorld.queue.length){ const topic=speechWorld.queue.pop(); spawnSpeechObject(topic); } }
function hasName(o,...parts){ const n=String(o.name||'').toLowerCase(); return parts.some(p=>n.includes(p)); }
function drawEdgeIndicator(o){
  const p = worldToScreen(o.x,o.y,.1);
  if(p.x > -24 && p.x < W+24 && p.y > -24 && p.y < H+24) return;
  const x = Math.max(18, Math.min(W-18, p.x));
  const y = Math.max(18, Math.min(H-18, p.y));
  const a = Math.atan2(p.y - H/2, p.x - W/2);
  ctx.save();
  ctx.translate(x,y); ctx.rotate(a);
  ctx.fillStyle='rgba(124,249,255,.9)'; ctx.strokeStyle='rgba(5,7,14,.95)'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(13,0); ctx.lineTo(-8,-8); ctx.lineTo(-5,0); ctx.lineTo(-8,8); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
}
function drawGeneratedObject(o){
  const p=worldToScreen(o.x,o.y,o.z||0), n=String(o.name||'object').toLowerCase(), cat=String(o.category||'object').toLowerCase(), t=state.time+(o.phase||0)*6;
  const sc=Math.max(.72,Math.min(1.45,p.scale*(o.objectScale||1)))*(1+Math.sin(t*2.2)*.018); ctx.save(); ctx.translate(p.x,p.y); ctx.scale(sc,sc); ctx.lineWidth=3; ctx.lineCap='round'; ctx.lineJoin='round'; const rec=ensureTopicGif(o); if(rec && rec.state==='ready' && rec.img && rec.img.naturalWidth){ const size=90; ctx.imageSmoothingEnabled=true; ctx.drawImage(rec.img,-size/2,-size/2,size,size); } else { drawImagePendingMarker(n,t); }
  ctx.font='700 13px system-ui, sans-serif'; ctx.textAlign='center'; ctx.textBaseline='top'; ctx.fillStyle='rgba(5,10,20,.82)'; ctx.strokeStyle='rgba(124,249,255,.75)'; ctx.lineWidth=1.5; const label=String(o.name||'object').replace(/\b\w/g,c=>c.toUpperCase()); const w=Math.max(56,Math.min(150,18+label.length*7)); ctx.beginPath(); ctx.roundRect(-w/2,34,w,21,8); ctx.fill(); ctx.stroke(); ctx.fillStyle='#eaffff'; ctx.fillText(label,0,38,w-8); ctx.restore();
}
function drawTopicVector(n,cat,t){ if(/poop|shit|crap|kacke/.test(n)) return drawPoop(t); if(/bone/.test(n)) return drawBone(t); if(/bicycle|bike|fahrrad|mountainbike|rennrad|racing/.test(n)) return drawBike(t,/mountain/.test(n),/racing|renn/.test(n)); if(/flower|blume|flauer/.test(n)) return drawFlowerObj(t); if(/tree|baum/.test(n)) return drawTreeObj(t); if(/street|ground/.test(n)) return drawStreetObj(t); if(/dog|hund/.test(n)) return drawDogObj(t); if(/dancing|dance/.test(n)) return drawDancer(t); if(/singer|sing|music/.test(n)) return drawSinger(t); if(/hobo|homeless|lying person/.test(n)) return drawLyingPerson(t); if(/people|jewish|jews/.test(n)) return drawPeople(t); if(/bottle|alcohol/.test(n)) return drawBottle(t); if(/decay|smell/.test(n)) return drawSmell(t); if(/trash/.test(n)) return drawTrashObj(t); if(/house|haus/.test(n)) return drawHouseObj(t); return drawGenericObj(t); }
function drawImagePendingMarker(n,t){
  ctx.save();
  ctx.strokeStyle='rgba(124,249,255,.85)'; ctx.fillStyle='rgba(5,10,20,.55)'; ctx.lineWidth=3;
  ctx.beginPath(); ctx.roundRect(-32,-32,64,64,14); ctx.fill(); ctx.stroke();
  ctx.setLineDash([10,8]); ctx.beginPath(); ctx.arc(0,0,22,t*2,t*2+Math.PI*1.35); ctx.stroke(); ctx.setLineDash([]);
  ctx.font='700 10px system-ui, sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillStyle='#eaffff'; ctx.fillText('GIF',0,0);
  ctx.restore();
}
function glowStroke(){ ctx.shadowColor='rgba(124,249,255,.45)'; ctx.shadowBlur=8; }
function drawPoop(t){ glowStroke(); ctx.fillStyle='#7a3b1d'; ctx.strokeStyle='#2b1209'; for(const e of [[0,18,28,9],[-8,7,20,12],[8,-5,17,11],[0,-17,11,8]]){ctx.beginPath();ctx.ellipse(e[0],e[1],e[2],e[3],0,0,Math.PI*2);ctx.fill();ctx.stroke();} ctx.fillStyle='#f4e6c8'; ctx.beginPath(); ctx.arc(-7,-6,3,0,Math.PI*2); ctx.arc(8,-7,3,0,Math.PI*2); ctx.fill(); for(let i=0;i<3;i++){const x=-28+i*28,y=-26-Math.sin(t*2+i)*5;ctx.strokeStyle='rgba(130,100,55,.75)';ctx.beginPath();ctx.moveTo(x,y+10);ctx.bezierCurveTo(x+8,y,x-8,y-8,x+4,y-16);ctx.stroke();}}
function drawBone(t){ glowStroke(); ctx.strokeStyle='#eadfcb'; ctx.fillStyle='#fff8e7'; ctx.lineWidth=10; ctx.beginPath(); ctx.moveTo(-24,8*Math.sin(t)); ctx.lineTo(24,-8*Math.sin(t)); ctx.stroke(); for(const x of [-30,30]) for(const y of [-8,8]){ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#6f604e';ctx.lineWidth=2;ctx.stroke();}}
function drawBike(t,mountain=false,racing=false){ glowStroke(); ctx.strokeStyle=racing?'#ffda5a':mountain?'#5df08a':'#7cf9ff'; ctx.fillStyle='transparent'; ctx.lineWidth=4; for(const x of [-22,22]){ctx.beginPath();ctx.arc(x,15,15,0,Math.PI*2);ctx.stroke();} ctx.beginPath(); ctx.moveTo(-22,15);ctx.lineTo(-4,-8);ctx.lineTo(11,15);ctx.lineTo(-22,15);ctx.lineTo(22,15);ctx.lineTo(-4,-8);ctx.lineTo(22,15);ctx.moveTo(11,15);ctx.lineTo(18,-6);ctx.lineTo(30,-9);ctx.moveTo(-4,-8);ctx.lineTo(-8,-18);ctx.lineTo(-17,-18);ctx.stroke();}
function drawFlowerObj(t){ glowStroke(); ctx.fillStyle='#ff58b8'; ctx.strokeStyle='#7a174c'; for(let i=0;i<8;i++){const a=i*Math.PI/4+t*.15;ctx.beginPath();ctx.ellipse(Math.cos(a)*14,Math.sin(a)*10-8,9,14,a,0,Math.PI*2);ctx.fill();ctx.stroke();} ctx.fillStyle='#ffe45a';ctx.beginPath();ctx.arc(0,-8,8,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.strokeStyle='#2fbf4a';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(0,2);ctx.lineTo(0,32);ctx.stroke();}
function drawTreeObj(t){ glowStroke(); ctx.fillStyle='#2fbf4a'; ctx.strokeStyle='#145a25'; ctx.beginPath(); ctx.arc(0,-12,25,0,Math.PI*2); ctx.fill(); ctx.stroke(); ctx.fillStyle='#8b5a2b'; ctx.fillRect(-6,5,12,32); }
function drawStreetObj(t){ ctx.strokeStyle='#444b55'; ctx.fillStyle='#303640'; ctx.beginPath(); ctx.roundRect(-38,-6,76,30,10); ctx.fill(); ctx.stroke(); ctx.strokeStyle='#ffd45a'; ctx.setLineDash([12,8]); ctx.beginPath(); ctx.moveTo(-30,9); ctx.lineTo(30,9); ctx.stroke(); ctx.setLineDash([]); }
function drawDogObj(t){ glowStroke(); ctx.fillStyle='#b8793a'; ctx.strokeStyle='#3a2415'; ctx.beginPath(); ctx.ellipse(0,5,28,16,0,0,Math.PI*2); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.arc(-24,-2,13,0,Math.PI*2); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(22,2); ctx.quadraticCurveTo(34,-13,39,-2+Math.sin(t*4)*5); ctx.stroke(); }
function drawDancer(t){ drawStandingPerson(t,'#ff6bd6',true); } function drawSinger(t){ drawStandingPerson(t,'#6bd6ff',false); ctx.strokeStyle='#fff06a'; for(let i=0;i<3;i++){ctx.beginPath();ctx.arc(22+i*9,-22-i*5,4,0,Math.PI*1.4);ctx.stroke();}}
function drawStandingPerson(t,color,dance){ glowStroke(); ctx.fillStyle='#d9905a'; ctx.strokeStyle='#3a1f14'; ctx.beginPath(); ctx.arc(0,-22,10,0,Math.PI*2); ctx.fill(); ctx.stroke(); ctx.strokeStyle=color; ctx.lineWidth=7; ctx.beginPath(); ctx.moveTo(0,-10);ctx.lineTo(0,12);ctx.stroke(); const a=Math.sin(t*5)*(dance?18:6); ctx.beginPath();ctx.moveTo(0,-2);ctx.lineTo(-20,4+a*.2);ctx.moveTo(0,-2);ctx.lineTo(20,-2-a*.2);ctx.moveTo(0,12);ctx.lineTo(-12,32);ctx.moveTo(0,12);ctx.lineTo(14,31);ctx.stroke();}
function drawLyingPerson(t){ glowStroke(); ctx.strokeStyle='#d9905a'; ctx.fillStyle='#d9905a'; ctx.lineWidth=8; ctx.beginPath(); ctx.arc(-24,10,9,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.moveTo(-12,12);ctx.lineTo(22,16);ctx.moveTo(0,14);ctx.lineTo(-10,28);ctx.moveTo(12,15);ctx.lineTo(27,28);ctx.stroke(); ctx.strokeStyle='#6b7cff'; ctx.beginPath(); ctx.moveTo(-8,8);ctx.lineTo(20,12);ctx.stroke();}
function drawPeople(t){ ctx.save(); ctx.translate(-13,0); drawStandingPerson(t,'#5aa9ff',false); ctx.translate(27,2); drawStandingPerson(t+1,'#ffda5a',false); ctx.restore(); }
function drawBottle(t){ glowStroke(); ctx.fillStyle='#2fbf8a'; ctx.strokeStyle='#063c2b'; ctx.beginPath(); ctx.roundRect(-10,-28,20,58,7); ctx.fill(); ctx.stroke(); ctx.fillStyle='#fff'; ctx.fillRect(-7,-5,14,15); }
function drawSmell(t){ ctx.strokeStyle='rgba(160,120,60,.9)'; ctx.lineWidth=4; for(let i=0;i<4;i++){const x=-24+i*16;ctx.beginPath();ctx.moveTo(x,26);ctx.bezierCurveTo(x+10,12,x-10,0,x+5,-16-Math.sin(t+i)*5);ctx.stroke();}}
function drawTrashObj(t){ glowStroke(); ctx.fillStyle='#6d7a75'; ctx.strokeStyle='#26302d'; ctx.beginPath(); ctx.roundRect(-22,-15,44,42,8); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-28,-18); ctx.lineTo(28,-18); ctx.stroke(); }
function drawHouseObj(t){ glowStroke(); ctx.fillStyle='#c96b3a'; ctx.strokeStyle='#6b2e1d'; ctx.fillRect(-24,-2,48,34); ctx.strokeRect(-24,-2,48,34); ctx.beginPath(); ctx.moveTo(-30,-2); ctx.lineTo(0,-30); ctx.lineTo(30,-2); ctx.closePath(); ctx.fill(); ctx.stroke(); }
function drawGenericObj(t){ glowStroke(); ctx.fillStyle='#9aa7b3'; ctx.strokeStyle='#34404a'; ctx.beginPath(); ctx.roundRect(-24,-24,48,48,12); ctx.fill(); ctx.stroke(); }

function drawEdgeIndicator(o){
  const p=worldToScreen(o.x,o.y,.1);
  if(p.x>-20&&p.x<W+20&&p.y>-20&&p.y<H+20) return;
  const cx=Math.max(16,Math.min(W-16,p.x));
  const cy=Math.max(16,Math.min(H-16,p.y));
  ctx.save(); ctx.fillStyle='rgba(124,249,255,.72)'; ctx.beginPath(); ctx.arc(cx,cy,5,0,Math.PI*2); ctx.fill(); ctx.restore();
}
function drawGrid(){
  const spacing = 80;
  const left = camera.x - W/2 - spacing*2;
  const right = camera.x + W/2 + spacing*2;
  const top = camera.y - H/2 - spacing*2;
  const bottom = camera.y + H/2 + spacing*2;
  ctx.save();
  ctx.lineWidth = 1;
  for(let x = Math.floor(left/spacing)*spacing; x < right; x += spacing){
    const a = worldToScreen(x, 0).x;
    ctx.strokeStyle = Math.abs(x) < 1 ? 'rgba(124,249,255,.22)' : 'rgba(124,249,255,.07)';
    ctx.beginPath(); ctx.moveTo(a, 0); ctx.lineTo(a, H); ctx.stroke();
  }
  for(let y = Math.floor(top/spacing)*spacing; y < bottom; y += spacing){
    const b = worldToScreen(0, y).y;
    ctx.strokeStyle = Math.abs(y) < 1 ? 'rgba(124,249,255,.22)' : 'rgba(124,249,255,.07)';
    ctx.beginPath(); ctx.moveTo(0, b); ctx.lineTo(W, b); ctx.stroke();
  }
  ctx.restore();
}
function draw(){ ctx.clearRect(0,0,W,H); const g=ctx.createRadialGradient(W/2,H/2,10,W/2,H/2,Math.max(W,H)); g.addColorStop(0,'#121d33'); g.addColorStop(1,'#02030a'); ctx.fillStyle=g; ctx.fillRect(0,0,W,H); drawGrid(); const items=[]; for(const listName of ['stones','echoes','gates','voids','wisps','glyphs','sparks','speechObjects']) for(const o of state[listName]) if(!o.got) items.push({type:listName,y:o.y,o}); items.push({type:'player',y:state.player.y,o:state.player}); items.sort((a,b)=>a.y-b.y); for(const it of items){ const o=it.o; if(it.type==='speechObjects') drawGeneratedObject(o); if(it.type==='stones') drawSprite('stone',o.x,o.y,44); if(it.type==='echoes') drawSprite('echo',o.x,o.y,46); if(it.type==='gates') { if(!drawAnim('gate_shimmer',o.x,o.y,72,0,o.phase||0)) drawSprite('gate',o.x,o.y,72); } if(it.type==='voids') { if(!drawAnim('void_pulse',o.x,o.y,Math.max(48,o.r*1.7),0,o.phase||0)) drawSprite('void',o.x,o.y,Math.max(48,o.r*1.7)); } if(it.type==='wisps') drawSprite('wisp',o.x,o.y,38,.3); if(it.type==='glyphs') drawSprite('glyph',o.x,o.y,44,.1); if(it.type==='sparks') { if(!drawAnim('spark_spin',o.x,o.y,34,o.z,o.x*.01)) drawSprite('spark',o.x,o.y,34,o.z); } if(it.type==='player'){ const q=worldToScreen(o.x,o.y,.2); ctx.fillStyle='rgba(0,0,0,.35)'; ctx.beginPath(); ctx.ellipse(q.x,q.y+18*q.scale,18*q.scale,7*q.scale,0,0,Math.PI*2); ctx.fill(); const moving=Math.hypot(o.vx,o.vy)>0.05; if(!drawAnim(moving?'player_walk':'player_idle',o.x,o.y,46,.2)) drawSprite('player',o.x,o.y,42,.2); } } for(const o of state.speechObjects) drawEdgeIndicator(o); if(state.player.pulse>0){ const p=worldToScreen(state.player.x,state.player.y); ctx.strokeStyle=`rgba(124,249,255,${state.player.pulse*.5})`; ctx.lineWidth=3; ctx.beginPath(); ctx.arc(p.x,p.y,180*(1-state.player.pulse)+40,0,Math.PI*2); ctx.stroke(); } }
function loop(now){ const dt=Math.min(.033,(now-last)/1000); last=now; tick(dt); draw(); requestAnimationFrame(loop); }
function pulse(){ state.player.pulse=1; state.insight+=1; say('Pulse sent. Hidden structure shivers at the edge of the field.'); }


let mic = {active:false, ws:null, stream:null, ctx:null, source:null, processor:null, zeroGain:null, lines:[], reconnectTimer:null, fullText:'', debugLines:[], pendingDebug:[], bytesSent:0, framesSent:0, lastMeter:0, httpActive:false, httpStarting:false, httpSession:null, httpChunks:[], httpBytes:0, httpLastPost:0, httpPosting:false, httpFailUntil:0, httpFailCount:0, heardSpeech:false, workingAudio:false, lastUsefulAudioAt:0, stableDeviceId:null};
const micStatus = document.getElementById('mic-status');
const micText = document.getElementById('mic-text');
const topicInput = document.getElementById('topic-input');
const topicTest = document.getElementById('topic-test');
const micToggle = document.getElementById('mic-toggle');
const micCopy = document.getElementById('mic-copy');
const micHide = document.getElementById('mic-hide');
const micShow = document.getElementById('mic-show');

function httpProbe(event, data={}){
  try{
    const q = new URLSearchParams({event, build:'20260711-1254-utterance-vad-no-tiny-whisper-slices', ts:String(Date.now())});
    for(const [k,v] of Object.entries(data||{})) q.set(k, typeof v === 'string' ? v.slice(0,180) : JSON.stringify(v).slice(0,180));
    const img = new Image(); img.src = `/llm_game_probe?${q.toString()}`;
  }catch(err){}
}
function timeoutAfter(ms, label){ return new Promise((_, reject)=>setTimeout(()=>reject(new Error(label || `timeout ${ms}ms`)), ms)); }
async function listAudioDevices(){
  try{
    if(!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return [];
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter(d=>d.kind==='audioinput').map(d=>({kind:d.kind,label:d.label||'',deviceId:d.deviceId||'',groupId:d.groupId||''}));
  }catch(err){ return [{error:String(err && (err.name||err.message) || err)}]; }
}
function shortDeviceId(id){ const s=String(id||''); return s.length>24 ? s.slice(0,10)+'…'+s.slice(-8) : s; }
function deviceLogList(devices){ return (devices||[]).map(d=>d && d.error ? d : ({kind:d.kind,label:d.label||'',deviceId:shortDeviceId(d.deviceId),groupId:shortDeviceId(d.groupId)})); }
function populateMicDeviceSelect(devices){
  const sel=document.getElementById('mic-device'); if(!sel) return;
  const old=sel.value || 'auto'; sel.innerHTML='';
  const opt=(value,label)=>{ const o=document.createElement('option'); o.value=value; o.textContent=label; sel.appendChild(o); };
  opt('auto','auto microphone');
  for(const d of devices||[]){
    if(!d || d.kind!=='audioinput') continue;
    const label=d.label || (d.deviceId==='default'?'default microphone':d.deviceId==='communications'?'communications microphone':'microphone');
    opt(d.deviceId || 'auto', label);
  }
  if([...sel.options].some(o=>o.value===old)) sel.value=old;
}

window.__LLM_GAME_BUILD='20260711-1254-utterance-vad-no-tiny-whisper-slices'; document.documentElement.dataset.llmGameBuild='20260711-1254-utterance-vad-no-tiny-whisper-slices'; httpProbe('script_loaded', {href:location.href, ua:navigator.userAgent||''});
window.addEventListener('error', e=>{ const msg=`${e.message||'error'} @ ${e.filename||''}:${e.lineno||''}:${e.colno||''}`; try{ appendMicDebug(`JS ERROR: ${msg}`); }catch(_){} httpProbe('js_error',{error:msg}); });
window.addEventListener('unhandledrejection', e=>{ const msg=String(e.reason && (e.reason.stack||e.reason.message) || e.reason || 'unhandled rejection'); try{ appendMicDebug(`JS PROMISE ERROR: ${msg}`); }catch(_){} httpProbe('js_promise_error',{error:msg}); });

function appendMicDebug(line){
  if(!micText) return;
  if(!mic.debugLines) mic.debugLines=[];
  if(!mic.debugLines) mic.debugLines=[];
  const stamp = new Date().toLocaleTimeString();
  mic.debugLines.push(`[${stamp}] ${line}`);
  if(mic.debugLines.length > 220) mic.debugLines.splice(0, mic.debugLines.length - 220);
  renderMicDebug();
}
function renderMicDebug(){
  if(!micText) return;
  if(!mic.debugLines) mic.debugLines=[];
  if(!mic.debugLines) mic.debugLines=[];
  const full = mic.fullText ? `FULL STT:\n${mic.fullText}\n\n` : '';
  micText.textContent = full + mic.debugLines.join('\n');
  micText.scrollTop = micText.scrollHeight;
}
function manualTopicItems(text){
  const words = String(text||'').toLowerCase().replace(/[^a-z0-9\s-]+/g,' ').split(/\s+/).filter(Boolean);
  const banned = new Set(['and','or','the','a','an','with','of','in','on','to','for','test','spawn']);
  const seen = new Set();
  const out = [];
  for(const w of words){
    if(banned.has(w) || seen.has(w)) continue;
    seen.add(w);
    let category = 'object';
    if(/cat|dog|horse|bird|chicken|rooster|elephant/.test(w)) category='animal';
    else if(/tree|flower|forest|grass|plant/.test(w)) category='plant';
    else if(/straw|apple|banana|pizza|cake|bread|food/.test(w)) category='food';
    else if(/castle|house|city|hotel|school/.test(w)) category='place';
    else if(/rain|storm|cloud|snow|wind|weather/.test(w)) category='weather';
    else if(/song|music|sound|bark/.test(w)) category='sound';
    out.push({name:w, category, weight:3, reason:'manual topic test', animation:'animated gif'});
  }
  return out.slice(0,24);
}
function runManualTopicTest(){
  const topicInput=document.getElementById('topic-input');
  const text = topicInput ? topicInput.value : '';
  appendMicDebug(`MANUAL SCENE TEST: ${JSON.stringify(text)}`);
  const ws = mic.ws;
  if(ws && ws.readyState === WebSocket.OPEN){ ws.send(JSON.stringify({type:'debug_transcript', text})); setMicStatus('manual scene sent to server planner'); return; }
  setMicStatus('manual scene test needs active STT websocket');
}

function namesOf(items){ return (items||[]).map(x => x && x.name ? x.name : String(x)).filter(Boolean).join(', ') || '(none)'; }
function shouldSuppressStatus(text){ return /duplicate silence|listening: silence/i.test(String(text||'')); }
function setMicStatus(text){
  if(shouldSuppressStatus(text)) return;
  if(micStatus){
    micStatus.textContent = text;
    const value=String(text||'').toLowerCase();
    micStatus.dataset.state = /error|failed|unavailable|disconnected/.test(value) ? 'error' : /transcrib|connecting|requesting|retry/.test(value) ? 'busy' : /heard|updated/.test(value) ? 'success' : /voice detected/.test(value) ? 'speech' : 'ready';
  }
  appendMicDebug(`STATUS: ${text}`);
}

function setMicButton(text){ if(micToggle) micToggle.textContent = text; }
function setMicFullText(text){ mic.fullText = String(text || ''); renderMicDebug(); }
function isPlaceholderSttText(text){
  const raw=String(text||'').trim();
  const f=raw.toLowerCase().replace(/[\[\]\(\)]/g,' ').replace(/[^a-z0-9 -]+/g,' ').replace(/\s+/g,' ').trim();
  return !f || f.includes('foreign language') || f.includes('non english speech') || raw.toLowerCase().includes('non-english speech');
}
function pushMicLine(text){ if(!text || isPlaceholderSttText(text)) return; if(!mic.lines) mic.lines=[]; mic.lines.push(String(text)); mic.lines=mic.lines.slice(-40); appendMicDebug(`STT LINE: ${text}`); }
function setTopicStatus(items){ const n=(items||[]).length; appendMicDebug(n ? `TOPIC STATUS: world topics detected ${n}: ${namesOf(items)}` : 'TOPIC STATUS: listening for world topics'); }
function flushClientDebug(){
  try{
    if(!mic.ws || mic.ws.readyState!==WebSocket.OPEN || !mic.pendingDebug) return;
    while(mic.pendingDebug.length) mic.ws.send(JSON.stringify({type:'client_debug', ...mic.pendingDebug.shift()}));
  }catch(err){}
}
function sendClientDebug(payload){
  try{
    if(payload && payload.event) httpProbe(`client_${payload.event}`, payload);
    if(!mic.pendingDebug) mic.pendingDebug=[];
    const item={ts:Date.now(), ...payload};
    if(mic.ws && mic.ws.readyState===WebSocket.OPEN) mic.ws.send(JSON.stringify({type:'client_debug', ...item}));
    else mic.pendingDebug.push(item);
  }catch(err){}
}

function browserSttLanguage(){
  const raw=((navigator.languages&&navigator.languages[0])||navigator.language||'en').toLowerCase().replace('_','-');
  const code=raw.split('-')[0];
  return /^[a-z]{2}$/.test(code) ? code : 'en';
}
function httpBase(){ return `${location.origin}/llm_game_stt/http`; }

async function startHttpFallback(reason='ws_failed'){
  if(!mic.active || mic.stopReason==='user_stop') return;
  if(mic.httpActive || mic.httpStarting || !mic.active) return;
  const now=performance.now();
  if(mic.httpFailUntil && now < mic.httpFailUntil) return;
  mic.httpStarting = true;
  appendMicDebug(`HTTP FALLBACK START: ${reason}`);
  httpProbe('http_fallback_start', {reason});
  try{
    const resp = await fetch(`${httpBase()}/start`, {method:'POST', cache:'no-store', headers:{'Accept':'application/json','Content-Type':'application/json'}, body:JSON.stringify({language:mic.language||browserSttLanguage()})});
    const ct = resp.headers.get('content-type') || '';
    const body = await resp.text();
    if(!resp.ok || !ct.includes('application/json')) throw new Error(`bad HTTP STT route status=${resp.status} content-type=${ct} body=${body.slice(0,80)}`);
    const data = JSON.parse(body);
    mic.httpSession = data.session;
    mic.httpActive = true;
    mic.httpStarting = false;
    mic.httpFailCount = 0; mic.httpFailUntil = 0;
    setMicStatus(`HTTP audio active ${mic.httpSession}`);
    handleServerMsg(data);
    httpProbe('http_fallback_ready', {session:mic.httpSession});
  }catch(err){
    mic.httpStarting = false;
    mic.httpActive = false;
    const msg = err && (err.message || err.name) ? (err.message || err.name) : String(err);
    mic.httpFailCount = (mic.httpFailCount||0)+1;
    const wait = Math.min(30000, 1200 * Math.pow(2, Math.min(5, mic.httpFailCount-1)));
    mic.httpFailUntil = performance.now() + wait;
    appendMicDebug(`HTTP FALLBACK FAIL: ${msg}; retry blocked ${Math.round(wait/1000)}s`);
    setMicStatus('STT HTTP route unavailable; waiting before retry');
    httpProbe('http_fallback_fail', {error:msg, wait});
  }
}

function combineInt16Chunks(chunks){
  let total=0; for(const c of chunks) total += c.length;
  const out = new Int16Array(total); let off=0;
  for(const c of chunks){ out.set(c, off); off += c.length; }
  return out;
}
async function flushHttpAudio(force=false){
  if(!mic.httpActive || !mic.httpSession || mic.httpPosting || !mic.httpChunks.length) return;
  if(!force && performance.now() - mic.httpLastPost < 1000 && mic.httpBytes < 96000) return;
  const chunks = mic.httpChunks.splice(0); const bytes = mic.httpBytes; mic.httpBytes = 0; mic.httpPosting = true; mic.httpLastPost = performance.now();
  try{
    const body = combineInt16Chunks(chunks).buffer;
    const resp = await fetch(`${httpBase()}/${encodeURIComponent(mic.httpSession)}/audio`, {method:'POST', headers:{'Content-Type':'application/octet-stream'}, body, cache:'no-store'});
    const data = await resp.json();
    appendMicDebug(`HTTP AUDIO POST: sent=${bytes} kept=${data.bytes_kept} messages=${(data.messages||[]).length}`);
    httpProbe('http_audio_post', {session:mic.httpSession, sent:bytes, kept:data.bytes_kept, messages:(data.messages||[]).length});
    for(const msg of (data.messages||[])) handleServerMsg(msg);
  }catch(err){
    const msg = err && (err.message || err.name) ? (err.message || err.name) : String(err);
    appendMicDebug(`HTTP AUDIO ERROR: ${msg}`); httpProbe('http_audio_error',{error:msg});
    mic.httpChunks = chunks.concat(mic.httpChunks); mic.httpBytes += bytes;
  }finally{ mic.httpPosting=false; }
}
function queueHttpAudio(pcm, rms=0, peak=0){
  if(!mic.httpActive){
    const wsState = mic.ws ? mic.ws.readyState : WebSocket.CLOSED;
    const connecting = wsState === WebSocket.CONNECTING;
    const waited = performance.now() - (mic.wsConnectStartedAt || 0);
    if(connecting && waited < 8000){
      if(performance.now()-mic.lastMeter>1500){ appendMicDebug(`MIC: waiting for websocket open; no HTTP fallback yet state=${wsState} rms=${rms.toFixed(5)} peak=${peak}`); mic.lastMeter=performance.now(); }
      return;
    }
    if(!(mic.httpFailUntil && performance.now()<mic.httpFailUntil)) startHttpFallback('audio_without_ws');
    return;
  }
  mic.httpChunks.push(new Int16Array(pcm)); mic.httpBytes += pcm.byteLength;
  if(performance.now()-mic.lastMeter>1000){ httpProbe('http_audio_buffer', {session:mic.httpSession, queued:mic.httpBytes, rms:rms.toFixed ? rms.toFixed(5) : rms, peak}); mic.lastMeter=performance.now(); }
  flushHttpAudio(false);
}
function handleServerMsg(msg){
  if(msg.type === 'ready') {
    const lang=msg.language||mic.language||browserSttLanguage();
    setMicStatus(`speech ready · listening (${lang})`);
    appendMicDebug(`READY: model=${msg.model||'unknown'} backend=${msg.backend||'unknown'} sample_rate=${msg.sample_rate} topic_interval=${msg.topics_interval_seconds}`);
  } else if(msg.type === 'ack' && msg.language) {
    mic.language=msg.language;
    setMicStatus(`listening (${msg.language})`);
  } else if(msg.type === 'stt_processing') {
    setMicStatus(`transcribing ${Number(msg.audio_seconds||0).toFixed(1)}s of speech…`);
    appendMicDebug(`STT PROCESSING: backend=${msg.backend||''} language=${msg.language||''} audio_seconds=${msg.audio_seconds}`);
  } else if(msg.type === 'stt') {
    const text = msg.new_text || msg.text || '';
    const silent = !text && (msg.reason === 'silence' || msg.duplicate || msg.suppressed);
    if(msg.suppressed){
      appendMicDebug(`STT BACKEND STATUS: reason=${msg.reason||''} rms=${msg.rms} voiced=${msg.voiced_ratio} seconds=${msg.seconds}`);
      if(msg.reason==='stt_unavailable' || msg.reason==='thor_stt_unavailable') setMicStatus('speech recognition unavailable; audio reached Nitro');
    } else if(!silent) {
      appendMicDebug(`STT RAW: engine=${msg.engine||''} text=${JSON.stringify(msg.text||'')} new=${JSON.stringify(msg.new_text||'')} duplicate=${!!msg.duplicate} reason=${msg.reason||''} rms=${msg.rms} voiced=${msg.voiced_ratio} seconds=${msg.seconds}`);
    }
    const rmsNum = Number(msg.rms)||0;
    if(text || rmsNum > 0.01){ mic.workingAudio=true; mic.lastUsefulAudioAt=performance.now(); mic.stableDeviceId=mic.currentDeviceId||mic.stableDeviceId; }
    if(text){ mic.heardSpeech=true; mic.hardSilent=false; mic.deviceRetryIndex=0; }
    if(msg.full_text && !isPlaceholderSttText(msg.full_text)) setMicFullText(msg.full_text);
    if(text) {
      pushMicLine(text);
      const seconds=Number(msg.seconds||msg.thor_seconds||0);
      setMicStatus(`heard: ${String(text).slice(0,46)}${seconds?` · ${seconds.toFixed(1)}s`:''}`);
    } else if(!silent) {
      setMicStatus('speech detected, but no transcript returned');
    }
  } else if(msg.type === 'topics') {
    appendMicDebug(`TOPICS FROM: ${JSON.stringify(msg.source_text||'')} engine=${msg.engine||''} accepted=${namesOf(msg.candidates||[])} ignored=${(msg.rejected||[]).length}`);
    handleTopics(msg.candidates || [], msg.engine || 'unknown');
    if((msg.candidates||[]).length) setMicStatus(`world updated: ${namesOf(msg.candidates||[]).slice(0,70)}`);
  } else if(msg.type === 'topic_error') {
    appendMicDebug(`TOPIC ERROR: ${msg.error}`); setMicStatus(`scene planner error: ${msg.error}`); sendClientDebug({event:'topic_error_seen', error:msg.error});
  } else if(msg.type === 'error' || msg.type === 'stt_error') {
    appendMicDebug(`SERVER ERROR: ${msg.error||msg.message}`); setMicStatus(`speech error: ${msg.error||msg.message||'unknown'}`);
  }
}
function sttUrl(){ return `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/llm_game_stt/ws/`; }
function connectStt(){
  if(!mic.active) return;
  if(mic.ws && (mic.ws.readyState === WebSocket.OPEN || mic.ws.readyState === WebSocket.CONNECTING)) return;
  const ws = new WebSocket(sttUrl());
  mic.ws = ws;
  ws.binaryType = 'arraybuffer';
  setMicStatus('connecting to Nitro STT');
  ws.onopen = () => { mic.language=mic.language||browserSttLanguage(); setMicStatus(`connected · negotiating ${mic.language}`); ws.send(JSON.stringify({type:'hello', sample_rate:16000, format:'pcm16le', language:mic.language})); sendClientDebug({event:'ws_open'}); flushClientDebug(); if(mic.httpActive || mic.httpSession){ appendMicDebug('WS opened; disabling HTTP fallback session'); } mic.httpActive=false; mic.httpStarting=false; mic.httpSession=null; mic.httpChunks=[]; mic.httpBytes=0; mic.httpPosting=false; mic.httpFailUntil=performance.now()+2500; };
  ws.onmessage = (event) => { try { handleServerMsg(JSON.parse(event.data)); } catch(err) { setMicStatus('STT parse error'); } };
  ws.onclose = (ev) => { appendMicDebug(`WS CLOSE: code=${ev.code} reason=${ev.reason||''} clean=${ev.wasClean}`); httpProbe('ws_close', {code:ev.code, reason:ev.reason||'', clean:ev.wasClean, stopReason:mic.stopReason||''}); if(mic.active && mic.stopReason!=='user_stop'){ startHttpFallback(`ws_close_${ev.code}`); setMicStatus('STT disconnected, reconnecting'); clearTimeout(mic.reconnectTimer); mic.reconnectTimer = setTimeout(connectStt, 1500); } };
  ws.onerror = () => { appendMicDebug('WS ERROR'); httpProbe('ws_error'); startHttpFallback('ws_error'); setMicStatus('STT websocket error'); };
}
function downsample(input, fromRate, toRate){ return downsampleTo16k(input, fromRate); }
function downsampleTo16k(input, inputRate){
  const ratio = inputRate / 16000;
  const length = Math.max(1, Math.round(input.length / ratio));
  const output = new Int16Array(length);
  let offset = 0;
  for(let i=0; i<length; i++){
    const next = Math.round((i+1) * ratio);
    let sum = 0, count = 0;
    for(let j=offset; j<next && j<input.length; j++){ sum += input[j]; count++; }
    offset = next;
    const sample = Math.max(-1, Math.min(1, count ? sum / count : 0));
    output[i] = sample < 0 ? sample * 32768 : sample * 32767;
  }
  return output;
}
function secureContextOk(){
  if(window.isSecureContext) return true;
  const msg = `insecure context: ${location.protocol}//${location.host}; microphone requires HTTPS`;
  setMicStatus(msg);
  appendMicDebug(`MIC FAIL: ${msg}`);
  httpProbe('insecure_context', {href:location.href, protocol:location.protocol});
  try{ location.replace('https://' + location.host + location.pathname + location.search + location.hash); }catch(err){}
  return false;
}
function audioConstraintsFor(deviceId=null, relaxed=false){
  const base={echoCancellation:true, noiseSuppression:true, autoGainControl:true, channelCount:{ideal:1}};
  if(relaxed || !deviceId || deviceId === 'auto') return {audio:base};
  if(deviceId === 'default' || deviceId === 'communications') return {audio:{...base, deviceId}};
  return {audio:{...base, deviceId:{exact:deviceId}}};
}

function candidateAudioDeviceIds(devices){
  const selected=document.getElementById('mic-device');
  const ids=[]; const seen=new Set();
  const add=id=>{ id=id||'auto'; if(!seen.has(id)){ seen.add(id); ids.push(id); } };
  if(selected && selected.value && selected.value!=='auto') add(selected.value);
  add('default');
  add('auto');
  for(const d of devices||[]) if(d && d.kind==='audioinput' && d.deviceId && d.deviceId!=='communications') add(d.deviceId);
  add('communications');
  appendMicDebug(`MIC DEVICE ORDER: ${ids.map(shortDeviceId).join(', ')}`);
  return ids;
}

async function cleanupAudioOnly(){
  try{ if(mic.processor){ mic.processor.disconnect(); } }catch(e){}
  try{ if(mic.zeroGain){ mic.zeroGain.disconnect(); } }catch(e){}
  try{ if(mic.source){ mic.source.disconnect(); } }catch(e){}
  try{ if(mic.stream){ for(const t of mic.stream.getTracks()) t.stop(); } }catch(e){}
  try{ if(mic.ctx){ await mic.ctx.close(); } }catch(e){}
  mic.processor=null; mic.zeroGain=null; mic.source=null; mic.stream=null; mic.ctx=null;
}

async function retrySilentMic(){
  if(!mic.active || mic.restarting || mic.hardSilent) return;
  // Critical: once the current device has carried real speech/useful audio, later silence is not a broken mic.
  if(mic.heardSpeech || mic.workingAudio){
    appendMicDebug('MIC: silence after successful audio; keeping current input device');
    mic.zeroFrames = 0;
    return;
  }
  mic.restarting = true;
  try{
    const devices = await listAudioDevices(); mic.lastDevices = devices; populateMicDeviceSelect(devices);
    const ids = candidateAudioDeviceIds(devices);
    const old = mic.currentDeviceId || 'auto';
    mic.deviceRetryIndex = (mic.deviceRetryIndex || 0) + 1;
    if(mic.deviceRetryIndex > (mic.zeroRetryLimit || 2)){
      mic.hardSilent = true;
      setMicStatus('mic stream is all zero samples; choose another input or unmute OS/browser microphone');
      appendMicDebug('MIC HARD FAIL: live microphone track produced only zero samples. Auto retry stopped. Use the microphone dropdown, unmute the OS input, or choose the headset/default input.');
      httpProbe('mic_zero_samples_hard_fail', {retry:mic.deviceRetryIndex, devices:deviceLogList(devices)});
      sendClientDebug({event:'mic_zero_samples_hard_fail', retry:mic.deviceRetryIndex, devices:deviceLogList(devices)});
      return;
    }
    const ranked = ids.filter(id=>id && id !== 'auto'); const nextId = ranked.length ? ranked[mic.deviceRetryIndex % ranked.length] : 'auto';
    appendMicDebug(`MIC SILENCE: zero samples before useful audio; retry ${mic.deviceRetryIndex}/${mic.zeroRetryLimit||2} old=${shortDeviceId(old)} next=${shortDeviceId(nextId)}`);
    setMicStatus('silent microphone stream; retrying input device');
    httpProbe('silent_mic_retry', {oldDeviceId:shortDeviceId(old), nextDeviceId:shortDeviceId(nextId), retry:mic.deviceRetryIndex, devices:deviceLogList(devices)});
    await cleanupAudioOnly();
    mic.bytesSent=0; mic.framesSent=0; mic.zeroFrames=0; mic.audioCallbacks=0; mic.lastNonZero=0; mic.lastMeter=0;
    await openMicStream(nextId || 'auto', nextId === 'auto');
  }catch(err){ appendMicDebug(`MIC RETRY FAIL: ${err.message||err}`); httpProbe('silent_mic_retry_failed',{error:err.message||String(err)}); }
  finally { mic.restarting = false; }
}

async function openRankedMicStream(devices){
  const ids = candidateAudioDeviceIds(devices);
  let lastErr = null;
  for(const id of ids){
    if(!id || id === 'auto') continue;
    try{
      appendMicDebug(`MIC: trying ranked input ${shortDeviceId(id)}`);
      await openMicStream(id, false);
      return;
    }catch(err){
      lastErr = err;
      appendMicDebug(`MIC: ranked input failed ${shortDeviceId(id)} ${err && err.message ? err.message : err}`);
    }
  }
  appendMicDebug('MIC: all ranked inputs failed; using browser auto fallback');
  await openMicStream('auto', true);
}

async function openMicStream(deviceId='auto', relaxed=false){
  await cleanupAudioOnly();
  mic.currentDeviceId = deviceId || 'auto';
  if(deviceId && deviceId !== 'auto') mic.hardSilent=false;
  mic.restarting = false;
  mic.bytesSent = 0; mic.framesSent = 0; mic.lastMeter = 0; mic.zeroFrames=0; mic.audioCallbacks=0;
  let stream;
  try{
    stream = await Promise.race([
      navigator.mediaDevices.getUserMedia(audioConstraintsFor(deviceId, relaxed)),
      timeoutAfter(8000, 'getUserMedia timeout after 8s')
    ]);
  }catch(err){
    const msg = err && err.message ? err.message : String(err);
    appendMicDebug(`MIC: getUserMedia failed device=${deviceId||'auto'} relaxed=${relaxed} error=${msg}`);
    httpProbe('getUserMedia_failed', {deviceId:deviceId||'auto', relaxed, error:msg});
    if(!relaxed){ throw err; }
    throw err;
  }
  mic.stream=stream;
  const tracks = mic.stream.getAudioTracks ? mic.stream.getAudioTracks().map(t=>({label:t.label, enabled:t.enabled, muted:t.muted, readyState:t.readyState, settings:t.getSettings ? t.getSettings() : {}})) : [];
  appendMicDebug(`MIC: getUserMedia ok device=${deviceId||'auto'} relaxed=${relaxed} tracks=${JSON.stringify(tracks)}`);
  httpProbe('getUserMedia_ok', {deviceId:deviceId||'auto', relaxed, tracks});
  sendClientDebug({event:'getUserMedia_ok', deviceId:deviceId||'auto', relaxed, tracks});
  mic.ctx = new (window.AudioContext || window.webkitAudioContext)();
  const localCtx = mic.ctx;
  appendMicDebug(`MIC: AudioContext created sampleRate=${localCtx.sampleRate} state=${localCtx.state}`);
  sendClientDebug({event:'audio_context_created', sampleRate:localCtx.sampleRate, state:localCtx.state});
  await localCtx.resume();
  appendMicDebug(`MIC: AudioContext resumed state=${localCtx.state}`); httpProbe('audio_context_resumed', {state:localCtx.state});
  sendClientDebug({event:'audio_context_resumed', state:localCtx.state});
  mic.source = localCtx.createMediaStreamSource(mic.stream);
  mic.processor = localCtx.createScriptProcessor(4096, 1, 1);
  mic.zeroGain = localCtx.createGain(); mic.zeroGain.gain.value = 0;
  mic.source.connect(mic.processor);
  mic.processor.connect(mic.zeroGain);
  mic.zeroGain.connect(localCtx.destination);
  mic.processor.onaudioprocess = (event) => {
    if(!mic.active || mic.ctx !== localCtx || localCtx.state === 'closed') return;
    const input = event.inputBuffer.getChannelData(0);
    const pcm = downsampleTo16k(input, localCtx.sampleRate);
    let sum=0, peak=0;
    for(let i=0;i<pcm.length;i++){ const v=Math.abs(pcm[i]); sum += v*v; if(v>peak) peak=v; }
    const rms = Math.sqrt(sum / Math.max(1, pcm.length)) / 32768;
    if(rms>0.010 && performance.now()-(mic.lastVoiceStatus||0)>1200){ mic.lastVoiceStatus=performance.now(); setMicStatus('voice detected'); }
    mic.audioCallbacks = (mic.audioCallbacks || 0) + 1;
    if(rms>0.0015 || peak>1200){ mic.lastNonZero=performance.now(); mic.workingAudio=true; mic.lastUsefulAudioAt=performance.now(); mic.stableDeviceId=mic.currentDeviceId||mic.stableDeviceId; mic.zeroFrames=0; } else { mic.zeroFrames++; }
    if((mic.audioCallbacks||0)>90 && mic.zeroFrames>90 && !mic.restarting && !mic.hardSilent && !mic.heardSpeech && !mic.workingAudio){ appendMicDebug('MIC: zero/near-silent input before any successful audio; retrying capture path'); retrySilentMic(); return; }
    if(mic.httpActive){ queueHttpAudio(pcm, rms, peak); return; }
    const ws = mic.ws;
    if(!ws || ws.readyState !== WebSocket.OPEN){
      queueHttpAudio(pcm, rms, peak);
      if(performance.now()-mic.lastMeter>1000){ if(mic.framesSent % 120 === 0) appendMicDebug(`MIC: audio frames but ws not open state=${ws?ws.readyState:'none'} rms=${rms.toFixed(5)} peak=${peak}`); httpProbe('audio_frame_ws_not_open', {wsState:ws?ws.readyState:null, rms:rms.toFixed(5), peak, zeroFrames:mic.zeroFrames, callbacks:mic.audioCallbacks, deviceId:mic.currentDeviceId||'auto'}); sendClientDebug({event:'audio_frame_ws_not_open', wsState:ws?ws.readyState:null, rms, peak, zeroFrames:mic.zeroFrames, callbacks:mic.audioCallbacks, deviceId:mic.currentDeviceId||'auto'}); mic.lastMeter=performance.now(); }
      return;
    }
    if(ws.bufferedAmount > 1_500_000){
      if(performance.now()-mic.lastMeter>1000){ appendMicDebug(`MIC: websocket backpressure buffered=${ws.bufferedAmount}; switching to HTTP fallback`); httpProbe('ws_backpressure_switch_http', {buffered:ws.bufferedAmount, rms:rms.toFixed(5), peak}); sendClientDebug({event:'ws_backpressure_switch_http', buffered:ws.bufferedAmount, rms, peak}); mic.lastMeter=performance.now(); }
      try{ ws.close(4000, 'audio backpressure'); }catch(e){}
      if(!(mic.httpFailUntil && performance.now()<mic.httpFailUntil)) startHttpFallback('ws_backpressure');
      return;
    }
    ws.send(pcm.buffer);
    mic.bytesSent += pcm.byteLength;
    mic.framesSent++;
    if(performance.now()-mic.lastMeter>1000){ if(mic.framesSent % 120 === 0) appendMicDebug(`MIC: sent frames=${mic.framesSent} bytes=${mic.bytesSent} rms=${rms.toFixed(5)} peak=${peak} zero=${mic.zeroFrames}`); httpProbe('audio_meter_http', {frames:mic.framesSent, bytes:mic.bytesSent, rms:rms.toFixed(5), peak, zeroFrames:mic.zeroFrames, callbacks:mic.audioCallbacks, deviceId:mic.currentDeviceId||'auto'}); sendClientDebug({event:'audio_meter', frames:mic.framesSent, bytes:mic.bytesSent, rms, peak, zeroFrames:mic.zeroFrames, callbacks:mic.audioCallbacks, deviceId:mic.currentDeviceId||'auto'}); mic.lastMeter=performance.now(); }
  };
  setMicStatus('mic active'); appendMicDebug('STATUS: mic active'); sendClientDebug({event:'mic_active', deviceId:deviceId||'auto', relaxed});
}

async function startMic(){
  if(mic.active) return;
  if(!secureContextOk()) return;
  if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){ setMicStatus('browser has no getUserMedia'); appendMicDebug('MIC FAIL: browser has no getUserMedia'); httpProbe('no_getUserMedia'); return; }
  mic.active = true;
  mic.language = browserSttLanguage();
  mic.bytesSent = 0; mic.framesSent = 0; mic.lastMeter = 0; mic.zeroFrames=0; mic.audioCallbacks=0; mic.lastNonZero=0; mic.deviceRetryIndex=0; mic.zeroRetryLimit=2; mic.currentDeviceId=null; mic.restarting=false; mic.hardSilent=false; mic.heardSpeech=false; mic.workingAudio=false; mic.lastUsefulAudioAt=0; mic.stableDeviceId=null;
  mic.pendingDebug = []; mic.httpActive=false; mic.httpStarting=false; mic.httpSession=null; mic.httpChunks=[]; mic.httpBytes=0; mic.httpPosting=false; mic.httpFailUntil=0; mic.httpFailCount=0;
  setMicButton('stop mic'); setMicStatus(`requesting microphone (${mic.language})`); appendMicDebug('MIC: startMic called'); httpProbe('startMic_called'); sendClientDebug({event:'start_mic_called', userAgent:navigator.userAgent||''});
  const beforeDevices = await listAudioDevices(); mic.lastDevices = beforeDevices;
  populateMicDeviceSelect(beforeDevices); appendMicDebug(`MIC DEVICES BEFORE: ${JSON.stringify(deviceLogList(beforeDevices))}`); httpProbe('devices_before', {audioInputs:beforeDevices.length, devices:beforeDevices});
  try {
    const afterDevices = await listAudioDevices(); mic.lastDevices = afterDevices;
    populateMicDeviceSelect(afterDevices); appendMicDebug(`MIC DEVICES AFTER: ${JSON.stringify(deviceLogList(afterDevices))}`); httpProbe('devices_after', {audioInputs:afterDevices.length, devices:afterDevices});
    connectStt();
    setTimeout(()=>{ if(mic.active && mic.stopReason!=='user_stop' && (!mic.ws || mic.ws.readyState!==WebSocket.OPEN)) startHttpFallback('ws_open_timeout'); }, 1600);
    await openRankedMicStream(afterDevices);
  } catch(err){ appendMicDebug(`MIC ERROR: ${err.stack || err.message || err}`); httpProbe('mic_error', {error:err.message||String(err)}); sendClientDebug({event:'mic_failed', error:err.message||String(err)}); setMicStatus(`mic failed: ${err.message || err}`); stopMic(); }
}
async function stopMic(){
  mic.stopReason='user_stop';
  if(mic.httpActive && mic.httpSession){ try{ await flushHttpAudio(); await fetch(httpBase() + '/' + mic.httpSession + '/stop', {method:'POST'}); }catch(e){} }
  if(mic.ws){ try{ mic.ws.close(); }catch(e){} }
  await cleanupAudioOnly();
  mic.active=false; mic.ws=null; mic.httpActive=false; mic.httpStarting=false; mic.httpSession=null; mic.httpChunks=[]; mic.httpBytes=0; mic.httpPosting=false; mic.restarting=false;
  setMicButton('start mic'); setMicStatus('mic off'); appendMicDebug('STATUS: mic off');
}
function isInsideMicPanelTarget(target){
  try { return !!(target && target.closest && target.closest('#mic-panel')); } catch(e) { return false; }
}
function copyMicLog(ev){
  if(ev){ try{ ev.preventDefault(); ev.stopPropagation(); }catch(e){} }
  const text = micText ? (micText.innerText || micText.textContent || '') : '';
  const done=(ok,err='')=>{ try{ setMicStatus(ok ? `log copied (${text.length} chars)` : `copy failed: ${err || 'select text manually'}`); appendMicDebug(ok ? `COPY OK chars=${text.length}` : `COPY FAIL: ${err || 'unknown'}`); httpProbe(ok?'copy_log_ok':'copy_log_failed',{chars:text.length,error:err}); }catch(e){} };
  if(!text){ done(false,'empty log'); return; }
  try{
    const ta=document.createElement('textarea'); ta.value=text; ta.setAttribute('readonly','');
    ta.style.position='fixed'; ta.style.left='0'; ta.style.top='0'; ta.style.width='1px'; ta.style.height='1px'; ta.style.opacity='0.01'; ta.style.zIndex='999999';
    document.body.appendChild(ta); ta.focus(); ta.select(); ta.setSelectionRange(0, ta.value.length);
    const ok=document.execCommand && document.execCommand('copy'); document.body.removeChild(ta);
    if(ok){ done(true); return; }
  }catch(e){}
  if(navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(()=>done(true)).catch(err=>done(false, err && err.message ? err.message : String(err)));
  else done(false,'clipboard unavailable');
}

function bindMic(){
  if(micToggle) micToggle.addEventListener('click', (ev) => { try{ev.preventDefault(); ev.stopPropagation();}catch(e){} httpProbe('mic_button_click', {active:mic.active}); mic.active ? stopMic() : startMic(); }, {passive:false});
  if(micCopy) micCopy.addEventListener('click', copyMicLog, {passive:false});
  if(micHide) micHide.addEventListener('click', ev => {
    try{ev.preventDefault(); ev.stopPropagation();}catch(e){}
    const p=document.getElementById('mic-panel'); if(!p) return;
    const collapsed=p.classList.toggle('debug-collapsed');
    micHide.textContent = collapsed ? 'show debug' : 'hide debug';
    httpProbe(collapsed ? 'debug_panel_hidden' : 'debug_panel_shown',{});
  }, {passive:false});
  if(micShow) micShow.hidden=true;
  if(topicTest) topicTest.addEventListener('click', (ev)=>{ try{ev.preventDefault(); ev.stopPropagation();}catch(e){} runManualTopicTest(); }, {passive:false});
  const panel=document.getElementById('mic-panel');
  if(panel){ ['pointerdown','pointermove','pointerup','touchstart','touchmove','touchend','mousedown','mousemove','mouseup','click','dblclick','contextmenu'].forEach(kind => panel.addEventListener(kind, ev => { try{ ev.stopPropagation(); }catch(e){} }, {passive:false})); }
  if(micText){ ['pointerdown','pointermove','pointerup','touchstart','touchmove','touchend','mousedown','mousemove','mouseup','click','dblclick','contextmenu'].forEach(kind => micText.addEventListener(kind, ev => { try{ ev.stopPropagation(); }catch(e){} }, {passive:false})); }
}

function bind(){ addEventListener('resize',resize); addEventListener('keydown',e=>{ keys.add(e.key); if(e.key===' ') pulse(); }); addEventListener('keyup',e=>keys.delete(e.key)); document.addEventListener('contextmenu',e=>{ if(!isInsideMicPanelTarget(e.target)) e.preventDefault(); }); document.addEventListener('selectstart',e=>{ if(!isInsideMicPanelTarget(e.target)) e.preventDefault(); }); document.getElementById('fullscreen').onclick=()=>document.documentElement.requestFullscreen?.(); document.getElementById('reset').onclick=reset; document.getElementById('pulse').onclick=pulse; bindMic(); bindStick(); }
resize(); bind(); reset(); requestAnimationFrame(loop);
