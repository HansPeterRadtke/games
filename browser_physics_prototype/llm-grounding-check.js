// Bounded grounding rules for the first story world, not general language understanding.
// Generated prose requires independent semantic review, not only valid JSON/geometry.
const BRIDGE_X=23.65;
export function checkNarrativeConsistency(scene){
 if(!scene||!Number.isFinite(scene.anchor)||typeof scene.description!=='string')return {ok:false,reasons:['Invalid story scene']};
 const text=scene.description.toLowerCase(),issues=[];
 const tooFarFromBridge=Math.abs(scene.anchor-BRIDGE_X)>9;
 if(tooFarFromBridge&&/bridge.{0,32}(abutment|supports|deck)|abutment.{0,32}bridge/.test(text))issues.push('Description requires physical contact with the distant bridge.');
 if(tooFarFromBridge&&/(planks you used|planks you carried|the planks you used)/.test(text))issues.push('Material from the original bridge appears at a distant location without transport.');
 if(scene.branch==='bridge_unrepaired'&&tooFarFromBridge&&/(traveler.s (worn )?footprints|the traveler walked)/.test(text))issues.push('A stranded traveler appears to have crossed an unrepaired bridge.');
 if(scene.objects?.some(o=>o.kind==='rock' && o.width_m<1.2)&&/arch over the stream/.test(text)&&Math.abs(scene.anchor-BRIDGE_X)>9)issues.push('An unmodeled stream and large stone arch appear in a simple rock collider.');
 return {ok:issues.length===0,reasons:issues};
}
