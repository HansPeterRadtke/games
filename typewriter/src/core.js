import { CHARACTERS_PER_WORD, DEFAULT_ROUND_WINDOW, scoreRound } from './rounds.js';
// Pure practice engine. No DOM, storage, or system-clock dependencies.
import {
  LEVEL_PASSAGES, TRAINING_KEY_ORDER, generateLevelExercise, normalizedPreset, allowedText,
} from './training_text.js';

export { LEVEL_PASSAGES } from './training_text.js';
export const isLevelPassage = id => LEVEL_PASSAGES.some(item => item.id === id);
export const KEY_ORDER = TRAINING_KEY_ORDER;
export const WINDOW_SIZES = Object.freeze([10, 20, 50, 100, 200, 500, 1000]);
export const GOALS = Object.freeze([10, 20, 50, 100, 200, 500, 1000]);
export const SEQUENCE_ROUNDS = Object.freeze([3, 5, 10, 20, 30]);
export const MAX_SEQUENCE_LENGTH = 150;
export const PASSAGES = Object.freeze([
  { id: 'de-everyday', name: 'Everyday German', language: 'DE', text: 'Flinke Finger finden jede Taste. Wer ruhig und genau tippt, wird mit jeder Runde schneller.' },
  { id: 'de-bodensee', name: 'At the Bodensee', language: 'DE', text: 'Heute liegt ein leichter Wind über dem Bodensee. Die Wolken ziehen langsam weiter, und das Wasser glitzert.' },
  { id: 'en-rhythm', name: 'Steady rhythm', language: 'EN', text: 'A clear mind and a steady rhythm turn practice into progress. Accuracy comes first, then speed.' },
  { id: 'en-fox', name: 'The quick brown fox', language: 'EN', text: 'The quick brown fox jumps over the lazy dog. Five quiet minutes of practice can make a difference.' },
]);

const cap = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
const positive = n => Number.isFinite(n) && n >= 0;
const rounded = n => Math.round(n * 10) / 10;
const copy = obj => JSON.parse(JSON.stringify(obj));

export function normalizeConfig(source = {}) {
  const level = Number.isInteger(source.level) ? source.level : 1;
  const goal = GOALS.includes(source.goal) ? source.goal : 50;
  const sequenceLength = cap(Number.isInteger(source.sequenceLength) ? source.sequenceLength : level + 1,
    cap(level + 1, 2, KEY_ORDER.length), MAX_SEQUENCE_LENGTH);
  const sequenceRounds = SEQUENCE_ROUNDS.includes(source.sequenceRounds) ? source.sequenceRounds : 10;
  const customText = typeof source.customText === 'string'
    ? Array.from(source.customText.normalize('NFC').replace(/\r\n?/g, '\n')).slice(0, 800).join('')
    : '';
  return {
    mode: ['keys', 'text', 'sequence'].includes(source.mode) ? source.mode : 'keys',
    level: cap(level, 1, KEY_ORDER.length - 1),
    goal,
    sequenceLength,
    sequenceRounds,
    adaptive: source.adaptive !== false,
    passageId: PASSAGES.some(p => p.id === source.passageId) || isLevelPassage(source.passageId) || source.passageId === 'custom'
      ? source.passageId : 'level-mixed',
    customText,
  };
}

export function passageFor(config) {
  if (config.passageId === 'custom') return config.customText;
  if (isLevelPassage(config.passageId)) return config.target || generateLevelExercise(config).text;
  return normalizedPreset(PASSAGES.find(p => p.id === config.passageId)?.text || PASSAGES[0].text);
}

export function levelTextValid(config, text) {
  return Boolean(text && text.trim()) && allowedText(text, unlockedKeys(config));
}

export function textRecordKey(state) {
  if (state.passageId === 'custom') return 'custom:' + passageFingerprint(state.target);
  if (isLevelPassage(state.passageId)) return state.passageId + ':' + state.level;
  return state.passageId;
}

export function newProfile() {
  return { keyStats: {}, records: {}, textRecords: {}, sequenceRecords: {}, keyRoundRecords: {}, roundWindow: DEFAULT_ROUND_WINDOW, celebrations: true, history: [] };
}

export function keyRoundKey(state) {
  return state.level + ':' + state.goal;
}

export function roundRecordFor(state, profile) {
  if (state.mode === 'sequence') return profile.sequenceRecords[sequenceRecordKey(state)];
  if (state.mode === 'text') return profile.textRecords[textRecordKey(state)];
  return profile.keyRoundRecords[keyRoundKey(state)];
}

export function validSequence(state, sequence) {
  if (typeof sequence !== 'string' || Array.from(sequence).length !== state.sequenceLength) return false;
  const keys = unlockedKeys(state);
  return keys.every(key => sequence.includes(key)) && [...sequence].every(key => keys.includes(key));
}

// Fisher–Yates shuffle of complete unlocked-key sets, not independent key draws.
// An extended sequence repeats shuffled complete sets, then a partial final set.
export function generateSequence(state, rng = Math.random) {
  const keys = unlockedKeys(state);
  const result = [];
  while (result.length < state.sequenceLength) {
    const group = [...keys];
    for (let i = group.length - 1; i > 0; i--) {
      const sample = Number(rng());
      const j = Math.floor(cap(Number.isFinite(sample) ? sample : 0, 0, 0.999999999) * (i + 1));
      [group[i], group[j]] = [group[j], group[i]];
    }
    result.push(...group.slice(0, state.sequenceLength - result.length));
  }
  return result.join('');
}

export function reshuffleSequence(state, rng = Math.random) {
  if (state.mode !== 'sequence' || state.phase === 'running') return false;
  let sequence = generateSequence(state, rng);
  // Even with a deterministic RNG, an explicit Shuffle must produce a new order.
  if (sequence === state.sequence && sequence.length > 1) {
    const chars = [...sequence];
    const other = chars.findIndex((key, i) => i > 0 && key !== chars[0]);
    if (other !== -1) [chars[0], chars[other]] = [chars[other], chars[0]];
    sequence = chars.join('');
  }
  state.sequence = sequence;
  state.target = sequence;
  state.typed = '';
  return true;
}

export function sequenceRecordKey(state) {
  return String(state.level) + '|' + state.sequence;
}

export function newSession(config = {}) {
  const normalized = normalizeConfig(config);
  const preservedSequence = validSequence(normalized, config.sequence) ? config.sequence : '';
  const exercise = normalized.mode === 'text' && isLevelPassage(normalized.passageId)
    ? generateLevelExercise(normalized) : null;
  const textTarget = normalized.mode === 'text' ? (exercise?.text || passageFor(normalized)) : '';
  return {
    ...normalized,
    phase: 'idle',
    target: normalized.mode === 'sequence' ? preservedSequence : textTarget,
    textKind: exercise?.kind || (normalized.passageId === 'custom' ? 'custom' : 'preset'),
    textLanguage: exercise?.language || null,
    legacyResume: false,
    sequence: preservedSequence,
    rounds: [],
    roundErrors: 0,
    roundStartMs: 0,
    lastAchievement: null,
    typed: '',
    lastTwo: [],
    trials: [],
    correct: 0,
    errors: 0,
    pendingErrors: 0,
    activeMs: 0,
    segmentStart: null,
    promptMs: 0,
    promptStart: null,
    feedback: '',
    wrongKey: '',
    startedAt: null,
    finishedAt: null,
    latestRecords: [],
  };
}

export function unlockedKeys(state) {
  return KEY_ORDER.slice(0, state.level + 1);
}

export function weightedKeyChoice(state, profile, rng = Math.random) {
  const keys = unlockedKeys(state);
  const previous = state.lastTwo;
  const eligible = previous.length === 2 && previous[0] === previous[1] && keys.length > 1
    ? keys.filter(k => k !== previous[1]) : keys;
  const speeds = keys.map(k => profile.keyStats?.[k]?.emaMs)
    .filter(n => Number.isFinite(n) && n > 0);
  const baseline = speeds.length ? speeds.reduce((a, b) => a + b, 0) / speeds.length : 750;
  const weights = eligible.map(k => {
    if (!state.adaptive) return 1;
    const s = profile.keyStats?.[k];
    if (!s || !positive(s.emaMs) || s.count === 0) return 1.35;
    const speedWeight = cap(s.emaMs / baseline, 0.45, 2.5);
    const mistakesWeight = cap((s.errors || 0) / Math.max(1, s.count + (s.errors || 0)), 0, 1) * 1.75;
    return speedWeight + mistakesWeight;
  });
  const total = weights.reduce((a, b) => a + b, 0);
  let pick = cap(Number(rng()) || 0, 0, 0.999999999) * total;
  for (let i = 0; i < eligible.length; i++) {
    pick -= weights[i];
    if (pick < 0) return eligible[i];
  }
  return eligible[eligible.length - 1];
}

export function elapsedMs(state, now) {
  return state.activeMs + (state.phase === 'running' && state.segmentStart !== null
    ? Math.max(0, now - state.segmentStart) : 0);
}

export function currentPromptMs(state, now) {
  return state.promptMs + (state.phase === 'running' && state.promptStart !== null
    ? Math.max(0, now - state.promptStart) : 0);
}

export function progressOf(state) {
  if (state.mode === 'keys') return { done: state.correct, total: state.goal };
  if (state.mode === 'sequence') return { done: state.correct, total: state.sequenceLength * state.sequenceRounds };
  return { done: Array.from(state.typed).length, total: Array.from(state.target || passageFor(state)).length };
}

export function currentExpected(state) {
  if (state.mode === 'keys') return state.target;
  return Array.from(state.target)[Array.from(state.typed).length] || '';
}

export function start(state, profile, now, rng = Math.random) {
  if (state.phase === 'running' || state.phase === 'complete') return false;
  if (state.phase === 'idle') {
    if (state.mode === 'sequence' && !validSequence(state, state.sequence)) reshuffleSequence(state, rng);
    state.target = state.mode === 'keys' ? weightedKeyChoice(state, profile, rng)
      : state.mode === 'sequence' ? state.sequence : (state.target || passageFor(state));
    if (!state.target || !state.target.trim()
        || (state.mode === 'text' && !state.legacyResume && !levelTextValid(state, state.target))) return false;
    state.startedAt = new Date().toISOString();
  }
  state.phase = 'running';
  state.segmentStart = now;
  state.promptStart = now;
  return true;
}

export function pause(state, now) {
  if (state.phase !== 'running') return false;
  state.activeMs = elapsedMs(state, now);
  state.promptMs = currentPromptMs(state, now);
  state.segmentStart = null;
  state.promptStart = null;
  state.phase = 'paused';
  if (state.mode === 'keys' || state.feedback !== 'incorrect') state.feedback = '';
  return true;
}

export function accuracyOf(correct, errors) {
  const attempts = correct + errors;
  return attempts ? 100 * correct / attempts : null;
}

export function median(numbers) {
  if (!numbers.length) return null;
  const sorted = [...numbers].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function summaryOf(state, now) {
  const durationMs = elapsedMs(state, now);
  const times = state.trials.map(t => t.ms);
  return {
    mode: state.mode,
    level: state.level,
    passageId: state.passageId,
    goal: state.mode === 'keys' ? state.goal
      : state.mode === 'sequence' ? state.sequenceLength * state.sequenceRounds : Array.from(state.target).length,
    sequence: state.mode === 'sequence' ? state.sequence : '',
    sequenceLength: state.mode === 'sequence' ? state.sequenceLength : null,
    sequenceRounds: state.mode === 'sequence' ? state.sequenceRounds : null,
    roundsCompleted: state.mode === 'sequence' ? state.rounds.length : null,
    bestRoundMs: state.mode === 'sequence' && state.rounds.length
      ? Math.min(...state.rounds.map(round => round.ms)) : null,
    correct: state.correct,
    errors: state.errors,
    accuracy: accuracyOf(state.correct, state.errors),
    durationMs: rounded(durationMs),
    avgMs: times.length ? rounded(times.reduce((a, b) => a + b, 0) / times.length) : null,
    bestMs: times.length ? Math.min(...times) : null,
    wpm: durationMs >= 100 ? rounded((state.correct / CHARACTERS_PER_WORD) / (durationMs / 60000)) : null,
  };
}

export function updateRecords(state, profile) {
  const added = [];
  if (state.mode !== 'keys') return added;
  const level = String(state.level);
  if (!profile.records[level]) profile.records[level] = {};
  for (const windowSize of WINDOW_SIZES) {
    if (state.trials.length < windowSize) continue;
    const trials = state.trials.slice(-windowSize);
    const times = trials.map(t => t.ms);
    const mistakes = trials.reduce((a, t) => a + t.errors, 0);
    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const values = {
      fastestMs: Math.min(...times),
      slowestMs: Math.max(...times),
      avgMs: rounded(avg),
      medianMs: rounded(median(times)),
      accuracy: rounded(accuracyOf(windowSize, mistakes)),
    };
    const record = profile.records[level][String(windowSize)] ?? {};
    for (const [metric, value] of Object.entries(values)) {
      const best = record[metric];
      const maximize = metric === 'accuracy';
      if (!best || (maximize ? value > best.value : value < best.value)) {
        record[metric] = { value, at: new Date().toISOString() };
        added.push({ windowSize, metric, value, previous: best?.value ?? null });
      }
    }
    profile.records[level][String(windowSize)] = record;
  }
  state.latestRecords = added;
  return added;
}

function recordSequenceRound(state, profile, now) {
  const ms = rounded(Math.max(0, elapsedMs(state, now) - state.roundStartMs));
  const roundNumber = state.rounds.length + 1;
  const key = sequenceRecordKey(state);
  const existing = profile.sequenceRecords[key];
  const previousBestMs = existing?.bestMs ?? null;
  const newRecord = previousBestMs === null || ms < previousBestMs;
  const kind = newRecord ? (previousBestMs === null ? 'first' : 'improved') : null;
  const accuracy = rounded(accuracyOf(state.sequenceLength, state.roundErrors));
  const scored = scoreRound(existing, ms, accuracy, true, profile.roundWindow);
  const round = { number: roundNumber, ms, errors: state.roundErrors, accuracy, newRecord };
  state.rounds.push(round);
  // Keep the most recently practiced sequence records; cap browser storage growth.
  if (existing) delete profile.sequenceRecords[key];
  profile.sequenceRecords[key] = {
    ...scored.record,
    lastMs: ms,
    bestAt: newRecord ? new Date().toISOString() : existing.bestAt,
  };
  while (Object.keys(profile.sequenceRecords).length > 300) {
    delete profile.sequenceRecords[Object.keys(profile.sequenceRecords)[0]];
  }
  if (newRecord) {
    state.lastAchievement = {
      kind, ms, previousBestMs, roundNumber,
      improvementMs: previousBestMs === null ? null : rounded(previousBestMs - ms),
    };
  } else {
    state.lastAchievement = null;
  }
  state.roundErrors = 0;
  state.typed = '';
  state.roundStartMs = elapsedMs(state, now);
  return { ...round, achievement: state.lastAchievement, reward: scored.reward };
}

function addKeyObservation(profile, key, ms, errors) {
  const old = profile.keyStats[key] || { count: 0, errors: 0, emaMs: 0, bestMs: null };
  const next = {
    count: old.count + 1,
    errors: old.errors + errors,
    emaMs: rounded(old.count ? old.emaMs * 0.8 + ms * 0.2 : ms),
    bestMs: old.bestMs === null ? ms : Math.min(old.bestMs, ms),
  };
  profile.keyStats[key] = next;
}

function addHistory(profile, state, now, status) {
  if (!state.correct && !state.errors) return;
  profile.history.unshift({ ...summaryOf(state, now), status, at: new Date().toISOString() });
  profile.history = profile.history.slice(0, 50);
}

export function finishEarly(state, profile, now) {
  if (state.phase === 'running') pause(state, now);
  if (state.phase !== 'complete') addHistory(profile, state, now, 'interrupted');
}

// Both physical Delete and Backspace mean "go back" in the practice interface.
// Errors remain counted in accuracy; clearing red must not silently erase them.
export function deleteCharacter(state, now) {
  if (state.phase !== 'running' && state.phase !== 'paused') return { kind: 'ignored' };
  const wasWrong = state.feedback === 'incorrect';
  state.feedback = '';
  state.wrongKey = '';
  state.latestRecords = [];
  // A rejected letter marks the current prompt without advancing the typed prefix.
  if (wasWrong) return { kind: 'cleared' };
  if (state.mode !== 'keys' && state.typed) {
    const letters = Array.from(state.typed);
    const deleted = letters.pop();
    state.typed = letters.join('');
    const undoneTrial = state.trials.pop();
    if (undoneTrial) {
      state.correct = Math.max(0, state.correct - 1);
      // Preserve every mistake and its attribution when the key is typed again.
      state.pendingErrors += undoneTrial.errors;
    }
    state.promptMs = 0;
    state.promptStart = state.phase === 'running' ? now : null;
    return { kind: 'moved-back', deleted, clearedWrong: false };
  }
  return { kind: 'nothing' };
}

export function typeCharacter(state, profile, input, now, rng = Math.random) {
  if (state.phase !== 'running') return { kind: 'ignored' };
  if (typeof input !== 'string' || !input) return { kind: 'ignored' };
  // Passage and sequence practice leave one editable typo at the cursor.
  if (state.mode !== 'keys' && state.feedback === 'incorrect') return { kind: 'ignored' };
  const expected = currentExpected(state);
  const char = (state.mode !== 'text' ? input.normalize('NFC').toLowerCase() : input.normalize('NFC'));
  if (Array.from(char).length !== 1 || !expected) return { kind: 'ignored' };
  if (char !== expected) {
    state.errors++;
    state.pendingErrors++;
    if (state.mode === 'sequence') state.roundErrors++;
    state.feedback = 'incorrect';
    if (state.mode !== 'keys') state.wrongKey = input.normalize('NFC');
    state.latestRecords = [];
    return { kind: 'incorrect', expected };
  }
  const responseMs = rounded(currentPromptMs(state, now));
  state.trials.push({ key: expected, ms: responseMs, errors: state.pendingErrors });
  state.correct++;
  state.pendingErrors = 0;
  state.feedback = 'correct';
  if (state.mode === 'keys') {
    addKeyObservation(profile, expected, responseMs, state.trials[state.trials.length - 1].errors);
    updateRecords(state, profile);
  } else {
    state.typed += expected;
    state.latestRecords = [];
  }
  let round = null;
  if (state.mode === 'sequence' && state.typed === state.sequence) {
    round = recordSequenceRound(state, profile, now);
  }
  const done = state.mode === 'keys' ? state.correct >= state.goal
    : state.mode === 'sequence' ? state.rounds.length >= state.sequenceRounds : state.typed === state.target;
  if (done) {
    state.activeMs = elapsedMs(state, now);
    state.segmentStart = null;
    state.promptStart = null;
    state.promptMs = 0;
    state.phase = 'complete';
    state.finishedAt = new Date().toISOString();
    const summary = summaryOf(state, now);
    let reward = round?.reward;
    if (state.mode !== 'sequence') {
      const text = state.mode === 'text';
      const records = text ? profile.textRecords : profile.keyRoundRecords;
      const key = text ? textRecordKey(state) : keyRoundKey(state);
      const scored = scoreRound(records[key], summary.wpm, rounded(summary.accuracy), false, profile.roundWindow);
      records[key] = scored.record;
      reward = scored.reward;
    }
    addHistory(profile, state, now, 'completed');
    return { kind: 'complete', summary, records: state.latestRecords, round, reward };
  }
  if (round) {
    pause(state, now);
    state.promptMs = 0;
    state.phase = 'between-rounds';
    return { kind: 'round-complete', round, reward: round.reward };
  }
  if (state.mode === 'keys') {
    state.lastTwo = [...state.lastTwo.slice(-1), expected];
    state.target = weightedKeyChoice(state, profile, rng);
  }
  state.promptMs = 0;
  state.promptStart = now;
  return { kind: 'correct', records: state.latestRecords };
}

// Non-cryptographic ID used only to compare a custom passage against itself.
export function passageFingerprint(text) {
  let h = 2166136261;
  for (const char of text) {
    h = Math.imul(h ^ char.codePointAt(0), 16777619);
  }
  return (h >>> 0).toString(36) + ':' + Array.from(text).length;
}

export function snapshot(state, now) {
  const saved = copy(state);
  if (state.phase === 'running') {
    saved.activeMs = elapsedMs(state, now);
    saved.promptMs = currentPromptMs(state, now);
    saved.phase = 'paused';
    saved.segmentStart = null;
    saved.promptStart = null;
  }
  return saved;
}

export function restoreSession(data) {
  if (!data || typeof data !== 'object') return newSession();
  const state = newSession(data);
  const trials = Array.isArray(data.trials) ? data.trials.slice(0, state.mode === 'sequence' ? 4500 : 1000).filter(t =>
    t && typeof t.key === 'string' && Array.from(t.key).length === 1 && positive(t.ms)
      && Number.isInteger(t.errors) && t.errors >= 0 && t.errors <= 100000) : [];
  state.trials = trials.map(t => ({ key: t.key, ms: Math.min(t.ms, 3600000), errors: t.errors }));
  state.correct = state.trials.length;
  state.errors = state.trials.reduce((n, t) => n + t.errors, 0);
  state.activeMs = positive(data.activeMs) ? Math.min(data.activeMs, 86400000) : 0;
  state.promptMs = positive(data.promptMs) ? Math.min(data.promptMs, 3600000) : 0;
  state.pendingErrors = Number.isInteger(data.pendingErrors) ? cap(data.pendingErrors, 0, 100000) : 0;
  state.errors += state.pendingErrors;
  state.lastTwo = Array.isArray(data.lastTwo) ? data.lastTwo.filter(k => KEY_ORDER.includes(k)).slice(-2) : [];
  state.startedAt = typeof data.startedAt === 'string' ? data.startedAt : null;
  state.finishedAt = typeof data.finishedAt === 'string' ? data.finishedAt : null;
  if (state.mode === 'keys') {
    state.target = unlockedKeys(state).includes(data.target) ? data.target : '';
  } else if (state.mode === 'sequence') {
    state.sequence = validSequence(state, data.sequence) ? data.sequence : '';
    state.target = state.sequence;
    const rounds = Array.isArray(data.rounds) ? data.rounds.slice(0, state.sequenceRounds) : [];
    const validRounds = rounds.every((r, i) => r && r.number === i + 1
      && positive(r.ms) && r.ms <= 86400000 && Number.isInteger(r.errors)
      && r.errors >= 0 && r.errors <= 100000 && positive(r.accuracy) && r.accuracy <= 100);
    const typed = typeof data.typed === 'string' ? data.typed.normalize('NFC') : '';
    const validTyped = state.sequence.startsWith(typed) && typed.length < state.sequenceLength;
    const required = rounds.length * state.sequenceLength + typed.length;
    if (state.sequence && validRounds && validTyped && state.trials.length === required) {
      state.rounds = rounds.map(r => ({ number: r.number, ms: rounded(r.ms),
        errors: r.errors, accuracy: rounded(r.accuracy), newRecord: r.newRecord === true }));
      state.typed = typed;
      state.correct = required;
      state.roundErrors = state.trials.slice(rounds.length * state.sequenceLength)
        .reduce((n, t) => n + t.errors, state.pendingErrors);
      state.roundStartMs = positive(data.roundStartMs) && data.roundStartMs <= state.activeMs
        ? data.roundStartMs : 0;
      const achievement = data.lastAchievement;
      if (achievement && ['first', 'improved'].includes(achievement.kind)
          && positive(achievement.ms) && achievement.ms <= 86400000
          && Number.isInteger(achievement.roundNumber)
          && achievement.roundNumber >= 1 && achievement.roundNumber <= state.rounds.length) {
        state.lastAchievement = {
          kind: achievement.kind, ms: achievement.ms, roundNumber: achievement.roundNumber,
          previousBestMs: positive(achievement.previousBestMs) ? achievement.previousBestMs : null,
          improvementMs: positive(achievement.improvementMs) ? achievement.improvementMs : null,
        };
      }
    } else {
      // An inconsistent, corrupted round ledger must not resume with fabricated records.
      return newSession(state);
    }
  } else {
    const stored = typeof data.target === 'string' && data.target.length <= 800
      ? data.target.normalize('NFC') : '';
    const typed = typeof data.typed === 'string' ? data.typed.normalize('NFC') : '';
    const preset = PASSAGES.find(p => p.id === state.passageId);
    const originalPreset = preset?.text || '';
    const matchesSource = isLevelPassage(state.passageId) ? levelTextValid(state, stored)
      : stored === passageFor(state) || (stored === originalPreset && Boolean(originalPreset));
    // Resuming pre-upgrade text (uppercase/punctuation) must not lose progress.
    // New sessions and fresh passages remain strictly limited to unlocked keys.
    state.target = stored && matchesSource && stored.startsWith(typed) ? stored : passageFor(state);
    state.legacyResume = !levelTextValid(state, state.target)
      && state.target === stored && ['running', 'paused', 'complete'].includes(data.phase);
    state.textKind = typeof data.textKind === 'string' && ['sentences', 'sentences+words', 'sentences+drills', 'words', 'words+drills', 'key-groups', 'preset', 'custom'].includes(data.textKind)
      ? data.textKind : state.textKind;
    state.textLanguage = ['de', 'en', 'mixed'].includes(data.textLanguage) ? data.textLanguage : state.textLanguage;
    state.typed = state.target.startsWith(typed) ? typed : '';
    state.correct = Array.from(state.typed).length;
    state.trials = state.trials.slice(0, state.correct);
    state.errors = state.trials.reduce((n, t) => n + t.errors, state.pendingErrors);
  }
  if (data.phase === 'complete' && progressOf(state).done >= progressOf(state).total) {
    state.phase = 'complete';
  } else if (data.phase === 'between-rounds' && state.mode === 'sequence' && !state.typed
      && state.rounds.length > 0 && state.rounds.length < state.sequenceRounds && !state.roundErrors) {
    state.phase = 'between-rounds';
    state.promptMs = 0;
    state.roundStartMs = state.activeMs;
  } else if (data.phase === 'paused' || data.phase === 'running') {
    state.phase = state.target ? 'paused' : 'idle';
    if (state.phase === 'paused' && state.mode !== 'keys' && state.pendingErrors > 0 && data.feedback === 'incorrect') {
      state.feedback = 'incorrect';
      // Previous saves identify an outstanding typo but did not store its character.
      if (typeof data.wrongKey === 'string' && Array.from(data.wrongKey).length === 1) {
        state.wrongKey = data.wrongKey;
      }
    }
  }
  return state;
}
