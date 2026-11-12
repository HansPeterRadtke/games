import test from 'node:test';
import assert from 'node:assert/strict';
import { newSession, newProfile, start, typeCharacter, deleteCharacter, pause } from '../src/core.js';
import { choosePracticeWord, wordDistribution, wordRecordKey } from '../src/word_practice.js';
import { wordPool } from '../src/training_text.js';
import { serializeData, parseExport } from '../src/storage.js';
const config = {mode:'word',level:10,wordLanguage:'de',wordStrategy:'selected',selectedWord:'glas',wordRepeats:3};

test('chosen word, repetitions, correction, pause and saved observations agree',()=>{
  const s=newSession(config), p=newProfile();
  start(s,p,0);
  let t=0;
  for(const k of 'glas') typeCharacter(s,p,k,t+=90);
  assert.equal(p.wordStats.glas.count,1);
  typeCharacter(s,p,' ',t+=60);
  typeCharacter(s,p,'!',t+=40);
  assert.equal(typeCharacter(s,p,'g',t+=40).kind,'ignored');
  pause(s,t);
  const recovered=parseExport(serializeData(s,p,t));
  const r=recovered.session, profile=recovered.profile;
  assert.equal(r.typed,'glas '); assert.equal(r.feedback,'incorrect');
  start(r,profile,10000); deleteCharacter(r);
  t=10000;
  for (const k of 'glas glas') typeCharacter(r,profile,k,t+=100);
  assert.equal(r.phase,'complete'); assert.equal(profile.wordStats.glas.count,3);
  assert.equal(profile.wordStats.glas.errors,1); assert.ok(profile.wordStats.glas.msPerChar<150);
  assert.equal(profile.wordRecords[wordRecordKey(r)].count,1);
  const saved=parseExport(serializeData(r,profile,t));
  assert.deepEqual(saved.profile.wordStats.glas,profile.wordStats.glas);
  assert.equal(saved.session.practiceWord,'glas'); assert.equal(saved.profile.history[0].mode,'word');
});

test('text practice teaches the adaptive draw from completed spellings, excluding separators and drills',()=>{
  const p=newProfile(), s=newSession({mode:'text',level:10,passageId:'custom',customText:'glas ä fass'});
  start(s,p,0);let t=0;
  for (const ch of s.target) {
    if (s.typed==='gl') { typeCharacter(s,p,'!',t+=50); deleteCharacter(s); }
    typeCharacter(s,p,ch,t+=ch===' '?5000:100);
  }
  assert.deepEqual(Object.keys(p.wordStats).sort(),['fass','glas']);
  assert.equal(p.wordStats.glas.errors,1); assert.equal(p.wordStats.fass.msPerChar,100);
  assert.equal(choosePracticeWord({...config,wordStrategy:'mistakes'},p.wordStats,()=>.5),'glas');
  const old=JSON.parse(serializeData(s,p,t));delete old.profile.wordStats;
  const imported=parseExport(JSON.stringify(old));
  assert.deepEqual(imported.profile.wordStats,p.wordStats);
});

test('adaptive draws explore and change probabilities as each repetition is completed',()=>{
  const p=newProfile(), pool=wordPool(10,'de');
  p.wordStats.glas={count:8,errors:9,errorRate:.6,msPerChar:850};
  p.wordStats.kalk={count:8,errors:2,errorRate:.2,msPerChar:300};
  p.wordStats.flug={count:50,errors:80,errorRate:.9,msPerChar:2000};
  const weights=kind=>Object.fromEntries(wordDistribution(pool,kind,p.wordStats).entries);
  assert.ok(weights('mistakes').glas > weights('mistakes').kalk);
  assert.ok(weights('slowest').glas > weights('slowest').kalk);
  assert.equal(weights('slowest').flug,undefined);
  const s=newSession({...config,wordRepeats:12},p);start(s,p,0);
  [...s.target].forEach((k,i)=>typeCharacter(s,p,k,(i+1)*60));
  assert.ok(weights('mistakes').glas < weights('mistakes').kalk);
  assert.ok(weights('slowest').glas < weights('slowest').kalk);
  const random=choosePracticeWord({...config,wordStrategy:'mistakes'},p.wordStats,()=>0);
  assert.equal(random,pool.words[0]);
  assert.notEqual(choosePracticeWord({...config,wordStrategy:'random'},p.wordStats,()=>0,pool.words[0]),pool.words[0]);
  const singleRate = errorRate => wordDistribution(pool,'mistakes',{glas:{count:20,errorRate}}).focus;
  assert.ok(singleRate(.01) < singleRate(.2));
  assert.equal(newSession({...config,selectedWord:'hajj'}).target,'');
  assert.equal(newSession({...config,level:1}).target,'');
});

function chances(profile, exclude = '') {
  const pool = wordPool(10, 'de');
  const {entries, total, focus} = wordDistribution(pool, 'combined', profile.wordStats, exclude, profile);
  const size = pool.words.length - Number(pool.members.has(exclude));
  const weight = new Map(entries);
  return word => word === exclude ? 0 : (1 - focus) / size + (total ? focus * (weight.get(word) || 0) / total : 0);
}

test('combined selection learns before a word ends, ignores blocked input and survives reload', () => {
  const p = newProfile(), s = newSession(config,p);
  start(s,p,0);
  const initial = chances(p)('glas');
  typeCharacter(s,p,'!',100);
  const afterTypo = chances(p)('glas');
  assert.ok(afterTypo > initial && afterTypo > .5);
  assert.equal(p.typingSignals.g.attempts,1);
  assert.equal(p.typingSignals.glas.attempts,1);
  const mistakeOnly = wordDistribution(wordPool(10,'de'),'mistakes',p.wordStats,'',p);
  assert.ok(new Map(mistakeOnly.entries).get('glas')>0);
  typeCharacter(s,p,'g',120);
  assert.equal(p.typingSignals.glas.attempts,1);
  assert.ok(chances(p)('gas') > chances(p)('kalk'));
  const loaded = parseExport(serializeData(s,p,125));
  assert.equal(chances(loaded.profile)('glas'),afterTypo);
  assert.equal(loaded.session.practiceWord,'glas');
  start(loaded.session,loaded.profile,9000);
  deleteCharacter(loaded.session);
  typeCharacter(loaded.session,loaded.profile,'g',9100);
  assert.equal(loaded.profile.typingSignals.glas.attempts,2);
  assert.equal(loaded.profile.typingSignals.glas.ms,225);
  assert.ok(loaded.profile.typingSignals.glas.errorRate < 1);
  assert.equal(loaded.profile.wordStats.glas,undefined);
  let time=9100;
  for (const c of loaded.session.target.slice(1)) typeCharacter(loaded.session,loaded.profile,c,time+=70);
  assert.ok(chances(loaded.profile)('glas') < afterTypo);
  assert.equal(loaded.profile.typingSignals[' '],undefined);
});

test('mistakes receive priority, accurate slow words stay eligible and key difficulty transfers to unseen words', () => {
  const p = newProfile();
  for (const [word, errorRate, pace] of [['glas',.35,110],['kalk',0,700],['fass',0,100]]) {
    p.wordStats[word] = {count:8,errors:Math.round(errorRate*30),errorRate,msPerChar:pace};
  }
  p.keyStats.g = {count:8,errors:4,emaMs:600,bestMs:100};
  p.keyStats.a = {count:10,errors:0,emaMs:100,bestMs:80};
  let chance = chances(p);
  assert.ok(chance('glas') > chance('kalk') && chance('kalk') > chance('fass'));
  assert.ok(chance('gas') > chance('saal'));
  const pool = wordPool(10,'de');
  assert.ok(Math.abs(pool.words.reduce((s,w)=>s+chance(w),0)-1) < 1e-9);
  assert.equal(chances(p,'glas')('glas'),0);
  let seed=100;
  const random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
  const draws={};
  for (let i=0;i<1000;i++) {
    const word=choosePracticeWord({...config, wordStrategy:'combined'},p.wordStats,random,'',p);
    draws[word]=(draws[word]||0)+1;
  }
  assert.ok(draws.glas>500 && draws.kalk>90 && draws.kalk>draws.fass);
  p.wordStats.glas.errorRate=0; p.keyStats.g.errors=0;
  chance=chances(p);
  assert.ok(chance('kalk') > chance('glas') && chance('gas') > chance('saal'));
});

test('letter-only practice influences word selection immediately and interrupted text retains its word signal', () => {
  const p=newProfile(), s=newSession({mode:'keys',level:10});
  start(s,p,0,()=>0);
  const key=s.target;
  typeCharacter(s,p,'!',100);
  const pool=wordPool(10,'de'), chance=chances(p);
  assert.ok(chance(pool.words.find(w=>w.includes(key))) > chance(pool.words.find(w=>!w.includes(key))));
  assert.equal(p.keyStats[key],undefined);
  const text=newSession({mode:'text',level:10,passageId:'custom',customText:'glas fass'});
  start(text,p,0);
  for(const [i,k] of [...'glas f!'].entries()) typeCharacter(text,p,k,(i+1)*100);
  assert.equal(p.typingSignals.fass.attempts,2);
  assert.equal(p.typingSignals.a.errorRate>0,true);
  assert.ok(chances(p)('fass') > chances(p)('glas'));
});

test('small speed differences in clean words count even if isolated key trials are much slower', () => {
  const p=newProfile();
  for (const [word,msPerChar] of [['glas',100],['kalk',105]]) {
    p.wordStats[word]={count:15,errors:0,errorRate:0,msPerChar};
  }
  for (const key of 'glak') p.keyStats[key]={count:30,errors:0,emaMs:1000,bestMs:700};
  assert.ok(chances(p)('kalk') > chances(p)('glas'));
});
