// Level-aware offline word practice. Saved passages keep their original text.
import germanTiers from '../vocabulary/de.js';
import englishTiers from '../vocabulary/en.js';
import covers from '../vocabulary/covers.js';

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

export const BOXED_DRILLS_VERSION = 2;
export const VOCABULARY_VERSION = 3;
export const MAX_TEXT_CHARACTERS = 800;
export const PASSAGE_MEMORY = 10;

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

// The build proves two optima per level and language: fewest words, and
// fewest typed characters. The latter may use more, shorter words.
const tiers = { de: germanTiers, en: englishTiers };
const tierWords = new Map();
const pools = new Map();
const order = TRAINING_KEY_ORDER;
const bits = Object.fromEntries(order.map((k, i) => [k, 1 << i]));
function maskOf(word) {
  let mask = 0;
  for (const k of word) mask |= bits[k];
  return mask;
}
function countBits(mask) {
  let n = 0;
  for (; mask; mask &= mask - 1) n++;
  return n;
}

export function wordPool(level, language = 'mixed') {
  const id = language + ':' + level;
  if (pools.has(id)) return pools.get(id);
  let words;
  if (language === 'mixed') {
    words = [...new Set([...wordPool(level, 'de').words, ...wordPool(level, 'en').words])];
  } else {
    words = [];
    for (let i = 0; i <= level; i++) {
      const tier = language + ':' + i;
      if (!tierWords.has(tier)) {
        const list = [];
        let prev = '';
        for (const [, prefix, suffix] of tiers[language][i].matchAll(/(\d+)([a-zäöü]+)/g)) {
          prev = prev.slice(0, Number(prefix)) + suffix;
          list.push(prev);
        }
        tierWords.set(tier, list);
      }
      words.push(...tierWords.get(tier));
    }
  }
  const masks = words.map(maskOf);
  const possible = masks.reduce((a, b) => a | b, 0);
  const unsupported = order.slice(0, level + 1).filter(k => !(possible & bits[k]));
  const byKey = Object.fromEntries(order.slice(0,level + 1).map(k => [k, []]));
  for (let i = 0; i < words.length; i++) for (const k of new Set(words[i])) byKey[k].push(i);
  const pool = { words, masks, byKey, members: new Set(words), unsupported, possible };
  pools.set(id, pool);
  return pool;
}

export function eligibleWords(keys, language = 'de') {
  const mask = maskOf(keys);
  const highest = order.findLastIndex(k => mask & bits[k]);
  if (highest < 0) return [];
  const pool = wordPool(highest, language);
  return pool.words.filter((_, i) => !(pool.masks[i] & ~mask));
}

export function minimumWordCharacters(level, language) {
  return covers[language][level - 1][1].join(' ').length;
}

export function passageLanguage(id) {
  return id === 'level-de' ? 'de' : id === 'level-en' ? 'en' : 'mixed';
}

// Compare sets of actual words. Moving the same words around is still a repeat.
function passageWords(text) {
  return [...new Set(text.split(' ').filter(w => w.length > 1))].sort();
}

function recentWords(history) {
  const cost = new Map(), sets = new Set();
  for (let age = 0; age < history.length; age++) {
    const words = passageWords(history[history.length - 1 - age]);
    sets.add(words.join(' '));
    for (const word of words) cost.set(word, (cost.get(word) || 0) + 1 / (age + 1));
  }
  return { cost, sets };
}

// Branch on the rarest outstanding letter. Every complete cover must use a
// word from that bucket. Bound the search on large dictionaries for fast redraws.
function rotatingCover(template, pool, budget, recent, allowExtra, rng) {
  if (!template.length) return [];
  const keys = Object.keys(pool.byKey).filter(k => pool.byKey[k].length)
    .sort((a, b) => pool.byKey[a].length - pool.byKey[b].length);
  let best, bestCost = Infinity;
  function consider(words) {
    const signature = [...words].sort().join(' ');
    const exposure = words.reduce((sum, w) => sum + (recent.cost.get(w) || 0), 0) / words.length;
    const cost = (recent.sets.has(signature) ? 100 : 0) + exposure + rng() * .015;
    if (cost < bestCost) { best = [...words]; bestCost = cost; }
  }
  consider(template);
  // A beam keeps alternative first words alive. Spending the entire search
  // budget below one promising first word recreates the same sets at high levels.
  const importance = keys.map(k => 1 + .7 * Math.log2(pool.words.length / pool.byKey[k].length));
  function search(slots) {
    let frontier = [{ ids: [], missing: pool.possible, room: budget, exposure: 0 }];
    for (let left = slots; left > 0; left--) {
      const next = new Map();
      for (const path of frontier) {
        const key = keys.find(k => path.missing & bits[k]);
        const bucket = pool.byKey[key];
        const sample = left === 1 ? bucket.length : Math.min(100, bucket.length);
        const offset = index(rng, bucket.length);
        for (let n = 0; n < sample; n++) {
          const pos = (offset + Math.floor(n * bucket.length / sample)) % bucket.length;
          const id = bucket[pos], word = pool.words[id], mask = pool.masks[id];
          if (word.length + (left - 1) * 3 > path.room) continue;
          const missing = path.missing & ~mask;
          if (left === 1) {
            if (missing) continue;
            // Each word in an expanded cover must contribute a letter of its own.
            if (slots > template.length && path.ids.some((_, skip) => {
              let other = mask;
              for (let i = 0; i < path.ids.length; i++) if (i !== skip) other |= pool.masks[path.ids[i]];
              return other === pool.possible;
            })) continue;
            consider([...path.ids.map(i => pool.words[i]), word]);
          } else if (countBits(missing) >= left - 1) {
            const room = path.room - word.length - 1;
            if (countBits(missing) + left - 2 > room) continue;
            const exposure = path.exposure + (recent.cost.get(word) || 0);
            let difficulty = 0;
            for (let i = 0; i < keys.length; i++) if (missing & bits[keys[i]]) difficulty += importance[i];
            const rank = -difficulty + .75 * room - 4 * exposure + 5 * rng();
            const old = next.get(missing);
            if (!old || rank > old.rank) next.set(missing, { ids: [...path.ids, id], missing, room, exposure, rank });
          }
        }
      }
      frontier = [...next.values()].sort((a, b) => b.rank - a.rank).slice(0, 56);
      if (!frontier.length) return;
    }
  }
  search(template.length);
  // Keep the minimum count whenever we find an unfamiliar combination. When
  // compact solutions keep recycling the same words, allow one useful word more.
  if (allowExtra && bestCost >= .49) search(template.length + 1);
  return shuffled(best, rng);
}

function partialCover(pool, limit, rng, recent) {
  const chosen = [];
  let needed = pool.possible;
  while (needed && limit >= 2) {
    let best = -Infinity, pick = '';
    for (let i = 0; i < pool.words.length; i++) {
      const w = pool.words[i], gain = countBits(pool.masks[i] & needed);
      if (!gain || w.length > limit) continue;
      const score = gain / (w.length + 1) + .04 * gain + .01 * rng() - .025 * (recent.cost.get(w) || 0);
      if (score > best) { best = score; pick = w; }
    }
    if (!pick) break;
    chosen.push(pick);
    needed &= ~maskOf(pick);
    limit -= pick.length + 1;
  }
  return chosen;
}

export function generateLevelExercise(config, rng = Math.random, history = []) {
  const level = Math.min(28, Math.max(1, config.level || 1));
  const language = passageLanguage(config.passageId);
  const keys = order.slice(0, level + 1);
  const pool = wordPool(level, language);
  const [fewest, shortest] = covers[language][level - 1];
  const manual = Number.isInteger(config.maxCharacters) && config.maxCharacters > 0;
  const limit = manual ? Math.min(config.maxCharacters, MAX_TEXT_CHARACTERS) : MAX_TEXT_CHARACTERS;
  const drills = shuffled(pool.unsupported, rng);
  const drillCost = drills.length * 2;
  const tokens = [];
  let length = 0;
  function append(word) {
    const cost = word.length + Number(tokens.length > 0);
    if (length + cost > limit) return false;
    tokens.push(word);
    length += cost;
    return true;
  }
  const fit = fewest.join(' ').length + drillCost <= limit ? fewest : shortest;
  const available = limit - (fit.join(' ').length + drillCost <= limit ? drillCost : 0);
  const recent = recentWords(history);
  const budget = manual ? available : Math.min(available, fit.join(' ').length + 10);
  const batch = fit.join(' ').length <= available
    ? rotatingCover(fit, pool, budget, recent, (manual || !config.strictMinimum) && history.length > 0, rng)
    : partialCover(pool, limit, rng, recent);
  // Reserve whole words first when a tight cap excludes some single-key drills.
  let used = batch.join(' ').length;
  for (const k of drills) {
    const cost = 1 + Number(batch.length > 0);
    if (used + cost > limit) break;
    batch.splice(index(rng, batch.length + 1), 0, k);
    used += cost;
  }
  for (const w of batch) append(w);
  if (manual) {
    const counts = keyCoverage(tokens.join(''), keys).counts;
    const seen = new Set(tokens);
    while (length + 1 < limit) {
      const room = limit - length - 1;
      const due = shuffled(keys, rng).sort((a,b) => counts[a] - counts[b]);
      let next = '';
      for (const k of due) {
        const bucket = pool.byKey[k];
        if (!bucket.length) { next = k; break; }
        const offset = index(rng, bucket.length);
        let best = -Infinity, considered = 0;
        for (let j = 0; j < bucket.length && considered < 36; j++) {
          const w = pool.words[bucket[(j + offset) % bucket.length]];
          if (w.length > room) continue;
          considered++;
          const cost = [...w].reduce((sum, ch) => sum + counts[ch], 0) / w.length;
          const score = rng() * 2 - cost - (seen.has(w) ? 8 : 0) - 3 * (recent.cost.get(w) || 0);
          if (score > best) { best = score; next = w; }
        }
        if (next) break;
      }
      if (!next) break;
      append(next);
      seen.add(next);
      for (const k of next) counts[k]++;
    }
  }
  const text = tokens.join(' ');
  return { text, kind: !pool.words.length ? 'key-groups' : tokens.some(w => w.length === 1) ? 'words+drills' : 'words',
    language: pool.words.length ? language : null, focusKeys: pool.unsupported, coverage: keyCoverage(text, keys) };
}
