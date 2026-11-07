# Corrected input archive: native Linux Player input acceptance

## November 7 measured result

The exact input-corrected archive now has a successful actual Linux x86-64 Player
build and execution with installed Unity **6000.6.7f1** and Input System **1.20.1**.
The native Editor build exits **0**, produces the binary, and emits the marker
only after the existing builder checks BuildReport.Succeeded. The resulting real
Player exits **0** after the existing private MonoBehaviour.Update probe passes
all four named input checks. Build duration is **189.4 seconds**; total build,
Player execution and final source checks take **194.1 seconds**.

Exact tested archive SHA-256:
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
This is new archive-specific Player evidence, separate from its
[Editor input-key regression](input-key-validation-2026-11-07.md),
[module tests](input-key-module-regression-2026-11-07.md),
[existing-game workflows](input-key-existing-game-regression-2026-11-07.md) and
[fresh Editor-process save test](input-key-cold-restart-2026-11-07.md).
No product, archive, builder or probe source changed in this continuation.

## What actually ran

The existing canonical private `qa/HprSuiteNewInputStandaloneBuilder.cs` creates a
new empty scene containing `qa/HprSuiteInputGameplayProbe.cs` and builds it with
BuildPipeline.BuildPlayer for StandaloneLinux64. Both fixture files are staged
byte-identical in a fresh private project copy, with the builder under Editor and
the runtime probe outside Editor. No source template is changed. The successful
prior actual native import is reused only after checking all 55 exact archive C#
scripts and the explicit package checksum; package import is not repeated.

The runtime probe queues KeyboardState events during actual game Update ticks
using dynamic input updates. It then reads the actual packaged input adapter:
W, LeftArrow, Alpha1, LeftControl and Keypad1 must all be held; W must report a new
press both through the adapter and raw native keyboard state. After queuing an
empty keyboard state, W must be released and must not report a fresh press.
The raw Player log confirms press, justPressed, native and deviceUpdated are true,
then records successful completion. Acceptance requires exactly the engine version
header and all four distinct expected PASS lines, no failure receipt, and Player
exit zero. A build binary alone is insufficient.

The artifact is independently identified as a Linux x86-64 ELF executable. The
Player runs with `-batchmode -nographics`, a separate actual process/log and an
explicit private receipt path. This tests native game-loop input behavior, not
physical OS input, keyboard layouts, rendering or a displayed game window.
Undefined-key suppression was tested in the earlier Editor probe, not added to
this unchanged Player probe; no exhaustive Player key-mapping claim is made.

## Reproduction, evidence and preservation

Private base:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
The create-only orchestration is retained as `run_player_20261107_0655.py` outside
Git; its hash is in `PLAYER_FINAL_AUDIT_20261107_0655.json`. It runs through an owned
bounded broker job with CPU/memory caps and separate native build/Player timeouts.
It uses the existing `green-play/project` template and successful native import
receipt. The untouched canonical C# helpers remain the reproducible test sources.

New output `player-input-20261107-0655` retains the private project, protected-file
baseline, launch/source hashes, BUILD_RESULT.json, RESULT.json, build.log,
player-launch.json, player.log, native-player-result.txt and the complete Linux
Player distribution. `player-bundle-sha256.json` preserves every built file hash.
The final audit records all evidence hashes and exact binary hash; private broker
control credentials are not committed.

All **437** staged protected files remain unchanged. All **55** packaged C# sources
remain exact. The independent full-archive identity report
`PLAYER_FULL_IDENTITY_20261107_0655.json` passes all **161** asset paths, **133**
payloads and **161** GUID identities after the native build/run. The original
source template's **435** file hashes match its earlier saved snapshot. All
**13** earlier Unity worktree heads/statuses and **21** dirty-file hashes remain
unchanged. The archive hash is unchanged. The owned job exited with zero cgroup
processes. Original files, prior outcomes and other workloads were preserved.

Both build and Player logs have zero `error CS`, `Exception:`, CS0618, CS0612,
GTK-critical or GLib-critical markers. The build retains five private
CleanEditorControl UAC0005 analyzer warnings; the Player has none of that marker.
This does not claim an entirely warning-free production package. The five input
receipt and ten full-identity Python regression methods also pass separately;
they are not fifteen additional Player observations. The private Python driver
passes syntax compilation.

## Remaining commercial gates

This closes one bounded **Linux/new-input game-loop Player** gap. It does not
certify Player healing/save/restart integration, legacy/both-input stacks, other
platforms, pointer/gamepad input, rendered Built-in/URP output, Inspector usability
or independent purchaser value. Earlier denied URP operations and graphical
software-terms interaction were not retried or bypassed. No broader Player matrix
or previously untested archive may inherit this result.

Commercial release remains **NO-GO** pending those compatibility/usability gates,
installer/source reconciliation, dependency-aware migration/uninstall and real
buyer/comparator validation. No seller-source merge, publisher action, purchase,
outreach, external account change or reminder occurred.
