# Duplicate Unity ability IDs: buyer-package regression and correction — 13 November 2026

## Defect

Two separate `AbilityData` assets with the same gameplay `Id` could occupy Ward and Heal slots. A slot activation looked up the ability again by that shared ID; the later definition overwrote the earlier one in the dictionary. In the previous *real Unity Editor* negative control, the Ward slot consumed **25 stamina**, not Ward's configured five, and healed the player by twenty. The previous QA branch retains the historical negative test and original XML, not a re-created negative claim.

## Change

The runtime keeps the first definition for lookup, marks the ID as conflicting when a different definition uses it, blocks activation by ID or any conflicting slot, and labels conflicting entries `DUPLICATE ID` rather than `READY`. Unrelated slots remain usable. Refreshing bindings after correcting the ID restores normal behavior. The module README, buyer Quickstart and native test count/acceptance contract were updated. The new NUnit cases test API-configured and Inspector-serialized loadouts, refusal without resource spending, unchanged cooldowns, independent slots, save/restore, visible HUD status and reconfiguration. No asset GUID, sample scene, external buyer file or publisher account was intentionally changed.

## Verified on patched Unity

A new clean repository worktree based on the current commercial branch was used. Its security-patched Unity `6000.6.8f1` export completed and `validate_release.py` accepted the package. A fresh Unity project then imported the actual archive successfully, and `unity_imported_archive_identity.py` matched every archived source/meta/GUID. Upgrade validation compared it to the previous package: **161 out of 161 GUIDs unchanged**.

The broker-managed native Unity EditMode runner used the exact imported package and ran **60 of 60 cases across all ten test assemblies**, with zero failed, skipped or inconclusive cases, native Editor exit zero and exact archive identity `PASS`. Both duplicate-ID cases passed. The NUnit runner found **no modified original project files across 358 protected files**, and the 55 packaged C# scripts matched the archive. The canonical source Python suite passed **386 tests**. This proves the packaged runtime contracts, not rendered usability or marketplace approval.

Private runtime evidence on Nitro, preserved outside Git:

- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/build.log`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/release/hpr-gameplay-systems-suite-candidate.unitypackage`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/upgrade-guids.json`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/import-receipt.json`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/import-identity.json`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/native-qa/RESULT.json`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/native-qa/test-results.xml`
- `/data/var/marketplace-account-setup/hpr-ability-id-verified-20261113/source-suite.log`

Reproduce the native QA with the private runner under `unity/tools/release/gameplay_suite/qa/NativeEditMode`, passing the above existing exact archive, import receipt and imported project template, a new output path, and the installed patched Unity Editor. Do not replay into an existing output directory.

## Remaining

This run does not certify manual mouse-driven Inspector usability, URP visual presentation, Player-build compatibility, independent buyer validation or Unity Asset Store publication. The original commercial checkout's pre-existing fourteen local changes were preserved throughout.
