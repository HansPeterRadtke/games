import assert from 'node:assert/strict';import {SemanticWorld} from '../semantic-world.js';
const s=new SemanticWorld();for(const value of [Infinity,NaN,-1,1.1])assert.throws(()=>s.step(value));for(const invalid of [null,Infinity,{x:0,y:0,z:Infinity}])assert.throws(()=>s.observe(invalid));
let data=s.state();for(const vx of [Infinity,NaN,3]){const corrupt=structuredClone(data);corrupt.entities[0].vx=vx;assert.equal(s.restore(corrupt),false,'invalid saved speed must be rejected');}
for(const range of [-1,Infinity]){const corrupt=structuredClone(data);corrupt.entities[0].range=range;assert.equal(s.restore(corrupt),false);}
const e=s.entities[0];e.vx=2;e.range=.1;e.home=e.x;for(let n=0;n<1000;n++){s.step(1);assert.ok(Number.isFinite(e.x)&&e.x>=e.home-e.range-1e-8&&e.x<=e.home+e.range+1e-8,'bounded reflection must not escape');}
console.log(JSON.stringify({passed:true,test:'bounded constant-time semantic reflection, malformed input, nonfinite and extreme speeds',time:s.time}));
for(const field of ['q','angular']){const bad=structuredClone(data);bad.entities[0][field]=field==='q'?{x:NaN,y:0,z:0,w:1}:{x:NaN,y:0,z:0};assert.equal(s.restore(bad),false,'nonfinite physical orientation must be rejected');}
