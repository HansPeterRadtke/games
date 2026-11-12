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
