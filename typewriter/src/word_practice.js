import { combinedDistribution } from './adaptive_words.js';
import { wordPool } from './training_text.js';

export const WORD_STRATEGIES = ['combined', 'selected', 'random', 'mistakes', 'slowest'];
export const MAX_WORD_REPEATS = 50;

export function wordSetText(word, repeats) {
  return word ? Array(repeats).fill(word).join(' ') : '';
}

export function wordDistribution(pool, strategy, stats = {}, exclude = '', profile = {}) {
  if (strategy === 'combined') return combinedDistribution(pool, { ...profile, wordStats:stats }, exclude);
  const entries = [];
  let total = 0;
  let strongest = 0;
  const observed = new Set([...Object.keys(stats), ...Object.keys(profile.typingSignals || {})]);
  for (const word of observed) {
    if (word === exclude || !pool.members.has(word)) continue;
    // Rates are per letter, so a longer spelling is not intrinsically harder.
    const live = profile.typingSignals?.[word], observation = stats[word];
    const rate = strategy === 'mistakes' ? live?.errorRate ?? observation?.errorRate : live?.ms ?? observation?.msPerChar;
    if (!rate) continue;
    const spellings = live ? live.attempts / word.length : observation.count;
    const confidence = spellings / (spellings + 2);
    const weight = rate * rate * confidence;
    strongest = Math.max(strongest, rate);
    total += weight;
    entries.push([word, weight]);
  }
  // Ease off even when a single observed word is the entire weighted pool.
  const reference = strategy === 'mistakes' ? .20 : 500;
  const focus = .85 * Math.min(1, strongest / reference);
  return { entries, total, focus };
}

export function choosePracticeWord(config, stats, rng = Math.random, exclude = '', profile = {}) {
  const pool = wordPool(config.level, config.wordLanguage);
  const words = exclude && pool.words.length > 1 ? pool.words.filter(w => w !== exclude) : pool.words;
  if (config.wordStrategy === 'selected') return pool.members.has(config.selectedWord) ? config.selectedWord : '';
  if (!words.length) return '';
  const randomWord = () => words[Math.min(words.length - 1, Math.floor(rng() * words.length))];
  if (config.wordStrategy === 'random' || !stats) return randomWord();
  const { entries, total, focus } = wordDistribution(pool, config.wordStrategy, stats, exclude, profile);
  // Keep discovering unmeasured words even after a long practice history.
  if (!entries.length || rng() < 1 - focus) return randomWord();
  let draw = rng() * total;
  for (const [word, weight] of entries) {
    draw -= weight;
    if (draw < 0) return word;
  }
  return entries.at(-1)[0];
}

// Called at the last accepted letter, before the separator. Trial durations
// already exclude pauses and include time spent correcting a typo.
export function observeCompletedWord(stats, target, end, trials) {
  if (!end || (end < target.length && !/\s/.test(target[end])) || /\s/.test(target[end - 1])) return;
  let start = end - 1;
  while (start && !/\s/.test(target[start - 1])) start--;
  const word = target.slice(start, end).toLowerCase();
  if (!/^[a-zäöü]{2,64}$/.test(word)) return;
  const sample = trials.slice(end - word.length, end);
  if (sample.length !== word.length) return;
  const errors = sample.reduce((sum, t) => sum + t.errors, 0);
  const pace = sample.reduce((sum, t) => sum + t.ms, 0) / word.length;
  const prev = Object.hasOwn(stats, word) ? stats[word] : null;
  const average = (old, value) => prev ? .7 * old + .3 * value : value;
  stats[word] = { count: (prev?.count || 0) + 1, errors: (prev?.errors || 0) + errors,
    errorRate: average(prev?.errorRate, errors / (errors + word.length)),
    msPerChar: average(prev?.msPerChar, pace) };
}

export function wordRecordKey(s) { return s.practiceWord + '|' + s.wordRepeats; }
