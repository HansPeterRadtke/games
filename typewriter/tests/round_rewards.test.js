import test from 'node:test';
import assert from 'node:assert/strict';
import { currentExpected, deleteCharacter, finishEarly, keyRoundKey, newProfile, newSession, pause,
  roundRecordFor, start, typeCharacter } from '../src/core.js';
import { recentStats, scoreRound } from '../src/rounds.js';
import { parseExport, serializeData } from '../src/storage.js';

test('recent comparisons exclude the new round, expire old scores and preserve the lifetime best', () => {
  for (const timed of [true, false]) {
    const speeds = timed ? [100, 160, 160, 160, 140, 140, 90] : [100, 40, 40, 40, 60, 60, 110];
    let record, result;
    const tiers = [];
    for (const score of speeds) {
      result = scoreRound(record, score, 100, timed, 3);
      tiers.push(result.reward.tier);
      record = result.record;
      if (record.count === 5) {
        assert.equal(result.reward.target, speeds[1]);
        assert.equal(result.reward.milestone, 5);
        assert.equal(record[timed ? 'bestMs' : 'bestWpm'], 100);
      }
    }
    assert.deepEqual(tiers, ['baseline', 'clean', 'clean', 'clean', 'recent', 'clean', 'all-time']);
    assert.equal(result.reward.target, 100);
    const recent = recentStats(record, 3, timed);
    assert.equal(recent.count, 3);
    assert.equal(recent.bestScore, speeds.at(-1));
    assert.equal(recent.meanScore, speeds.slice(-3).reduce((a,b) => a+b)/3);
    assert.equal(recent.meanAccuracy, 100);
  }
});

test('accuracy can win independently, ties and plateaus get accurate feedback and milestones', () => {
  let record = scoreRound(null, 50, 95, false, 3).record;
  for (const a of [75, 85, 80]) record = scoreRound(record, 40, a, false, 3).record;
  const accuracy = scoreRound(record, 40, 90, false, 3);
  assert.deepEqual([accuracy.reward.tier, accuracy.reward.metric, accuracy.reward.target, accuracy.reward.milestone],
    ['recent', 'accuracy', 85, 5]);
  const strict = scoreRound(accuracy.record, 40, 96, false, 3);
  assert.equal(strict.reward.tier, 'all-time');
  assert.equal(strict.reward.metric, 'accuracy');
  const tie = scoreRound(strict.record, 50, 96, false, 3);
  assert.equal(tie.reward.tier, 'recent'); // Ties the lifetime pace but beats all three preceding rounds.
  for (let i=0; i<50; i++) {
    const r = scoreRound(tie.record, 50, 96, false, 3);
    assert.equal(r.reward.tier, 'matched');
    assert.equal(r.reward.milestone !== null, r.record.count % 5 === 0);
    tie.record = r.record;
  }
  assert.equal(tie.record.recentRounds.length, 20);
  assert.equal(recentStats(tie.record, 1, false).count, 1);
});

test('completed rounds are the only writes across all three modes and survive export/resume', () => {
  for (const mode of ['keys', 'sequence', 'text']) {
    const p = newProfile();
    p.roundWindow = 10;
    const state = newSession({mode, goal:10, sequenceRounds:3, passageId:'custom', customText:'fj'});
    start(state, p, 0);
    typeCharacter(state, p, 'x', 25);
    if (mode !== 'keys') deleteCharacter(state, 60);
    typeCharacter(state, p, currentExpected(state), 100);
    pause(state, 150);
    assert.equal(roundRecordFor(state, p), undefined);
    const data = parseExport(serializeData(state, p, 200));
    const s = data.session, profile = data.profile;
    start(s, profile, 1000);
    let now = 1000, last;
    for (let i = 0; i < 10 && !last?.reward; i++) {
      now += 100;
      last = typeCharacter(s, profile, currentExpected(s), now);
    }
    assert.equal(last.reward.tier, 'baseline');
    assert.ok(last.reward.accuracy < 100);
    assert.equal(roundRecordFor(s, profile).count, 1);
    if (mode === 'sequence') {
      for (let i = 0; i < s.sequenceLength * (s.sequenceRounds - 1); i++) {
        if (s.phase === 'between-rounds') start(s, profile, now);
        now += 100;
        typeCharacter(s, profile, currentExpected(s), now);
      }
      assert.equal(s.phase, 'complete');
      assert.equal(roundRecordFor(s, profile).count, 3);
    }
    assert.equal(typeCharacter(s, profile, 'x', now+50).kind, 'ignored');
    const loaded = parseExport(serializeData(s, profile, now));
    assert.equal(loaded.profile.roundWindow, 10);
    assert.deepEqual(roundRecordFor(loaded.session, loaded.profile), roundRecordFor(s, profile));
    const next = newSession(s);
    start(next, profile, now);
    finishEarly(next, profile, now+200);
    assert.equal(roundRecordFor(next, profile).count, mode === 'sequence' ? 3 : 1);
  }
});

test('an older save recovers only identifiable rounds and keeps existing lifetime records', () => {
  const p = newProfile();
  delete p.keyRoundRecords;
  delete p.roundWindow;
  const s = newSession({mode:'sequence',sequence:'fj'});
  p.sequenceRecords['1|fj'] = {bestMs:100, lastMs:300, bestAccuracy:100, count:19};
  p.textRecords['level-mixed:1'] = {bestWpm:90, bestAccuracy:100};
  p.history = [
    {mode:'text', level:1, correct:1, goal:1, passageId:'__proto__', accuracy:100,wpm:90,status:'completed'},
    {mode:'keys', level:1, correct:5, goal:10, accuracy:100, wpm:200,status:'interrupted'},
    {mode:'keys', level:1, correct:10, goal:10, accuracy:98, wpm:60,status:'completed'},
    {mode:'text', level:1, correct:55, goal:55, passageId:'level-mixed', accuracy:95,wpm:65,status:'completed'},
  ];
  const {profile} = parseExport(JSON.stringify({version:1, profile:p, session:s}));
  assert.equal(Object.hasOwn(Object.prototype, 'recentRounds'), false);
  assert.equal(profile.roundWindow, 3);
  assert.equal(profile.sequenceRecords['1|fj'].bestMs, 100);
  assert.deepEqual(profile.sequenceRecords['1|fj'].recentRounds, [{score:300, accuracy:null}]);
  assert.equal(profile.textRecords['level-mixed:1'].bestWpm, 90);
  assert.deepEqual(profile.textRecords['level-mixed:1'].recentRounds,[{score:65,accuracy:95}]);
  assert.equal(profile.keyRoundRecords['1:10'].bestWpm, 60);
  assert.equal(profile.keyRoundRecords['1:10'].count,1);
  assert.equal(profile.keyRoundRecords[keyRoundKey({level:2,goal:10})],undefined);
  assert.deepEqual(parseExport(serializeData(s, profile, 0)).profile, profile);
});
