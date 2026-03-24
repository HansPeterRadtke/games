# Unity Asset Store tooling

Uses the authenticated Unity Hub session for `hans` to list and download owned Asset Store packages.

Examples:

```bash
cd /data/src/github/games
sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 \
  /data/venv/bin/python unity/tools/assetstore/unity_assetstore.py list
```

```bash
cd /data/src/github/games
sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 \
  /data/venv/bin/python unity/tools/assetstore/unity_assetstore.py download-all --skip-existing
```

Downloads land in `unity/assetstore/downloads/`.
State/cached catalog land in `unity/assetstore/metadata/`.
