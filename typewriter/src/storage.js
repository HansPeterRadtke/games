import { MAX_TEXT_CHARACTERS, PASSAGE_MEMORY } from './training_text.js';
import { MAX_WORD_REPEATS, observeCompletedWord } from './word_practice.js';
import { ROUND_WINDOWS, MAX_RECENT_ROUNDS } from './rounds.js';
import { GOALS, isLevelPassage, textRecordKey, keyRoundKey, sequenceRecordKey, KEY_ORDER, PASSAGES, WINDOW_SIZES, MAX_SEQUENCE_LENGTH, newProfile, newSession, restoreSession, snapshot } from './core.js';

export const STORAGE_KEY = 'typewriter.practice.v1';
export const DATA_VERSION = 1;
export const MAX_BACKUP_LENGTH = 8000000; // Includes per-word typing signals and all progress that fits in browser local storage.
const metrics = ['fastestMs', 'slowestMs', 'avgMs', 'medianMs', 'accuracy'];
const finite = (v, max = 1e9) => Number.isFinite(v) && v >= 0 && v <= max;
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v);

const maxPace = 120000; // 1,000 correct keys in the shortest measurable session (100 ms).

function readRecent(record, maxScore) {
  if (!Array.isArray(record.recentRounds)) return {};
  const recentRounds = record.recentRounds.slice(-MAX_RECENT_ROUNDS).filter(r =>
    plain(r) && (r.score === null || finite(r.score, maxScore)) && (r.accuracy === null || finite(r.accuracy, 100)))
    .map(({score, accuracy}) => ({score, accuracy}));
  return { recentRounds, count: Number.isSafeInteger(record.count) && record.count >= recentRounds.length
    ? record.count : recentRounds.length };
}

function paceRecord(record) {
  return {
    bestWpm: finite(record.bestWpm, maxPace) ? record.bestWpm : null,
    bestAccuracy: finite(record.bestAccuracy, 100) ? record.bestAccuracy : null,
    ...readRecent(record, maxPace),
  };
}

export function sanitizeProfile(raw) {
  const p = newProfile();
  if (!plain(raw)) return p;
  p.celebrations = raw.celebrations !== false;
  if (ROUND_WINDOWS.includes(raw.roundWindow)) p.roundWindow = raw.roundWindow;
  if (plain(raw.recentPassages)) {
    for (const [key, history] of Object.entries(raw.recentPassages)) {
      if (!/^level-(mixed|de|en):(?:[1-9]|1[0-9]|2[0-8])$/.test(key) || !Array.isArray(history)) continue;
      p.recentPassages[key] = history.slice(-PASSAGE_MEMORY).filter(text =>
        typeof text === 'string' && text.length <= MAX_TEXT_CHARACTERS && /^[a-zäöü]+(?: [a-zäöü]+)*$/.test(text));
    }
  }
  if (plain(raw.typingSignals)) {
    for (const [token, signal] of Object.entries(raw.typingSignals)) {
      if (!/^[a-zäöü]{1,64}$/.test(token) || !plain(signal) || !Number.isSafeInteger(signal.attempts)
          || signal.attempts < 1 || !finite(signal.errorRate, 1) || !(signal.ms === null || finite(signal.ms, 3600000))) continue;
      p.typingSignals[token] = { attempts:signal.attempts, errorRate:signal.errorRate, ms:signal.ms };
    }
  }
  if (plain(raw.wordStats)) {
    for (const [word, stat] of Object.entries(raw.wordStats)) {
      if (!/^[a-zäöü]{2,64}$/.test(word) || !plain(stat) || !Number.isSafeInteger(stat.count)
          || stat.count < 1 || !Number.isSafeInteger(stat.errors) || stat.errors < 0
          || !finite(stat.errorRate, 1) || !finite(stat.msPerChar, 3600000)) continue;
      p.wordStats[word] = { count: stat.count, errors: stat.errors, errorRate: stat.errorRate, msPerChar: stat.msPerChar };
    }
  }
  if (plain(raw.wordRecords)) {
    for (const [key, record] of Object.entries(raw.wordRecords).slice(-300)) {
      const m = /^([a-zäöü]{2,64})\|([1-9][0-9]?)$/.exec(key);
      if (m && Number(m[2]) <= MAX_WORD_REPEATS && plain(record)) p.wordRecords[key] = paceRecord(record);
    }
  }
  if (plain(raw.keyRoundRecords)) {
    for (const [key, record] of Object.entries(raw.keyRoundRecords)) {
      const [level, goal] = key.split(':').map(Number);
      if (key === level + ':' + goal && Number.isInteger(level) && level >= 1 && level < KEY_ORDER.length
          && GOALS.includes(goal) && plain(record)) p.keyRoundRecords[key] = paceRecord(record);
    }
  }
  if (plain(raw.keyStats)) {
    for (const k of KEY_ORDER) {
      const s = raw.keyStats[k];
      if (!plain(s) || !Number.isInteger(s.count) || s.count < 0 || s.count > 10000000) continue;
      p.keyStats[k] = {
        count: s.count,
        errors: Number.isInteger(s.errors) && s.errors >= 0 ? Math.min(s.errors, 10000000) : 0,
        emaMs: finite(s.emaMs, 3600000) ? s.emaMs : 0,
        bestMs: finite(s.bestMs, 3600000) ? s.bestMs : null,
      };
    }
  }
  if (plain(raw.records)) {
    for (let level = 1; level < KEY_ORDER.length; level++) {
      const bySize = raw.records[String(level)];
      if (!plain(bySize)) continue;
      p.records[String(level)] = {};
      for (const n of WINDOW_SIZES) {
        const record = bySize[String(n)];
        if (!plain(record)) continue;
        const result = {};
        for (const metric of metrics) {
          const cell = record[metric];
          if (plain(cell) && finite(cell.value, metric === 'accuracy' ? 100 : 3600000)) {
            result[metric] = { value: cell.value, at: typeof cell.at === 'string' ? cell.at.slice(0, 40) : '' };
          }
        }
        p.records[String(level)][String(n)] = result;
      }
    }
  }
  if (plain(raw.textRecords)) {
    for (const [key, v] of Object.entries(raw.textRecords).slice(0, 100)) {
      if (!(PASSAGES.some(p => p.id === key) || /^custom:[a-z0-9]+:[0-9]{1,3}$/.test(key)
        || /^level-(mixed|de|en):(?:[1-9]|1[0-9]|2[0-8])$/.test(key))) continue;
      if (!plain(v)) continue;
      p.textRecords[key] = paceRecord(v);
    }
  }
  if (plain(raw.sequenceRecords)) {
    for (const [key, record] of Object.entries(raw.sequenceRecords).slice(-300)) {
      const separator = key.indexOf('|');
      if (separator < 1 || separator > 2) continue;
      const level = Number(key.slice(0, separator));
      const sequence = key.slice(separator + 1);
      const unlocked = KEY_ORDER.slice(0, level + 1);
      if (!Number.isInteger(level) || level < 1 || level >= KEY_ORDER.length
          || sequence.length < unlocked.length || sequence.length > MAX_SEQUENCE_LENGTH
          || ![...sequence].every(char => unlocked.includes(char))
          || !unlocked.every(char => sequence.includes(char))) continue;
      if (!plain(record) || !finite(record.bestMs, 86400000)
          || !Number.isInteger(record.count) || record.count < 1 || record.count > 1000000) continue;
      p.sequenceRecords[key] = {
        ...readRecent(record, 86400000),
        bestMs: record.bestMs,
        bestAccuracy: finite(record.bestAccuracy, 100) ? record.bestAccuracy : 0,
        lastMs: finite(record.lastMs, 86400000) ? record.lastMs : record.bestMs,
        count: record.count,
        bestAt: typeof record.bestAt === 'string' ? record.bestAt.slice(0, 40) : '',
      };
    }
  }
  if (Array.isArray(raw.history)) {
    p.history = raw.history.slice(0, 50).filter(h => plain(h) && ['keys', 'text', 'sequence', 'word'].includes(h.mode)
      && Number.isInteger(h.correct) && h.correct >= 0 && h.correct <= 4500).map(h => ({
      mode: h.mode,
      ...(h.mode === 'word' && { practiceWord: typeof h.practiceWord === 'string' ? h.practiceWord.slice(0,64) : '',
        wordRepeats: Number.isInteger(h.wordRepeats) ? Math.min(MAX_WORD_REPEATS, Math.max(1,h.wordRepeats)) : 10 }),
      level: Number.isInteger(h.level) ? Math.max(1, Math.min(KEY_ORDER.length - 1, h.level)) : 1,
      passageId: typeof h.passageId === 'string' ? h.passageId.slice(0, 60) : '',
      goal: Number.isInteger(h.goal) ? Math.max(1, Math.min(4500, h.goal)) : 50,
      sequence: typeof h.sequence === 'string' ? h.sequence.slice(0, MAX_SEQUENCE_LENGTH) : '',
      sequenceLength: Number.isInteger(h.sequenceLength) ? Math.max(2, Math.min(MAX_SEQUENCE_LENGTH, h.sequenceLength)) : null,
      sequenceRounds: Number.isInteger(h.sequenceRounds) ? Math.max(1, Math.min(30, h.sequenceRounds)) : null,
      roundsCompleted: Number.isInteger(h.roundsCompleted) ? Math.max(0, Math.min(30, h.roundsCompleted)) : null,
      bestRoundMs: finite(h.bestRoundMs, 86400000) ? h.bestRoundMs : null,
      correct: h.correct,
      errors: Number.isInteger(h.errors) ? Math.max(0, Math.min(100000, h.errors)) : 0,
      accuracy: finite(h.accuracy, 100) ? h.accuracy : null,
      durationMs: finite(h.durationMs, 86400000) ? h.durationMs : 0,
      avgMs: finite(h.avgMs, 3600000) ? h.avgMs : null,
      bestMs: finite(h.bestMs, 3600000) ? h.bestMs : null,
      wpm: finite(h.wpm, maxPace) ? h.wpm : null,
      status: h.status === 'completed' ? 'completed' : 'interrupted',
      at: typeof h.at === 'string' ? h.at.slice(0, 40) : '',
    }));
  }
  return p;
}

// Older backups retained completed sessions, the active sequence log, and separate lifetime records.
function recoverRoundHistory(profile, session) {
  const groups = new Map();
  for (const h of [...profile.history].reverse()) {
    if (h.status !== 'completed' || ['sequence','word'].includes(h.mode) || h.accuracy === null) continue;
    let entry;
    if (h.mode === 'keys') {
      if (!GOALS.includes(h.goal) || h.correct !== h.goal) continue;
      entry = profile.keyRoundRecords[keyRoundKey(h)] ??= {};
    } else {
      // Older custom history has no passage fingerprint.
      const key = isLevelPassage(h.passageId) ? h.passageId + ':' + h.level : h.passageId;
      if (!Object.hasOwn(profile.textRecords, key)) continue;
      entry = profile.textRecords[key];
    }
    if (!entry || entry.recentRounds) continue;
    if (!groups.has(entry)) groups.set(entry, []);
    groups.get(entry).push({ score: h.wpm, accuracy: Math.round(h.accuracy * 10) / 10 });
  }
  for (const [entry, rounds] of groups) {
    const speeds = rounds.map(r => r.score).filter(Number.isFinite);
    if (speeds.length) entry.bestWpm = Math.max(entry.bestWpm ?? 0, ...speeds);
    entry.bestAccuracy = Math.max(entry.bestAccuracy ?? 0, ...rounds.map(r => r.accuracy));
    entry.count = rounds.length;
    entry.recentRounds = rounds.slice(-MAX_RECENT_ROUNDS);
  }
  for (const [key, record] of Object.entries(profile.sequenceRecords)) {
    if (record.recentRounds) continue;
    const log = session.mode === 'sequence' && key === sequenceRecordKey(session) ? session.rounds : [];
    record.recentRounds = log.length && log.at(-1).ms === record.lastMs
      ? log.slice(-MAX_RECENT_ROUNDS).map(r => ({ score: r.ms, accuracy: r.accuracy }))
      : [{ score: record.lastMs, accuracy: null }];
  }
}

export function parseExport(text) {
  if (typeof text !== 'string' || text.length > MAX_BACKUP_LENGTH) throw new Error('The backup is too large or invalid.');
  let data;
  try { data = JSON.parse(text); } catch { throw new Error('The file is not valid JSON.'); }
  if (!plain(data) || data.version !== DATA_VERSION || !plain(data.profile) || !plain(data.session)) {
    throw new Error('This is not a supported Typewriter backup.');
  }
  const profile = sanitizeProfile(data.profile);
  const session = restoreSession(data.session);
  // Seed the rotation from the visible passage when opening a pre-rotation save.
  if (session.mode === 'text' && isLevelPassage(session.passageId) && session.target
      && session.textKind !== 'key-groups' && !profile.recentPassages[textRecordKey(session)]) {
    profile.recentPassages[textRecordKey(session)] = [session.target];
  }
  if (!Object.hasOwn(data.profile, 'wordStats') && session.mode === 'text') {
    for (let end = 1; end <= session.typed.length; end++) {
      observeCompletedWord(profile.wordStats, session.target, end, session.trials);
    }
  }
  recoverRoundHistory(profile, session);
  return { profile, session };
}

export function serializeData(session, profile, now) {
  return JSON.stringify({
    version: DATA_VERSION,
    exportedAt: new Date().toISOString(),
    profile: sanitizeProfile(profile),
    session: snapshot(session, now),
  });
}

export function loadData(storage) {
  try {
    const text = (storage ?? globalThis.localStorage).getItem(STORAGE_KEY);
    if (!text) return { profile: newProfile(), session: newSession(), error: null };
    return { ...parseExport(text), error: null };
  } catch {
    return { profile: newProfile(), session: newSession(), error: 'Saved progress could not be loaded. Check browser storage permissions or import a backup.' };
  }
}

export function saveData(session, profile, now, storage) {
  try {
    (storage ?? globalThis.localStorage).setItem(STORAGE_KEY, serializeData(session, profile, now));
    return null;
  } catch {
    return 'Progress cannot be stored on this device. Export your data to keep it.';
  }
}
