import {GameCore,initializePhysics} from '../physics-core.js';
await initializePhysics();const g=new GameCore();g.command({type:'SetRagdollMode',mode:'walk'});g.player.setTranslation({x:14,y:.86,z:0},true);
for(let i=0;i<180;i++)g.step();const before=process.memoryUsage().rss,now=performance.now();for(let i=0;i<1200;i++)g.step();const elapsed=performance.now()-now,after=process.memoryUsage().rss;
const perStep=elapsed/1200;console.log(JSON.stringify({step:1/60,physicsMillisecondsPerTick:+perStep.toFixed(3),realtimeFactor:+(16.667/perStep).toFixed(2),memoryMB:+(after/1048576).toFixed(1),deltaMemoryMB:+((after-before)/1048576).toFixed(1),activePhysicalActors:g.worldBridge.active.size,bodyParts:Object.keys(g.activeRagdoll.parts).length}));if(!(perStep<16.67))process.exitCode=1;
