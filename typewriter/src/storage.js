import { KEY_ORDER, PASSAGES, WINDOW_SIZES, MAX_SEQUENCE_LENGTH, newProfile, newSession, restoreSession, snapshot } from './core.js';

export const STORAGE_KEY = 'typewriter.practice.v1';
export const DATA_VERSION = 1;
const metrics = ['fastestMs', 'slowestMs', 'avgMs', 'medianMs', 'accuracy'];
const finite = (v, max = 1e9) => Number.isFinite(v) && v >= 0 && v <= max;
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v);

export function sanitizeProfile(raw) {
  const p = newProfile();
  if (!plain(raw)) return p;
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
      p.textRecords[key] = {
        bestWpm: finite(v.bestWpm, 2000) ? v.bestWpm : null,
        bestAccuracy: finite(v.bestAccuracy, 100) ? v.bestAccuracy : null,
      };
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
        bestMs: record.bestMs,
        bestAccuracy: finite(record.bestAccuracy, 100) ? record.bestAccuracy : 0,
        lastMs: finite(record.lastMs, 86400000) ? record.lastMs : record.bestMs,
        count: record.count,
        bestAt: typeof record.bestAt === 'string' ? record.bestAt.slice(0, 40) : '',
      };
    }
  }
  if (Array.isArray(raw.history)) {
    p.history = raw.history.slice(0, 50).filter(h => plain(h) && ['keys', 'text', 'sequence'].includes(h.mode)
      && Number.isInteger(h.correct) && h.correct >= 0 && h.correct <= 4500).map(h => ({
      mode: h.mode,
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
      wpm: finite(h.wpm, 2000) ? h.wpm : null,
      status: h.status === 'completed' ? 'completed' : 'interrupted',
      at: typeof h.at === 'string' ? h.at.slice(0, 40) : '',
    }));
  }
  return p;
}

export function parseExport(text) {
  if (typeof text !== 'string' || text.length > 1000000) throw new Error('The backup is too large or invalid.');
  let data;
  try { data = JSON.parse(text); } catch { throw new Error('The file is not valid JSON.'); }
  if (!plain(data) || data.version !== DATA_VERSION || !plain(data.profile) || !plain(data.session)) {
    throw new Error('This is not a supported Typewriter backup.');
  }
  return { profile: sanitizeProfile(data.profile), session: restoreSession(data.session) };
}

export function serializeData(session, profile, now) {
  return JSON.stringify({
    version: DATA_VERSION,
    exportedAt: new Date().toISOString(),
    profile: sanitizeProfile(profile),
    session: snapshot(session, now),
  });
}

export function loadData(storage = globalThis.localStorage) {
  try {
    const text = storage.getItem(STORAGE_KEY);
    if (!text) return { profile: newProfile(), session: newSession(), error: null };
    return { ...parseExport(text), error: null };
  } catch {
    return { profile: newProfile(), session: newSession(), error: 'Saved progress could not be loaded. Check browser storage permissions or import a backup.' };
  }
}

export function saveData(session, profile, now, storage = globalThis.localStorage) {
  try {
    storage.setItem(STORAGE_KEY, serializeData(session, profile, now));
    return null;
  } catch {
    return 'Progress cannot be stored on this device. Export your data to keep it.';
  }
}
