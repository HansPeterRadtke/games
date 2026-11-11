import test from 'node:test';
import assert from 'node:assert/strict';
import { newSession, newProfile, start, typeCharacter } from '../src/core.js';
import { DATA_VERSION, MAX_BACKUP_LENGTH, STORAGE_KEY, loadData, parseExport, sanitizeProfile, saveData, serializeData } from '../src/storage.js';

function memoryStorage() {
  const data = new Map();
  return {
    getItem(k) { return data.get(k) || null; },
    setItem(k, v) { data.set(k, v); },
  };
}

test('progress can be saved and restored with a paused active clock', () => {
  const storage = memoryStorage();
  const session = newSession(), profile = newProfile();
  start(session, profile, 0, () => 0);
  typeCharacter(session, profile, 'f', 200, () => 0);
  assert.equal(saveData(session, profile, 350, storage), null);
  const saved = loadData(storage);
  assert.equal(saved.error, null);
  assert.equal(saved.session.phase, 'paused');
  assert.equal(saved.session.correct, 1);
  assert.equal(saved.session.activeMs, 350);
  assert.equal(saved.profile.keyStats.f.count, 1);
  assert.ok(storage.getItem(STORAGE_KEY).includes('"version":1'));
});

test('export/import round trip retains historical records and key observations', () => {
  const session = newSession({ goal: 10 }), profile = newProfile();
  start(session, profile, 0, () => 0);
  for (let i = 0, now = 0; i < 10; i++) {
    now += 300;
    typeCharacter(session, profile, session.target, now, () => 0);
  }
  const parsed = parseExport(serializeData(session, profile, 3000));
  assert.equal(parsed.session.phase, 'complete');
  assert.equal(parsed.session.correct, 10);
  assert.equal(parsed.profile.records['1']['10'].avgMs.value, 300);
  assert.equal(parsed.profile.history.length, 1);
});

test('malformed file and incompatible backup format are rejected', () => {
  assert.throws(() => parseExport('oops'), /JSON/);
  assert.throws(() => parseExport(JSON.stringify({ version: DATA_VERSION + 1, profile: {}, session: {} })), /supported/);
  assert.throws(() => parseExport('a'.repeat(MAX_BACKUP_LENGTH + 1)), /too large/);
});

test('storage unavailability is visible but does not crash', () => {
  const bad = {
    getItem() { throw new Error('Denied'); },
    setItem() { throw new Error('Quota'); },
  };
  const loaded = loadData(bad);
  assert.match(loaded.error, /could not be loaded/);
  assert.match(saveData(newSession(), newProfile(), 0, bad), /cannot be stored/);
});

test('import sanitizes arbitrary record keys and incorrect numbers', () => {
  const raw = {
    keyStats: {
      f: { count: 2, errors: 1, emaMs: 300, bestMs: 200 },
      evil: { count: 100, errors: 0, emaMs: 200, bestMs: 200 },
      j: { count: -1, errors: 0, emaMs: 0, bestMs: 0 },
    },
    records: {
      '1': { '10': { accuracy: { value: 200 }, avgMs: { value: 250, at: 'today' } } },
      evil: { '10': { avgMs: { value: 0 } } },
    },
    textRecords: { evil: { bestWpm: 9999 }, 'en-fox': { bestWpm: 90, bestAccuracy: 99 } },
    history: [{ mode: 'keys', correct: 2, errors: 1, accuracy: 66.7, status: 'completed' }],
  };
  const p = sanitizeProfile(raw);
  assert.deepEqual(Object.keys(p.keyStats), ['f']);
  assert.equal(p.records['1']['10'].accuracy, undefined);
  assert.equal(p.records['1']['10'].avgMs.value, 250);
  assert.deepEqual(Object.keys(p.textRecords), ['en-fox']);
  assert.equal(p.history.length, 1);
  assert.equal(p.history[0].accuracy, 66.7);
});

test('old version-one backups load with empty sequence records without losing high scores', () => {
  const original = JSON.stringify({ version: DATA_VERSION, profile: {
    keyStats: { f: { count: 8, errors: 1, emaMs: 220, bestMs: 180 } },
    records: { 1: { 10: { avgMs: { value: 250, at: '2026-11-08' } } } },
    textRecords: {}, history: [],
  }, session: { mode: 'keys', phase: 'idle', level: 1, goal: 50 } });
  const data = parseExport(original);
  assert.deepEqual(data.profile.sequenceRecords, {});
  assert.equal(data.profile.records['1']['10'].avgMs.value, 250);
  assert.equal(data.profile.keyStats.f.count, 8);
  assert.equal(data.session.mode, 'keys');
});

test('sequence records and round log survive version-one export and import', async () => {
  const { reshuffleSequence, sequenceRecordKey, currentExpected } = await import('../src/core.js');
  const state = newSession({ mode: 'sequence', sequenceRounds: 3, level: 4 });
  const p = newProfile();
  reshuffleSequence(state, () => 0);
  start(state, p, 0);
  let t = 0;
  for (let round = 0; round < 2; round++) {
    if (round) start(state, p, t);
    for (let i = 0; i < state.sequenceLength; i++) {
      t += 150;
      typeCharacter(state, p, currentExpected(state), t);
    }
  }
  const json = serializeData(state, p, t + 30);
  const restored = parseExport(json);
  assert.equal(restored.session.phase, 'between-rounds');
  assert.equal(restored.session.rounds.length, 2);
  assert.equal(restored.session.sequence, state.sequence);
  assert.equal(restored.profile.sequenceRecords[sequenceRecordKey(state)].count, 2);
  assert.equal(restored.profile.sequenceRecords[sequenceRecordKey(state)].bestMs, 750);
  assert.equal(restored.session.correct, 10);
  assert.equal(restored.session.roundStartMs, 1500);
});

test('malformed imported sequence records are discarded safely', () => {
  const profile = sanitizeProfile({ sequenceRecords: {
    '1|fj': { bestMs: 330, bestAccuracy: 100, lastMs: 350, count: 2, bestAt: 'today' },
    '__proto__': { bestMs: 1, count: 1 },
    '1|xx': { bestMs: 1, count: 1 },
    '1|ff': { bestMs: 1, count: 1 },
    '1|fj': { bestMs: 330, bestAccuracy: 100, lastMs: 350, count: 2, bestAt: 'today' },
    '18|fjd': { bestMs: 1, count: 1 },
    '1|jf': { bestMs: -1, count: 1 },
  } });
  assert.deepEqual(Object.keys(profile.sequenceRecords), ['1|fj']);
  assert.equal(profile.sequenceRecords['1|fj'].bestMs, 330);
});
