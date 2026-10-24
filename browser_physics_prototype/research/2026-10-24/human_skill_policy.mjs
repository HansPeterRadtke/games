// Research-only bounded models. Every training row must originate in an opt-in trial
// captured from the authoritative GameCore, never from synthetic teacher code.
export function features(state, previous=null){
  if(!state||!state.player||!state.crate)throw Error('Missing game state');
  const p=state.player,c=state.crate;
  const rel=c.x-p.x, distance=state.goalX-c.x, last=previous||state;
  const values=[rel*.38,p.vx*.35,distance*.45,c.vx*.45,
    (p.y-.82)*.7,p.vy*.3,c.y-.57,c.vy*.5,
    state.contact?1:0,
    last.player.vx*.25,
    last.crate.vx*.35,
    state.speedFactor??1];
  if(!values.every(Number.isFinite))throw Error('Nonfinite observations');
  return values.map(v=>Math.max(-8,Math.min(8,v)));
}
const moves=[-1,0,1];
export function validateRows(rows){
 if(!Array.isArray(rows)||rows.length<30||rows.length>30000)return false;
 return rows.every(r=>Array.isArray(r.f)&&r.f.length===12&&r.f.every(Number.isFinite)&&moves.includes(r.move)&&typeof r.jump==='boolean');
}
function pick(seed){let s=seed>>>0;return ()=>((s=(1664525*s+1013904223)>>>0)/4294967296);}
function forward(weights,f){
 const h=weights.h.map((w,j)=>Math.tanh(w.reduce((sum,v,i)=>sum+v*f[i],weights.bh[j])));
 const logits=weights.out.map((w,j)=>w.reduce((sum,v,i)=>sum+v*h[i],weights.bo[j]));
 const max=Math.max(...logits.slice(0,3)),ex=logits.slice(0,3).map(x=>Math.exp(x-max));
 const denom=ex.reduce((a,b)=>a+b,0),probs=ex.map(x=>x/denom);
 const jump=1/(1+Math.exp(-Math.max(-25,Math.min(25,logits[3]))));
 return {h,probs,jump};
}
export function trainSmallMLP(rows,{epochs=35,hidden=16}={}){
 if(!validateRows(rows)||hidden<4||hidden>32||epochs<1||epochs>100)throw Error('Invalid genuine teaching data');
 const random=pick(915713),d=12;
 const w={
 h:Array.from({length:hidden},()=>Array.from({length:d},()=>(random()-.5)*.25)),
 bh:Array(hidden).fill(0),
 out:Array.from({length:4},()=>Array.from({length:hidden},()=>(random()-.5)*.25)),
 bo:[0,0,0,0]
 };
 const order=Array.from({length:rows.length},(_,i)=>i);
 let loss=0;
 // SGD is intentionally simple and offline; not a state-of-the-art policy.
 for(let epoch=0;epoch<epochs;epoch++){
  for(let i=order.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[order[i],order[j]]=[order[j],order[i]];}
  const rate=.018/(1+epoch*.055);
  loss=0;
  for(const index of order){
   const row=rows[index],{h,probs,jump}=forward(w,row.f);
   const desired=moves.indexOf(row.move),grad=probs.map((p,i)=>p-(i===desired?1:0));
   grad.push((jump-(row.jump?1:0))*.6);
   loss+=-Math.log(Math.max(1e-9,probs[desired]))-.6*(row.jump?Math.log(Math.max(1e-9,jump)):Math.log(Math.max(1e-9,1-jump)));
   const gh=h.map((v,k)=>{
    let sum=0;
    for(let j=0;j<4;j++)sum+=grad[j]*w.out[j][k];
    return sum*(1-v*v);
   });
   for(let j=0;j<4;j++){
    for(let k=0;k<hidden;k++)w.out[j][k]-=rate*grad[j]*h[k];
    w.bo[j]-=rate*grad[j];
   }
   for(let k=0;k<hidden;k++){
    for(let j=0;j<d;j++)w.h[k][j]-=rate*gh[k]*row.f[j];
    w.bh[k]-=rate*gh[k];
   }
  }
 }
 return {kind:'tiny_mlp',weights:w,fitLoss:loss/rows.length,trainedRows:rows.length};
}
export function trainKnn(rows){
 if(!validateRows(rows))throw Error('Invalid genuine teaching data');
 // Time-adjacent frames are autocorrelated; keep labels, and do not claim independent examples.
 const max=2400,step=Math.max(1,Math.ceil(rows.length/max));
 return {kind:'knn',rows:rows.filter((_,i)=>i%step===0),trainedRows:rows.length};
}
export function infer(model,vec){
 if(!Array.isArray(vec)||vec.length!==12||!vec.every(Number.isFinite))throw Error('Bad inference state');
 if(model.kind==='knn'){
  const q=model.rows.map((r,i)=>({i,dist:r.f.reduce((sum,v,j)=>sum+(v-vec[j])**2,0)}))
  .sort((a,b)=>a.dist-b.dist||a.i-b.i).slice(0,9);
  const tally=[0,0,0],jumpCount=q.filter(x=>model.rows[x.i].jump).length;
  for(const x of q)tally[moves.indexOf(model.rows[x.i].move)]++;
  return {move:moves[tally.indexOf(Math.max(...tally))],jump:jumpCount>=5};
 }
 if(model.kind==='tiny_mlp'){
  const r=forward(model.weights,vec);
  return {move:moves[r.probs.indexOf(Math.max(...r.probs))],jump:r.jump>.58};
 }
 throw Error('Invalid policy kind');
}
export function countParameters(model){
 if(model.kind==='tiny_mlp')return model.weights.h.length*12+model.weights.bh.length+model.weights.out.length*model.weights.h.length+4;
 if(model.kind==='knn')return model.rows.length*14;
 return 0;
}
