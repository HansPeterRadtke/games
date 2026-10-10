// Serializable PRSE prototype: semantic facts stay authoritative outside perception.
export class SemanticWorld {
 constructor(){this.radius=6;this.entities=[{id:'wanderer-1',kind:'wanderer',name:'Forest wanderer',x:17,y:.85,z:0,home:17,range:4,speed:.55,phase:0,revision:0,description:'A wandering traveler follows the forest path.',materialized:false}];this.time=0;}
 step(dt,playerX){if(!Number.isFinite(dt)||dt<0||dt>1)throw Error('Invalid step');this.time+=dt;for(const e of this.entities){if(!e.materialized){e.x=e.home+e.range*Math.sin(this.time*e.speed+e.phase);e.revision++;}e.materialized=Math.abs(e.x-playerX)<=this.radius;}}
 observe(playerX){return this.entities.filter(e=>Math.abs(e.x-playerX)<=this.radius).map(e=>({id:e.id,kind:e.kind,name:e.name,position:{x:e.x,y:e.y,z:e.z},description:e.description,revision:e.revision}));}
 state(){return {version:1,time:this.time,radius:this.radius,entities:this.entities.map(e=>({...e}))};}
 restore(s){if(!s||s.version!==1||!Number.isFinite(s.time)||s.time<0||!Array.isArray(s.entities)||s.entities.length>1000)return false;for(const e of s.entities)if(typeof e.id!=='string'||e.id.length>80||!['x','y','z','home','range','speed','phase'].every(k=>Number.isFinite(e[k])))return false;this.time=s.time;this.entities=s.entities.map(e=>({...e}));return true;}
}
