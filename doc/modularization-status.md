# Modularization Status

## Release-ready package set
The current release-ready set is:
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

## What changed since the earlier release set
The release set is no longer limited to low-level infrastructure. The package line now includes:
- gameplay-adjacent reusable runtime (`save`, `stats`, `inventory`, `interaction`, `abilities`)
- authored reusable data products (`weapons`, `ai`, `world`)

## What remains internal
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.input`
- `com.hpr.ui`
- `com.hpr.bootstrap`
- `com.hpr.fpsdemo`

## Current extraction target order
1. continue shrinking `com.hpr.fpsdemo`
2. decide whether `com.hpr.input` can be productized cleanly
3. separate generic UI widgets from game-specific UI flow
4. either productize or keep internal the remaining support packages based on actual dependency cleanliness
