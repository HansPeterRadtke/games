import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {resonanceAt,measureResonance} from '../../hidden-mechanism.js';

// Offline observers receive recorded instrument readings, NOT the generating formula.
// Model structure and candidate grid are intentionally specified before evaluating predictions.
const periods=Array.from({length:39},(_,i)=>2.5+i*.25);
const kinds={
 existing:t=>resonanceAt(t),
 simple:t=>.75*Math.sin(2*Math.PI*t/7.4+.6),
 dual:t=>.6*Math.sin(2*Math.PI*t/8+.3)+.4*Math.sin(2*Math.PI*t/3.4+.8),
 constant:t=>.24,
 slow:t=>.75*Math.sin(2*Math.PI*t/120+.1),
};
const grid=Array.from({length:16},(_,i)=>i*1.5);
const future=Array.from({length:24},(_,i)=>24+i*1.5);
function gaussian(mat, rhs) {
  const n=rhs.length,aug=mat.map((r,i)=>[...r,rhs[i]]);
  for(let i=0;i<n;i++){
    let pivot=i;for(let j=i+1;j<n;j++)if(Math.abs(aug[j][i])>Math.abs(aug[pivot][i]))pivot=j;
    if(Math.abs(aug[pivot][i])<1e-10)return null;
    [aug[i],aug[pivot]]=[aug[pivot],aug[i]];
    const denom=aug[i][i];for(let k=i;k<=n;k++)aug[i][k]/=denom;
    for(let j=0;j<n;j++)if(j!==i){const factor=aug[j][i];for(let k=i;k<=n;k++)aug[j][k]-=factor*aug[i][k];}
  }
  return aug.map(r=>r[n]);
}
function basis(kind,periods,time) {
  const v=[1];
  for(const p of periods){v.push(Math.sin(2*Math.PI*time/p),Math.cos(2*Math.PI*time/p));}
  return v;
}
function solve(times,ys,kind,periods) {
  const features=times.map(t=>basis(kind,periods,t)),k=features[0].length;
  const matrix=Array.from({length:k},()=>Array(k).fill(0)),rhs=Array(k).fill(0);
  for(let i=0;i<features.length;i++)for(let j=0;j<k;j++){
    rhs[j]+=features[i][j]*ys[i];
    for(let m=0;m<k;m++)matrix[j][m]+=features[i][j]*features[i][m];
  }
  for(let j=0;j<k;j++)matrix[j][j]+=1e-6;
  const coeff=gaussian(matrix,rhs);if(!coeff)return null;
  const predict=t=>basis(kind,periods,t).reduce((s,v,i)=>s+v*coeff[i],0);
  const mse=times.reduce((s,t,i)=>s+(ys[i]-predict(t))**2,0)/times.length;
  return {kind,periods,coeff,trainMSE:mse,score:times.length*Math.log(mse+1e-4)+k*Math.log(times.length),predict};
}
function fit(times,ys){
  const fits=[solve(times,ys,'constant',[])];
  for(const p of periods) fits.push(solve(times,ys,'one',[p]));
  for(let i=0;i<periods.length;i++)for(let j=i+1;j<periods.length;j++){
    if(Math.abs(periods[i]-periods[j]) < .75)continue;
    fits.push(solve(times,ys,'two',[periods[i],periods[j]]));
  }
  return fits.filter(Boolean).sort((a,b)=>a.score-b.score)[0];
}
const readings={};
for(const [kind,rule] of Object.entries(kinds)){
  const noise=time=>.02*Math.sin(17.123*time+1.7);
  const obs=grid.map(t=>Math.round(100*(rule(t)+noise(t)))/100);
  const choice=fit(grid,obs);
  const errors=future.map(t=>choice.predict(t)-rule(t));
  const rmse=Math.sqrt(errors.reduce((s,v)=>s+v*v,0)/errors.length);
  const oracleClass=kind==='slow'?'one':kind==='constant'?'constant':kind==='dual'||kind==='existing'?'two':'one';
  const windowAccuracy=future.filter(t=>(choice.predict(t)>=.66)===(rule(t)>=.66)).length/future.length;
  readings[kind]={oracleClass,selectedFamily:choice.kind,periods:choice.periods,
    trainRMSE:Math.sqrt(choice.trainMSE),heldoutRMSE:rmse,
    heldoutWindowAccuracy:windowAccuracy,trainingSamples:obs.length,forecastSamples:future.length};
}
assert(measureResonance(3).time===3);
const phaseTimes=[0,3,6,9,12,15,18,21];
const background=t=>.11*Math.sin(t/3);
const direct=(t,enabled)=>background(t)+(enabled?.35:0);
const confoundedTime=t=>background(t)+(t>=12?.35:0);
const passive=phaseTimes.map(t=>({t,enabled:t>=12,direct:direct(t,t>=12),timeExplanation:confoundedTime(t)}));
assert(passive.every(r=>Math.abs(r.direct-r.timeExplanation)<1e-12));
const interventions=[{t:6,enabled:true},{t:18,enabled:false}].map(x=>({...x,direct:direct(x.t,x.enabled),timeExplanation:confoundedTime(x.t)}));
assert(interventions.every(r=>Math.abs(r.direct-r.timeExplanation)>.34));
function windows(rule,threshold,span,dt){
  const runs=[],open=[];
  let begun=null;
  for(let t=0;t<span+dt*.5;t+=dt){
    const active=rule(t)>=threshold;
    if(active){if(begun===null)begun=t;}
    else if(begun!==null){runs.push(t-begun);begun=null;}
  }
  if(begun!==null)runs.push(span-begun);
  return runs;
}
const existingWindows=windows(resonanceAt,.66,120,1/120);
const shortFast=windows(t=>Math.sin(2*Math.PI*t/4),.66,120,1/120);
const longSlow=windows(t=>Math.sin(2*Math.PI*t/86400),.66,86400,20);
const minimum=arr=>arr.length?Math.min(...arr):null;
const mean=arr=>arr.reduce((s,x)=>s+x,0)/arr.length;
const successFromWindowOnset = lengths => Object.fromEntries([.15,.3,.6,1].map(delay => [String(delay), {canAct: lengths.filter(length=>length>=delay).length, windows:lengths.length, fraction:lengths.filter(length=>length>=delay).length/lengths.length}]));
const timing={
  existing:{events:existingWindows.length,minWindowSeconds:minimum(existingWindows),meanWindowSeconds:mean(existingWindows),onsetDelaySuccess:successFromWindowOnset(existingWindows)},
  fast:{events:shortFast.length,minWindowSeconds:minimum(shortFast),meanWindowSeconds:mean(shortFast),onsetDelaySuccess:successFromWindowOnset(shortFast)},
  slow:{events:longSlow.length,minWindowSeconds:minimum(longSlow),meanWindowSeconds:mean(longSlow)},
  observation:'Analytic opportunity durations only; no perceptual latency, player ability or real-time fairness evidence'};
const results={metadata:{provenance:'GameCore hidden-mechanism.js for existing; other rules synthetic comparison hypotheses',
  instrument:'rounded intensity with deterministic bounded sensor error',trainTimes:grid,testTimes:future,
  candidateFamilies:'constant + Fourier periodic single and dual families, periods 2.5..12 at 0.25 increments; BIC penalized',
  warning:'Model inferability on specified signals is not people discovering laws'},
  inference:readings,causal:{
    observationalIdentical:passive.every(r=>r.direct===r.timeExplanation),passive,
    interventions,interventionDistinguishes:interventions.every(r=>Math.abs(r.direct-r.timeExplanation)>.34),
    caveat:'synthetic causal counterexample, not implemented in production PRSE'},
  timing};
writeFileSync(new URL('./hidden_inference_results.json',import.meta.url),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify({observer:readings,causalIdentifiablePassively:false,
  distinguishWithInterventions:results.causal.interventionDistinguishes,timing}));
