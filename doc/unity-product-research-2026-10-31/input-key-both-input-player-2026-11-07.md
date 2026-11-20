# Corrected input archive: Both-mode Linux Player regression

## November 7 measured result

The exact corrected archive now passes the bounded Linux Player input probe with
**Both** legacy and new input backends enabled. Installed Unity **6000.6.7f1** and
Input System **1.20.1** complete the actual StandaloneLinux64 build with native
Editor exit **0** in **249.4 seconds**. The real headless Player passes all four
named game-update checks and exits **0**. Total build/run/preservation time is
**255.4 seconds**. This is a distinct configuration from the earlier
[new-input-only Player run](input-key-linux-player-2026-11-07.md).

Archive SHA-256 remains
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
No product code or archive payload changed. The only tracked code edit generalizes
the private probe receipt from `new_input_only_real_game_update=PASS` to
`new_input_adapter_real_game_update=PASS`: it describes the API being observed,
without incorrectly asserting that the legacy backend is disabled. Existing
native receipts and the prior Player distribution are preserved as historical
evidence; they are not rewritten to the new label.

## Configuration is independently evidenced

The new create-only private project copy explicitly sets activeInputHandler to
**2** before its protected baseline and first Editor launch. The source template
retains value **1**. The actual non-Editor Player compilation response
`Library/Bee/artifacts/2400b0aP.dag/Assembly-CSharp.rsp` includes both
`ENABLE_INPUT_SYSTEM` and `ENABLE_LEGACY_INPUT_MANAGER`, and excludes `UNITY_EDITOR`.
Its hash and observations are saved separately, then verified unchanged after
execution. Thus a setting value or an Editor-only compile does not substitute for
actual Both-mode Player compilation.

The packaged adapter's conditional compilation selects the new-input branch when
both symbols exist. The unchanged probe behavior exercises that public adapter in
real MonoBehaviour.Update ticks: W, LeftArrow, Alpha1, LeftControl and Keypad1 are
held, W has a new-press edge in both adapter and raw native device state, and W is
released without a new edge after the empty keyboard event. The actual Player
records all four distinct expected PASS lines plus the correct engine header.
Acceptance requires those exact lines, no failure receipt and native Player exit
zero, in addition to a successful native BuildReport and existing binary.

This proves the new adapter path works with Both enabled. It does **not** inject
legacy OS key events or separately prove Input.GetKey behavior, mixed game code's
subscription semantics, arbitrary gamepad/pointer input or all key layouts.

## Reproduction and preserved evidence

Private base:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
`run_both_input_player_20261107_0955.py` is the retained create-only orchestration,
with a hash in `BOTH_PLAYER_FINAL_AUDIT_20261107_0955.json`. It derives from the
previous private Player driver, selecting a fresh output, the changed private
receipt label and explicit copied-project Both setting. The existing native-import
receipt and exact 55 archived C# sources are verified before reuse. It does not
repeat package import, change downloaded dependencies or rewrite a source template.
The unchanged canonical builder and current one-line-updated runtime probe are
staged and independently compared against source after execution. Native build
and Player execution have separate bounded timeouts under an owned broker job.

Fresh output `player-both-input-20261107-0955` retains the private project, protected
baseline, launch/source hashes, native build and Player logs, BUILD_RESULT.json,
RESULT.json, native-player-result.txt, the distribution and every distribution
file hash in player-bundle-sha256.json. `both-input-player-compiler.json` retains
the actual Player compiler response hash and both-backend observations.
`BOTH_PLAYER_FULL_IDENTITY_20261107_0955.json` verifies all **161** archive asset
paths, **133** payloads and **161** GUID identities in the built project.

The final audit records all evidence hashes, exact native outcomes, configuration,
compiler proof and ownership. All **437** staged protected files remain unchanged;
all **55** packaged scripts remain exact. All **435** source-template file hashes
match the earlier snapshot. All **13** original Unity worktree heads/statuses and
**21** original dirty-file hashes are unchanged. Every file hash in the previous
new-input-only Player distribution also remains unchanged. The tested archive is
unchanged. The new owned job exited with zero cgroup processes. Private broker
control credentials remain outside Git.

Build and Player logs have zero `error CS`, `Exception:`, CS0618, CS0612, GTK-critical
or GLib-critical markers. Five inherited private CleanEditorControl UAC0005 analyzer
warnings occur only in the build log. The 21 suite and ten full-archive identity
Python methods pass separately; these are not extra native Player observations.
The private orchestration passes Python syntax compilation and tracked edits pass
whitespace checks.

## Remaining limits

The Player runs with `-batchmode -nographics`; no rendered frames or physical input
are claimed. No full Player healing/save/restart workflow, legacy-only Player,
other platform, URP or human Inspector usability follows from this probe. Earlier
denied URP operations and the normal graphical software-terms gate were not retried
or bypassed. Commercial release remains **NO-GO** pending the wider compatibility
matrix, rendered usability, source/installer reconciliation, dependency-aware
migration/uninstall and independent buyer/comparator validation. No seller-source
merge, marketplace publication, purchase, outreach, account change or reminder
occurred.
