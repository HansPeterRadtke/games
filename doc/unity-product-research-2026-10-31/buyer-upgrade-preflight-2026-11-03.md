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

The buyer-file inventory initially excluded every package whose name began with com.hpr. That was a separate false-negative: customer-built packages such as com.hpr.customerbridge could be silently excluded from file hashing, GUID collision checks and the uninstall dependency scan. The revised source restricts vendor exclusions to the ten exact package module names verified against the original frozen HPR archive. The uninstall scanner instead derives exact vendor modules from the archive's actual Modules folder. Unknown similarly prefixed modules are always treated as customer-owned inputs. No customer file is removed from the scanned set based on its prefix alone.

The new unit contracts were developed with failing tests first for missing embedded customer protection, package GUID collisions, a foreign file changed mid-scan, moved vendor paths and silent source updates. Negative and positive test outputs are retained separately.

## Genuine archive and existing-customer checks

The exact earlier frozen HPR Unity package and the newer reviewed private candidate were used as actual input archives, with their SHA-256 pins. On the preserved previous populated customer project, the preflight verified all one hundred sixty-one old HPR vendor asset/GUID identities and sixty-three original customer file hashes. It reported ten HPR consumer dependencies and correctly required review instead of authorizing an update.

A second disposable, populated customer project included an editable embedded package. The preflight verified sixty-seven customer files and thirteen HPR dependencies, including embedded assembly and package-manifest dependencies, without altering any input.

Other separately preserved disposable tests changed a vendor HPR script and introduced a customer embedded-package .meta with an exact existing HPR vendor GUID. The preflight refused both upgrades. A test simulating the creation of a customer C-sharp modification during the read-only dependency scan also required review. The strict metadata checks were subsequently rerun on both preserved projects without false collisions.

All source-to-source comparisons and private JSON receipts remain under the owner's protected marketplace-account-setup QA folders. The original customer project, original private candidate, owner commercial worktree and concurrently dirty QA branches were not edited.

A separate private positive/negative comparison used the actual reviewed HPR package and a newly created customer project containing com.hpr.customerbridge. The previous committed scanner incorrectly reported no customer references, no asset GUID collision and omitted the customer package files from its checksum snapshot. The revised scanner detected a customer assembly reference, C-sharp use, embedded package dependency, exact vendor GUID collision and eight protected customer source files. SHA-256 records confirmed all disposable customer files were unchanged by both scans. The previous committed source was read from Git without changing or resetting any working branch.

## Still unavailable and commercial decision

The real Unity six point six Editor import, Build-in/URP and old/new Input System compilation, scene persistence, custom controller Play mode, domain reload disabled, intentional interrupted-copy failure, real Inspector UI, professional key images, safe full dependent-game uninstall, and independent experienced-developer competitor benchmark are NOT complete.

Nitro's owner resource broker remains active but has not started Unity because CPU pressure is far above its configured safe admission limit. Do not run an unbrokered heavyweight Unity process in parallel with other owner work.

Commercial decision remains NO-GO. There was no public upload, publisher-account modification, purchase, trading effect, data deletion, or false buyer testimonial.

## November 12 archive and upgrade checks

The previous upgrade check accepted both of these modified copies of the integrated archive when supplied their matching SHA-256 hashes. One kept the installer's pathname and GUID but omitted its C# payload. The other added an asset at the same path as the test game's own player script. The current check validates the contents and destinations in the incoming archive before scanning the project. Both copies were rejected and the diagnostics named the affected paths.

The project GUID and dependency scans now recognize Unity's older `./<guid>/pathname` records. A known-good v2 archive and its original import passed a same-version source check with all 151 identities. The immediately preceding commercial archive retained all 160 of its identities in the current 161-asset candidate.

### Historical compatibility

These results compare archived internal builds with the revised package. Every old asset path still exists in the new candidate. A changed GUID means that an existing serialized reference to that ID no longer resolves to the corresponding vendor asset.

| Internal preview | Shared asset paths | Paths with changed GUIDs |
| --- | ---: | ---: |
| v2 through v5 | 151 | 43 |
| v6 through v8 | 156 | 48 |
| v9 and v10 | 160 | 0 |
| v11 | 160 | 52 |
| v12 through v15 | 160 | 0 |

An independently saved copy of the v2 showcase scene contained 23 distinct vendor references. Sixteen of those GUIDs are absent from the candidate, including the raider definition and a material. The corrected preflight identified those references in the copied scene and blocked the upgrade. The v11 showcase contained 21 such references, and the v15 showcase contained none. The buyer quick start now explains how to test a preview upgrade in a project copy and locate missing references before updating a working game.

### Verification of the revised package

Unity 6000.6.8f1 built the private archive from commit `7a07af9f65203f071862f5c750a8bb9d71b57f33` and imported it into a fresh project. All 161 metadata files and GUIDs matched the preceding integrated package. Only the README, quick start and architecture guide changed contents. All 133 payloads matched the exported archive after Play. Thirteen scene bindings resolved, eleven runtime checks passed and all eight native showcase Play checks passed.

All 377 source tests passed. A separate rehearsal with the fourteen pending commercial files passed 379. Applying the preserved commercial patch to the new commit reproduced those fourteen rehearsed files byte for byte.

The revised archive SHA-256 is `d948a746850d4c45bffa4617fc8a704c7b1ed73f5c80865fe5a3bc9cbb3934bb`. The before-and-after command output, historical GUID comparisons, scene references, import and Play receipts are on Nitro in `/data/var/marketplace-account-setup/hpr-upgrade-archive-20261112`. The consolidated result is `verified.json`.
