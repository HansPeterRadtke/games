// Game-domain decisions. No renderer/physics imports: effects must pass through the core.
import {attemptResonance,measureResonance} from './hidden-mechanism.js';
const reach=1.4;
export function nearbyInteraction(player,semantic,active){
 if(!player||!semantic)return null;
 let options=[];for(const e of semantic.entities){if(e.state?.collected||!['plank','resonator','workbench','spring','wanderer','destination'].includes(e.kind))continue;
  const pos=active.get(e.id)?.translation()||e;const distance=Math.hypot(pos.x-player.x,pos.y-player.y,pos.z-player.z);
  if(distance<reach)options.push({id:e.id,kind:e.kind,name:e.name,distance});}
 options.sort((a,b)=>a.distance-b.distance);
 const chosen=options[0];if(!chosen)return null;
 const labels={plank:'Pick up plank',resonator:'Measure mechanism',workbench:'Repair bridge',spring:'Drink',wanderer:'Talk',destination:'Explore'};
 return {...chosen,label:labels[chosen.kind]};
}
export function resolveInteraction({actor,character,semantic,active,time}){
 const candidate=nearbyInteraction(actor,semantic,active);
 if(!candidate)return {ok:false,event:'nothing_nearby',message:'Nothing is within reach. Move closer to an object.'};
 const target=semantic.entity(candidate.id);
 switch(candidate.kind){
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
 case 'wanderer':return {ok:true,event:'conversation',message:character.bridgeRepaired?'Traveler: "The bridge is usable again. Thank you."':'Traveler: "The footbridge ahead lost its deck. There are loose timbers by the old beech."'};
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
