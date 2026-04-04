# Asset Basket Showcase Project

This is a local Unity project used to rebuild a generated showcase scene from the purchased Unity Asset Store basket on this machine.

Tracked here:

- `Assets/Editor/` showcase tooling
- `Packages/`
- `ProjectSettings/`
- `.gitignore`

Not tracked here:

- imported third-party Asset Store assets under `Assets/`
- generated preview assets under `Assets/Generated/`
- the generated showcase scene file itself
- Unity cache, logs, and user settings

To rebuild the full scene from local purchased assets, run from the repo root:

```bash
unity/assetstore/build_asset_basket_showcase.sh
```
