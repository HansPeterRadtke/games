import test from 'node:test';
import assert from 'node:assert/strict';
import { currentExpected, deleteCharacter, newProfile, newSession, pause, progressOf,
  reshuffleSequence, restoreSession, snapshot, start, typeCharacter, accuracyOf } from '../src/core.js';

test('Delete and Backspace clear incorrect highlight in single-key training without erasing actual mistakes', () => {
  const s = newSession({ mode: 'keys' }), p = newProfile();
  start(s, p, 0, () => 0);
  const expected = s.target;
  assert.equal(typeCharacter(s, p, 'x', 50).kind, 'incorrect');
  assert.equal(s.feedback, 'incorrect');
  const erased = deleteCharacter(s, 100);
  assert.equal(erased.kind, 'cleared');
  assert.equal(s.feedback, '');
  assert.equal(s.correct, 0);
  assert.equal(s.errors, 1);
  assert.equal(s.pendingErrors, 1);
  assert.equal(s.target, expected);
  typeCharacter(s, p, expected, 160, () => 0);
  assert.equal(accuracyOf(s.correct, s.errors), 50);
  assert.equal(s.trials[0].errors, 1);
});

test('repeated Delete with no typed prefix does not invent progress or alter records', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'f j' });
  const p = newProfile();
  start(s, p, 0);
  typeCharacter(s, p, 'x', 25);
  assert.equal(deleteCharacter(s, 50).kind, 'cleared');
  assert.equal(deleteCharacter(s, 75).kind, 'nothing');
  assert.equal(s.typed, '');
  assert.equal(s.errors, 1);
  assert.equal(s.correct, 0);
  assert.equal(progressOf(s).done, 0);
});

test('text Delete clears the typo first, then removes one accepted character per press', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'f j' });
  const p = newProfile();
  start(s, p, 0);
  typeCharacter(s, p, 'f', 100);
  typeCharacter(s, p, ' ', 200);
  assert.equal(s.typed, 'f ');
  typeCharacter(s, p, 'x', 250);
  assert.equal(s.feedback, 'incorrect');
  assert.equal(deleteCharacter(s, 300).kind, 'cleared');
  assert.equal(s.feedback, '');
  assert.equal(s.typed, 'f ');
  assert.equal(currentExpected(s), 'j');
  assert.equal(progressOf(s).done, 2);
  assert.equal(s.correct, 2);
  assert.equal(s.trials.length, 2);
  assert.equal(s.pendingErrors, 1);
  assert.equal(s.promptStart, 200);
  const removed = deleteCharacter(s, 350);
  assert.equal(removed.kind, 'moved-back');
  assert.equal(removed.deleted, ' ');
  assert.equal(s.typed, 'f');
  assert.equal(currentExpected(s), ' ');
  assert.equal(progressOf(s).done, 1);
  assert.equal(s.correct, 1);
  assert.equal(s.errors, 1);
  typeCharacter(s, p, ' ', 400);
  assert.equal(s.typed, 'f ');
  assert.equal(s.correct, 2);
  assert.equal(typeCharacter(s, p, 'j', 500).kind, 'complete');
  assert.equal(accuracyOf(s.correct, s.errors), 75);
});

test('corrected key with preceding errors cannot erase those errors by deleting and retyping', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'fj' });
  const p = newProfile();
  start(s, p, 0);
  typeCharacter(s, p, 'x', 50);
  deleteCharacter(s, 75);
  typeCharacter(s, p, 'f', 100);
  assert.equal(s.trials[0].errors, 1);
  assert.equal(deleteCharacter(s, 150).kind, 'moved-back');
  assert.equal(s.correct, 0);
  assert.equal(s.errors, 1);
  assert.equal(s.pendingErrors, 1);
  typeCharacter(s, p, 'f', 250);
  assert.equal(s.trials[0].errors, 1);
  typeCharacter(s, p, 'j', 350);
  assert.equal(s.phase, 'complete');
  assert.equal(accuracyOf(s.correct, s.errors), 200 / 3);
});

test('sequence cursor moves back within the current round, not into completed rounds', () => {
  const s = newSession({ mode: 'sequence', sequenceRounds: 3 }), p = newProfile();
  reshuffleSequence(s, () => 0);
  start(s, p, 0);
  const first = s.sequence[0], second = s.sequence[1];
  typeCharacter(s, p, first, 100);
  typeCharacter(s, p, 'x', 150);
  assert.equal(deleteCharacter(s, 175).kind, 'cleared');
  assert.equal(s.typed, first);
  assert.equal(currentExpected(s), second);
  assert.equal(s.roundErrors, 1);
  const result = typeCharacter(s, p, second, 300);
  assert.equal(result.kind, 'round-complete');
  assert.equal(result.round.errors, 1);
  assert.equal(result.round.ms, 300);
  assert.equal(deleteCharacter(s, 325).kind, 'ignored');
  assert.equal(s.correct, 2);
  assert.equal(s.rounds.length, 1);
});

for (const mode of ['sequence', 'text']) {
  test(mode + ' keeps an outstanding typo through pause, save, and resume', () => {
    const s = newSession({ mode, passageId: 'custom', customText: 'fj' });
    const p = newProfile();
    start(s, p, 0);
    const [first, second] = s.target;
    typeCharacter(s, p, first, 100);
    typeCharacter(s, p, 'x', 200);
    assert.equal(s.wrongKey, 'x');
    assert.equal(typeCharacter(s, p, second, 210).kind, 'ignored');
    assert.equal(typeCharacter(s, p, 'y', 220).kind, 'ignored');
    assert.equal(s.wrongKey, 'x');
    pause(s, 250);
    const restored = restoreSession(snapshot(s, 300));
    assert.equal(restored.wrongKey, 'x');
    start(restored, p, 350);
    assert.equal(typeCharacter(restored, p, second, 360).kind, 'ignored');
    assert.equal(deleteCharacter(restored, 400).kind, 'cleared');
    assert.equal(restored.typed, first);
    assert.equal(currentExpected(restored), second);
    assert.equal(restored.errors, 1);
    assert.equal(restored.trials.length, 1);
    assert.equal(restored.wrongKey, '');
    assert.notEqual(typeCharacter(restored, p, second, 500).kind, 'ignored');
  });
}

test('deleting within paused text changes the saved cursor but not elapsed time', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'f j' }), p = newProfile();
  start(s, p, 0);
  typeCharacter(s, p, 'f', 100);
  pause(s, 200);
  assert.equal(deleteCharacter(s, 90000).kind, 'moved-back');
  assert.equal(s.typed, '');
  assert.equal(s.activeMs, 200);
  const stored = restoreSession(snapshot(s, 90000));
  assert.equal(stored.phase, 'paused');
  assert.equal(stored.typed, '');
  assert.equal(stored.correct, 0);
  assert.equal(stored.target, 'f j');
  assert.equal(stored.activeMs, 200);
  start(stored, p, 90100);
  typeCharacter(stored, p, 'f', 90200);
  assert.equal(stored.trials[0].ms, 100);
});

test('completed exercises do not allow Delete to roll back their record', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'f' }), p = newProfile();
  start(s, p, 0);
  typeCharacter(s, p, 'f', 500);
  assert.equal(s.phase, 'complete');
  const record = JSON.stringify(p.textRecords);
  assert.equal(deleteCharacter(s, 600).kind, 'ignored');
  assert.equal(s.typed, 'f');
  assert.equal(JSON.stringify(p.textRecords), record);
});

test('older saves require deletion only when their error marker is still present', () => {
  const s = newSession({ mode: 'text', passageId: 'custom', customText: 'fj' }), p = newProfile();
  start(s, p, 0);
  typeCharacter(s, p, 'x', 10);
  const old = snapshot(s, 20);
  delete old.wrongKey;
  const blocked = restoreSession(old);
  start(blocked, p, 30);
  assert.equal(typeCharacter(blocked, p, 'f', 40).kind, 'ignored');
  assert.equal(deleteCharacter(blocked, 50).kind, 'cleared');
  assert.equal(typeCharacter(blocked, p, 'f', 60).kind, 'correct');
  const cleared = restoreSession({ ...old, feedback: '' });
  start(cleared, p, 30);
  assert.equal(typeCharacter(cleared, p, 'f', 40).kind, 'correct');
  assert.equal(cleared.trials[0].errors, 1);
});
