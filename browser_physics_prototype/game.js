// DOM and keyboard/touch adapter. All gameplay mutations go through typed core commands.
import {GameCore,initializePhysics,SETTINGS} from './physics-core.js';
import {SideViewRenderer} from './side-view-renderer.js';
import {observeResearch} from './research-view.js';
const $=id=>document.getElementById(id);
const renderer=new SideViewRenderer($('scene'));
let core,moveLeft=false,moveRight=false,frameBefore=0,accumulator=0,eventCursor=0,lastSave=null;
let lastJournalKey='',lastUiState='';
function say(message){$('message').textContent=message;}
function locationName(x){if(x< -4.5)return 'Old beech grove';if(x<5.2)return 'The clearing';if(x<14)return 'Beyond the fence';if(x<22.2)return 'Stream approach';if(x<33)return 'Far bank';if(x<42)return 'Riverside shelter';return 'Valley path';}
function missionText(character){if(character.farBankReached)return 'You crossed the footbridge. Explore the abandoned shelter further east →';
 if(character.bridgeRepaired)return 'Cross the repaired footbridge and reach the far bank →';
 if(character.inventory.plank<2)return 'Find two loose timber planks by the old beech tree ←';
 return 'Carry the timber past the fence to the bridge repair stand →';}
function updateUI(state){const character=state.character,$near=$('nearby-prompt');
 const key=JSON.stringify([character.inventory.plank,Math.round(character.fatigue/5),Math.round(character.hydration/10),character.bridgeRepaired,character.farBankReached,state.nearby?.label,Math.round(state.player.x/5)]);
 if(key!==lastUiState){lastUiState=key;$('location').textContent=locationName(state.player.x);$('mission').textContent=missionText(character);
  const fatigue=character.fatigue<25?'Rested':character.fatigue<60?'Tiring':'Exhausted';$('condition').textContent=`Timber ${character.inventory.plank}/2 · ${character.inventory.plank*6} kg carried · ${fatigue}`;
  $near.textContent=state.nearby?`E · ${state.nearby.label}`:'';}
 const journalKey=`${character.notes.length}:${character.knowledge?.length||0}`;
 if(journalKey!==lastJournalKey){lastJournalKey=journalKey;$('field-notes').replaceChildren();
  if(!character.notes.length&&!(character.knowledge||[]).length)$('field-notes').textContent='No observations yet.';
  else{const list=document.createElement('ul');
   for(const item of character.notes.slice(-16).reverse()){const li=document.createElement('li');li.textContent=`Time ${item.time.toFixed(1)} s — needle ${item.intensity}, ${item.trend}`;list.append(li);}
   for(const fact of (character.knowledge||[]).slice(-16).reverse()){const li=document.createElement('li');li.textContent=`Observed: ${fact.text}`;list.append(li);}
   $('field-notes').append(list);}}
 if(core.events.some(e=>e.sequence>eventCursor)){for(const event of core.events.filter(e=>e.sequence>eventCursor)){
   if(event.visibility==='offscreen'||event.type==='limb_contact'&&!$('physical-experiment').open)continue;
   if(event.message)say(event.message);
  }eventCursor=core.eventSequence;}

}
function runFrame(now){if(!core)return;const dt=frameBefore?Math.min(.12,(now-frameBefore)/1000):0;frameBefore=now;accumulator+=dt;let count=0;
 while(accumulator>=SETTINGS.step&&count++<7){core.step();accumulator-=SETTINGS.step;}
 const state=core.state();renderer.draw(state);updateUI(state);requestAnimationFrame(runFrame);
}
function command(type,extra={}){if(!core)return false;return core.command({type,...extra});}
function movement(){command('Move',{direction:Number(moveRight)-Number(moveLeft)});}
function bindHold(id,direction){const element=$(id),down=()=>{if(direction<0)moveLeft=true;else moveRight=true;movement();},up=()=>{if(direction<0)moveLeft=false;else moveRight=false;movement();};
 element.addEventListener('pointerdown',e=>{e.preventDefault();element.setPointerCapture(e.pointerId);down();});for(const kind of ['pointerup','pointercancel','lostpointercapture'])element.addEventListener(kind,up);
}
bindHold('left',-1);bindHold('right',1);
const bindings={jump:()=>command('Jump'),interact:()=>command('Interact'),tune:()=>command('Experiment'),goal:()=>command('Goal',{intent:'crossFence'}),cancel:()=>command('CancelGoal'),
 ragdoll:()=>command('PushRagdoll'),'ragdoll-balance':()=>command('SetRagdollMode',{mode:'balance'}),'ragdoll-walk':()=>command('SetRagdollMode',{mode:'walk'}),'ragdoll-relax':()=>command('SetRagdollMode',{mode:'relax'}),'ragdoll-injure':()=>command('InjureRagdoll',{part:'leftKnee',injury:'sprain',severity:.85}),'ragdoll-heal':()=>command('HealRagdoll')};
for(const [id,action]of Object.entries(bindings))$(id).addEventListener('click',action);
function refreshResearch(){if(!core)return;const state=observeResearch(core);$('research-result').textContent=state.explain+'\n\n'+state.text;$('research-raw').textContent=JSON.stringify(state.detail,null,2);}
const shelterVisit=x=>{if(!core)return;core.command({type:'CancelGoal'});core.command({type:'Move',direction:0});core.player.setTranslation({x,y:.86,z:0},true);core.player.setLinvel({x:0,y:0,z:0},true);for(let i=0;i<10;i++)core.step();refreshResearch();};
const experiments={
 'research-shelter':()=>shelterVisit(37),
 'research-light':()=>{core.command({type:'Interact',targetId:'shelter-candle',verb:'light'});refreshResearch();},
 'research-ignite':()=>{core.command({type:'Interact',targetId:'shelter-note',verb:'ignite'});refreshResearch();},
 'research-observe':()=>{for(let i=0;i<60*12;i++)core.step();refreshResearch();},
 'research-offscreen':()=>shelterVisit(26),
 'research-return':()=>shelterVisit(37),
 'research-inspect':refreshResearch
};
for(const [id,action]of Object.entries(experiments))$(id).addEventListener('click',action);
$('prse-research').addEventListener('toggle',()=>{if($('prse-research').open)refreshResearch();});
$('view-lab').addEventListener('click',()=>renderer.setView('lab'));
$('view-world').addEventListener('click',()=>renderer.setView('world'));
function handleKey(e,down){const inField=e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement;
 if(inField){if(e.key==='Escape'&&down){e.target.blur();e.preventDefault();}return;}
 const k=e.key.toLowerCase();if(['arrowleft','arrowright',' ','a','d','e','f','g','escape','enter'].includes(k))e.preventDefault();
 if(k==='enter'&&down&&!e.repeat&&!e.isComposing){$('semantic-input').focus();return;}
 if(k==='a'||k==='arrowleft'){moveLeft=down;movement();}else if(k==='d'||k==='arrowright'){moveRight=down;movement();}
 else if(!down||e.repeat)return;else if(k===' ')command('Jump');else if(k==='e')command('Interact');else if(k==='f')command('Experiment');else if(k==='g')command('Goal',{intent:'crossFence'});else if(k==='escape')command('CancelGoal');}
window.addEventListener('keydown',e=>handleKey(e,true));window.addEventListener('keyup',e=>handleKey(e,false));window.addEventListener('blur',()=>{moveLeft=false;moveRight=false;movement();});
$('semantic-form').addEventListener('submit',event=>{event.preventDefault();if(!core)return;const field=$('semantic-input');const text=field.value.trim();if(!text)return;say(core.textCommand(text));field.value='';field.blur();});
$('save').addEventListener('click',()=>{if(!core)return;lastSave=JSON.stringify(core.snapshot());try{localStorage.setItem('prse-world-save-v5',lastSave);say('World and physical state saved on this device.');}catch{say('World saved for this browser session.');}});
$('load').addEventListener('click',()=>{if(!core)return;try{const text=lastSave||localStorage.getItem('prse-world-save-v5')||localStorage.getItem('prse-world-save-v4')||localStorage.getItem('world-physics-prototype-save-v3')||localStorage.getItem('world-physics-prototype-save-v2');if(!text){say('No saved world found.');return;}if(!core.restore(JSON.parse(text)))throw Error('Invalid save');eventCursor=core.eventSequence;lastUiState='';lastJournalKey='';say('Saved world restored.');}catch(e){say('Could not restore that save.');}});
$('restart').addEventListener('click',()=>{if(!core)return;core.create();renderer.setView('world');eventCursor=0;accumulator=0;lastUiState='';lastJournalKey='';say('New world started.');});
try{await initializePhysics();core=new GameCore();$('status').textContent='3D physics ready';$('details').textContent='Rapier 3D simulation · semantic world · 2D renderer · works offline after loading';
 say('Gather two planks by the old tree, then repair the stream crossing.');window.__gameDebug={core,snapshot:()=>core.snapshot(),settings:SETTINGS,renderer};requestAnimationFrame(runFrame);
}catch(error){$('status').textContent='Simulation unavailable';say(`Physics failed: ${error.message}`);console.error(error);}
