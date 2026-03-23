# FPS Demo

First-person Unity prototype built against the shared local package `com.hpr.foundation`.

Project path:
- `unity/projects/fps_demo`

Current gameplay slice:
- title menu, pause menu, save/load, exit, options
- graphics/audio/input options including FOV and key rebinding
- 9 equipment slots with primitive weapon/tool viewmodels
- pickups, keys, locked doors, enemies, player HP/stamina
- inventory panel, minimap/full map view, interaction prompts

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

Default controls:
- `WASD` move
- mouse look
- `Shift` run
- `Space` jump
- `E` interact
- `I` inventory
- `M` map
- `R` reload
- `F` flashlight
- `1`..`9` switch equipment
- left mouse use current equipment
- mouse wheel cycle equipment
- `Esc` menu / cursor release

Notes:
- key bindings are editable in the options menu
- save file is written under `Application.persistentDataPath`
