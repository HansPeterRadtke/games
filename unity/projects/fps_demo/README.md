# FPS Demo

Basic first-person Unity demo project built against the shared local package `com.hpr.foundation`.

Project path:
- `unity/projects/fps_demo`

Open in Unity Hub:
- add `/data/src/github/games/unity/projects/fps_demo`
- editor version: `6000.4.0f1`

Build from CLI:
```bash
sudo -u hans -H env HOME=/home/hans DISPLAY=:1 XAUTHORITY=/run/user/1000/gdm/Xauthority XDG_RUNTIME_DIR=/run/user/1000 \
  /data/src/github/games/unity/tools/fps_demo/setup_project.sh
```

Run the built game:
```bash
/data/src/github/games/unity/projects/fps_demo/Build/Linux/FPSDemo.x86_64
```

Controls:
- `WASD` move
- mouse look
- `Space` jump
- `Esc` release cursor / quit depending on player state
