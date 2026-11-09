import test from 'node:test';
import assert from 'node:assert/strict';
import { KEY_ORDER, PASSAGES, currentExpected, newProfile, newSession, pause, restoreSession,
  snapshot, start, summaryOf, textRecordKey, typeCharacter, unlockedKeys } from '../src/core.js';
import { TRAINING_KEY_ORDER, SENTENCES, WORDS, LEVEL_PASSAGES, allowedText, eligibleSentences,
  eligibleWords, generateLevelExercise, invalidTextKeys, normalizedPreset } from '../src/training_text.js';
import { parseExport, serializeData, sanitizeProfile } from '../src/storage.js';

const rng = seed => {
  let n = seed >>> 0;
  return () => ((n = (Math.imul(n, 1664525) + 1013904223) >>> 0) / 0x100000000);
};

test('the generator and game use the same unlocked-key order', () => {
  assert.equal(KEY_ORDER, TRAINING_KEY_ORDER);
  assert.equal(KEY_ORDER.length, 29);
  assert.equal(newSession().passageId, 'level-mixed');
  assert.deepEqual(LEVEL_PASSAGES.map(p => p.id), ['level-mixed', 'level-de', 'level-en']);
});

test('every generated character is legal for every level and language, with varied seeds', () => {
  for (let level = 1; level < KEY_ORDER.length; level++) {
    const keys = KEY_ORDER.slice(0, level + 1);
    for (const passageId of LEVEL_PASSAGES.map(p => p.id)) {
      for (let seed = 1; seed <= 12; seed++) {
        const result = generateLevelExercise({ level, passageId }, rng(seed * 571));
        assert.ok(allowedText(result.text, keys), `bad letters in level ${level}: ${result.text}`);
        assert.equal(/[A-Z.,!?0-9]/.test(result.text), false);
        assert.ok(result.text.length >= 50 && result.text.length < 170, `${level} ${result.text.length}`);
        assert.ok(['sentences', 'words', 'key-groups'].includes(result.kind));
        if (passageId === 'level-de' && result.kind === 'sentences') assert.equal(result.language, 'de');
        if (passageId === 'level-en' && result.kind === 'sentences') assert.equal(result.language, 'en');
      }
    }
  }
});

test('the first levels are labelled as letter groups, not fake sentences', () => {
  for (let level = 1; level <= 5; level++) {
    const result = generateLevelExercise({ level, passageId: 'level-mixed' }, rng(level));
    assert.equal(result.kind, 'key-groups');
    assert.ok(result.text.includes(' '));
  }
});

test('real English and German phrases start as soon as their letters permit', () => {
  const de = generateLevelExercise({ level: 6, passageId: 'level-de' }, rng(123));
  const en = generateLevelExercise({ level: 6, passageId: 'level-en' }, rng(456));
  assert.equal(de.kind, 'sentences');
  assert.equal(en.kind, 'sentences');
  assert.ok(de.text.includes('lass das'));
  assert.ok(/ask dad|dad asks|a sad dad|a sad lad/.test(en.text));
  assert.ok(eligibleSentences(unlockedKeys({ level: 13 }), 'de').some(s => s === 'er sah das haus'));
  assert.ok(eligibleSentences(unlockedKeys({ level: 19 }), 'en').some(s => s === 'the dog is fast'));
  assert.ok(eligibleSentences(unlockedKeys({ level: 24 }), 'de').some(s => s === 'ich esse eis'));
  assert.ok(eligibleSentences(unlockedKeys({ level: 28 }), 'en').length > 100);
});

test('curated sentences and words are within the complete keyboard alphabet', () => {
  const set = new Set(KEY_ORDER);
  for (const language of ['de', 'en']) {
    for (const text of SENTENCES[language]) {
      assert.ok(text.includes(' '), `not a phrase: ${text}`);
      assert.ok(allowedText(text, set), `invalid phrase: ${text}`);
    }
    for (const word of WORDS[language]) {
      assert.ok(allowedText(word, set), `invalid word: ${word}`);
    }
    assert.ok(eligibleWords(unlockedKeys({ level: 28 }), language).length > 100);
  }
});

test('generated text is created once and never regenerates while typing or reloading', () => {
  const s = newSession({ mode: 'text', level: 15, passageId: 'level-mixed' });
  const p = newProfile();
  const preview = s.target;
  assert.ok(preview.length > 50);
  assert.equal(start(s, p, 500), true);
  assert.equal(s.target, preview);
  const first = currentExpected(s);
  typeCharacter(s, p, first, 700);
  pause(s, 750);
  const reloaded = restoreSession(snapshot(s, 750));
  assert.equal(reloaded.target, preview);
  assert.equal(reloaded.typed, first);
  assert.equal(reloaded.phase, 'paused');
  assert.equal(start(reloaded, p, 90000), true);
  assert.equal(reloaded.target, preview);
});

test('the level determines whether a requested existing or custom passage is legal', () => {
  const a = newSession({ mode: 'text', passageId: 'custom', customText: 'f j' });
  assert.equal(start(a, newProfile(), 0), true);
  const illegal = newSession({ mode: 'text', passageId: 'custom', customText: 'a b' });
  assert.equal(start(illegal, newProfile(), 0), false);
  assert.deepEqual(invalidTextKeys(illegal.target, unlockedKeys(illegal)), ['a', 'b']);
  const preset = newSession({ mode: 'text', passageId: 'de-everyday' });
  assert.equal(start(preset, newProfile(), 0), false);
  const full = newSession({ mode: 'text', level: 28, passageId: 'de-everyday' });
  assert.equal(start(full, newProfile(), 0), true);
  assert.equal(/[.!?,]/.test(full.target), false);
  assert.ok(allowedText(full.target, unlockedKeys(full)));
  assert.equal(full.target, normalizedPreset(PASSAGES[0].text));
  const customUpper = newSession({ mode: 'text', level: 10, passageId: 'custom', customText: 'Ä a' });
  assert.equal(start(customUpper, newProfile(), 0), true);
});

test('a generated exercise earns a level-specific best record that survives import', () => {
  const s = newSession({ mode: 'text', level: 6, passageId: 'level-de' });
  const p = newProfile();
  const original = s.target;
  start(s, p, 0);
  let time = 0;
  for (const c of original) {
    time += 110;
    typeCharacter(s, p, c, time);
  }
  assert.equal(s.phase, 'complete');
  assert.equal(summaryOf(s, time).errors, 0);
  const id = textRecordKey(s);
  assert.equal(id, 'level-de:6');
  assert.ok(p.textRecords[id].bestWpm > 0);
  const loaded = parseExport(serializeData(s, p, time));
  assert.equal(loaded.profile.textRecords[id].bestWpm, p.textRecords[id].bestWpm);
  assert.equal(loaded.session.target, original);
  assert.equal(loaded.session.phase, 'complete');
});

test('older saved passage progress, spelling and high scores remain recoverable', () => {
  const s = newSession({ mode: 'text', level: 1, passageId: 'de-everyday' });
  const oldSource = PASSAGES[0].text;
  const legacy = {
    ...s, phase: 'paused', target: oldSource,
    trials: [{ key: 'F', ms: 150, errors: 0 }], typed: 'F', correct: 1,
    activeMs: 160, promptMs: 10,
  };
  const restored = restoreSession(legacy);
  assert.equal(restored.target, oldSource);
  assert.equal(restored.typed, 'F');
  assert.equal(restored.legacyResume, true);
  assert.equal(start(restored, newProfile(), 2000), true);
  const score = sanitizeProfile({ textRecords: { 'de-everyday': { bestWpm: 50, bestAccuracy: 90 } } });
  assert.equal(score.textRecords['de-everyday'].bestWpm, 50);
});
