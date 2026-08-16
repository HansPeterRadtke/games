# LLM Game

A browser game that turns live speech into an evolving scene. The browser captures mono audio, sends 16 kHz PCM to Nitro, and receives transcripts and scene objects.

The production path is:

`browser -> Apache -> Nitro llm-game-stt -> local faster-whisper tiny -> Thor fallback -> scene planner -> browser`

Nitro uses the installed multilingual tiny model as the low-latency primary recognizer. Thor large-v3 remains a fallback when the local model is unavailable or returns no text. The existing whisper.cpp base English model is the final fallback.

Project code and static assets live in this repository. Runtime logs, session metadata, generated topic images, and deployment reports live under `/data/var/llm_game` and are ignored by Git.

Run `./tests/run_all.sh` for repository checks. Nitro deployment is installed through `sudo ./deploy/install-nitro.sh`; direct system files are never symlinked into `/data`.

## PRSE basic playable testbed

The current `/llm_game/` build deliberately starts with simple static transparent square sprites and a small deterministic simulation. The player moves with WASD/arrows or the touch joystick, pushes an orange block, collides with solid gray/moving blocks, and uses a nearby green door with `E`. A dashed circle shows the perception boundary. Objects inside it are materialized into physical state; objects outside it are semantic-only and keep evolving according to their semantic motion rule. When they enter perception again, physical position is reconstructed from the current semantic state. The action field supports `wait N`, `create block`, `describe`, and `use door`; voice input remains optional through the existing STT websocket.
