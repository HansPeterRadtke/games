// Semantic cause/effect supervisor: off-screen changes remain prose/facts, without
// running distant physics; visible changes pass through sequential states and events.
const STAGES=[
 {after:0,type:'paper_smolders',entity:'shelter-note',condition:'smoldering',message:'The paper begins to smolder.'},
 {after:5,type:'paper_burning',entity:'shelter-note',condition:'burning',message:'Flames begin consuming the paper.'},
 {after:12,type:'bench_smoldering',entity:'shelter-bench',condition:'smoldering',message:'Heat spreads to the dry oak bench.'},
 {after:19,type:'paper_ashes',entity:'shelter-note',condition:'ashes',message:'The writing crumbles into ash.'},
 {after:23,type:'bench_scorching',entity:'shelter-bench',condition:'burning',message:'Small flames crawl along the wooden bench.'},
 {after:34,type:'bench_scorched',entity:'shelter-bench',condition:'scorched',message:'The bench is blackened, but its supports remain standing.'},
 {after:38,type:'shelter_smoky',entity:'shelter-setting',condition:'smoky',message:'Soot settles under the shelter roof.'}
];
const ALLOWED=new Set(['paper_smolders','paper_burning','bench_smoldering','paper_ashes','bench_scorching','bench_scorched','shelter_smoky']);
const finite=(n)=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<1e12;
export class WorldConsequences {
 constructor(){this.pending=[];this.episode=0;this.history=[];}
 startPaperFire(time,semantic){
  if(!finite(time))return {ok:false,message:'Invalid time.'};
  const candle=semantic.entity('shelter-candle'),note=semantic.entity('shelter-note');
  if(!candle||!note)return {ok:false,message:'The objects do not exist here.'};
  if(!candle.state.lit)return {ok:false,message:'The candle is not lit.'};
  if(note.state.wet)return {ok:false,message:'The note is too wet to ignite.'};
  if(note.state.condition!=='intact')return {ok:false,message:'The note is already damaged.'};
  this.episode++;
  this.pending.push(...STAGES.map(s=>({time:time+s.after,type:s.type,entity:s.entity,condition:s.condition,message:s.message,episode:this.episode})));
  this.pending.sort((a,b)=>a.time-b.time);
  return {ok:true,message:'You hold the lit candle to the note. A tiny ember starts to glow.',episode:this.episode};
 }
 extinguish(time,semantic){
  if(!finite(time))return {ok:false,message:'Invalid time.'};
  const jug=semantic.entity('shelter-jug'),note=semantic.entity('shelter-note'),bench=semantic.entity('shelter-bench');
  if(!jug||!note||!bench||jug.state.water<=0)return {ok:false,message:'There is no water left.'};
  const burning=[note,bench].some(e=>['smoldering','burning'].includes(e.state.condition));
  if(!burning)return {ok:false,message:'Nothing is burning here.'};
  jug.state.water=0;jug.state.wet=true;jug.revision++;
  for(const e of [note,bench]){
   if(['smoldering','burning'].includes(e.state.condition)){e.state.condition=e.id==='shelter-note'?'wet':'scorched';e.state.wet=true;e.revision++;}
  }
  this.pending=[];
  this.history.push({id:`extinguish-${this.episode}`,time,type:'fire_extinguished',message:'Water extinguishes the fire before it can spread further.'});
  return {ok:true,message:'The jug empties over the flames. Steam rises and the fire goes out.'};
 }
 advance(time,semantic,observed,emit){
  if(!finite(time)||typeof observed!=='function'||typeof emit!=='function')throw Error('Invalid consequence step');
  let n=0;while(this.pending.length&&this.pending[0].time<=time+1e-7){
   const event=this.pending.shift(),entity=semantic.entity(event.entity);if(!entity)continue;
   if(entity.state.wet||['wet','ashes'].includes(entity.state.condition)&&event.condition!=='ashes')continue;
   entity.state.condition=event.condition;entity.state.lastCause='paper_ignited_by_lit_candle';entity.revision++;
   const visibility=observed(entity)?'visible':'offscreen';
   const out={id:`fire-${event.episode}-${event.type}`,type:event.type,entityId:entity.id,cause:'fire_spread',outcome:event.condition,visibility,time:event.time,message:event.message};
   this.history.push(out);if(this.history.length>100)this.history.shift();emit(out);n++;
  }
  return n;
 }
 snapshot(){return {version:1,episode:this.episode,pending:this.pending.map(e=>({...e})),history:this.history.map(e=>({...e}))};}
 restore(s){
  if(!s||s.version!==1||!Number.isInteger(s.episode)||s.episode<0||!Array.isArray(s.pending)||s.pending.length>64||!Array.isArray(s.history)||s.history.length>100)return false;
  for(const x of s.pending){if(!finite(x.time)||!ALLOWED.has(x.type)||!['shelter-note','shelter-bench','shelter-setting'].includes(x.entity)||typeof x.message!=='string'||x.message.length>350||!Number.isInteger(x.episode)||x.episode<0||x.episode>s.episode||!STAGES.some(stage=>stage.type===x.type&&stage.entity===x.entity&&stage.condition===x.condition))return false;}
  if(s.pending.some((e,i)=>i>0&&s.pending[i-1].time>e.time))return false;
  this.episode=s.episode;this.pending=s.pending.map(e=>({...e}));this.history=s.history.map(e=>({...e}));return true;
 }
}
