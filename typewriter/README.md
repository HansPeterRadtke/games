# Typewriter

Standalone browser typing trainer in the Games repository. Fresh implementation of ideas from the archived Test_TypeWriter_01.ipynb and Test_TypeWriter_02.ipynb notebooks on Nitro Data01. The originals remain untouched.

## Start

From this folder run `npm run serve`, then visit http://127.0.0.1:8765/ on Nitro. The application needs no downloaded JavaScript packages, backend, sign-in, or build step. It uses browser ES modules; opening the file directly without a web server is not supported. Do not expose the development server to the public internet.

## Training

Key training preserves the original German QWERTZ-oriented learning order, introduces one new key per level, and supports rounds of ten to one thousand correct keys. Mistakes do not advance a prompt and contribute to accuracy. Both the correct-key latency and the number of preceding mistakes are recorded. Adaptive selection gives more practice to slower and error-prone keys; turn it off for uniform selection. Space starts or pauses key training, Escape pauses any session, and plus/minus switches levels between rounds.

Text training supports four built-in German and English passages or up to eight hundred characters of user-defined text. It checks case, punctuation, whitespace, and characters exactly; paste is disabled during an active round. Space is a normal input in text training. A large practice surface can focus the on-screen keyboard on touch devices.

Live statistics include attempts, accuracy, correct characters per minute, words per minute, elapsed time, per-key latency, and a response rhythm chart. Records cover multiple consecutive correct-key windows for each level. Text passage records are separate. Recent sessions and key statistics are kept locally.

## Persistence

The app autosaves in browser local storage. Active rounds are saved as paused on reload to avoid counting time while closed. Export a JSON backup for durable retention or transfer across browsers; Import validates it and asks before replacing existing progress. This is a privacy-preserving local application with no account or telemetry. Custom passages are included in the local save and backup: never enter passwords or other secrets as training passages.

## Verification

Run `npm test` for logic and storage tests. Run `python3 tests/browser_headless.py` for the local real-Chromium interaction probe. The browser harness tests button and key events against the actual page. No network services beyond the temporary localhost test server are needed.

## Organization and known limits

`src/core.js` contains framework-independent scoring and session state. `src/storage.js` contains versioned storage and validation. `src/app.js` contains UI and input handling. The HTML/CSS implement the responsive layout.

This is a first functional implementation, not a production-ready release. Browser and desktop functionality is tested; German mobile IME input, screen-reader accessibility, and cross-browser compatibility require further hands-on testing. Local personal records are implemented; online leaderboards and migration of old binary scores are not. A few score definitions intentionally improve on the original: measured time includes corrections, accuracy includes wrong attempts, and the slowest-key metric improves only when lower.

## Sequence challenge

The third tab, **Sequence challenge**, is a timed competition against an identical sequence of unlocked letters. The default sequence length equals the current number of unlocked keys; it can be increased up to 150 but cannot go below the unlocked key count. The generator shuffles a complete copy of every unlocked key using Fisher–Yates, repeats full shuffled copies for longer sequences, and uses a shuffled partial copy for any remainder. It never draws independently with replacement, so each full group contains every unlocked key exactly once. The resulting sequence remains fixed for all rounds, across browser reloads and after **New session**. Changing modes without changing the level or sequence length also preserves it. Only **Shuffle sequence** or changing the unlocked keys/sequence length creates another arrangement.

A session defaults to ten rounds; three, five, ten, twenty and thirty are available. Click the mode and press Space to start the first round. After every completed round, the game stops the timer, displays the result and waits for Space or the on-screen Start button. The final round completes the challenge. Each full sequence produces a measured round time and error count, visible in the round-by-round log. The global session display continues to report total correct keystrokes, mistakes, accuracy, typing pace and elapsed time. Pausing stops both the session and current round clock; mistakes do not advance the cursor and correction time is included in the measured round.

Directly beneath the target, the current round shows active time, correct characters per minute, accuracy and mistakes. Its result stays visible during the break and after reloading. When the next sequence round starts, the previous result remains in a labeled line below the live readings. Shuffle sequence is beside the mode status, outside Practice settings. The recent target and round position sit beside progress. The first round sets a baseline. Beating the saved best for the same ordered sequence and level triggers the gold record popup with the measured improvement. The record survives new sessions, pauses, reloads and version-one JSON export/import. Other shuffled arrangements have separate records because their difficulty can differ. Up to three hundred recently practiced sequence records are retained to bound local storage.

Run `python3 tests/browser_sequence.py` for the sequence mode Chromium interaction checks, covering the visible first-record and improved-record announcements, repeat rounds, history, reshuffle, and preservation of the existing modes.

## Shared typing level and level-aware text exercises

Practice settings show the level and currently unlocked letters for all three modes. Changing the level affects key training, sequence training and text training; any partially completed session is protected by the existing confirmation before replacement.

Text practice builds a passage of individual dictionary words from the unlocked letters. Choose German, English or a mix of both. New session draws another passage. Started passages are saved exactly for pause, resume and backup. An unstarted preview from the old vocabulary refreshes on upgrade. Custom passages and the original German and English samples remain available when their characters are unlocked.

Generated text records are stored separately by selected level and language, while personal high scores from the two original modes and earlier text versions are preserved.

In Sequence challenge and Text practice, the wrong character stays red and blocks further typing. Delete or Backspace removes that one typo. Accepted characters stay in place, including when the key is held, tapped twice, or reported twice by a keyboard. Correction time and the original mistake count toward the round result.

Verification commands are `npm test`, `python3 tests/browser_headless.py`, `python3 tests/browser_sequence.py`, `python3 tests/browser_level_text.py`, and `python3 tests/browser_word_practice.py`. The tests cover unlocked alphabets at every level, old progress compatibility, typo-only correction, held and repeated Delete, touch-keyboard deletion, dictionary coverage and word variety, and both original modes.

## Vocabulary and letter distribution

The offline word banks contain about ten thousand German and thirteen thousand English words. All early-level prompts and all words shorter than five letters come from the reviewed practice lists. Other entries must be frequent in their language, have a thesaurus entry and appear in its spelling dictionary. Mixed practice draws from both languages. The [vocabulary sources and build instructions](vocabulary/README.md) document the selection.

Generated Text practice defaults to the minimum number of real words covering every letter that can occur in a word at the selected level and language. A separate boxed key covers a letter with no eligible word. At the earliest levels each unlocked key appears once. Enter a maximum from 1 to 800 characters for a longer or shorter passage. The cap counts spaces and never truncates a word. If the cap cannot cover everything, the badge names the missing letters. If no complete word or applicable key drill fits, the start button explains how to raise the limit. The build solves both minimum word count and minimum typed length. Runtime substitutions preserve coverage and the selected budget.

## Single-word practice

Select **Single word** to repeat one word ten times by default. Set one to fifty repetitions. Choose a word from the searchable unlocked vocabulary, draw one at random, or select **Most mistakes** or **Slowest words**. The word stays fixed for the set. Space separates repetitions. At the end, Space starts the next set. The manual choice stays selected; automatic strategies draw again from current measurements. At levels without real words, the level-six button opens the first word level.

Text practice and Single word update the word's error rate and milliseconds per character after each completed spelling. Spaces and paused time are excluded. Each new spelling supplies thirty percent of the moving average. Adaptive sets give higher weight to words with more recent errors or slower pace per character. At least fifteen percent of draws explore the full eligible pool. Exploration increases as mistakes fall or words get faster, even with only one measured word. Before there is relevant evidence, draws are uniform. The adaptive controls show the leading probabilities for the next draw. The session, observations and separate records for each word and repetition count survive reload and export/import. Older backups can contribute word measurements when they contain the original passage and per-letter trials.

## Round records and celebrations

Each full sequence repeat, finished key-training goal, or finished text passage scores one round. The comparison board shows the best and mean speed and accuracy across the last one, three, five, ten, or twenty comparable rounds. Three is the default. Sequence speed is elapsed time for the exact sequence. Key-training pace compares rounds at the same level and goal. Pace targets for key and text practice show characters per minute, converted from the existing standard-word records. Generated text uses level and language, preset and custom passages use the existing passage identity. Accuracy includes mistakes, including corrected ones. Averages give each completed round equal weight. When there are fewer rounds, the board shows the available count. A dash means no measurement is available.

Each result is judged against the preceding rounds **before** it enters the window. A strictly faster or more accurate round can earn a recent best even when a lifetime record is much stronger. The first round sets a baseline. Ties, improvements over only the previous round, and clean rounds have distinct messages. Every fifth recorded round earns a practice milestone, including on a plateau. Existing all-time speed and accuracy records have priority over recent records. An all-time improvement gets a larger gold popup with the actual gain and the previous score. The popup stays out of the typing cursor's way, keeps keyboard focus and respects reduced motion. The selected consecutive-keystroke window in key training also celebrates strictly improved records.

The round-performance chart plots characters per minute, accuracy, or the original round score across the selected rounds. Character pace counts accepted characters, including required spaces, over active minutes. Correction time counts and waiting between rounds is excluded. One standard word is five characters. Historical character rates for key and text practice use the saved WPM precision. For sequence times, shorter times sit higher. Exact round scores are available below the plot. The chart sits alongside the exercise on a wide screen and follows it on a phone. Open **Practice settings** to turn off record celebrations while keeping the result and the chart. The [GUI design notes](GUI-design.md) document the research, screen priorities and walkthrough.

Recent history and the window preference travel with the existing version-one backup. Older backups retain their saved lifetime records. The migration recovers identifiable completed rounds from session history and from the saved sequence log. For other previously played sequences, it can recover the last time but cannot infer that round's accuracy. The original format did not retain older individual rounds indefinitely.

### Research and balance decisions

The owner's game-design recording of September 25 describes intermediate improvements that are meaningful before a player can win outright. The Infra guides on playability, reward and first-minute engagement call for a visible consequence, a feasible next action and testing with players. Here the two targets serve different purposes. Recent performance supplies a reachable challenge. The lifetime record preserves the achievement across quieter sessions.

In the Raspi Knowledge Library's copy of OpenStax *Psychology 2e*, section 6.3 (PDF pages 211–212) explains how reinforcement schedules influence response persistence. Section 10.1 (PDF pages 334–335) discusses how the form and expectation of feedback affect motivation. The score display therefore acknowledges what the player actually did, gives a specific comparison, and makes regular completion milestones predictable. The library's *SayCheck* system paper (pages 1–2) provides an example of linking a game event to actual practice and diagnostic feedback. Its speech-practice design does not establish reward frequency for typing. [OpenStax, Operant Conditioning](https://openstax.org/books/psychology-2e/pages/6-3-operant-conditioning) · [OpenStax, Motivation](https://openstax.org/books/psychology-2e/pages/10-1-motivation) · [SayCheck](https://www.isca-archive.org/interspeech_2026/shahin26_interspeech.html)

Ryan, Rigby and Przybylski's studies link perceived competence and autonomy with enjoyment. Sailer and colleagues found that a configuration including performance feedback, badges and leaderboards affected perceived competence. Mekler and colleagues found increased task output without a corresponding increase in intrinsic motivation in an image-annotation experiment. Research reviewed by Griffiths and Nuyens also distinguishes reward features that encourage repetition from evidence that a feature causes problematic play. These results motivate self-comparison, player-selected targets and a larger celebration reserved for measurable improvement. They do not establish an optimal window length or popup duration for this game. [Ryan et al.](https://doi.org/10.1007/s11031-006-9051-8) · [Sailer et al.](https://doi.org/10.1016/j.chb.2016.12.033) · [Mekler et al.](https://doi.org/10.1016/j.chb.2015.08.048) · [Griffiths and Nuyens](https://pmc.ncbi.nlm.nih.gov/articles/PMC5554268/)

**Why three rounds?** For equally distributed, independent continuous scores, any one of four observations has the same chance of being best. The newest therefore beats the preceding three roughly once in four rounds. For the preceding ten the chance is one in eleven. A lifetime record becomes progressively harder. A deterministic balance check used one thousand simulated clean sequence times, with no underlying improvement (uniform 700–800 milliseconds, rounded to tenths, a 32-bit LCG with seed 42, multiplier 1664525 and increment 1013904223). On the same samples the game awarded nine lifetime improvements, 250 additional three-round bests, and 82 additional ten-round bests. These are synthetic counts. Human play can include learning, fatigue and many ties. A useful human playtest is whether a returning player can tell what they beat, can see a reachable target after a plateau, and can start the next round with Space while the celebration is visible. Enjoyment has not been measured with players.
