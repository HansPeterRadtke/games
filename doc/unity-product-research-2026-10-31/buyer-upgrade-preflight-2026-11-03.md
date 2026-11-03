# HPR customer-game update: read-only source and dependency preflight

November 3, 2026. Independent QA only. This is not a new Unity Editor feature, an approved marketplace release, or an automatic upgrade.

## Buyer problem and risk

A customer using HPR abilities in an existing scene can have edited HPR source, serialized HPR MonoBehaviour GUIDs, custom source code using HPR interfaces, assembly-definition references, embedded package dependencies and unrelated unsaved or modified project files. Re-importing even an archive with all original vendor GUIDs may overwrite an edited HPR script, disturb user-owned files, or leave a dependent game uncompilable.

The previous handover proved that the latest private HPR package has one hundred sixty-one original stable GUIDs, but that source identity alone does not prove a safe customer upgrade.

## Source-only conservative preflight

The new independent module at unity/tools/release/gameplay_suite/qa/unity_safe_upgrade_preview.py combines these existing verified parts without modifying customer files:

1. SHA-256 pin for the old, actually installed archive and the exact proposed new private archive.
2. Full old vendor asset payload and GUID identity check against the current buyer game, before and after the audit.
3. Old/new archive GUID and pathname comparison, with explicit review for removed/moved paths even if their GUID is stable.
4. Hashing of all customer-owned Assets, ProjectSettings and Packages, including customer-owned embedded package C-sharp, .asmdef, .asmref, package.json and .meta bytes; a second scan catches changes during preflight.
5. Read-only dependency review for serialized customer scenes/assets, C-sharp uses, package manifests, customer embedded package manifests, Unity Assembly Definition Reference assets, and uninspectable files.
6. Source GUID collision audit covering both Assets and embedded customer Packages, with fail-closed handling of malformed metadata, multiple GUID fields, duplicate customer GUIDs, invalid UTF-8, and file reads exceeding the bounded metadata limit.

The result is a review decision. Every result explicitly reports automatic_upgrade_authorized=false and deletion_permitted=false, including when all source-level preconditions pass. The module cannot invoke the Unity Editor, import a package, rewrite source or delete assets.

The new unit contracts were developed with failing tests first for missing embedded customer protection, package GUID collisions, a foreign file changed mid-scan, moved vendor paths and silent source updates. Negative and positive test outputs are retained separately.

## Genuine archive and existing-customer checks

The exact earlier frozen HPR Unity package and the newer reviewed private candidate were used as actual input archives, with their SHA-256 pins. On the preserved previous populated customer project, the preflight verified all one hundred sixty-one old HPR vendor asset/GUID identities and sixty-three original customer file hashes. It reported ten HPR consumer dependencies and correctly required review instead of authorizing an update.

A second disposable, populated customer project included an editable embedded package. The preflight verified sixty-seven customer files and thirteen HPR dependencies, including embedded assembly and package-manifest dependencies, without altering any input.

Other separately preserved disposable tests changed a vendor HPR script and introduced a customer embedded-package .meta with an exact existing HPR vendor GUID. The preflight refused both upgrades. A test simulating the creation of a customer C-sharp modification during the read-only dependency scan also required review. The strict metadata checks were subsequently rerun on both preserved projects without false collisions.

All source-to-source comparisons and private JSON receipts remain under the owner's protected marketplace-account-setup QA folders. The original customer project, original private candidate, owner commercial worktree and concurrently dirty QA branches were not edited.

## Still unavailable and commercial decision

The real Unity six point six Editor import, Build-in/URP and old/new Input System compilation, scene persistence, custom controller Play mode, domain reload disabled, intentional interrupted-copy failure, real Inspector UI, professional key images, safe full dependent-game uninstall, and independent experienced-developer competitor benchmark are NOT complete.

Nitro's owner resource broker remains active but has not started Unity because CPU pressure is far above its configured safe admission limit. Do not run an unbrokered heavyweight Unity process in parallel with other owner work.

Commercial decision remains NO-GO. There was no public upload, publisher-account modification, purchase, trading effect, data deletion, or false buyer testimonial.
