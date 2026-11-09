// Level-aware offline text exercises. Every generated letter is an unlocked key.
// Curated phrases are complete, ordinary German or English utterances. There are
// deliberately no punctuation marks: punctuation keys aren't part of the levels.
// At extremely small alphabets we label the output as key groups, not sentences.
export const TRAINING_KEY_ORDER = Object.freeze(Array.from('fjdkslaöghärueiwoqptzüvmcxybn'));

export const LEVEL_PASSAGES = Object.freeze([
  { id: 'level-mixed', name: 'Level practice · German / English', language: 'DE/EN' },
  { id: 'level-de', name: 'Level practice · German', language: 'DE' },
  { id: 'level-en', name: 'Level practice · English', language: 'EN' },
]);

export const SENTENCES = Object.freeze({
  de: `
lass das
ja lass das
das lag da
das glas lag da
das gras lag da
das rad lag da
das rad lag im gras
der hase sah das gras
der hase sah das rad
er sah das rad
er sah das haus
er sah das glas
er sah das gras
er sah die frau
er sah sie
sie sah das haus
sie sah das rad
sie sah das glas
sie las es
sie las das
sie rief es
du sahst das
du warst da
wer war das
was war das
das war es
wer sah das
wer sah das rad
wer sah das haus
wer sah das gras
wer war hier
wir sahen das
wir sahen sie
wir sahen das haus
wo war das
wo war er
es war so
was war los
wer war wo
hallo du
wer rief da
wer ruft da
wo ist das rad
wo ist das haus
wo ist die frau
wo ist der hase
sie ist da
sie ist hier
sie ist froh
sie war froh
sie hat das rad
sie hat das glas
der hase ist hier
der hase ist froh
der hase war da
das ist gut
das ist sehr gut
das ist das rad
das ist das haus
das ist das glas
die frau ist da
die frau ist froh
die frau geht
die frau geht hier
die frau fragt
die frau hat es
die frau hat das rad
wir gehen
wir gehen raus
wir gehen hier raus
wir gehen zum haus
wir gehen zum tor
wer geht mit
du gehst mit
du gehst raus
sie geht mit
sie geht raus
sie geht zum haus
er geht ins haus
er geht raus
papa ist da
papa ist froh
papa hat das rad
papa geht mit
papa ist hier
papa fragt sie
mama ist da
mama kommt
mama ist froh
mama kommt mit
mama mag das
mama geht mit
mama ist hier
mama hat das rad
ich gehe
ich gehe mit
ich gehe raus
ich mag das
ich mag das haus
ich mag das rad
ich mag die frau
ich sehe das
ich sehe es
ich sehe das rad
ich sehe das haus
ich sehe die frau
ich sehe das glas
ich sehe das licht
ich frage dich
ich mag dich
ich esse eis
ich esse das
ich esse mit
ich will das
ich will hier raus
ich komme mit
ich komme gern
ich komme heute
ich komme zum haus
ich habe zeit
ich habe das rad
ich habe eine idee
ich habe ein buch
ich habe das buch
ich suche das buch
ich finde das buch
ich finde das gut
ich bin hier
ich bin froh
ich bin bereit
ich bin gleich da
ich gehe nach hause
ich gehe ins haus
wir gehen nach hause
wir sehen das haus
wir haben zeit
wir haben ein ziel
wir haben ein buch
wir machen das
wir machen eine pause
wir kommen mit
wir kommen heute
wir laufen durch den park
wir gehen durch den wald
wir lesen ein buch
wir lesen zusammen
es ist heute warm
heute ist es warm
heute ist das wetter gut
das wetter ist gut
das wetter wird besser
heute regnet es
morgen wird es warm
morgen gehen wir raus
morgen ist ein guter tag
jetzt geht es los
jetzt ist die zeit
jetzt habe ich zeit
jetzt machen wir pause
jetzt gehen wir los
alles ist in ordnung
alles ist wieder gut
alles wird besser
wir schaffen das
wir lernen das zusammen
jeden tag wird es besser
wir machen weiter
ich werde immer schneller
ich tippe heute schneller
ich tippe ganz ruhig
ich lerne gern
das tippen macht freude
ich habe genug zeit
wir nehmen uns zeit
die sonne scheint heute
der hund ist hier
der hund liegt im gras
das kind spielt im haus
das kind lacht laut
das kind lernt neue worte
ich sehe einen vogel
der vogel fliegt hoch
der vogel sitzt im gras
der tag geht zu ende
der himmel ist blau
die wolken ziehen weiter
wir gehen heute an den see
am morgen ist die luft klar
heute ist ein guter tag
jeder schritt macht uns besser
wir halten das tempo ruhig
`.trim().split('\n').filter(Boolean),
  en: `
a sad lad
a sad dad
ask dad
dad asks
a glad lad
a glad dad
dad has a glass
dad had a glass
a lad has a glass
a sad lad has a glass
a dad has a glass
he has a glass
she has a glass
she had a glass
he has a red glass
she had a red glass
he is glad
she is glad
he said yes
she said yes
he said hello
she said hello
he had a glass
i had a glass
i see a glass
i see a red glass
i see a dog
i saw a dog
i saw a red glass
i saw the dog
i see the dog
i see the glass
i see the red door
i see a fox
i saw a fox
i see the fox
we are glad
we are here
we saw a glass
we saw a dog
we saw the red door
we saw the dog
we saw the fox
we are safe
we are ready
we are happy
we are on the way
we are home
we are at home
a dog is here
a dog has a glass
a dog is glad
a dog is fast
a dog is near
a fox is fast
the fox is fast
the dog is fast
the dog is here
the dog is glad
the dog is happy
the dog was here
the dog sat here
the dog sat near the door
the red dog is here
the red door is open
the red door is wide
the door was open
we walk to the door
we walk to the lake
we walk to the park
we can walk there
we go to the park
we go to the lake
we go home
we are going home
we want to go home
we need to go home
i am glad
i am happy
i am here
i am ready
i am at home
i am on the way
i like it
i like the dog
i like the fox
i like the red door
i like to play
i like to read
i like to write
i like to type
i can do it
i can see it
i can type fast
i can type with ease
i can go home
i can read this
i can make it
i will do it
i will try again
i want to learn
i want to go home
i want to type fast
i feel good today
i feel ready to learn
i feel more at ease today
he is at home
he likes to read
he likes the dog
he can read this
he can type fast
she likes to read
she likes the dog
she can type fast
she can do it
she is here with us
she is ready to go
he has a new idea
she has a new idea
the day is warm
the day is bright
the sky is blue
the light is bright
the sun is warm
the sun is up
the sun is out
the rain is light
the rain is over
the wind is soft
the air is clear
the lake is calm
the water is clear
the water is warm
the sun shines today
the morning is quiet
this is a good day
this is a quiet day
this is a good idea
this is a new start
this is the right key
this is just practice
let us start again
let us try once more
let us keep going
let us take our time
we can learn together
we are getting better
we get faster every day
we learn from each mistake
we type with care and speed
slow and steady wins the race
practice makes progress
make time for a short break
keep your hands relaxed
keep a steady rhythm
try again and do your best
`.trim().split('\n').filter(Boolean),
});

export const WORDS = Object.freeze({
  de: `ja das lass als glas gas lag da gras rad haar hals haus raus frau ruf er es der hase sah frage fragte fragte sie die hier dir wir wer war was wo so oder froh rosa rot tag gut gehe geh geht gehst gehen sagte sagt sieh sieht hat hatte hatte bitte bitte papa mama kommt mit am im zum bei auf zeit zwei heute sehr stets das ist los da darf soll sollst egal leider weise leise reis reise seit fort dort tor torf tief stolz zart warm hart mild wasser wisst lass das du der die das ein eine einer wir ihr ich mich dich euch sich habe haben hat er sie so hoch licht nacht frage spiel spiele spiele spiele klar echt frei froh klar schön hübsch leise leicht gerade sofort weiter gegen sein nur ruhig gute guten guter froh glücklich grün gross klein stark kurz lange langsam schneller lesen lerne lernen tipp tippe tippen schreib schreiben wort worte satz sätze taste tasten tastenfeld finger fingerspitzen hände üben übung besser minuten morgen abend tag nacht kind hund katze maus vogel wald haus park see bodensee baum gras sonne regen wolke wolken himmel luft wind wasser ufer licht lichtblick freude spass lachen lacht lächeln ruhig pause pausen zeit ziel ziele heute morgen gleich wieder gemeinsam zusammen genau richtig falsch fehler neue neu starten beginne beginnen ende ende geschafft schön klappt geht gut machen spiele jetzt kann kannst können gewinnt laufen gehen spricht spricht lesen lachen lachen kinder warten fragen antwort sage sage danke bitte guten guten tag hallo servus tschüss raus rein dort drinnen draussen bitte bitte danke dir` .split(/\s+/).filter(Boolean),
  en: `a i as sad dad lad ask asks glad glass had has all hall fall half lads lads fail fails gash lag gas lash dash adds dash a glad dad he she see says said his her hers here side dice ice ride rise sir sure use user else deer red read dear are was were we where who what why how wow low slow show so soda goal go dog dogs door doors fox foxes for from frog frogs fog got get give gave have has just must rust dust best test fast faster fastest past last later late little bit this that those there then them the these their with without to top stop spot step steps part park play plays player plane paper people just time timer type typing typed speed pace quick quiet quickness joy jump jumps sun son sand hand hands hard head heart heal heap ship shop fish dish wish wishful window wide wide open calm calmness lake lakes water weather warm warmer clear sky blue bright right light night high low rain rainy wind words word yes no maybe yes you your yours my mine in on at of off out up down never ever when where while why look looks looking make makes making take takes taking good great happy smile smiles smiling learn learning practice practice makes perfect each every improve improvement again tries try careful care error errors mistake mistakes focus focused action actions round rounds time times score scores best record records win wins winning goal today tomorrow tomorrow morning afternoon evening week weeknight minutes second seconds easy easier hard harder ready work world speed fast faster slow slower slowly steady proper same different one two three four five six seven eight nine ten friends friend family child children bird birds tree trees forest field stone lake water sea island coast house home room desk chair keyboard fingers hands mind nature outside inside calm music art sound voice story stories book books page pages read reading write writing speak speaking listen listening walk walking walking bike bicycle car cars road roads traffic safe safety good wonderful great day morning night today tonight tomorrow now soon soonish` .split(/\s+/).filter(Boolean),
});

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

// Alphabet/locale eligibility is immutable for a level; avoid repeated scans
// when a player starts another round or switches language settings.
const sentenceCache = new Map();
const wordCache = new Map();
export function eligibleSentences(keys, language = 'de') {
  const id = language + ':' + [...keys].join('');
  if (!sentenceCache.has(id)) {
    sentenceCache.set(id, Object.freeze(SENTENCES[language].filter(sentence => allowedText(sentence, keys, false))));
  }
  return sentenceCache.get(id);
}
export function eligibleWords(keys, language = 'de') {
  const id = language + ':' + [...keys].join('');
  if (!wordCache.has(id)) {
    wordCache.set(id, Object.freeze([...new Set(WORDS[language].filter(word => allowedText(word, keys, false)))]));
  }
  return wordCache.get(id);
}

function shuffled(items, rng) {
  const list = [...items];
  for (let i = list.length - 1; i > 0; i--) {
    const j = index(rng, i + 1);
    [list[i], list[j]] = [list[j], list[i]];
  }
  return list;
}

function practiceGroups(keys, rng) {
  const results = [];
  let previous = '';
  while (results.join(' ').length < 56) {
    const len = 2 + index(rng, 4);
    let word = '';
    for (let i = 0; i < len; i++) {
      const different = keys.filter(key => key !== previous);
      const choices = different.length && i > 0 ? different : keys;
      const picked = choices[index(rng, choices.length)];
      word += picked;
      previous = picked;
    }
    results.push(word);
  }
  return results.join(' ');
}

function collectUnits(units, rng, targetSize) {
  let text = '';
  let bag = shuffled(units, rng);
  let i = 0;
  let previous = null;
  let attempts = 0;
  while (text.length < targetSize && attempts++ < Math.max(100, units.length * 20)) {
    if (i === bag.length) { bag = shuffled(units, rng); i = 0; }
    const part = bag[i++];
    if (part && (part !== previous || attempts > units.length * 4)) {
      text += (text ? ' ' : '') + part;
      previous = part;
    }
    if (text.length > 160) break;
  }
  // Guarantee a non-empty, bounded prompt even if a tiny pool repeats.
  if (text.length < targetSize && units.length) {
    while (text.length < targetSize) text += (text ? ' ' : '') + units[index(rng, units.length)];
  }
  return text;
}

export function generateLevelExercise(config, rng = Math.random) {
  const level = Number.isInteger(config.level) ? Math.min(28, Math.max(1, config.level)) : 1;
  const keys = TRAINING_KEY_ORDER.slice(0, level + 1);
  const preference = config.passageId === 'level-de' ? ['de']
    : config.passageId === 'level-en' ? ['en'] : ['de', 'en'];
  const pools = preference.map(language => ({ language, sentences: eligibleSentences(keys, language), words: eligibleWords(keys, language) }));
  const bestSentencePools = pools.filter(pool => pool.sentences.length >= 2);
  const languageOptions = bestSentencePools.length ? bestSentencePools : pools.filter(pool => pool.words.length >= 2);
  if (languageOptions.length) {
    const chosen = languageOptions[index(rng, languageOptions.length)];
    if (chosen.sentences.length >= 2) {
      const text = collectUnits(chosen.sentences, rng, level < 10 ? 65 : 100);
      return { text, kind: 'sentences', language: chosen.language };
    }
    const text = collectUnits(chosen.words.filter(word => word.length >= 2).length >= 2
      ? chosen.words.filter(word => word.length >= 2) : chosen.words, rng, 60);
    return { text, kind: 'words', language: chosen.language };
  }
  return { text: practiceGroups(keys, rng), kind: 'key-groups', language: null };
}
