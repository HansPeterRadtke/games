// Tested lightweight language-to-action feasibility adapter; it never executes
// a guessed action until a single concrete object and allowed verb are resolved.
// Gameplay and distance checks still belong to GameCore / gameplay-rules.js.
const OBJECTS=[
 {id:'shelter-candle',tokens:['candle','wax','wick','flame','beeswax'],verbs:['light','extinguish','tip','inspect']},
 {id:'shelter-note',tokens:['note','paper','letter','writing','handwriting'],verbs:['read','ignite','inspect']},
 {id:'shelter-jug',tokens:['jug','pitcher','waterjug','water','pot'],verbs:['pour','inspect']},
 {id:'shelter-bench',tokens:['bench','seat','table'],verbs:['inspect']},
 {id:'shelter-setting',tokens:['shelter','hut','shack','building'],verbs:['inspect']},
 {id:'wanderer-1',tokens:['traveler','traveller','wanderer','person','stranger'],verbs:['talk','tell']},
 {id:'plank',tokens:['plank','timber','wood','board','lumber'],verbs:['take','inspect']},
];
const VERB_PATTERNS=[
 {verb:'extinguish',patterns:[['put','out'],['blow','out'],['extinguish'],['snuff'],['douse']]},
 {verb:'light',patterns:[['light'],['ignite','candle'],['start','flame']]},
 {verb:'tip',patterns:[['tip'],['knock'],['push','over'],['nudge']]},
 {verb:'ignite',patterns:[['burn'],['ignite'],['set','fire'],['set','alight']]},
 {verb:'read',patterns:[['read'],['decipher']]},
 {verb:'pour',patterns:[['pour'],['empty'],['splash'],['douse']]},
 {verb:'talk',patterns:[['talk'],['speak'],['ask'],['chat']]},
 {verb:'tell',patterns:[['tell'],['warn'],['inform']]},
 {verb:'take',patterns:[['take'],['pick'],['grab'],['collect'],['lift']]},
 {verb:'inspect',patterns:[['look'],['examine'],['inspect'],['study'],['check']]},
];
const STOPWORDS=new Set(['the','a','an','this','that','at','about','to','some','please','now','can','i','you','with','it','my','on','up','in','from','of','and']);
const tokenize=text=>text.toLowerCase().replace(/[^a-z0-9 ]+/g,' ').split(/\s+/).filter(w=>w&&!STOPWORDS.has(w));
const matches=(tokens,pattern)=>pattern.every(t=>tokens.includes(t));
const normalizeObjectToken=token=>token==='candles'?'candle':token==='planks'?'plank':token==='boards'?'board':token==='notes'?'note':token;
export function resolveNaturalAction(text,semantic,player){
 if(typeof text!=='string'||text.length>120||!semantic||!player||!['x','y','z'].every(k=>Number.isFinite(player[k])))return {ok:false,reason:'Invalid command.'};
 const tokens=tokenize(text).map(normalizeObjectToken);
 if(!tokens.length)return {ok:false,reason:'The command contains no action.'};
 const candidates=OBJECTS.map(obj=>({obj,overlap:obj.tokens.filter(t=>tokens.includes(t)).length})).filter(x=>x.overlap>0);
 if(!candidates.length)return {ok:false,reason:'I could not identify an object in that request.'};
 const bestCount=Math.max(...candidates.map(x=>x.overlap));const best=candidates.filter(x=>x.overlap===bestCount);
 if(best.length>1)return {ok:false,reason:`Ambiguous object: ${best.map(v=>v.obj.tokens[0]).join(' or ')}. Specify one object.`};
 const selected=best[0].obj;
 const matching=[];
 for(const entry of VERB_PATTERNS){if(!selected.verbs.includes(entry.verb))continue;
  if(entry.patterns.some(pattern=>matches(tokens,pattern)))matching.push(entry.verb);
 }
 // Do not silently reinterpret an explicit invalid action as an inspection or nearby interaction.
 if(!matching.length)return {ok:false,reason:`No supported action for ${selected.tokens[0]}.`};
 if(matching.length>1){const priority=['extinguish','tell','pour','ignite','light','read','take','tip','talk','inspect'];matching.sort((a,b)=>priority.indexOf(a)-priority.indexOf(b));
  if(matching[0]==='inspect'&&matching[1])matching.shift();
  if(matching.length>1)return {ok:false,reason:'Ambiguous action. Use a more specific verb.'};
 }
 let targetId=selected.id;
 if(targetId==='plank'){
  const matches=semantic.entities.filter(e=>e.kind==='plank'&&!e.state?.collected);
  matches.sort((a,b)=>Math.hypot(a.x-player.x,a.y-player.y,a.z-player.z)-Math.hypot(b.x-player.x,b.y-player.y,b.z-player.z));
  if(!matches.length)return {ok:false,reason:'There are no available planks.'};
  targetId=matches[0].id;
 }
 return {ok:true,type:'Interact',targetId,verb:matching[0],derivedFrom:'bounded-token-matcher',tokens};
}
