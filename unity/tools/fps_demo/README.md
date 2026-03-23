# FPS Demo Bootstrap

This tool syncs the scripted FPS demo sources into the Unity project, regenerates the scene, and builds the Linux player.

Target project:
- `unity/projects/fps_demo`

Shared package used:
- `unity/packages/com.hpr.foundation`

Source layout:
- `Source/Editor` -> copied into `Assets/Editor`
- `Source/Scripts` -> copied into `Assets/Scripts`

Build command:
```bash
sudo -u hans -H env HOME=/home/hans DISPLAY=:1 XAUTHORITY=/run/user/1000/gdm/Xauthority XDG_RUNTIME_DIR=/run/user/1000 \
  /data/src/github/games/unity/tools/fps_demo/setup_project.sh
```
