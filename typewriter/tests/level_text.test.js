import test from 'node:test';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { KEY_ORDER, PASSAGES, currentExpected, newProfile, newSession, pause, restoreSession,
  snapshot, start, summaryOf, textRecordKey, typeCharacter, unlockedKeys } from '../src/core.js';
import { TRAINING_KEY_ORDER, LEVEL_PASSAGES, allowedText,
  eligibleWords, generateLevelExercise, invalidTextKeys, normalizedPreset,
  keyCoverage, MIN_KEY_OCCURRENCES } from '../src/training_text.js';
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
      for (let seed = 1; seed <= 6; seed++) {
        const result = generateLevelExercise({ level, passageId }, rng(seed * 571));
        assert.ok(allowedText(result.text, keys), `bad letters in level ${level}: ${result.text}`);
        assert.equal(/[A-Z.,!?0-9]/.test(result.text), false);
        assert.ok(result.text.length >= 50 && result.text.length <= 800, `${level} ${result.text.length}`);
        const coverage = keyCoverage(result.text, keys);
        assert.equal(coverage.covered, keys.length, `omitted unlocked letters at level ${level}`);
        assert.ok(coverage.weakest >= MIN_KEY_OCCURRENCES, `undertrained letter at ${level}: ${JSON.stringify(coverage.counts)}`);
        assert.ok(coverage.counts[keys.at(-1)] >= 5, `newest key missing practice at ${level}`);
        const letters = result.text.replaceAll(' ', '');
        for (let q = 0; q < 4; q++) {
          const quarter = letters.slice(Math.floor(q * letters.length / 4), Math.floor((q + 1) * letters.length / 4));
          for (const key of keys) assert.ok(quarter.split(key).length - 1 >= 2, `${passageId} level ${level}, quarter ${q}, key ${key}`);
        }
        assert.deepEqual(result.coverage.counts, coverage.counts);
        assert.ok(['words', 'words+drills', 'key-groups'].includes(result.kind), result.kind);
        if (passageId === 'level-de' && result.kind !== 'key-groups') assert.equal(result.language, 'de');
        if (passageId === 'level-en' && result.kind !== 'key-groups') assert.equal(result.language, 'en');
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

test('real words start at level six and key drills only use unsupported letters', () => {
  for (const language of ['de', 'en']) {
    const all = new Set(eligibleWords(KEY_ORDER, language));
    assert.ok(all.size > 8_000);
    for (const token of 'hajj haj dak öd ad kläff jäh öls höhl gasöl sh ka fa'.split(' ')) {
      assert.ok(!all.has(token), language + ' admitted ' + token);
    }
    const approved = new Set(readFileSync(new URL('../vocabulary/practice-' + language + '.txt', import.meta.url), 'utf8').trim().split(/\s+/));
    for (const w of eligibleWords(unlockedKeys({ level: 12 }), language)) assert.ok(approved.has(w), w);
    for (const w of all) if (w.length < 5) assert.ok(approved.has(w), w);
    const low = eligibleWords(unlockedKeys({ level: 6 }), language);
    assert.ok(low.length >= 15 && low.every(w => [...w].every(k => 'fjdksla'.includes(k))));
    for (let level = 6; level <= 28; level++) {
      const s = generateLevelExercise({ level, passageId: 'level-' + language }, rng(41 * level));
      const keys = unlockedKeys({ level });
      const eligible = eligibleWords(keys, language);
      const unsupported = keys.filter(k => !eligible.some(w => w.includes(k)));
      assert.deepEqual(s.focusKeys, unsupported);
      for (const word of s.text.split(' ')) assert.ok(all.has(word) || (word.length === 1 && unsupported.includes(word)), word);
      assert.equal(s.kind, unsupported.length ? 'words+drills' : 'words');
    }
  }
});

test('fresh passages draw varied vocabulary and balance the full alphabet', () => {
  for (const passageId of LEVEL_PASSAGES.map(p => p.id)) {
    const unique = new Set();
    let relativeDeviation = 0;
    for (let seed = 0; seed < 16; seed++) {
      const s = generateLevelExercise({ level: 28, passageId }, rng(13 + seed * 173));
      if (passageId === 'level-mixed') assert.equal(s.language, 'mixed');
      for (const w of s.text.split(' ')) unique.add(w);
      const counts = Object.values(s.coverage.counts);
      const mean = counts.reduce((a, b) => a + b) / counts.length;
      relativeDeviation += Math.sqrt(counts.reduce((sum, c) => sum + (c - mean) ** 2, 0) / counts.length) / mean;
    }
    assert.ok(unique.size > 400, passageId + ' distinct words: ' + unique.size);
    assert.ok(relativeDeviation / 16 < .55, passageId + ' relative deviation: ' + relativeDeviation / 16);
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

test('a stale idle preview refreshes on upgrade and a started round keeps its passage', () => {
  const old = newSession({ mode: 'text', level: 10, passageId: 'level-mixed' });
  delete old.vocabularyVersion;
  old.target = 'flash ad gag hajj öl ask kläff dads öd jäh dak';
  const fresh = restoreSession(old);
  assert.notEqual(fresh.target, old.target);
  assert.equal(restoreSession(snapshot(fresh, 0)).target, fresh.target);
  const started = restoreSession({ ...old, phase: 'paused', typed: 'f', trials: [{ key: 'f', ms: 120, errors: 0 }] });
  assert.equal(started.target, old.target);
  assert.equal(started.typed, 'f');
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

test('newly unlocked rare keys are meaningfully practiced, not silently omitted', () => {
  const keyOrder = [...KEY_ORDER];
  for (const [level, newest] of [[7, 'ö'], [10, 'ä'], [17, 'q'],
    [21, 'ü'], [22, 'v'], [25, 'x'], [26, 'y'], [27, 'b'], [28, 'n']]) {
    assert.equal(keyOrder[level], newest);
    for (const id of ['level-de', 'level-mixed', 'level-en']) {
      for (const rngInput of [() => 0, () => .42, () => .9999999, rng(73 + level)]) {
        const exercise = generateLevelExercise({ level, passageId: id }, rngInput);
        const stats = keyCoverage(exercise.text, keyOrder.slice(0, level + 1));
        assert.ok(stats.counts[newest] >= 5,
          `new key ${newest} only ${stats.counts[newest]} occurrences at ${id}, level ${level}`);
        assert.ok(stats.weakest >= MIN_KEY_OCCURRENCES);
        assert.equal(exercise.coverage.covered, level + 1);
      }
    }
  }
});

test('German and mixed exercises use natural vocabulary whenever the alphabet permits it', () => {
  for (const level of [7, 11, 17, 21, 25, 26, 28]) {
    for (const id of ['level-de', 'level-mixed']) {
      const exercise = generateLevelExercise({ level, passageId: id }, rng(level * 7));
      assert.ok(!exercise.kind.includes('drills'), `${id} level ${level} should have real-word coverage`);
      assert.ok(exercise.text.length < 800, 'exercises must survive JSON restore');
    }
  }
  const en = generateLevelExercise({ level: 10, passageId: 'level-en' }, () => .23);
  assert.equal(en.kind, 'words+drills');
  assert.ok(en.text.includes('ä') && en.text.includes('ö'));
  assert.equal(en.language, 'en');
});

test('key coverage reports the truth for legacy generated text and custom text', () => {
  const keys = [...'fjdkslaö'];
  assert.deepEqual(keyCoverage('f f j j', keys).missing, ['d', 'k', 's', 'l', 'a', 'ö']);
  assert.deepEqual(keyCoverage('f j d k s l a ö', keys).missing, []);
  assert.equal(keyCoverage('f j', keys).weakest, 0);
  assert.equal(keyCoverage('', keys).covered, 0);
});
