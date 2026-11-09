import test from 'node:test';
import assert from 'node:assert/strict';
import {
  KEY_ORDER, PASSAGES, WINDOW_SIZES, accuracyOf, currentExpected, elapsedMs, finishEarly,
  newProfile, newSession, normalizeConfig, passageFingerprint, pause, progressOf, restoreSession,
  snapshot, start, summaryOf, typeCharacter, weightedKeyChoice,
} from '../src/core.js';

function typePerfect(state, profile, count, { startTime = 0, pace = 250, rng = () => 0 } = {}) {
  let time = startTime;
  for (let i = 0; i < count; i++) {
    time += pace;
    typeCharacter(state, profile, currentExpected(state), time, rng);
  }
  return time;
}

test('original German key ordering and gradually unlocked levels are preserved', () => {
  assert.equal(KEY_ORDER.join(''), 'fjdkslaöghärueiwoqptzüvmcxybn');
  assert.equal(newSession().level, 1);
  assert.equal(newSession().goal, 50);
  assert.equal(normalizeConfig({ level: 500 }).level, KEY_ORDER.length - 1);
  assert.deepEqual(WINDOW_SIZES, [10, 20, 50, 100, 200, 500, 1000]);
});

test('starting the key trainer produces an actual target, not a placeholder', () => {
  const s = newSession(), p = newProfile();
  assert.equal(start(s, p, 100, () => 0), true);
  assert.equal(s.target, 'f');
  assert.equal(s.phase, 'running');
  assert.equal(start(s, p, 110), false);
});

test('a correct round records key timing, unlocks records, and ends at the selected length', () => {
  const s = newSession({ goal: 10 }), p = newProfile();
  start(s, p, 0, () => 0);
  const finish = typePerfect(s, p, 10);
  assert.equal(s.phase, 'complete');
  assert.equal(s.correct, 10);
  assert.equal(s.errors, 0);
  assert.equal(summaryOf(s, finish).avgMs, 250);
  assert.equal(summaryOf(s, finish).accuracy, 100);
  assert.equal(summaryOf(s, finish).wpm, 48);
  assert.equal(progressOf(s).done, 10);
  assert.equal(p.history[0].status, 'completed');
  assert.equal(p.records['1']['10'].avgMs.value, 250);
  assert.equal(p.records['1']['10'].accuracy.value, 100);
  assert.equal(start(s, p, finish + 1), false);
});

test('wrong keys do not advance; accuracy includes mistakes; time includes correction', () => {
  const s = newSession({ goal: 10 }), p = newProfile();
  start(s, p, 0, () => 0);
  assert.equal(typeCharacter(s, p, 'z', 50).kind, 'incorrect');
  assert.equal(typeCharacter(s, p, 'g', 100).kind, 'incorrect');
  assert.equal(s.correct, 0);
  assert.equal(typeCharacter(s, p, 'F', 300, () => 0).kind, 'correct');
  assert.equal(s.trials[0].ms, 300);
  assert.equal(s.trials[0].errors, 2);
  assert.equal(s.correct, 1);
  assert.equal(s.errors, 2);
  assert.equal(accuracyOf(s.correct, s.errors), 100 / 3);
  assert.equal(p.keyStats.f.errors, 2);
});

test('pause and resume remove downtime from both the timer and next key latency', () => {
  const s = newSession(), p = newProfile();
  start(s, p, 0, () => 0);
  assert.equal(pause(s, 120), true);
  assert.equal(elapsedMs(s, 60000), 120);
  assert.equal(s.phase, 'paused');
  assert.equal(typeCharacter(s, p, 'f', 60000).kind, 'ignored');
  assert.equal(start(s, p, 60000), true);
  typeCharacter(s, p, 'f', 60200, () => 0);
  assert.equal(s.trials[0].ms, 320);
  assert.equal(elapsedMs(s, 60200), 320);
});

test('corrupted or unobserved adaptive speeds cannot cause divide-by-zero', () => {
  const p = newProfile(), s = newSession();
  assert.equal(weightedKeyChoice(s, p, () => 0), 'f');
  p.keyStats.f = { count: 1, errors: 0, emaMs: 1000, bestMs: 1000 };
  p.keyStats.j = { count: 1, errors: 0, emaMs: 1000, bestMs: 1000 };
  assert.equal(weightedKeyChoice(s, p, () => .8), 'j');
  assert.equal(weightedKeyChoice(s, p, () => 1), 'j');
});

test('adaptive practice gives slower keys more probability, but uniform mode does not', () => {
  const p = newProfile(), s = newSession();
  p.keyStats.f = { count: 20, errors: 0, emaMs: 100, bestMs: 70 };
  p.keyStats.j = { count: 20, errors: 5, emaMs: 1000, bestMs: 700 };
  assert.equal(weightedKeyChoice(s, p, () => .3), 'j');
  s.adaptive = false;
  assert.equal(weightedKeyChoice(s, p, () => .3), 'f');
});

test('selection excludes three identical prompts in a row', () => {
  const s = newSession(), p = newProfile();
  s.lastTwo = ['f', 'f'];
  assert.equal(weightedKeyChoice(s, p, () => 0), 'j');
});

test('high-score windows never treat mistakes as correct hits', () => {
  const s = newSession({ goal: 20 }), p = newProfile();
  start(s, p, 0, () => 0);
  let t = typePerfect(s, p, 10);
  assert.equal(p.records['1']['10'].accuracy.value, 100);
  for (let i = 0; i < 10; i++) {
    const c = currentExpected(s);
    typeCharacter(s, p, 'x', t + 50);
    t += 250;
    typeCharacter(s, p, c, t, () => 0);
  }
  assert.equal(s.phase, 'complete');
  assert.equal(summaryOf(s, t).accuracy, 100 * 20 / 30);
  assert.equal(p.records['1']['20'].accuracy.value, Math.round(1000 * 20 / 30) / 10);
  assert.equal(p.records['1']['10'].accuracy.value, 100);
  assert.equal(p.records['1']['10'].slowestMs.value <= 250, true);
});

test('text practice is case-sensitive, permits spaces, and finishes on the last character', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'Ä a' });
  const p = newProfile();
  assert.equal(start(s, p, 0), true);
  assert.equal(typeCharacter(s, p, 'ä', 100).kind, 'incorrect');
  assert.equal(typeCharacter(s, p, 'Ä', 200).kind, 'correct');
  assert.equal(typeCharacter(s, p, ' ', 400).kind, 'correct');
  assert.equal(typeCharacter(s, p, 'a', 600).kind, 'complete');
  assert.equal(s.typed, 'Ä a');
  assert.equal(s.correct, 3);
  assert.equal(s.errors, 1);
  assert.equal(summaryOf(s, 600).accuracy, 75);
  assert.equal(p.history[0].mode, 'text');
  const key = 'custom:' + passageFingerprint('Ä a');
  assert.equal(p.textRecords[key].bestAccuracy, 75);
});

test('passage list contains usable German and English practice texts', () => {
  assert.equal(PASSAGES.length >= 4, true);
  assert.equal(PASSAGES.every(p => p.text.length >= 50 && p.name && p.id), true);
  assert.equal(PASSAGES.some(p => p.language === 'DE'), true);
  assert.equal(PASSAGES.some(p => p.language === 'EN'), true);
});

test('snapshot can restore interrupted practice without counting browser downtime', () => {
  const s = newSession(), p = newProfile();
  start(s, p, 1000, () => 0);
  typeCharacter(s, p, 'x', 1150);
  const snap = snapshot(s, 1250);
  assert.equal(s.phase, 'running');
  assert.equal(snap.phase, 'paused');
  assert.equal(snap.promptMs, 250);
  const resumed = restoreSession(snap);
  assert.equal(resumed.phase, 'paused');
  assert.equal(resumed.errors, 1);
  assert.equal(start(resumed, p, 90000), true);
  typeCharacter(resumed, p, 'f', 90100, () => 0);
  assert.equal(resumed.trials[0].ms, 350);
  assert.equal(resumed.errors, 1);
});

test('ending a partial round archives its actual result and keeps records', () => {
  const s = newSession(), p = newProfile();
  start(s, p, 0, () => 0);
  typePerfect(s, p, 11);
  finishEarly(s, p, 4000);
  assert.equal(s.phase, 'paused');
  assert.equal(p.history[0].status, 'interrupted');
  assert.equal(p.history[0].correct, 11);
  assert.equal(p.records['1']['10'].avgMs.value, 250);
});

test('invalid persisted session values are bounded and safe to restore', () => {
  const s = restoreSession({ phase: 'running', mode: 'keys', level: 900,
    target: 'untrusted', trials: [{ key: 'f', ms: -1, errors: 1 }], activeMs: Infinity });
  assert.equal(s.phase, 'idle');
  assert.equal(s.level, KEY_ORDER.length - 1);
  assert.equal(s.trials.length, 0);
  assert.equal(s.activeMs, 0);
});

test('zero elapsed time does not produce an infinite speed', () => {
  const s = newSession(), p = newProfile();
  start(s, p, 0, () => 0);
  typeCharacter(s, p, 'f', 0, () => 0);
  assert.equal(summaryOf(s, 0).wpm, null);
});
