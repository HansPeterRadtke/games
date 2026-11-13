# Current Unity buyer package: real Play Mode and Linux Player acceptance — November 13, 2026

This is new evidence for the **latest exact installed commercial-candidate archive**, including the November 13 duplicate-ability-ID and resource-pool-choice changes. Earlier Player/Play Mode successes used different archives and do not substitute for this run. The current package was built with the security-patched Unity `6000.6.8f1`; all tests use an independently imported, byte-verified package with **161 asset paths / GUIDs and 55 C# scripts**. No external publisher operation occurred. The main seller checkout's fourteen dirty files were preserved.

## Real Editor Play Mode result

A new isolated project was copied from the current exact imported buyer template. The existing public `qa/run_verified_playmode.py` driver checked package SHA-256 against the successful release builder receipt before launching, staged private QA scripts only, started Unity batch Editor Play Mode and repeated archive verification afterward. Native engine exit zero and all eight checks passed:

- Imported showcase entered actual Play Mode and scene objects ran their Awake initializers
- Player CharacterController collided and moved, and enemy advanced automatically
- Composition services and world registry bound correctly
- Actual damage event reduced health; healing restored health with the expected stamina cost
- Weapon firing decremented ammunition and damaged the target; checkpoint restore returned weapon/enemy state

A separate file-hash audit compared `Assets`, `Packages`, and `ProjectSettings` in the copied project with its pre-test imported original. **318 original files unchanged, zero removed, five private QA script/metadata files added**. Unity's own verifier also found the selected archive unchanged before/after Play.

Private evidence: `/data/var/marketplace-account-setup/hpr-current-native-playmode-20261113/release/actual-playmode-receipt.txt`, `release/actual-playmode.unity.log`, `pre-play-identity.json`, `preservation-and-runtime.json`.

## Actual standalone Linux Player

The independent `qa/SaveSlotPlayer/run_player.py` took the exact same archive and an untouched copy of that same imported buyer project. It built the real packaged showcase into a Linux x86-64 Player using patched Unity. The private fixture then launched **three distinct real executable processes**:

- **Write:** from one hundred health / six rounds, take one attack and fire one round; persist a local schema-three JSON slot containing health **92**, magazine **5**.
- **Cold read:** start at one hundred health and six rounds in a new process; load the same disk slot, restore health **92** and magazine **5**. Verify the slot bytes and the neighboring `.writing` file remain unchanged.
- **Damaged JSON:** use another isolated process/profile with a truncated slot; refuse the invalid data, retain one hundred health and six rounds, and leave the corrupt original and neighboring file intact.

The helper verified its output JSON against the in-game observations, independently verified the source template and all copied staged-file hashes, and repeated exact package identity after the Player build: all **161 package assets and 55 C# scripts unchanged**. The template contained **318 protected original files**; no original file was changed. The new run's Player logs had no `Screen position out of view frustum`, invalid screen-position, managed exception, or C# compiler-error diagnostic matching the explicitly checked patterns. The full Player/result receipts are retained in `/data/var/marketplace-account-setup/hpr-current-save-player-20261113/verify/` with build, write, read and reject logs and the `result.json` file.

The **tested imported project has `activeInputHandler: 0`, legacy Input Manager only**. This Player result must not be presented as new-input-only or Both-mode Player proof. Likewise it is a **Built-in pipeline headless Player test**, not URP Player acceptance or a visual mouse/keyboard usability study. Genuine rendered URP *Editor* acceptance for this exact package was separately recorded in `current-urp-render-2026-11-13.md`.

## Reproduction and release boundary

Run the existing checked-in native `qa/run_verified_playmode.py` using a **new** release/output copy, the exact archive and builder receipt, and a disposable exact imported project template. Run `qa/SaveSlotPlayer/run_player.py` with the same archive checksum, a fresh output path and the patched installed Unity Editor. Both drivers intentionally fail rather than accept an existing success receipt or replace a customer-owned test file. Do not overwrite the private evidence directories above.

These results improve the verified current package readiness but **do not approve release**. Normal graphical Unity Editor installer interaction still encounters a separate software-terms consent gate that was not retried or bypassed. Manual rendered buyer GUI, accessibility, new-input-only and URP Player variants, independent experienced-developer onboarding and competitive buyer value remain outstanding. Nothing was published, sold, uploaded or sent to the marketplace.
