# Handoff Guide

## Start here
The repo is currently handed off from a release-candidate checkpoint.
Read in this order:
1. `doc/release-candidate-status.md`
2. `doc/current-state.md`
3. `doc/package-validation.md`
4. `doc/package-dependency-map.md`
5. `doc/local-assets.md` if you need local art state

## Current proven truth
### Sale-ready packages
- `com.hpr.eventbus`
- `com.hpr.composition`

### Not sale-ready yet
Everything else under `unity/packages/com.hpr.*` remains internal.
Do not market or upload those packages yet.

## Authoritative validation entrypoint
```bash
cd /data/src/github/games
unity/tools/release/validate_release_candidate.sh
```

This is the command to rerun before any release, upload, or architectural checkpoint claim.

## Current code changes included in this handoff
- standalone productized package set for:
  - `com.hpr.eventbus`
  - `com.hpr.composition`
- release audit tooling
- dependency audit that now fails for forbidden references in the designated sellable set
- clean-project package validation with execute-method support
- package-owned demo scenes and package validators
- full-game build + smoke still green after the package split work

## What is local-only and not reproducible from git alone
Not committed:
- downloaded Unity Asset Store packages
- imported vendor asset folders in `Assets/`
- local-only art scene dressing based on those imports
- generated logs/builds/temp state

If the next developer wants the same art state, they must recreate it locally with the asset pipeline.

## Verified commands
Release-candidate pass:
```bash
cd /data/src/github/games
unity/tools/release/validate_release_candidate.sh
```

Full game build only:
```bash
cd /data/src/github/games
unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux
```

Full game smoke only:
```bash
cd /data/src/github/games
NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh
```

## Current open follow-up areas
- remove remaining forbidden lookup patterns from internal packages
- shrink `com.hpr.fpsdemo` further until it is only game-specific composition/content
- decide the next package to productize only after it has a standalone demo, standalone validator, and clean-project proof
- keep local art integration strictly local-only and out of sellable packages
