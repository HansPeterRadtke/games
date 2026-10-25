// Research-only bounded offscreen transition over the EXISTING authoritative
// PRSE GameCore/Rapier simulation. No second solver or synthetic motion teacher.
//
// Unload a region only after real physics has made all its moving bodies
// stationary for a continuous observation window with actual contact evidence.
// Otherwise refuse the optimization and retain full authoritative physics.
//
// This is conservative and applies only to this bounded single research region:
// it is NOT a production global clock or unseen active NPC simulation solution.
import {PRSELoop} from '../2026-10-24/prse_semantic_roundtrip.mjs';

const finite=n=>typeof n==='number'&&Number.isFinite(n);
const vectorLength=v=>Math.hypot(v.x,v.y,v.z);
const pointDistance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const rotationDifference=(a,b)=>{
 const dot=Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w);
 return 2*Math.acos(Math.min(1,Math.max(-1,dot)));
};
function collides(loop,one,two){
 let contacts=false;
 if(!one?.numColliders()||!two?.numColliders())return false;
 for(let i=0;i<one.numColliders();i++)
 for(let j=0;j<two.numColliders();j++){
  loop.game.world.contactPair(one.collider(i),two.collider(j),m=>{
   if(m.numContacts()>0)contacts=true;
  });
  if(contacts)return true;
 }
 return false;
}
export function probeSettlement(loop,previous=null,{linearSpeed=.012,angularSpeed=.03,
 displacementPerTick=.0003,rotationPerTick=.0006}={}){
 if(!(loop instanceof PRSELoop))throw Error('Must use existing PRSE physics core');
 if(loop.game.goal)throw Error('Active player goal prevents unloaded-region transition');
 let moving=0,uncontacted=0,maxLinear=0,maxAngular=0,maxMovement=0,maxRotation=0;
 const next=new Map();
 for(const [id,body] of loop.active){
  if(!body.isDynamic())continue;
  const lin=body.linvel(),ang=body.angvel(),p=body.translation(),q=body.rotation();
  const speed=vectorLength(lin),rotSpeed=vectorLength(ang);
  const pos=previous?.get(id);
  const movement=pos?pointDistance(p,pos.translation):Infinity;
  const rotation=pos?rotationDifference(q,pos.rotation):Infinity;
  next.set(id,{translation:{...p},rotation:{...q}});
  moving++;
  maxLinear=Math.max(maxLinear,speed);maxAngular=Math.max(maxAngular,rotSpeed);
  maxMovement=Math.max(maxMovement,movement);
  maxRotation=Math.max(maxRotation,rotation);
  let contact=collides(loop,body,loop.floor);
  if(!contact){
   for(const [otherId,other]of loop.active){
    if(id!==otherId&&collides(loop,body,other)){contact=true;break;}
   }
  }
  if(!contact)uncontacted++;
 }
 const quiet=moving>0&&uncontacted===0&&maxLinear<=linearSpeed&&maxAngular<=angularSpeed
  &&maxMovement<=displacementPerTick&&maxRotation<=rotationPerTick;
 return {quiet,moving,uncontacted,maxLinear,maxAngular,maxMovement,maxRotation,next};
}
export function physicallySettleThenUnload(loop,{
 maxPhysicalTicks=150,requiredQuietTicks=20,totalTicks=300,
 linearSpeed=.012,angularSpeed=.03,displacementPerTick=.0003,rotationPerTick=.0006
}={}){
 if(!(loop instanceof PRSELoop)||loop.active.size===0)throw Error('Must start in authoritative active physics');
 if(!Number.isInteger(totalTicks)||totalTicks<1||totalTicks>7200||
    !Number.isInteger(maxPhysicalTicks)||maxPhysicalTicks<1||maxPhysicalTicks>totalTicks||
    !Number.isInteger(requiredQuietTicks)||requiredQuietTicks<2||requiredQuietTicks>maxPhysicalTicks)
  throw Error('Invalid bounded offscreen sampling policy');
 const startingTick=loop.game.stepCount,startingTime=loop.time,eventsBefore=loop.events.length;
 let prior=null,quietTicks=0,probes=0,last;
 for(let i=0;i<maxPhysicalTicks;i++){
  loop.tick(1);
  last=probeSettlement(loop,prior,{linearSpeed,angularSpeed,displacementPerTick,rotationPerTick});
  prior=last.next;probes++;
  if(last.quiet)quietTicks++;
  else quietTicks=0;
  if(quietTicks>=requiredQuietTicks){
   // Strict built-in independent speed guard must also pass. Preserve source
   // actual bodies and event history before changing materialization boundary.
   const unloaded=loop.dematerialize();
   if(unloaded<=0)throw Error('Settled scene was not actually dematerialized');
   const offscreenTicks=totalTicks-probes;
   if(offscreenTicks>0)loop.advanceOffscreen(offscreenTicks/60);
   const savedWhileSemantic=JSON.parse(JSON.stringify(loop.snapshot()));
   const priorTime=loop.time;
   const rematerialized=loop.materialize();
   return {offloaded:true,reason:'contact_verified_quiet_window',startingTick,startingTime,
    fullHorizonTicks:totalTicks,physicalTicks:probes,
    skippedPhysicsTicks:offscreenTicks,quietTicks,
    physicsBeforeUnload:unloaded,rematerialized,
    savedWhileSemantic,expectedWorldTime:startingTime+totalTicks/60,
    realWorldTime:loop.time,physicalEventsDuringSettling:loop.events.length-eventsBefore,
    lastProbe:{quiet:last.quiet,uncontacted:last.uncontacted,maxLinear:last.maxLinear,
     maxAngular:last.maxAngular,maxMovement:last.maxMovement,maxRotation:last.maxRotation}};
  }
 }
 // Failure to find a safe unload boundary is NOT grounds for freezing motion.
 // Continue the one authoritative 3D solver for the rest of the requested
 // horizon and report that no CPU offscreen optimization is established.
 for(let i=maxPhysicalTicks;i<totalTicks;i++)loop.tick(1);
 return {offloaded:false,reason:'could_not_verify_sustained_physical_settlement',
  startingTick,startingTime,fullHorizonTicks:totalTicks,physicalTicks:totalTicks,
  skippedPhysicsTicks:0,quietTicks,lastProbe:{
   quiet:last?.quiet??false,uncontacted:last?.uncontacted??null,
   maxLinear:last?.maxLinear??null,maxAngular:last?.maxAngular??null,
   maxMovement:last?.maxMovement??null,maxRotation:last?.maxRotation??null},
  physicalEventsDuringSettling:loop.events.length-eventsBefore,
  expectedWorldTime:startingTime+totalTicks/60,realWorldTime:loop.time};
}
