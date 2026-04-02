# Package Launch Strategy

## First wave
- `com.hpr.eventbus` — HPR Typed Event Bus — $9.99 — Clear standalone value, isolated API surface, strong reusable fit across gameplay and tool layers, and easy screenshotable story once event flow is visualized.
- `com.hpr.composition` — HPR Composition Root — $9.99 — Architecturally clean, independently useful, validated headless, and strong companion product for teams building modular Unity runtime composition.
- `com.hpr.save` — HPR Save Snapshots — $9.99 — Narrow, understandable product scope: snapshot contracts and restore flow that buyers can integrate into their own persistence layer without framework lock-in.
- `com.hpr.stats` — HPR Stats & Damage — $14.99 — Clear gameplay-system value, real runtime behavior, validated bugs already fixed, and an easy buyer story around health, stamina, damage, and healing.
- `com.hpr.inventory` — HPR Inventory Core — $14.99 — Clear reusable runtime value with actual quantity tracking, sample items, and straightforward integration into pickups, save systems, and gameplay logic.
- `com.hpr.interaction` — HPR Interaction Toolkit — $14.99 — Buyer-facing value is easy to understand from demos and screenshots: sensors, pickups, keys, and doors with explicit bindings and package-safe runtime boundaries.
- `com.hpr.abilities` — HPR Ability Runtime — $19.99 — The package already reads like a real product: ability assets, effect assets, cooldowns, unlock tracking, and visible runtime behavior backed by clean validations.

## Second wave
- `com.hpr.weapons` — HPR Weapon Data Kit — $9.99 — Technically clean, but the current value proposition is data-definition heavy and weaker than the first-wave systems unless paired with a stronger runtime controller or bundle story.
- `com.hpr.ai` — HPR Enemy Archetype Data — $9.99 — The package is technically solid, but buyer-facing value is narrower because it defines AI archetype data without a stronger runtime behavior/controller story.

## Bundle-only / support packages
- `com.hpr.world` — HPR World Asset Registry — Useful supporting code, but too thin to lead as a standalone paid Asset Store listing today; best packaged inside a broader world-authoring or gameplay-data bundle.

## Upsell and cross-sell recommendations
- `com.hpr.eventbus` -> com.hpr.composition, com.hpr.stats, com.hpr.abilities, com.hpr.interaction
- `com.hpr.composition` -> com.hpr.eventbus, com.hpr.save, com.hpr.stats, com.hpr.abilities
- `com.hpr.save` -> com.hpr.stats, com.hpr.inventory, com.hpr.interaction, com.hpr.abilities
- `com.hpr.stats` -> com.hpr.abilities, com.hpr.eventbus, com.hpr.save, com.hpr.interaction
- `com.hpr.inventory` -> com.hpr.interaction, com.hpr.save, com.hpr.abilities
- `com.hpr.interaction` -> com.hpr.inventory, com.hpr.stats, com.hpr.abilities, com.hpr.eventbus
- `com.hpr.abilities` -> com.hpr.stats, com.hpr.eventbus, com.hpr.save, com.hpr.interaction
- `com.hpr.weapons` -> com.hpr.stats, com.hpr.ai, com.hpr.world
- `com.hpr.ai` -> com.hpr.weapons, com.hpr.stats, com.hpr.world
- `com.hpr.world` -> com.hpr.ai, com.hpr.weapons

## Naming recommendations
- `com.hpr.eventbus` — Use 'HPR Typed Event Bus' as the storefront title; keep the package id unchanged.
- `com.hpr.composition` — Use 'HPR Composition Root' as the storefront title.
- `com.hpr.save` — Use 'HPR Save Snapshots' as the storefront title for clearer buyer-facing value.
- `com.hpr.stats` — Use 'HPR Stats & Damage' as the storefront title.
- `com.hpr.inventory` — Use 'HPR Inventory Core' as the storefront title.
- `com.hpr.interaction` — Use 'HPR Interaction Toolkit' as the storefront title.
- `com.hpr.abilities` — Use 'HPR Ability Runtime' as the storefront title.
- `com.hpr.weapons` — Use 'HPR Weapon Data Kit' as the storefront title.
- `com.hpr.ai` — Use 'HPR Enemy Archetype Data' as the storefront title.
- `com.hpr.world` — Use 'HPR World Asset Registry' if it is ever surfaced directly.

## Free vs paid recommendation
- `com.hpr.eventbus` — Paid low-ticket first-wave package.
- `com.hpr.composition` — Paid low-ticket first-wave package.
- `com.hpr.save` — Paid low-ticket first-wave package.
- `com.hpr.stats` — Paid first-wave package.
- `com.hpr.inventory` — Paid first-wave package.
- `com.hpr.interaction` — Paid first-wave package.
- `com.hpr.abilities` — Paid first-wave package.
- `com.hpr.weapons` — Paid second-wave package or bundle component.
- `com.hpr.ai` — Paid second-wave package or bundle component.
- `com.hpr.world` — Bundle-only; do not prioritize a standalone paid upload in wave one.
