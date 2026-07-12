# LLM Game

A browser game that turns live speech into an evolving scene. The browser captures mono audio, sends 16 kHz PCM to Nitro, and receives transcripts and scene objects.

The production path is:

`browser -> Apache -> Nitro llm-game-stt -> local faster-whisper tiny -> Thor fallback -> scene planner -> browser`

Nitro uses the installed multilingual tiny model as the low-latency primary recognizer. Thor large-v3 remains a fallback when the local model is unavailable or returns no text. The existing whisper.cpp base English model is the final fallback.

Project code and static assets live in this repository. Runtime logs, session metadata, generated topic images, and deployment reports live under `/data/var/llm_game` and are ignored by Git.

Run `./tests/run_all.sh` for repository checks. Nitro deployment is installed through `/data/bin/install_llm_game.sh`; direct system files are never symlinked into `/data`.
