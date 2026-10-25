// RESEARCH-ONLY ATOMIC PRSE SEMANTIC + NATIVE RAPIER WORLD SNAPSHOT.
//
// Existing GameCore JSON deliberately rebuilds physics objects and thereby
// loses some Rapier narrow-phase/contact solver state. An externally authored
// source case showed 0.62 m divergence after a subsequent interaction despite
// identical saved 3D positions. Rapier's native World.takeSnapshot preserves
// more of its internal physics state.
//
// This bounded trusted experiment snapshots the WHOLE existing PRSE/GameCore
// Rapier World plus the exact existing structured GameCore and literary state,
// and binds the restored native World back to the original project's player,
// crate, kinematic fence, stone, ragdoll parts/joints, WorldBridge bodies and
// research sidecar entity IDs. It does not create a second physical solver.
//
// NOT yet suitable for user-controlled saves: native binary requires same
// WASM/build, trust verification and atomic core/world/observer transactions.
// Other regions cannot progress independently while this global World sleeps.
import RAPIER from '../../vendor/rapier.es.js';
import {readFileSync}from'node:fs';
import {createHash}from'node:crypto';
import {PRSELoop}from'../2026-10-24/prse_semantic_roundtrip.mjs';

const SHA=b=>createHash('sha256').update(b).digest('hex');
const VENDOR_SHA=SHA(readFileSync(new URL('../../vendor/rapier.es.js',import.meta.url)));
const hasName=id=>typeof id==='string'&&/^[a-z][a-z0-9-]{2,80}$/.test(id);
const entries=m=>[...m].map(([id,b])=>[id,b.handle]);
function handles(loop){
 const game=loop.game;
 const parts=Object.fromEntries(Object.entries(game.activeRagdoll.parts).map(([id,b])=>[id,b.handle]));
 const joints=Object.fromEntries(Object.entries(game.activeRagdoll.joints).map(([id,j])=>[id,j.handle]));
 return {player:game.player.handle,crate:game.crate.handle,
  stone:game.stone.handle,fence:game.fence.handle,floor:loop.floor.handle,
  ragdollParts:parts,ragdollJoints:joints,
  materializedSemanticWorld:entries(game.worldBridge.active),
  materializedLocalWorld:entries(loop.active)};
}
const trustedHandles=h=>h&&typeof h==='object'&&
 ['player','crate','stone','fence','floor'].every(k=>typeof h[k]==='number'&&Number.isFinite(h[k]))&&
 Object.values(h.ragdollParts||{}).every(v=>typeof v==='number'&&Number.isFinite(v))&&
 Object.values(h.ragdollJoints||{}).every(v=>typeof v==='number'&&Number.isFinite(v))&&
 ['materializedSemanticWorld','materializedLocalWorld'].every(k=>
  Array.isArray(h[k])&&h[k].length<=320&&h[k].every(([id,value])=>
   hasName(id)&&typeof value==='number'&&Number.isFinite(value)));
function actualEntityIDs(loop){
 return loop.scene.entities.map(e=>e.id).sort();
}
export function recordNativePRSEState(loop){
 if(!(loop instanceof PRSELoop)||loop.time!==loop.game.time)
  throw Error('World clocks inconsistent or non-PRSE core');
 const structured=JSON.parse(JSON.stringify(loop.snapshot()));
 const binary=loop.game.world.takeSnapshot();
 if(!(binary instanceof Uint8Array)||binary.length<100||binary.length>8*1024*1024)
  throw Error('Unexpected native physics world snapshot size');
 const refs=handles(loop),contacts=[...loop.contactPairs];
 return {schema:1,requiresTrustedInput:true,
  rapierVendoredSha256:VENDOR_SHA,
  semanticSHA256:SHA(Buffer.from(JSON.stringify(structured))),
  handleMapSHA256:SHA(Buffer.from(JSON.stringify(refs))),
  currentContactPairsSHA256:SHA(Buffer.from(JSON.stringify(contacts))),
  nativeBytes:binary.length,nativeSha256:SHA(binary),
  nativeBase64:Buffer.from(binary).toString('base64'),
  currentWorldTime:loop.time,expectedEventSequence:loop.nextSeq,
  worldId:loop.scene.id,exactEntityIDs:actualEntityIDs(loop),
  originallyMaterialized:loop.active.size>0,
  frameContactPairs:contacts,
  structured,handles:refs};
}
export function restoreNativePRSEState(snapshot){
 if(!snapshot||snapshot.schema!==1||snapshot.requiresTrustedInput!==true||
  snapshot.rapierVendoredSha256!==VENDOR_SHA||
  !Number.isInteger(snapshot.nativeBytes)||snapshot.nativeBytes<100||
  snapshot.nativeBytes>8*1024*1024||!hasName(snapshot.worldId)||
  !Array.isArray(snapshot.exactEntityIDs)||snapshot.exactEntityIDs.length>320||
  !trustedHandles(snapshot.handles)||!Number.isFinite(snapshot.currentWorldTime)||
  !Array.isArray(snapshot.frameContactPairs)||snapshot.frameContactPairs.length>10000||
  !snapshot.frameContactPairs.every(k=>typeof k==='string'&&k.length<200)||
  snapshot.semanticSHA256!==SHA(Buffer.from(JSON.stringify(snapshot.structured||{})))||
  snapshot.handleMapSHA256!==SHA(Buffer.from(JSON.stringify(snapshot.handles)))||
  snapshot.currentContactPairsSHA256!==SHA(Buffer.from(JSON.stringify(snapshot.frameContactPairs))))
  return {ok:false,reason:'untrusted_or_different_build_or_corrupt_structure'};
 let loop=null,native=null;
 try{
  const bytes=Buffer.from(snapshot.nativeBase64||'','base64');
  if(bytes.length!==snapshot.nativeBytes||SHA(bytes)!==snapshot.nativeSha256)
   throw Error('Native physics data mismatched SHA and bounded size');
  const restored=PRSELoop.restore(snapshot.structured);
  if(!restored.ok)throw Error('GameCore structured semantic snapshot invalid');
  loop=restored.loop;
  if(loop.scene.id!==snapshot.worldId||
   JSON.stringify(actualEntityIDs(loop))!==JSON.stringify(snapshot.exactEntityIDs)||
   loop.nextSeq!==snapshot.expectedEventSequence||
   Math.abs(loop.time-snapshot.currentWorldTime)>1e-6)
   throw Error('Semantic identity, event sequence or authoritative clock was changed');
  native=RAPIER.World.restoreSnapshot(bytes);
  if(!native)throw Error('Rapier native world could not deserialize');
  const h=snapshot.handles;
  const body=(handle,label)=>{
   const b=native.getRigidBody(handle);
   if(!b)throw Error('Missing native physical body: '+label);
   return b;
  };
  const joint=(handle,label)=>{
   const j=native.getImpulseJoint(handle);
   if(!j)throw Error('Missing native joint: '+label);
   return j;
  };
  const core=loop.game;
  const restoredCoreRefs={
   player:body(h.player,'player'),crate:body(h.crate,'crate'),
   stone:body(h.stone,'stone'),fence:body(h.fence,'fence')
  };
  const restoredParts=Object.fromEntries(Object.entries(h.ragdollParts).map(([id,v])=>[id,body(v,id)]));
  const restoredJoints=Object.fromEntries(Object.entries(h.ragdollJoints).map(([id,v])=>[id,joint(v,id)]));
  const semanticActive=new Map(h.materializedSemanticWorld.map(([id,v])=>[id,body(v,id)]));
  const localActive=new Map(h.materializedLocalWorld.map(([id,v])=>[id,body(v,id)]));
  const exactSorted=m=>JSON.stringify([...m.keys()].sort());
  if(exactSorted(semanticActive)!==exactSorted(core.worldBridge.active)||
     exactSorted(localActive)!==exactSorted(loop.active))
   throw Error('Native body mapping differs from structured semantic active IDs');
  if(Object.keys(restoredParts).length!==10||Object.keys(restoredJoints).length!==9)
   throw Error('Native ragdoll parts/joints mismatch existing PRSE GameCore');
  // Neither sidecar nor GameCore should silently claim a body not in the
  // structured semantic snapshot.
  for(const id of localActive.keys())if(!loop.entities.has(id))
   throw Error('Unidentified body appeared in native world');
  const inactiveKeys=[...loop.entities].filter(([id,e])=>e.materialized&&!localActive.has(id));
  if(inactiveKeys.length)throw Error('Semantic active/physics active mappings diverged');
  // Atomic hand-off only after ALL handle references have been resolved.
  const previousWorld=core.world;
  core.world=native;loop.floor=body(h.floor,'floor');
  Object.assign(core,restoredCoreRefs);
  core.activeRagdoll.world=native;core.activeRagdoll.parts=restoredParts;
  core.activeRagdoll.joints=restoredJoints;
  core.worldBridge.world=native;core.worldBridge.active=semanticActive;
  loop.active=localActive;
  loop.contactPairs=new Set(snapshot.frameContactPairs||[]);
  // Player, ragdoll and scene bridges now point exclusively to the new world.
  previousWorld.free();
  native=null;
  return {ok:true,loop,bytes:bytes.length};
 }catch(error){
  native?.free();loop?.dispose();
  return {ok:false,reason:String(error.message).slice(0,250)};
 }
}
