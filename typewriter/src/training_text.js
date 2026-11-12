// Level-aware offline word practice. Saved passages keep their original text.
import germanTiers from '../vocabulary/de.js';
import englishTiers from '../vocabulary/en.js';

export const TRAINING_KEY_ORDER = Object.freeze(Array.from('fjdkslaöghärueiwoqptzüvmcxybn'));

export const LEVEL_PASSAGES = Object.freeze([
  { id: 'level-mixed', name: 'Level practice · German / English', language: 'DE/EN' },
  { id: 'level-de', name: 'Level practice · German', language: 'DE' },
  { id: 'level-en', name: 'Level practice · English', language: 'EN' },
]);

const index = (rng, length) => {
  const sample = Number(rng());
  return Math.floor((Number.isFinite(sample) ? Math.max(0, Math.min(.999999999, sample)) : 0) * length);
};
const clean = text => String(text).normalize('NFC').toLocaleLowerCase('de').replace(/[^a-zäöü\s]/g, ' ').replace(/\s+/g, ' ').trim();
export function allowedText(text, keys, allowLineBreaks = true) {
  const set = new Set(keys);
  return [...String(text).normalize('NFC')].every(char => char === ' ' || (allowLineBreaks && char === '\n')
    || ([...char.toLocaleLowerCase('de')].length === 1 && set.has(char.toLocaleLowerCase('de'))));
}
export function invalidTextKeys(text, keys) {
  const set = new Set(keys);
  return [...new Set([...String(text).normalize('NFC')].filter(char => char !== ' ' && char !== '\n'
    && !set.has(char.toLocaleLowerCase('de'))))];
}
export function normalizedPreset(text) { return clean(text); }

function shuffled(items, rng) {
  const list = [...items];
  for (let i = list.length - 1; i > 0; i--) {
    const j = index(rng, i + 1);
    [list[i], list[j]] = [list[j], list[i]];
  }
  return list;
}

export const VOCABULARY_VERSION = 2;
export const MIN_KEY_OCCURRENCES = 3;

export function keyCoverage(text, keys) {
  const count = Object.fromEntries(keys.map(key => [key, 0]));
  const letters = [...String(text)].filter(char => Object.hasOwn(count, char));
  const quarters = Array.from({ length: 4 }, () => ({ ...count }));
  for (let q = 0; q < quarters.length; q++) {
    const end = Math.floor((q + 1) * letters.length / 4);
    for (let i = Math.floor(q * letters.length / 4); i < end; i++) {
      count[letters[i]]++;
      quarters[q][letters[i]]++;
    }
  }
  const quarterMinimum = keys.length ? Math.min(...quarters.flatMap(q => Object.values(q))) : 0;
  const missing = keys.filter(key => count[key] === 0);
  const weakest = keys.length ? Math.min(...keys.map(key => count[key])) : 0;
  return { counts: count, missing, weakest, quarterMinimum, covered: keys.length - missing.length, total: keys.length };
}

// Append each newly unlocked dictionary tier once. Earlier levels sample only
// the prefix recorded for them, even after visiting the full alphabet.
class Vocabulary {
  constructor(tiers) {
    this.tiers = tiers;
    this.words = [];
    this.groups = new Map();
    this.limits = [];
  }

  unlock(level) {
    while (this.limits.length <= level) {
      let previous = '';
      for (const entry of this.tiers[this.limits.length].matchAll(/(\d+)([a-zäöü]+)/g)) {
        const word = previous.slice(0, Number(entry[1])) + entry[2];
        previous = word;
        this.words.push(word);
        const groups = [...new Set(word), word.length];
        for (const group of groups) {
          if (!this.groups.has(group)) this.groups.set(group, []);
          this.groups.get(group).push(word);
        }
      }
      const sizes = new Map([...this.groups].map(([key, words]) => [key, words.length]));
      this.limits.push({ sizes, total: this.words.length });
    }
    return this.limits[level];
  }
}

const banks = { de: new Vocabulary(germanTiers), en: new Vocabulary(englishTiers) };

export function eligibleWords(keys, language = 'de') {
  const unlocked = new Set(keys);
  const highest = TRAINING_KEY_ORDER.findLastIndex(key => unlocked.has(key));
  if (highest < 0) return [];
  const bank = banks[language];
  const entries = bank.words.slice(0, bank.unlock(highest).total);
  return unlocked.size === highest + 1 ? entries : entries.filter(w => [...w].every(k => unlocked.has(k)));
}

function keyGroups(keys, rng) {
  const letters = [];
  while (letters.length < 72) letters.push(...shuffled(keys, rng));
  const words = [];
  for (let i = 0; i < letters.length;) {
    const end = i + 2 + index(rng, 4);
    words.push(letters.slice(i, end).join(''));
    i = end;
  }
  return words.join(' ');
}

// Sample across the whole eligible bucket, including late alphabetic entries.
// Stratification also produces different candidates when a bucket is smaller
// than the sample or a caller supplies a constant random source.
function bestWord(bank, sizes, group, rng, score) {
  const words = bank.groups.get(group);
  const size = sizes.get(group) || 0;
  const samples = Math.min(size, 48);
  let best = null;
  let high = -Infinity;
  for (let i = 0; i < samples; i++) {
    const lo = Math.floor(i * size / samples);
    const hi = Math.floor((i + 1) * size / samples);
    const word = words[lo + index(rng, hi - lo)];
    const value = score(word);
    if (value > high) { best = word; high = value; }
  }
  return best;
}

// Keep a quarter's chosen words and letter counts. Spread standalone keys
// through the words and give repeated spellings room whenever possible.
function orderQuarters(quarters) {
  const result = [];
  const lastUsed = new Map();
  for (const tokens of quarters) {
    const words = tokens.filter(t => t.length > 1);
    const keys = tokens.filter(t => t.length === 1);
    const slots = tokens.length;
    let keyIndex = 0;
    for (let i = 0; i < slots; i++) {
      if (keyIndex < Math.round((i + 1) * keys.length / slots)) {
        result.push(keys[keyIndex++]);
        continue;
      }
      let pick = 0;
      for (let j = 0; j < words.length; j++) {
        const seen = lastUsed.get(words[j]) ?? -Infinity;
        if (seen < result.length - 3) { pick = j; break; }
        if (seen < (lastUsed.get(words[pick]) ?? -Infinity)) pick = j;
      }
      const [word] = words.splice(pick, 1);
      lastUsed.set(word, result.length);
      result.push(word);
    }
  }
  return result.join(' ');
}

// Rare draws of long compound words can exceed the saved-passage limit.
// Keep real words and quarter coverage even for that case. The shortest
// eligible spellings give a bounded cover for every supported alphabet.
function compactPassage(keys, sources, rng) {
  const shortest = new Map();
  for (const source of shuffled(sources, rng)) {
    for (const key of keys) {
      const pool = source.bank.groups.get(key);
      const size = source.sizes.get(key) || 0;
      let best = shortest.get(key);
      for (let i = 0; i < size; i++) {
        if (!best || pool[i].length < best.word.length) best = { word: pool[i], language: source.language };
      }
      if (best) shortest.set(key, best);
    }
  }
  const count = Object.fromEntries(keys.map(k => [k, 0]));
  const words = [];
  const languages = new Set();
  for (const goal of [1, 2]) {
    for (const key of shuffled(keys, rng)) {
      if (count[key] >= goal) continue;
      const unit = shortest.get(key);
      const word = unit?.word || key;
      if (unit) languages.add(unit.language);
      words.push(word);
      for (const char of word) count[char]++;
    }
  }
  return { text: orderQuarters(Array.from({ length: 4 }, () => shuffled(words, rng))), languages };
}

export function generateLevelExercise(config, rng = Math.random) {
  const level = Number.isInteger(config.level) ? Math.min(28, Math.max(1, config.level)) : 1;
  const keys = TRAINING_KEY_ORDER.slice(0, level + 1);
  const languages = config.passageId === 'level-de' ? ['de']
    : config.passageId === 'level-en' ? ['en'] : ['de', 'en'];
  const sources = languages.map(language => ({ language, bank: banks[language],
    sizes: banks[language].unlock(level).sizes }));
  if (sources.every(s => !s.sizes.size)) {
    const text = keyGroups(keys, rng);
    return { text, kind: 'key-groups', language: null, focusKeys: [...keys], coverage: keyCoverage(text, keys) };
  }

  const drills = keys.filter(key => sources.every(s => !s.sizes.has(key)));
  const lengths = [...new Set(sources.flatMap(s => [...s.sizes.keys()].filter(k => typeof k === 'number')))];
  if (drills.length && !lengths.includes(1)) lengths.push(1);
  lengths.sort((a, b) => a - b);
  const counts = Object.fromEntries(keys.map(k => [k, 0]));
  const last = Object.fromEntries(keys.map(k => [k, -keys.length]));
  const used = new Map();
  const usedLanguages = new Set();
  let languageTurn = index(rng, sources.length);
  let position = 0;

  function add(section, word, language) {
    section.words.push(word);
    section.length += word.length;
    used.set(word, (used.get(word) || 0) + 1);
    if (language) usedLanguages.add(language);
    for (const k of word) {
      counts[k]++;
      section.counts[k]++;
      last[k] = position++;
    }
  }

  function choose(section, group) {
    let source = sources[languageTurn % sources.length];
    if (!source.sizes.has(group)) source = sources.find(s => s.sizes.has(group));
    if (!source) return null;
    const score = word => {
      let cost = 0;
      const seen = new Set();
      for (const k of word) {
        // Repeated, already plentiful and recently seen letters cost more.
        cost += counts[k] + 1.6 * section.counts[k] + (seen.has(k) ? 2.5 : 0)
          + Math.max(0, 1 - (position - last[k]) / keys.length);
        seen.add(k);
      }
      const gain = [...seen].filter(k => !section.counts[k]).length;
      return .95 * gain - 1.4 * cost / word.length - .45 * Math.abs(word.length - 5)
        - 30 * (used.get(word) || 0) + 3 * rng();
    };
    const word = bestWord(source.bank, source.sizes, group, rng, score);
    if (word) { languageTurn++; add(section, word, source.language); }
    return word;
  }

  // Construct each quarter around overdue letters. A key with no eligible
  // word gets a short drill at the point it is due, including in English.
  const sections = [];
  for (let part = 0; part < 4; part++) {
    const section = { words: [], length: 0, counts: Object.fromEntries(keys.map(k => [k, 0])) };
    sections.push(section);
    const order = shuffled(keys, rng);
    while (true) {
      let due = order.filter(k => section.counts[k] < 2);
      if (!due.length) {
        if (section.length >= Math.max(16, keys.length * 2)) break;
        due = [...order];
      }
      due.sort((a, b) => section.counts[a] - section.counts[b] || counts[a] - counts[b] || last[a] - last[b]);
      if (!choose(section, due[0])) {
        add(section, due[0], null);
      }
    }
  }

  // Equal letter counts make the four coverage guarantees hold in the actual
  // passage, whatever lengths the selected words have. Use real word lengths
  // to fill differences; tiny alphabets need not contain a one-letter word.
  const longest = Math.max(...sections.map(s => s.length));
  const reachable = [true];
  let target = longest;
  for (let size = 1; ; size++) {
    reachable[size] = lengths.some(n => n <= size && reachable[size - n]);
    if (size >= longest && sections.every(s => reachable[size - s.length])) { target = size; break; }
  }
  for (const section of sections) {
    while (section.length < target) {
      const remaining = target - section.length;
      const fits = lengths.filter(n => n <= remaining && reachable[remaining - n]);
      // Prefer everyday typing lengths. A short exact fit finishes the quarter.
      const viable = fits.filter(n => n >= 2 && n <= 9);
      const options = viable.length ? viable : fits;
      const length = options.includes(remaining) ? remaining : options[index(rng, options.length)];
      if (!choose(section, length)) {
        const key = [...drills].sort((a, b) => counts[a] - counts[b])[0];
        add(section, key, null);
      }
    }
  }
  let text = orderQuarters(sections.map(s => s.words));
  let actualLanguages = usedLanguages;
  if (text.length > 800) {
    const compact = compactPassage(keys, sources, rng);
    text = compact.text;
    actualLanguages = compact.languages;
  }
  return { text, kind: drills.length ? 'words+drills' : 'words',
    language: actualLanguages.size === 2 ? 'mixed' : [...actualLanguages][0],
    focusKeys: drills, coverage: keyCoverage(text, keys) };
}
