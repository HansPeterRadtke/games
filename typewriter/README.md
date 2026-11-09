# Typewriter

Standalone browser typing trainer in the Games repository. Fresh implementation of ideas from the archived Test_TypeWriter_01.ipynb and Test_TypeWriter_02.ipynb notebooks on Nitro Data01. The originals remain untouched.

## Start

From this folder run `npm run serve`, then visit http://127.0.0.1:8765/ on Nitro. The application needs no downloaded JavaScript packages, backend, sign-in, or build step. It uses browser ES modules; opening the file directly without a web server is not supported. Do not expose the development server to the public internet.

## Training

Key training preserves the original German QWERTZ-oriented learning order, introduces one new key per level, and supports rounds of ten to one thousand correct keys. Mistakes do not advance a prompt and contribute to accuracy. Both the correct-key latency and the number of preceding mistakes are recorded. Adaptive selection gives more practice to slower and error-prone keys; turn it off for uniform selection. Space starts or pauses key training, Escape pauses any session, and plus/minus switches levels between rounds.

Text training supports four built-in German and English passages or up to eight hundred characters of user-defined text. It checks case, punctuation, whitespace, and characters exactly; paste is disabled during an active round. Space is a normal input in text training. A large practice surface can focus the on-screen keyboard on touch devices.

Live statistics include attempts, accuracy, words per minute, elapsed time, per-key latency, and a response rhythm chart. Records cover multiple consecutive correct-key windows for each level. Text passage records are separate. Recent sessions and key statistics are kept locally.

## Persistence

The app autosaves in browser local storage. Active rounds are saved as paused on reload to avoid counting time while closed. Export a JSON backup for durable retention or transfer across browsers; Import validates it and asks before replacing existing progress. This is a privacy-preserving local application with no account or telemetry. Custom passages are included in the local save and backup: never enter passwords or other secrets as training passages.

## Verification

Run `npm test` for logic and storage tests. Run `python3 tests/browser_headless.py` for the local real-Chromium interaction probe. The browser harness tests button and key events against the actual page. No network services beyond the temporary localhost test server are needed.

## Organization and known limits

`src/core.js` contains framework-independent scoring and session state. `src/storage.js` contains versioned storage and validation. `src/app.js` contains UI and input handling. The HTML/CSS implement the responsive layout.

This is a first functional implementation, not a production-ready release. Browser and desktop functionality is tested; German mobile IME input, screen-reader accessibility, and cross-browser compatibility require further hands-on testing. Local personal records are implemented; online leaderboards and migration of old binary scores are not. A few score definitions intentionally improve on the original: measured time includes corrections, accuracy includes wrong attempts, and the slowest-key metric improves only when lower.

## Sequence challenge

The third tab, **Sequence challenge**, is a timed competition against an identical sequence of unlocked letters. The default sequence length equals the current number of unlocked keys; it can be increased up to 150 but cannot go below the unlocked key count. The generator shuffles a complete copy of every unlocked key using Fisher–Yates, repeats full shuffled copies for longer sequences, and uses a shuffled partial copy for any remainder. It never draws independently with replacement, so each full group contains every unlocked key exactly once. The resulting sequence remains fixed for all rounds, across browser reloads and after **New session**. Changing modes without changing the level or sequence length also preserves it. Only **Shuffle new sequence** or changing the unlocked keys/sequence length creates another arrangement.

A session defaults to ten rounds; three, five, ten, twenty and thirty are available. Each full sequence produces a measured round time and error count, visible in the round-by-round log. The global session display continues to report total correct keystrokes, mistakes, accuracy, typing pace and elapsed time. Pausing stops both the session and current round clock; mistakes do not advance the cursor and correction time is included in the measured round.

**New personal best** highlights appear directly beneath the practice sequence when a complete round beats the saved best for that exact ordered sequence and level. The first completed round establishes the baseline, while subsequent record announcements show the improvement. The record survives new sessions, pauses, reloads and version-one JSON export/import. Other shuffled arrangements have separate records because their difficulty can differ. Up to three hundred recently practiced sequence records are retained to bound local storage.

Run `python3 tests/browser_sequence.py` for the sequence mode Chromium interaction checks, covering the visible first-record and improved-record announcements, repeat rounds, history, reshuffle, and preservation of the existing modes.

## Shared typing level and level-aware text exercises

Level and the currently unlocked letters are shown above all three modes. Changing the level affects key training, sequence training and text training; any partially completed session is protected by the existing confirmation before replacement.

Text practice defaults to a generated exercise containing only lowercase unlocked letters and spaces, with German, English and mixed-language choices. The offline corpus contains curated short phrases and words. Each generated candidate is checked against the level's alphabet. The generator uses real German or English phrases as soon as possible and labels its fallback as key groups where no real words are available, especially at the first five levels. No punctuation or extra letters are introduced, because they are not in the original levels. A new session offers a new exercise; the current exercise is stored exactly for restart, paused resume and backup. Custom passages are still available but cannot start unless all their characters are unlocked. The former full-length German and English samples remain selectable at a sufficiently high level, without punctuation. Incomplete older saved passages can still be resumed.

Generated text records are stored separately by selected level and language, while personal high scores from the two original modes and earlier text versions are preserved.

Backspace and Delete clear the red incorrect-key highlight in all modes. In the sequence and text modes they also remove the most recently accepted character within the current active exercise, visibly moving the cursor backward. Incorrect attempts and elapsed time remain counted; deleting a character does not erase history or improve accuracy artificially. A sequence cannot backspace into a previously finished round. Physical and touch-keyboard deletion events are supported.

Verification commands are `npm test`, `python3 tests/browser_headless.py`, `python3 tests/browser_sequence.py`, and `python3 tests/browser_level_text.py`. The tests cover unlocked alphabets at every level, old progress compatibility, red highlight clearing, cursor retreat, touch-keyboard deletion, sentence generation, and both original modes.

## Complete unlocked-key coverage (November 9, 2026)

Earlier generated passages checked only that letters belonged to the selected level; they could accidentally omit the newest or rarest keys entirely. Every newly generated level-based text exercise now has a verified coverage contract: **each unlocked key occurs at least three times and the newest key at least five times**. This applies independently at every level to German-only, English-only and mixed exercises. The interface displays the true coverage count. Existing paused/finished passages are not silently rewritten; the coverage display flags any older passage with incomplete coverage and offers a new exercise.

Selection prefers real, level-compatible phrases. The phrase bank contains additional German and English examples specifically for rare letters (for example, *das öl*, *äh ja*, *die quelle*, *die tür ist zu*, *das taxi ist da*, *yoga tut gut*, *a flask falls*, and *a jar has a lid*). Where a sentence does not contain every key, the generator prefers a meaningful focus word. If a language genuinely has no usable word for a newly unlocked key (for example German umlauts in English-only mode), a plainly labelled key drill covers that gap. Mixed and German exercises can avoid such drills from the point real words become possible. The fallback at very early levels is still a complete, repeatedly shuffled key set.

The generator uses bounded coverage-driven selection and cached candidate letter counts. It never returns a passage that fails the minimum-count contract, and it does not send text to an external provider. The text remains lowercase and uses only the unlocked letters and spaces. At higher levels, passages may be longer to provide enough practice of all the letters. Generated exercise text is retained unmodified throughout active practice, pause, browser restore and export/import. A regression suite tests all levels, all language settings and multiple seeded random selections, plus browser checks of the displayed coverage status and the rare keys at the highest level.
