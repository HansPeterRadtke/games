# Games Repo Documentation

This folder is the handoff and release-status entrypoint for the Unity package workspace and FPS composition project.

Read in this order:
1. `release-candidate-status.md` - which packages are actually sale-ready right now
2. `current-state.md` - repository layout and current architectural truth
3. `package-validation.md` - authoritative validation entrypoints and proof logs
4. `package-dependency-map.md` - package boundaries and remaining internal violations
5. `dependency-audit-phase1.md` - generated forbidden-reference audit
6. `release-audit.md` - generated sellable-package release audit
7. `workflows.md` - build, smoke, package, and local-asset workflows
8. `handoff.md` - takeover summary for the next developer/bot
9. `local-assets.md` - real local Asset Store inventory and current integration state
10. `report.txt` - compact technical checkpoint summary

Current sale-ready package set:
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`

Key rule for this repo:
- imported Unity / Asset Store data stays local-only and must not be committed
- gameplay code, tooling, package docs, release audits, and reproducible setup scripts must be committed
