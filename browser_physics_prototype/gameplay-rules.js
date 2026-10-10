// Game-domain decisions. No renderer/physics imports: effects must pass through the core.
import {attemptResonance,measureResonance} from './hidden-mechanism.js';
const reach=1.45;
const SCENE_ACTIONS=new Set(['bench','candle','jug','note','shelter']);
export function nearbyInteraction(player,semantic,active){
 if(!player||!semantic)return null;
 let options=[];for(const e of semantic.entities){if(e.state?.collected||!['plank','resonator','workbench','spring','wanderer','destination','bench','candle','jug','note'].includes(e.kind))continue;
  const pos=active.get(e.id)?.translation()||e;const distance=Math.hypot(pos.x-player.x,pos.y-player.y,pos.z-player.z);
  if(distance<reach)options.push({id:e.id,kind:e.kind,name:e.name,distance});}
 options.sort((a,b)=>a.distance-b.distance);
 const chosen=options[0];if(!chosen)return null;
 const labels={bench:'Examine bench',candle:'Light candle',jug:'Inspect water jug',note:'Read handwritten note',shelter:'Inspect shelter',plank:'Pick up plank',resonator:'Measure mechanism',workbench:'Repair bridge',spring:'Drink',wanderer:'Talk',destination:'Explore'};
 const e=semantic.entity(chosen.id);const suggested=e.affordances?.find(a=>a.verb===(e.kind==='candle'?'light':e.kind==='note'?'read':e.kind==='jug'?'pour':'inspect'));const label=suggested?.label||labels[chosen.kind];return {...chosen,label:chosen.kind==='candle'&&e.state.lit?'Extinguish candle':chosen.kind==='note'&&e.state.condition==='ashes'?'Examine ashes':label};
}
export function resolveInteraction({actor,character,semantic,active,time,targetId=null,verb=null}){
 let candidate=targetId?null:nearbyInteraction(actor,semantic,active);
 if(targetId){const entity=semantic.entity(targetId);
  if(!entity||entity.state?.collected)return {ok:false,event:'invalid_target',message:'There is no such object.'};
  const pos=active.get(entity.id)?.translation()||entity;
  const distance=Math.hypot(pos.x-actor.x,pos.y-actor.y,pos.z-actor.z);
  if(distance>reach)return {ok:false,event:'too_far',message:`${entity.name} is out of reach.`};
  candidate={id:entity.id,kind:entity.kind,name:entity.name,distance};
 }

 if(!candidate)return {ok:false,event:'nothing_nearby',message:'Nothing is within reach. Move closer to an object.'};
 const target=semantic.entity(candidate.id);
 const allowedVerbs={shelter:['inspect'],bench:['inspect'],candle:['light','extinguish','tip','inspect'],note:['read','inspect','ignite'],jug:['pour','inspect'],plank:['take'],resonator:['measure'],workbench:['repair'],spring:['drink'],wanderer:['talk','tell'],destination:['explore']};
 if(verb!==null&&!allowedVerbs[candidate.kind]?.includes(verb))return {ok:false,event:'invalid_action',message:`That action is not possible with ${candidate.name}.`};
 switch(candidate.kind){
 case 'shelter':return {ok:true,event:'scene_inspected',message:target.description};
 case 'bench':return {ok:true,event:'bench_inspected',message:target.state.condition==='intact'?target.description:`${target.description} Its condition is ${target.state.condition}.`};
 case 'candle':{
  if(verb==='inspect')return{ok:true,event:'candle_inspected',message:`${target.description} It is ${target.state.lit?'lit':'unlit'}.`};
  if(verb==='tip')return {ok:true,event:'candle_tipped',message:'You knock the candle sideways; its movement follows physical forces.',effects:[{type:'tipCandle'}]};
  if(verb!==null&&!['light','extinguish'].includes(verb))return {ok:false,event:'invalid_action',message:'Cannot perform that action with a candle.'};
  if(verb==='light'||verb===null&&!target.state.lit){if(target.state.condition==='ashes'||target.state.wet)return {ok:false,event:'not_flammable',message:'The candle cannot be lit in this condition.'};return{ok:true,event:'candle_lit',message:'You light the candle. A small steady flame appears.',effects:[{type:'lightCandle'}]};}
  if(!target.state.lit)return{ok:false,event:'already_unlit',message:'The candle is not burning.'};
  return {ok:true,event:'candle_extinguished',message:'You snuff out the flame.',effects:[{type:'extinguishCandle'}]};
 }
 case 'note':{
  if(verb==='ignite')return {ok:true,event:'ignition_requested',message:'',effects:[{type:'igniteNote'}]};
  if(verb!==null&&!['read','inspect'].includes(verb))return {ok:false,event:'invalid_action',message:'Unsupported action for this note.'};
  if(target.state.condition==='ashes')return{ok:false,event:'writing_destroyed',message:'The note is ash. Its writing is no longer readable.'};
  return {ok:true,event:'note_read',message:`${target.description} The handwriting adds: “Fire will follow any careless flame, even after its maker has left.”`,effects:[{type:'readNote'}]};
 }
 case 'jug':{
  if(verb==='pour')return{ok:true,event:'water_poured',message:'',effects:[{type:'pourWater'}]};
  return{ok:true,event:'jug_inspected',message:`${target.description} ${target.state.water>0?'Water remains inside.':'The jug is empty.'}`};
 }
 case 'plank':if(character.inventory.plank>=3)return {ok:false,event:'full_pack',message:'You cannot comfortably carry more than three heavy planks.'};
  return {ok:true,event:'plank_collected',message:'You picked up one six-kilogram plank.',effects:[{type:'collect',id:target.id}]};
 case 'resonator':{
  const previous=character.notes.length?character.notes.at(-1).intensity:null;
  const sample=measureResonance(time,previous);
  return {ok:true,event:'measurement',message:`The needle reads ${sample.intensity}. ${sample.trend==='unknown'?'Measure again to find its trend.':'The signal is '+sample.trend+'.'}`,effects:[{type:'recordMeasurement',sample}]};}
 case 'workbench':if(character.bridgeRepaired)return {ok:true,event:'bridge_inspection',message:'The repaired timber deck remains solid.'};
  if(character.inventory.plank<2)return {ok:false,event:'missing_planks',message:`The bridge needs two planks. You are carrying ${character.inventory.plank}. Collect more from the old tree.`};
  return {ok:true,event:'bridge_repaired',message:'You fit the planks onto the surviving bridge supports. The stream is passable.',effects:[{type:'repairBridge'}]};
 case 'spring':return {ok:true,event:'drink',message:'You drink fresh spring water.',effects:[{type:'drink'}]};
 case 'wanderer':{
   const informed=target.state?.knowsShelterFire===true;
   if(character.knows('shelter_fire')&&!informed)return {ok:true,event:'conversation',message:'You tell the traveler about the blackened shelter. They promise to warn others.',effects:[{type:'informTraveler',id:target.id}]};
   if(informed)return {ok:true,event:'conversation',message:'Traveler: "I will warn the village about the shelter fire. We should be careful with open flames."'};
   return {ok:true,event:'conversation',message:character.bridgeRepaired?'Traveler: "The bridge is usable again. Thank you."':'Traveler: "The footbridge ahead lost its deck. There are loose timbers by the old beech."'};
  }
 case 'destination':return {ok:true,event:'discovery',message:'You reached the far bank. The path continues into unexplored country.'};
 default:return {ok:false,event:'invalid_target',message:'This object cannot be used.'};
 }
}
export function resolveExperiment({actor,semantic,character,time}){
 const station=semantic.entity('resonator-1');if(!station||Math.hypot(actor.x-station.x,actor.y-station.y,actor.z-station.z)>1.45)return {ok:false,event:'not_at_station',message:'The mechanism is out of reach.'};
 if(character.fenceOpened)return {ok:true,event:'mechanism_open',message:'The lifting fence is already open.'};
 const result=attemptResonance(time);
 return result.success?{ok:true,event:'resonance_success',message:'The old mechanism clicks. Its lifting fence begins to rise.',effects:[{type:'unlockFence'}]}:{ok:false,event:'resonance_miss',message:'The mechanism vibrates but does not catch. Try a different moment.'};
}
