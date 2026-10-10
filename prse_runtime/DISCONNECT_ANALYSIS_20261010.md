# PRSE connection reliability repair — 2026-10-10

Reported symptom: the viewer at the original Nitro `/llm_game/` URL repeatedly disconnected after introducing the independent simulation service. No crash was visible in `prse-engine.service`; `NRestarts=0`, and a 150-second diagnostic using parallel direct, Apache-proxied, and public Cloudflare WSS connections delivered around 1,500 state packets per connection without unexpected closure. This does not rule out intermittent real mobile network interruptions.

Two reproducible software defects were identified and repaired:

1. The viewer heartbeat measured elapsed time from its initial page load, not its current connection. After a long suspension/disconnect it could close freshly established WebSockets again when the heartbeat callback resumed. All received server packets now refresh liveness. Every new WebSocket open/hello resets the heartbeat timestamp, and stale sockets close once, then reconnect rather than entering a repeated close cycle. New connections no longer repeatedly overwrite in-game messages. Reconnects log browser close codes, and the server records close code, reason, duration and time since last application ping. The viewer preserves displayed state across interruptions, retries with backoff, resumes the same server world and retains its token even if persistent browser storage is unavailable.

2. The server's low `MAX_ACTIVE=4` slots plus its asynchronous idle-session reclamation could reject the new session **after successfully freeing an inactive slot**, because the pending session reservation was counted twice. `tests/session-capacity.mjs` reproduced this and now proves that a new viewer receives an explicit capacity rejection when all slots are occupied, can join an existing world without using another slot, and can reclaim an inactive session. The limit is now eight active worlds, with a per-world server-side snapshot and bounded session expiry. A concurrent-creation lock prevents creating multiple authoritative instances for the same token.

Bandwidth and input-load reduction: baseline live frames contained around 7,310 bytes of uncompressed JSON. `view-projection.mjs` sends only the fields needed by the graphical presentation, around 2,637 bytes, a **64% uncompressed reduction**, with normal WebSocket permessage-deflate negotiated in supported clients. The simulation continues at 60 Hz; display messages remain up to 10 Hz. Movement-key autorepeat no longer sends redundant commands, movement commands do not trigger immediate full world snapshots, and the viewer performs small capped **visual-only** extrapolations between authoritative frames. The server's simulation does not trust any client extrapolation.

Verification:

- `tests/view-projection.mjs`: projection shape, 64% byte reduction, state immutability.
- `tests/headless-smoke.mjs`: actual headless 3D world, movement, server save, reconnect, old-save import and event logging.
- `tests/session-capacity.mjs`: full slots, explicit error, reuse of an existing slot, idle reclamation.
- Real public desktop and 320px-mobile Chromium tests: unchanged URL, server-authoritative movement, saved state, keyboard focus, explicit WebSocket closure and subsequent reconnect without resetting world, no mobile horizontal overflow.
- Eight consecutive forced link interruptions in an isolated browser test were observed in the server session log (eleven connections including initial navigation and reload, with expected test close codes).
- A mobile Chromium test with simulated 450ms latency, 16,000 bytes/s download and 3,000 bytes/s upload continued to receive and render state; world time advanced more than six seconds and the test completed.

The current deployed files are `/etc/systemd/system/prse-engine.service` and the original public page's `viewer.js` script under `/data/src/github/games/browser_physics_prototype/`. Deployment requires a **browser refresh once** because already-loaded JavaScript remains old until the page is reloaded. Other applications sharing Apache were not changed. Exact disconnect reasons from the user’s browser cannot be reconstructed from the earlier server version because it logged only `viewer_disconnected` without close codes. New logs include the reason data for any future occurrence. Neither the broader internet connection nor Cloudflare availability can be guaranteed.
