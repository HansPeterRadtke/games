import test from 'node:test';
import assert from 'node:assert/strict';
import {
  KEY_ORDER, MAX_SEQUENCE_LENGTH, SEQUENCE_ROUNDS, currentExpected, deleteCharacter, elapsedMs, finishEarly,
  generateSequence, newProfile, newSession, normalizeConfig, pause, progressOf,
  reshuffleSequence, restoreSession, sequenceRecordKey, snapshot, start,
  summaryOf, typeCharacter, unlockedKeys, validSequence,
} from '../src/core.js';

function enterRound(state, profile, beginning, pace = 100) {
  if (state.phase === 'between-rounds') assert.ok(start(state, profile, beginning));
  const sequence = state.sequence;
  let time = beginning;
  let result;
  for (const key of sequence) {
    time += pace;
    result = typeCharacter(state, profile, key, time);
  }
  return { time, result };
}

test('sequence mode defaults to all unlocked keys and ten short rounds', () => {
  const s = newSession({ mode: 'sequence' });
  assert.equal(s.sequenceLength, 2);
  assert.equal(s.sequenceRounds, 10);
  assert.equal(s.mode, 'sequence');
  assert.ok(SEQUENCE_ROUNDS.every(n => n < 50));
  assert.equal(newSession({ mode: 'sequence', level: 6 }).sequenceLength, 7);
  assert.equal(normalizeConfig({ mode: 'sequence', level: 6, sequenceLength: 2 }).sequenceLength, 7);
  assert.equal(normalizeConfig({ mode: 'sequence', sequenceLength: 999 }).sequenceLength, MAX_SEQUENCE_LENGTH);
  assert.equal(normalizeConfig({ mode: 'sequence', sequenceRounds: 999 }).sequenceRounds, 10);
  assert.equal(newSession().mode, 'keys');
});

test('Fisher–Yates creates whole-key permutations rather than random replacement', () => {
  const s = newSession({ mode: 'sequence', level: 5, sequenceLength: 17 });
  const keys = unlockedKeys(s);
  const result = generateSequence(s, () => 0);
  assert.equal(result.length, 17);
  for (const chunk of [result.slice(0, 6), result.slice(6, 12)]) {
    assert.equal(chunk.length, 6);
    assert.deepEqual([...chunk].sort(), [...keys].sort());
  }
  assert.equal(new Set([...result.slice(12, 17)]).size, 5);
  assert.ok([...result].every(c => keys.includes(c)));
  assert.ok(validSequence(s, result));
});

test('shuffle is explicit and always changes an existing arrangement', () => {
  const s = newSession({ mode: 'sequence', level: 3 });
  assert.ok(reshuffleSequence(s, () => 0));
  const first = s.sequence;
  assert.equal(s.target, first);
  assert.ok(reshuffleSequence(s, () => 0));
  assert.notEqual(s.sequence, first);
  assert.equal(s.sequence.length, 4);
  const p = newProfile();
  start(s, p, 0);
  assert.equal(reshuffleSequence(s, () => 0), false);
});

test('same fixed sequence persists between rounds and across a new session', () => {
  const s = newSession({ mode: 'sequence', level: 2, sequenceRounds: 3 });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  const initial = s.sequence;
  assert.equal(start(s, p, 0), true);
  const first = enterRound(s, p, 0, 100);
  assert.equal(first.result.kind, 'round-complete');
  assert.equal(s.sequence, initial);
  assert.equal(s.target, initial);
  assert.equal(currentExpected(s), initial[0]);
  assert.equal(progressOf(s).done, 3);
  const second = enterRound(s, p, first.time, 90);
  assert.equal(second.result.kind, 'round-complete');
  assert.equal(s.sequence, initial);
  const third = enterRound(s, p, second.time, 80);
  assert.equal(third.result.kind, 'complete');
  assert.equal(s.phase, 'complete');
  assert.equal(s.correct, 9);
  assert.equal(progressOf(s).total, 9);
  const repeat = newSession(s);
  assert.equal(repeat.sequence, initial);
  assert.equal(repeat.rounds.length, 0);
  assert.equal(profileRecord(p, s).count, 3);
  assert.equal(profileRecord(p, s).bestMs, 240);
});

function profileRecord(profile, session) { return profile.sequenceRecords[sequenceRecordKey(session)]; }

test('records improve only for faster entire rounds, with clear old-best comparison', () => {
  const s = newSession({ mode: 'sequence', sequenceRounds: 3 });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  start(s, p, 0);
  const first = enterRound(s, p, 0, 200);
  assert.equal(first.result.round.newRecord, true);
  assert.equal(first.result.round.achievement.kind, 'first');
  assert.equal(profileRecord(p, s).bestMs, 400);
  const second = enterRound(s, p, first.time, 100);
  assert.equal(second.result.round.achievement.kind, 'improved');
  assert.equal(second.result.round.achievement.previousBestMs, 400);
  assert.equal(second.result.round.achievement.improvementMs, 200);
  assert.equal(profileRecord(p, s).bestMs, 200);
  const third = enterRound(s, p, second.time, 300);
  assert.equal(third.result.kind, 'complete');
  assert.equal(third.result.round.newRecord, false);
  assert.equal(s.lastAchievement, null);
  assert.equal(profileRecord(p, s).lastMs, 600);
  assert.equal(profileRecord(p, s).bestMs, 200);
  assert.equal(profileRecord(p, s).count, 3);
  assert.equal(s.rounds.length, 3);
  assert.equal(summaryOf(s, third.time).bestRoundMs, 200);
  assert.equal(p.history[0].roundsCompleted, 3);
  assert.equal(p.history[0].sequence, s.sequence);
});

test('mistakes count against the specific round and do not advance', () => {
  const s = newSession({ mode: 'sequence', sequenceRounds: 3 });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  start(s, p, 0);
  const target = s.sequence;
  assert.equal(typeCharacter(s, p, 'x', 100).kind, 'incorrect');
  assert.equal(s.typed, '');
  assert.equal(s.roundErrors, 1);
  assert.equal(typeCharacter(s, p, target[0], 130).kind, 'ignored');
  assert.equal(deleteCharacter(s, 150).kind, 'cleared');
  assert.equal(typeCharacter(s, p, target[0].toUpperCase(), 200).kind, 'correct');
  const result = typeCharacter(s, p, target[1], 400);
  assert.equal(result.kind, 'round-complete');
  assert.equal(result.round.ms, 400);
  assert.equal(result.round.errors, 1);
  assert.equal(result.round.accuracy, 66.7);
  assert.equal(s.roundErrors, 0);
  assert.equal(s.errors, 1);
  assert.equal(s.trials[0].ms, 200);
  assert.equal(s.trials[0].errors, 1);
});

test('pauses are excluded from the current sequence round clock', () => {
  const s = newSession({ mode: 'sequence', sequenceRounds: 3 });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  start(s, p, 0);
  const k0 = s.sequence[0], k1 = s.sequence[1];
  typeCharacter(s, p, k0, 100);
  pause(s, 120);
  assert.equal(s.phase, 'paused');
  assert.equal(typeCharacter(s, p, k1, 90000).kind, 'ignored');
  start(s, p, 90000);
  const result = typeCharacter(s, p, k1, 90080);
  assert.equal(result.round.ms, 200);
  assert.equal(result.round.achievement.ms, 200);
  const next = enterRound(s, p, 90080, 75);
  assert.equal(next.result.round.ms, 150);
});

test('snapshot and restore keep the sequence, partial round, timer and record', () => {
  const s = newSession({ mode: 'sequence', sequenceRounds: 3, level: 3 });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  start(s, p, 0);
  const first = enterRound(s, p, 0, 100);
  start(s, p, first.time);
  typeCharacter(s, p, s.sequence[0], first.time + 150);
  typeCharacter(s, p, 'x', first.time + 200);
  const data = snapshot(s, first.time + 250);
  assert.equal(data.phase, 'paused');
  const restored = restoreSession(data);
  assert.equal(restored.phase, 'paused');
  assert.equal(restored.sequence, s.sequence);
  assert.equal(restored.rounds.length, 1);
  assert.equal(restored.typed, s.sequence[0]);
  assert.equal(restored.roundErrors, 1);
  assert.equal(restored.correct, 5);
  assert.equal(restored.activeMs, first.time + 250);
  start(restored, p, 90000);
  deleteCharacter(restored, 90010);
  for (let i = 1; i < restored.sequence.length; i++) {
    typeCharacter(restored, p, restored.sequence[i], 90100 + i * 100);
  }
  assert.equal(restored.rounds.length, 2);
  assert.equal(restored.rounds[1].errors, 1);
  assert.equal(restored.rounds[1].ms, 650);
  assert.ok(profileRecord(p, restored));
});

test('invalid sequence or mismatching trial ledger cannot resurrect a fabricated round', () => {
  const s = newSession({ mode: 'sequence', sequenceRounds: 3 });
  reshuffleSequence(s, () => 0);
  const invalid = { ...s, sequence: 'xx', target: 'xx', phase: 'paused', rounds: [] };
  const a = restoreSession(invalid);
  assert.equal(a.phase, 'idle');
  assert.equal(a.sequence, '');
  const fake = { ...s, phase: 'complete', rounds: [{ number: 1, ms: 50, errors: 0, accuracy: 100 }], trials: [] };
  const b = restoreSession(fake);
  assert.equal(b.phase, 'idle');
  assert.equal(b.rounds.length, 0);
});

test('repeat fixed sequence after abandoning a partially completed session', () => {
  const s = newSession({ mode: 'sequence' });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  start(s, p, 0);
  const first = enterRound(s, p, 0, 100);
  start(s, p, first.time);
  typeCharacter(s, p, s.sequence[0], first.time + 50);
  finishEarly(s, p, first.time + 75);
  assert.equal(p.history[0].status, 'interrupted');
  assert.equal(p.history[0].roundsCompleted, 1);
  assert.equal(newSession(s).sequence, s.sequence);
});

test('changing modes without changing unlocked keys preserves the competition sequence', () => {
  const p = newProfile();
  const s = newSession({ mode: 'sequence', level: 3, sequenceRounds: 3 });
  reshuffleSequence(s, () => 0);
  const original = s.sequence;
  const keys = newSession({ ...s, mode: 'keys' });
  assert.equal(keys.mode, 'keys');
  assert.equal(keys.sequence, original);
  assert.equal(keys.target, '');
  start(keys, p, 0);
  assert.equal(keys.target.length, 1);
  const text = newSession({ ...keys, mode: 'text' });
  assert.equal(text.sequence, original);
  const back = newSession({ ...text, mode: 'sequence' });
  assert.equal(back.sequence, original);
  assert.equal(back.target, original);
  assert.equal(newSession({ ...back, level: 4 }).sequence, '');
});

test('record retention keeps the currently played sequence after many prior shuffles', () => {
  const s = newSession({ mode: 'sequence', level: 3, sequenceRounds: 3 });
  const p = newProfile();
  reshuffleSequence(s, () => 0);
  for (let i = 0; i < 305; i++) p.sequenceRecords['1|old_' + i] = { bestMs: 1, count: 1 };
  start(s, p, 0);
  enterRound(s, p, 0, 100);
  assert.equal(Object.keys(p.sequenceRecords).length, 300);
  assert.equal(profileRecord(p, s).bestMs, 400);
});

test('longest allowed sequence session survives saved-state restoration', () => {
  const s = newSession({ mode: 'sequence', sequenceLength: MAX_SEQUENCE_LENGTH, sequenceRounds: 30 });
  const p = newProfile();
  reshuffleSequence(s, () => .37);
  start(s, p, 0);
  let t = 0;
  for (let round = 0; round < 30; round++) {
    const next = enterRound(s, p, t, 12);
    t = next.time;
  }
  assert.equal(s.correct, 4500);
  assert.equal(s.phase, 'complete');
  assert.equal(s.rounds.length, 30);
  const recovered = restoreSession(snapshot(s, t));
  assert.equal(recovered.phase, 'complete');
  assert.equal(recovered.correct, 4500);
  assert.equal(recovered.rounds.length, 30);
  assert.equal(recovered.sequence, s.sequence);
  assert.equal(profileRecord(p, recovered).bestMs, 1800);
});

test('round breaks ignore letters, survive reload and exclude all waiting time', () => {
  const s = newSession({ mode: 'sequence', sequence: 'fj', sequenceRounds: 3 }), p = newProfile();
  start(s, p, 0);
  enterRound(s, p, 0, 125);
  assert.equal(s.phase, 'between-rounds');
  assert.equal(elapsedMs(s, 50000), 250);
  assert.equal(typeCharacter(s, p, 'f', 50000).kind, 'ignored');
  assert.equal(s.correct, 2);
  const restored = restoreSession(snapshot(s, 60000));
  assert.equal(restored.phase, 'between-rounds');
  assert.equal(typeCharacter(restored, p, 'j', 65000).kind, 'ignored');
  start(restored, p, 70000);
  const next = enterRound(restored, p, 70000, 80);
  assert.equal(next.result.round.ms, 160);
  assert.equal(restored.trials[2].ms, 80);
  assert.equal(elapsedMs(restored, 90000), 410);
});
