# Modularization Status

## Frozen first-release package set
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.world`

## Excluded packages
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.input`
- `com.hpr.ui`
- `com.hpr.bootstrap`
- `com.hpr.fpsdemo`

## Current truth
- the frozen first-release set validated successfully in fresh clean-project imports during the current run
- the internal game still builds and its smoke path completes during the current run
- the release tooling now emits in-repo proof logs for audits, build, and smoke instead of pointing outside the repo
- the selected packages no longer contain runtime parent/child lookup shortcuts in their runtime code
