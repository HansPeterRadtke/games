// Network transport view of an authoritative game-state snapshot.
// No world state or physics is altered by this projection.
const q = n => typeof n === 'number' ? Math.round(n * 1000) / 1000 : 0;
const v3 = v => ({x:q(v?.x),y:q(v?.y),z:q(v?.z)});
const quat = v => ({x:q(v?.x),y:q(v?.y),z:q(v?.z),w:q(v?.w)});
export function projectViewerState(s){
 if(!s?.player||!s?.character||!Array.isArray(s.visibleEntities))throw Error('Invalid core state projection');
 const c=s.character;
 return {
  time:q(s.time),player:v3(s.player),velocity:v3(s.velocity),crate:v3(s.crate),grounded:s.grounded,goal:s.goal,
  character:{inventory:{plank:c.inventory.plank},fatigue:q(c.fatigue),hydration:q(c.hydration),bridgeRepaired:c.bridgeRepaired,farBankReached:c.farBankReached,fenceOpened:c.fenceOpened,
   notes:c.notes.slice(-16),knowledge:(c.knowledge||[]).slice(-16)},
  nearby:s.nearby?{id:s.nearby.id,kind:s.nearby.kind,label:s.nearby.label}:null,
  gateProgress:q(s.gateProgress),fence:v3(s.fence),direction:s.direction,playerDimensions:s.playerDimensions,fenceHeight:s.fenceHeight,
  visibleEntities:s.visibleEntities.map(e=>({id:e.id,kind:e.kind,name:e.name,position:v3(e.position),size:e.size||null,rotation:e.rotation?quat(e.rotation):null,
   physical:!!e.physical,state:{condition:e.state?.condition,lit:e.state?.lit,wet:e.state?.wet,water:e.state?.water,repaired:e.state?.repaired}})),
  ragdoll:{mode:s.ragdoll.mode,parts:Object.fromEntries(Object.entries(s.ragdoll.parts).map(([name,part])=>[name,{position:v3(part.position),rotation:quat(part.rotation)}]))}
 };
}
