# Corrected input archive: fresh-process save/cooldown regression

## November 7 actual native result

The corrected input archive passes all **15 distinct cold-process observations**
in installed Unity **6000.6.7f1**, Input System **1.20.1**, domain reload disabled,
with native exit **0** in **129.1 seconds**. This is fresh archive-specific evidence,
not a transfer of older lifetime-archive results. No product, archive, installer,
probe or driver source changed in this continuation.

Exact archive SHA-256:
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
The source scene and save came from the completed reload-disabled
[existing-game workflow](input-key-existing-game-regression-2026-11-07.md).
The unique newly authored integrated scene was selected by comparing the previous
workflow project against its original template, rather than choosing an arbitrary
historical scene. The existing save contains health 60, stamina 80 and a 30-second
remaining customer-heal cooldown.

A new native Editor process opens the unchanged integrated scene, observes its
serialized baseline, restores existing vitals and the optional packaged ability
snapshot, checks the existing HUD data binding, and queues native input. Cooldown
blocks the first request without charging resources. A malformed snapshot is
rejected while customer state and cooldown remain intact. After about 30.2 game
seconds, cooldown naturally expires; existing input activates once, raising health
to 80, reducing stamina to 60 and updating the HUD. Source save and scene bytes
remain unchanged before and after Play.

The recorded native process ID was independently observed in the actual OS process
list while running, matches cold-process-observation.json, and differs from the
prior workflow's native pipeline receipt. Its save digest also independently
matches the source JSON bytes. This supplements the probe's declared fresh-process
flag with actual process identity and a serialized-baseline check.

## Reproduction and evidence

The unchanged `qa/ExistingGameWorkflow/run_native_workflow.py` runs wired/reload-off
with explicit cold-save-source, cold-source-receipt and cold-scene arguments,
settled startup and fresh copied script caches. It uses a new private project copy,
the installed Editor and exact archive checksum. The successful prior actual native
import is reused only after verifying all 55 packaged C# scripts; package import
and archive construction were not repeated. Execution used an owned, bounded
CPU/memory-capped broker job with no graphical terms interaction.

Private base:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
The new directory `cold-restart-20261107-0555` retains native-cold-result.txt,
cold-process-observation.json, RESULT.json, launch.json, raw unity.log, both
protected baselines, the copied save/project and preserved copied caches.
`COLD_PROCESS_OBSERVED_20261107_0555.json` records the independently seen OS process.
`COLD_SOURCE_BEFORE_20261107_0555.json` records the exact source scene/save selection
and template hashes. `COLD_FINAL_AUDIT_20261107_0555.json` records native outcomes,
source/evidence hashes, process comparison, full archive identity and preservation.
Broker credentials remain private and are not committed.

All 151 preexisting nonvendor/staged protected files survive unchanged, and all 55
packaged scripts match. The separate full archive identity checker verifies all
161 asset paths, 133 payloads and 161 GUID identities in the actual native project;
its receipt is `COLD_FULL_IDENTITY_20261107_0555.json`. All 444 source-template file
hashes, original scene and source/copy save bytes remain identical. All 13 earlier
Unity worktree heads/statuses and 21 original dirty-file hashes remain unchanged.
The archive hash is unchanged. The new owned job exited with zero cgroup processes.

The native log has zero `error CS`, `Exception:`, CS0618 or CS0612 markers. Five
private CleanEditorControl UAC0005 analyzer warnings and two headless GTK teardown
critical messages remain. No warning-free graphical Editor claim is made.
The 13 existing workflow receipt methods (including the cold contract's every
missing observation, failure marker and wrong-exit checks) and ten archive-identity
methods also pass in Python. They are separate from the 15 native observations.

## Limits

This is a fresh **Editor** process using a representative self-authored game and
simulated native keyboard input, not a Player build or independent buyer project.
Cooldown is restored relative to a new game clock, with offline time paused; no
wall-clock expiry policy is claimed. Rendering, physical keyboard behavior,
Inspector interaction, legacy-input gameplay and URP remain unverified here.
Earlier denied URP operations and the normal graphical software-terms gate were
not retried or bypassed. The prior full workflow's Built-in observations do not
become a newly instrumented pipeline observation for this separate cold run.

Commercial release remains **NO-GO** pending changed-archive URP/Player coverage,
physical/rendered usability, installer/source reconciliation, dependency-aware
migration/uninstall and independent buyer/comparator validation. No seller-source
merge, marketplace action, purchase, outreach, account change or reminder occurred.
