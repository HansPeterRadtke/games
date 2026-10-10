// Noninteractive alternate presentation of the *same* PRSE physics/game rules.
// Proof that neither a web server nor a browser is a prerequisite for simulation.
import fs from 'node:fs';
import {GameCore,initializePhysics,SETTINGS} from '../browser_physics_prototype/physics-core.js';
import {TextAdapter} from '../browser_physics_prototype/text-adapter.js';
import {narrateWorld} from '../browser_physics_prototype/narrative-view.js';
function fail(text){console.error(text);process.exit(2)}
const options=Object.fromEntries(process.argv.slice(2).map(arg=>{const [k,...v]=arg.split('=');return [k,v.join('=')]}));
if(process.argv.includes('--help')){console.log('headless-cli.mjs [--steps=N] [--command="look"] [--script=/absolute/commands.json] (No browser required)');process.exit(0)}
const steps=options['--steps']===undefined?0:Number(options['--steps']);if(!Number.isInteger(steps)||steps<0||steps>36000)fail('--steps must be 0..36000');
await initializePhysics();const core=new GameCore(),adapter=new TextAdapter(core);const output=[];
if(options['--script']){let script;try{script=JSON.parse(fs.readFileSync(options['--script'],'utf8'))}catch(e){fail('Invalid script: '+e.message)}
 if(!Array.isArray(script)||script.length>300)fail('Script must be an array of <=300 commands');
 for(const row of script){if(!row||typeof row!=='object')fail('Invalid command row');
  if(row.text!==undefined){output.push(adapter.run(row.text));}
  else if(row.command!==undefined){const ok=core.command(row.command);output.push({ok,command:row.command.type||null});}
  else fail('Unknown script entry');
  if(row.steps!==undefined){if(!Number.isInteger(row.steps)||row.steps<0||row.steps>36000)fail('Invalid step count');for(let i=0;i<row.steps;i++)core.step();}
 }
}
if(options['--command']!==undefined)output.push(adapter.run(options['--command']));
for(let i=0;i<steps;i++)core.step();
const state=core.state();console.log(JSON.stringify({engine:'PRSE authoritative headless game core',platform:'Node.js',browserRequired:false,graphicsRequired:false,simulationTime:state.time,player:state.player,physicalEntities:core.worldBridge.active.size,semanticEntities:core.semantic.entities.length,output,description:narrateWorld(state),events:core.events.slice(-8)},null,2));core.world.free();
