# Corrected input archive: legacy-only Linux Player compatibility smoke

## November 7 native result

Installed Unity **6000.4.0f1** builds the exact corrected archive into a real Linux
x86-64 Player using legacy-only input and **no Input System package dependency**.
The native build exits **0** in **122.0 seconds**. The actual headless Player starts,
advances ten game frames, passes all **three** smoke observations and exits **0**;
total build/run/preservation time is **125.9 seconds**. This is a different input
path and Editor version from the existing
[new-input](input-key-linux-player-2026-11-07.md) and
[Both-mode](input-key-both-input-player-2026-11-07.md) Player checks.

Exact archive SHA-256 remains
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
No product source, archive or buyer configuration changed. New unshipped QA sources
are `qa/LegacyPlayerSmoke/LegacyInputPlayerBuilder.cs` and
`LegacyInputPlayerProbe.cs`, with a scoped README. Both are actually compiled by
this run; the runtime probe is then executed in the built Player.

The builder makes a fresh private scene containing only the smoke component and
requires BuildReport.Succeeded plus an actual Linux binary. The runtime probe
requires legacy enabled / new input disabled, waits ten actual game frames, and
checks that the packaged input source reports neither held nor new-press state
for KeyCode.None. It records the exact engine header and three distinct passes:
legacy-only startup, unbound-key held false, unbound-key edge false. Acceptance
requires exactly those lines, no failure marker, successful native build and
Player exit zero, plus all preservation checks. A binary or receipt alone cannot
prove completion.

## Actual configuration and evidence

Both manifest.json and packages-lock.json omit com.unity.inputsystem. The copied
ProjectSettings retain activeInputHandler **0**. The actual non-Editor Player
`Assembly-CSharp.rsp` includes `ENABLE_LEGACY_INPUT_MANAGER`, excludes
`ENABLE_INPUT_SYSTEM` and excludes `UNITY_EDITOR`. Its observed hash is verified
unchanged after execution. The C# fixtures also fail on other input compile paths;
thus the result is not inferred solely from a setting or package-list snapshot.

Private base:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
The retained create-only orchestration is `run_legacy_player_20261107_1055.py`,
derived from the already verified Player driver with explicit legacy template,
6.4 Editor, fixture sources and strict legacy receipt expectations. Its hash is in
`LEGACY_PLAYER_FINAL_AUDIT_20261107_1055.json`. It reuses the matching successful
actual native import from `legacy-compat-20261107` only after checking the exact
archive and all 55 packaged scripts. It does not repeat import or install a new
package. Execution uses a bounded owned broker job and separate build/Player
subprocesses; no graphical terms interaction occurs.

New output `player-legacy-input-20261107-1055` retains the private project, staged
protected baseline, launch/source hashes, BUILD_RESULT.json, RESULT.json, actual
build.log and player.log, native-player-result.txt, actual compiler evidence in
legacy-only-player-compiler.json and the full Player distribution/file-hash map.
The final audit stores native outcomes, compiler proof, raw evidence hashes and
owned process state. Broker credentials remain private and outside Git.

All **552** staged protected files remain unchanged, with all **55** packaged C#
paths exact. `LEGACY_PLAYER_FULL_IDENTITY_20261107_1055.json` independently verifies
all **161** archive asset paths, **133** payloads and **161** GUID identities. All
**550** source-template hashes match the earlier snapshot. All **13** original
Unity worktree heads/statuses and **21** original dirty-file hashes remain
unchanged. The archive hash is unchanged. The new job exited with zero remaining
cgroup processes. The staged fixtures match canonical source byte-for-byte.

Both native logs have zero scanned `error CS`, `Exception:`, CS0618, CS0612,
UAC0005, GTK-critical and GLib-critical markers. This is a scoped log scan, not an
unqualified clean/complete commercial certification. Separately, 21 existing suite
and ten archive-identity Python methods pass, the private driver compiles, and
tracked changes pass whitespace checks. Those Python checks are not extra native
Player observations.

## Limits and release decision

This is **legacy-only Player compile/startup and unbound-key smoke coverage**.
There is no injected or physical key press, held/edge transition, pointer test,
full Player healing/save workflow, rendered frame, URP result or independent buyer
study. The already native new-input/Both-mode transition tests do not substitute
for actual legacy key-transition evidence. Normal graphical software terms and
earlier resource-denied URP operations were not retried or bypassed.

Commercial release remains **NO-GO** pending broader input/gameplay/platform
coverage, rendered usability, source/installer reconciliation, dependency-aware
migration/uninstall and independent buyer/comparator validation. No seller-source
merge, marketplace publication, purchase, outreach, account change or reminder
occurred.
