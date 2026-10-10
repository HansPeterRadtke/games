// Experimental task/load-dependent capabilities, deliberately distinct from an HP counter.
// All parameters are provisional and require biomechanics calibration before realism claims.
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export class CharacterModel {
 constructor(){this.fatigue=0;this.hydration=100;this.skill={hauling:0};this.injuries={leftKnee:{kind:'healthy',severity:0},rightKnee:{kind:'healthy',severity:0}};this.inventory={plank:0};this.notes=[];this.knowledge=[];this.bridgeRepaired=false;this.fenceOpened=false;this.farBankReached=false;}
 carriedMass(){return this.inventory.plank*6;}
 locomotion(){const mass=this.carriedMass();const knee=Math.max(this.injuries.leftKnee.kind==='sprain'?this.injuries.leftKnee.severity:0,this.injuries.rightKnee.kind==='sprain'?this.injuries.rightKnee.severity:0);
 // Heavier load, fatigue and knee impairment affect locomotion differently.
 const loadPenalty=clamp(mass/55,0,.65),fatiguePenalty=this.fatigue/350,kneePenalty=knee*.45;
 return {speedFactor:clamp(1-loadPenalty-fatiguePenalty-kneePenalty,.27,1),mass,loadPenalty,kneePenalty};}
 step(dt,physicalSpeed){if(!Number.isFinite(dt)||dt<0||dt>1||!Number.isFinite(physicalSpeed))throw Error('Invalid physiological update');const intensity=clamp(Math.abs(physicalSpeed)/3.3,0,2);
 this.fatigue=clamp(this.fatigue+(intensity>0.15?(intensity*intensity*(1+this.carriedMass()/28)*.22):-.36)*dt,0,100);
 this.hydration=clamp(this.hydration-dt*(.004+intensity*.018),0,100);
 if(intensity>.25)this.skill.hauling=clamp(this.skill.hauling+dt*intensity*.008,0,1);
 }
 drink(){this.hydration=Math.min(100,this.hydration+30);return this.hydration;}
 collectPlank(){if(this.inventory.plank>=3)return false;this.inventory.plank++;return true;}
 spendPlanks(n){if(!Number.isInteger(n)||n<0||this.inventory.plank<n)return false;this.inventory.plank-=n;return true;}
 note(note){if(!note||!Number.isFinite(note.time)||!Number.isFinite(note.intensity)||!['rising','falling','steady','unknown'].includes(note.trend))return false;this.notes.push({...note});if(this.notes.length>64)this.notes.shift();return true;}
 learn(fact,text,source,time){if(typeof fact!=='string'||!/^[a-z_]{3,48}$/.test(fact)||typeof text!=='string'||text.length>350||typeof source!=='string'||source.length>80||!Number.isFinite(time)||time<0)return false;
 if(this.knowledge.some(k=>k.fact===fact))return false;
 this.knowledge.push({fact,text,source,time});if(this.knowledge.length>64)this.knowledge.shift();return true;}
 knows(fact){return this.knowledge.some(k=>k.fact===fact);}
 snapshot(){return {version:1,fatigue:this.fatigue,hydration:this.hydration,skill:{...this.skill},injuries:structuredClone(this.injuries),inventory:{...this.inventory},notes:this.notes.map(n=>({...n})),knowledge:this.knowledge.map(k=>({...k})),bridgeRepaired:this.bridgeRepaired,fenceOpened:this.fenceOpened,farBankReached:this.farBankReached};}
 restore(s){if(!s||s.version!==1||!Number.isFinite(s.fatigue)||s.fatigue<0||s.fatigue>100||!Number.isFinite(s.hydration)||s.hydration<0||s.hydration>100||!Number.isFinite(s.skill?.hauling)||s.skill.hauling<0||s.skill.hauling>1||!Number.isInteger(s.inventory?.plank)||s.inventory.plank<0||s.inventory.plank>20||!Array.isArray(s.notes)||s.notes.length>64||!s.notes.every(n=>Number.isFinite(n.time)&&Number.isFinite(n.intensity)&&Math.abs(n.intensity)<=100&&['rising','falling','steady','unknown'].includes(n.trend))||!['bridgeRepaired','fenceOpened','farBankReached'].every(k=>typeof s[k]==='boolean'))return false;
 for(const key of ['leftKnee','rightKnee'])if(!['healthy','sprain','bruise'].includes(s.injuries?.[key]?.kind)||!Number.isFinite(s.injuries[key].severity)||s.injuries[key].severity<0||s.injuries[key].severity>1)return false;
 if(s.knowledge!==undefined&&(!Array.isArray(s.knowledge)||s.knowledge.length>64||!s.knowledge.every(k=>typeof k.fact==='string'&&/^[a-z_]{3,48}$/.test(k.fact)&&typeof k.text==='string'&&k.text.length<=350&&typeof k.source==='string'&&k.source.length<=80&&Number.isFinite(k.time)&&k.time>=0)||new Set(s.knowledge.map(k=>k.fact)).size!==s.knowledge.length))return false;
 this.knowledge=(s.knowledge||[]).map(k=>({...k}));
 this.fatigue=s.fatigue;this.hydration=s.hydration;this.skill={...s.skill};this.injuries=structuredClone(s.injuries);this.inventory={...s.inventory};this.notes=s.notes.map(n=>({...n}));this.bridgeRepaired=s.bridgeRepaired;this.fenceOpened=s.fenceOpened;this.farBankReached=s.farBankReached;return true;}
}
