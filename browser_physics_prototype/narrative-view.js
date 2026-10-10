// Text-medium projection of the same authoritative world state as the 2D canvas.
// Do not reveal off-screen facts or hidden rules that the character has not observed.
function humanState(entity){const state=entity.state||{};
 if(entity.kind==='note'&&state.condition==='ashes')return 'Only fragile gray ash remains where a handwritten warning once lay. Its words cannot be read.';
 if(entity.kind==='note'&&state.condition==='wet')return 'A waterlogged note lies on the bench, its ink smudged and the flames out.';
 if(entity.kind==='bench'&&state.condition==='scorched')return 'The oak bench is blackened by fire. Its frame is still standing.';
 if(entity.kind==='shelter'&&state.condition==='smoky')return 'Smoke and soot stain the shelter roof. Something burned here.';
 if(entity.kind==='candle')return `${entity.description} ${state.lit?'The wick is burning.':'The wick is unlit.'}`;
 if(entity.kind==='jug')return `${entity.description} ${state.water>0?'It still contains water.':'It is empty.'}`;
 return entity.description;
}
export function narrateWorld(state){if(!state?.player||!Array.isArray(state.visibleEntities))return 'The surroundings cannot be perceived.';
 const p=state.player,visible=state.visibleEntities.filter(e=>!e.state?.collected).map(e=>({...e,distance:Math.hypot(e.position.x-p.x,e.position.y-p.y,e.position.z-p.z)})).sort((a,b)=>a.distance-b.distance);
 const location=visible.find(e=>e.kind==='shelter'&&e.distance<4);
 const scene=location?humanState(location):`You are on a forest path. ${p.y>2?'You are above the ground.':'The ground is under your feet.'}`;
 const nearby=visible.filter(e=>e.id!==location?.id&&e.distance<=3.2).slice(0,4);
 const description=nearby.length?nearby.map(e=>humanState(e)).join(' '):'There are no obvious objects within immediate reach.';
 const interactive=state.nearby?`You could ${state.nearby.label.toLowerCase()}.`:'';
 return `You are at x ${p.x.toFixed(1)}m, y ${p.y.toFixed(1)}m, z ${p.z.toFixed(1)}m. ${scene} ${nearby.length?'Nearby: '+nearby.map(e=>e.name).join(', ')+'.':''} ${description} ${interactive}`.trim();
}
export function narrateEvents(events,minSequence=0){if(!Array.isArray(events))return '';
 return events.filter(e=>(e.sequence||0)>minSequence&&e.visibility!=='offscreen'&&e.message).map(e=>e.message).join(' ');
}
