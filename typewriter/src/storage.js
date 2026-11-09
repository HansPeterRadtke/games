import { KEY_ORDER, PASSAGES, WINDOW_SIZES, newProfile, newSession, restoreSession, snapshot } from './core.js';

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
      if (!(PASSAGES.some(p => p.id === key) || /^custom:[a-z0-9]+:[0-9]{1,3}$/.test(key))) continue;
      if (!plain(v)) continue;
      p.textRecords[key] = {
        bestWpm: finite(v.bestWpm, 2000) ? v.bestWpm : null,
        bestAccuracy: finite(v.bestAccuracy, 100) ? v.bestAccuracy : null,
      };
    }
  }
  if (Array.isArray(raw.history)) {
    p.history = raw.history.slice(0, 50).filter(h => plain(h) && ['keys', 'text'].includes(h.mode)
      && Number.isInteger(h.correct) && h.correct >= 0 && h.correct <= 1000).map(h => ({
      mode: h.mode,
      level: Number.isInteger(h.level) ? Math.max(1, Math.min(KEY_ORDER.length - 1, h.level)) : 1,
      passageId: typeof h.passageId === 'string' ? h.passageId.slice(0, 60) : '',
      goal: Number.isInteger(h.goal) ? Math.max(1, Math.min(1000, h.goal)) : 50,
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
