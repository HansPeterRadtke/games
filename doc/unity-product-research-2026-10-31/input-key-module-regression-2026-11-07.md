# Corrected input archive: native module regressions, November 7

## Question and exact candidate

The previous input-key fix had actual 12-case new-input Play evidence and a fresh
17-case legacy-input configuration run, but broader module NUnit results belonged
to the earlier lifetime archive. This bounded continuation runs the existing
canonical module tests against the corrected input archive itself. No product,
installer, probe or archive bytes were changed in this continuation.

Candidate SHA-256:
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
The [input-key recovery report](input-key-validation-2026-11-07.md) records its
single-payload fix, previous native red/green controls and private package origin.

## Fresh actual Editor executions

| Installed Editor | Input configuration | Bundled test framework | Native result | Duration | Protected baseline |
| --- | --- | --- | --- | --- | --- |
| 6000.6.7f1 | activeInputHandler 1, Input System 1.20.1 | 1.8.0 | 56/56 PASS, exit 0 | 95.2 seconds | 475 files |
| 6000.4.0f1 | activeInputHandler 0, no Input System dependency | 1.6.0 | 56/56 PASS, exit 0 | 69.6 seconds | 590 files |

Both runs select the ten actual EditMode assemblies through the installed Unity
Test Framework. Each covers Abilities 25, AI 6, Composition 4, Eventbus 4,
Interaction 3, Inventory 4, Save 2, Stats 2, Weapons 5 and World 1. XML validation
requires distinct test identities, all assemblies, consistent root counts, no
failed/skipped/inconclusive results and native exit zero. The existing 13 native
receipt regression methods and five input receipt methods also pass separately;
those Python checks are not additional native Unity cases.

The unchanged create-only driver is
`unity/tools/release/gameplay_suite/qa/NativeEditMode/run_native_editmode.py`.
It uses explicit archive checksum, native import receipt, installed Editor and
fresh private output arguments. The 6.6 template is `green-play/project`, and the
6.4 template is `legacy-compat-20261107/project` under the input-key private task
runtime. Their existing successful native import receipts select this exact
candidate. Each run copies its source template, rebuilds copied script databases,
stages canonical module tests with their existing asmdefs, and uses only the
installed Editor's bundled Test Framework/NUnit. The test framework dependency is
intentionally added only to each private copy before its protected baseline.

There are no modified protected original files in either run. The only permitted
post-baseline update is copied `Packages/packages-lock.json`, and both resolutions
match the strictly planned bundled versions, dependencies and depths while
retaining unrelated dependencies. All 55 product scripts match the archive exactly.
The independent read-only full identity checker also passes all 161 asset paths,
133 payloads and 161 GUID identities in each actual native test project.

## Preserved evidence and ownership

Private runtime:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
New output directories are `module-nunit66-20261107-0255` and
`module-nunit64-20261107-0255`. Each retains RESULT.json, raw test-results.xml,
launch/source hashes, protected-before.json, native unity.log and the private
project. Broker control receipts remain private and are not committed.

`MODULE_FINAL_AUDIT_20261107_0255.json` records both native results, independent
full archive identity, evidence hashes, log markers, ownership and preservation.
`MODULE66_FULL_IDENTITY_20261107_0255.json` and
`MODULE64_FULL_IDENTITY_20261107_0255.json` are the full identity receipts.
`MODULE_TEMPLATES_BEFORE_20261107_0255.json` captures both source-template snapshots;
they compare byte-identical after both runs. The historically protected template
files also retain their earlier hashes (434 new-input, 188 legacy-input files).
All 13 earlier Unity worktree heads/statuses and all 21 original dirty-file hashes
remain unchanged from the earlier recovery snapshot. The tested archive hash is
unchanged. Both newly admitted bounded broker jobs exited with zero remaining
cgroup processes. No active owner workload was interrupted.

Both native logs have zero `error CS`, `Exception:`, CS0618 or CS0612 markers.
The 6.6 log retains five private CleanEditorControl UAC0005 analyzer warnings;
the 6.4 log has none. Both have two headless GTK teardown critical messages.
This is not a warning-free graphical Editor claim.

## Remaining gates

These are headless module API regressions in Built-in projects, not new physical
keyboard events, rendered scenes, Inspector interaction, Player builds, URP or
exhaustive input-stack/layout certification. The earlier 12-case input Play run
was not repeated or relabeled as part of these 56-case module runs. The earlier
resource-denied URP operations and graphical software-terms gate remain untouched.

Commercial release remains **NO-GO**: changed-archive pipeline/workflow and Player
coverage, physical/rendered Editor acceptance, installer/source reconciliation,
dependency-aware migration/uninstall and independent buyer/comparator validation
remain open. No marketplace publication, outreach, purchase, reminder, source
merge into the dirty seller worktree or external account change occurred.
