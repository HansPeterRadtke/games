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
