// Small authored PRSE seed. The description is narrative source material;
// physics hints are typed, validated data rather than generated executable code.
const place=(id,kind,name,x,y,description,physical={},state={},extras={})=>({
 id,kind,name,x,y,z:0,home:x,range:0,speed:0,phase:0,vx:0,vy:0,vz:0,
 q:{x:0,y:0,z:0,w:1},angular:{x:0,y:0,z:0},
 revision:0,materialized:false,source:'world-seed:v2',description,
 physical,state,...extras
});
export function createWorldSeed(){const entities=[
 place('wanderer-1','wanderer','Path traveler',17.2,.82,'A traveler searches for a way across the stream.',{body:'dynamic',collider:'capsule',halfHeight:.56,radius:.24}, {},{home:17.2,range:2.2,speed:.55,vx:.55}),
 place('grove-1','tree','Old beech',-6.85,1.30,'An old beech gives shade to an abandoned timber stack. The tree itself is still alive.',{body:'fixed',collider:'none'},{}),
 place('resonator-1','resonator','Old mechanism',2.45,.63,'An old resonant machine is connected to a lifting fence. Its response depends on timing.',{body:'fixed',collider:'none'}, {opened:false}),
 place('spring-1','spring','Fresh spring',14.1,.33,'A cold spring runs through the stones. Its water looks clear.',{body:'fixed',collider:'none'},{}),
 place('bridge-stand-1','workbench','Bridge repairs',21.0,.52,'A neglected footbridge is missing two wooden deck planks. The support beams remain intact.',{body:'fixed',collider:'none'},{repaired:false,requiredPlanks:2}),
 place('bridge-1','bridge','Footbridge',23.65,0,'A stream cuts through the path. A timber crossing could restore the route.',{body:'fixed',collider:'cuboid',halfExtents:[1.24,.12,1.1]},{repaired:false}),
 place('far-bank-1','destination','Far bank',27.2,.35,'The far bank has a quiet grassy path leading away into unknown country.',{body:'fixed',collider:'none'},{}),
 ];
 for(let i=0;i<4;i++)entities.push(place(`plank-${i+1}`,'plank','Loose timber plank',-6.55+i*.28, .55+i*.46, 'A solid timber plank, roughly six kilograms. It can be carried to repair the footbridge.',{body:'dynamic',collider:'cuboid',halfExtents:[.37,.17,.25],mass:6},{collected:false}));
 return entities;
}
export const WORLD_OBJECTIVES=Object.freeze({primary:'Repair the footbridge using two timber planks, then explore the far bank.',secondary:'Study the old mechanism to open the fence without jumping.'});
