import assert from 'node:assert/strict';
import {createInterface} from 'node:readline/promises';
import {stdin as input,stdout as output} from 'node:process';
import {writeFileSync} from 'node:fs';
import {resonanceAt} from '../../hidden-mechanism.js';

// Optional study interface, never an automated participant. Formula access is intentionally
// only in the investigator's script, not the interactive measurement display.
// Use investigator-controlled code isolation for genuinely blind trials.
const cli = createInterface({input,output,terminal:input.isTTY});
const trials = [
  {id:'rule_a', label:'Generator A', f:t=>.72*Math.sin(2*Math.PI*t/7.4+.6)},
  {id:'rule_b', label:'Generator B', f:t=>resonanceAt(t)},
  {id:'rule_c', label:'Generator C', f:t=>.2},
];
const families=['constant','single periodic','multi periodic'];
let commands=[],results=[];
async function query(prompt) {
  const answer=await cli.question(prompt);
  if(answer === undefined)throw Error('Input closed');
  return answer.trim().toLowerCase();
}
function reading(f,time) {return Math.round(100*f(time));}
try{
 output.write('Hidden-rule human study preparation. No participant identity is requested or stored.\n');
 output.write('For each unknown generator, use up to twelve readings at world times from zero to twenty-four seconds.\n');
 output.write('Predict a family, then forecast if the generator will pass threshold 0.66 at a new time.\n');
 for(const rule of trials){
  output.write('\n'+rule.label+'\n');
  const rows=[];
  for(let turn=0;turn<12;turn++){
   let answer=await query('Reading time 0..24, or done: ');
   if(answer==='done')break;
   const time=Number(answer);
   if(!answer||!Number.isFinite(time)||time<0||time>24){output.write('Invalid time.\n');turn--;continue;}
   const value=reading(rule.f,time);
   rows.push({time,roundedIntensity:value});
   output.write('Measured intensity: '+value+'\n');
  }
  let guess=await query('Family constant / single periodic / multi periodic: ');
  while(!families.includes(guess)){output.write('Choose a known family.\n');guess=await query('Family: ');}
  const predictionTimes=[28,33,38,43];
  let hitPredictions=[];
  for(const t of predictionTimes){
   let outcome=await query('At world time '+t+', is intensity at least 66? (yes/no): ');
   while(outcome!=='yes'&&outcome!=='no'){output.write('yes or no\n');outcome=await query('At world time '+t+', yes/no: ');}
   hitPredictions.push({time:t,predicted:outcome==='yes',actual:rule.f(t)>=.66});
  }
  const correct = rule.id==='rule_a'?'single periodic':rule.id==='rule_b'?'multi periodic':'constant';
  results.push({anonymousTrial:rule.id,measurements:rows,reportedFamily:guess,familyCorrect:guess===correct,
    forecasts:hitPredictions.map(({time,predicted,actual})=>({time,predicted,correct:predicted===actual}))});
 }
 output.write('\nCausal investigation: instrument intensity may change with a switch or with the clock.\n');
 output.write('Observe one baseline timeline: at time 6 switch off intensity 20, at time 18 switch on intensity 55.\n');
 let tests=[];
 for(let i=0;i<3;i++){
  let command=await query('At world time 6 or 18, set switch on/off (e.g. 6 on), or done: ');
  if(command==='done')break;
  const m=/^(6|18) (on|off)$/.exec(command);
  if(!m){output.write('Use: 6 on, 6 off, 18 on, 18 off, or done.\n');i--;continue;}
  const t=Number(m[1]), enabled=m[2]==='on';
  const intensity=Math.round(100*(.2+.35*(enabled?1:0)));
  output.write('Measured intensity '+intensity+'\n');
  tests.push({time:t,enabled,roundedIntensity:intensity});
 }
 const causalGuess=await query('Main influence on intensity: switch or clock? ');
 results.push({anonymousTrial:'causal',switchInterventions:tests,reportedCause:causalGuess,correct:causalGuess==='switch'});
 const summary={schema:1,kind:'unverified-interactive-participant-protocol',participantHumanStatus:'unverified',
  budgets:{timeRange:[0,24],measurementsMax:12,forecastTimes:[28,33,38,43],causalInterventionsMax:3},
  results};
 const outIndex=process.argv.indexOf('--output');
 if(outIndex>=0){
  const dest=process.argv[outIndex+1];assert(dest&&!dest.startsWith('-'),'--output requires a path');
  writeFileSync(dest,JSON.stringify(summary,null,2)+'\n',{flag:'wx'});
  output.write('Anonymous measurement and answer record written.\n');
 }
 output.write('Three family predictions correct: '+results.slice(0,3).filter(r=>r.familyCorrect).length+'/3.\n');
 output.write('Causal explanation correct: '+String(results[3].correct)+'. This does not assess enjoyment.\n');
}finally{cli.close();}
