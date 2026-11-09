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
