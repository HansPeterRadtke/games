// Per-attempt measurements feed the combined word draw, including unfinished words.
// A null time denotes a typo: it changes accuracy as soon as it is entered.
function previousSignal(token, profile) {
  if (profile.typingSignals && Object.hasOwn(profile.typingSignals, token)) return profile.typingSignals[token];
  if (token.length === 1) {
    const key = profile.keyStats?.[token];
    if (key?.count) return { attempts:key.count + key.errors, errorRate:key.errors / (key.count + key.errors), ms:key.emaMs };
  } else {
    const word = profile.wordStats?.[token];
    if (word?.count) return { attempts:word.count * token.length + word.errors, errorRate:word.errorRate, ms:word.msPerChar };
  }
  return null;
}

export function observeTypingAttempt(profile, state, expected, ms) {
  const key = expected.toLowerCase();
  if (!/^[a-zäöü]$/.test(key)) return;
  profile.typingSignals ??= Object.create(null);
  function update(token) {
    const old = previousSignal(token, profile);
    const attempts = (old?.attempts || 0) + 1;
    const alpha = 1 / Math.min(16, attempts);
    const errorRate = (old?.errorRate || 0) * (1 - alpha) + Number(ms === null) * alpha;
    const pace = ms === null ? old?.ms ?? null
      : old?.ms == null ? ms : old.ms + alpha * (ms - old.ms);
    profile.typingSignals[token] = { attempts, errorRate, ms:pace };
  }
  update(key);
  if (state.mode === 'word') update(state.practiceWord);
  if (state.mode === 'text') {
    let start = state.typed.length, end = start + 1;
    while (start && !/\s/.test(state.target[start - 1])) start--;
    while (end < state.target.length && !/\s/.test(state.target[end])) end++;
    const word = state.target.slice(start, end).toLowerCase();
    if (/^[a-zäöü]{2,64}$/.test(word)) update(word);
  }
}

function errorWeight(signal) {
  return signal.errorRate * signal.attempts / (signal.attempts + 2);
}

export function combinedDistribution(pool, profile, exclude) {
  const letters = new Map(), words = new Map();
  for (const key of Object.keys(pool.byKey)) {
    const signal = previousSignal(key, profile);
    if (pool.byKey[key].length && signal) letters.set(key, signal);
  }
  const known = new Set([...Object.keys(profile.wordStats || {}), ...Object.keys(profile.typingSignals || {})]);
  for (const word of known) {
    if (word === exclude || !pool.members.has(word)) continue;
    const signal = previousSignal(word, profile);
    if (signal) words.set(word, signal);
  }
  // Isolated key prompts can be slower than continuous typing. Compare each
  // kind of timing to its own median once there are comparable observations.
  const times = signals => [...signals.values()].map(s => s.ms).filter(ms => ms > 0).sort((a,b) => a-b);
  const median = values => values[Math.floor((values.length - 1) / 2)];
  const letterTimes = times(letters), wordTimes = times(words);
  const wordBaseline = median(wordTimes.length >= 2 || !letterTimes.length ? wordTimes : letterTimes);
  const keyBaseline = median(letterTimes.length >= 2 || !wordTimes.length ? letterTimes : wordTimes);
  const slowWeight = (s, usual) => usual && s.ms > 0 ? Math.min(4, Math.max(0, s.ms / usual - 1)) : 0;

  const mistakes = new Map(), slow = new Map(), weakKeys = new Map();
  let errorStrength = 0, speedStrength = 0, keyStrength = 0;
  for (const [word, signal] of words) {
    const error = errorWeight(signal), pace = slowWeight(signal, wordBaseline);
    if (error > 0) mistakes.set(word, error);
    if (pace > 0) slow.set(word, pace);
    errorStrength = Math.max(errorStrength, Math.min(1, error / .10));
    speedStrength = Math.max(speedStrength, Math.min(1, pace));
  }
  for (const [key, signal] of letters) {
    const weight = 5 * errorWeight(signal) + slowWeight(signal, keyBaseline);
    if (weight > 0) weakKeys.set(key, weight);
    keyStrength = Math.max(keyStrength, Math.min(1, weight));
  }
  const weights = new Map();
  function add(word, weight) { weights.set(word, (weights.get(word) || 0) + weight); }
  function distribute(group, share, apply) {
    let sum = 0;
    for (const weight of group.values()) sum += weight;
    if (sum) for (const [item, weight] of group) apply(item, share * weight / sum);
  }
  // Separate probability budgets keep frequent weak letters in a large
  // dictionary from drowning out a word the player actually mistyped.
  distribute(mistakes, .68 * errorStrength, add);
  distribute(slow, .21 * speedStrength, add);
  const byLetter = new Float64Array(pool.words.length);
  distribute(weakKeys, .11 * keyStrength, (key, share) => {
    const bucket = pool.byKey[key];
    const size = bucket.length - Number(Boolean(exclude && pool.members.has(exclude) && exclude.includes(key)));
    if (!size) return;
    for (const id of bucket) if (pool.words[id] !== exclude) byLetter[id] += share / size;
  });
  let total = 0;
  const entries = [];
  for (let i = 0; i < pool.words.length; i++) {
    const word = pool.words[i], weight = byLetter[i] + (weights.get(word) || 0);
    if (weight > 0) { entries.push([word, weight]); total += weight; }
  }
  const focus = total > 0 ? .85 * Math.max(errorStrength, speedStrength, keyStrength) : 0;
  return { entries, total, focus };
}
