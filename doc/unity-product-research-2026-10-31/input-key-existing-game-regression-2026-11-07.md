# Corrected input archive: existing-game workflow, November 7

## Exact scope

This continuation closes a Built-in same-process gameplay gap for the input-key
corrected archive itself, rather than transferring earlier lifetime-archive
results. No product source, archive, installer or private test code changed.

Candidate SHA-256:
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
See the [input fix](input-key-validation-2026-11-07.md) and the separately completed
[56-case module runs](input-key-module-regression-2026-11-07.md).

## Fresh actual native outcomes

Both fresh project copies ran installed Unity 6000.6.7f1 with Input System 1.20.1,
activeInputHandler 1, settled startup and rebuilt copied script caches. Each used
`run_native_workflow.py` in `qa/ExistingGameWorkflow`, scenario wired and explicit
`--expected-render-pipeline builtin`, once per domain-reload condition.

| Private run | Native gameplay contract | Effective pipeline observations | Exit | Duration | Protected files |
| --- | --- | --- | --- | --- | --- |
| Domain reload on | 16/16 PASS | Built-in before authoring, during Play, after Play | 0 | 112.9 seconds | 142 |
| Domain reload off | 16/16 PASS | Built-in before authoring, during Play, after Play | 0 | 91.1 seconds | 142 |

The representative game is self-authored QA, not an independent purchaser project.
The checks author an independent original scene and a separate integrated scene,
use the actual packaged selected-object installer, save/reopen the integrated
scene, queue native keyboard events through the existing input action, and observe
authoritative health/stamina, HUD data binding, cooldown, disable/enable lifetime,
a real JSON save/load roundtrip and detach of only the optional runner/input
connection. Original scene bytes remain unchanged; detached existing input and
health remain usable. The gate requires every distinct observation and native
exit zero, not merely a count of PASS log lines.

Both explicit native pipeline receipts contain the three ordered Edit/Play/Edit
phases, empty selected/default/quality-override asset identities and Null graphics.
This proves effective Built-in selection and headless functional compatibility,
not rendered frames, materials or shader appearance.

The driver reused the existing successful actual native import receipt from
`green-play/IMPORT_RESULT.json` after checking all 55 exact packaged C# sources.
It did not repeat package import or rebuild an archive. It copied the template
into distinct private projects, changed reload flags only there, preserved the
copied script databases separately, and staged canonical current workflow fixtures.
The complete preexisting nonvendor baseline and staged-probe baseline both retain
all 142 protected files without changes. The independent full-archive verifier
passes all 161 asset paths, 133 payloads and 161 GUID identities in each test project.

## Evidence and preservation

Private base:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
Fresh run directories are `workflow-builtin-on-20261107-0455` and
`workflow-builtin-off-20261107-0455`. They retain raw native-result.txt, native
pipeline JSON, unity.log, launch.json, both protected baselines, RESULT.json,
private projects and preserved copied caches. No failed/uncertain output was reused
or deleted. The current probe files were independently compared byte-for-byte
against canonical source in both projects.

`WORKFLOW_FINAL_AUDIT_20261107_0455.json` records exact native results, independent
full-archive identities, raw evidence hashes, canonical fixture hashes, log markers,
owned process state and preservation. `WORKFLOW_ON_FULL_IDENTITY_20261107_0455.json`
and `WORKFLOW_OFF_FULL_IDENTITY_20261107_0455.json` retain the identity reports.
`WORKFLOW_TEMPLATE_BEFORE_20261107_0455.json` matches the original template after
both runs. All 13 earlier Unity worktree heads/statuses and all 21 original dirty
file hashes remain unchanged. The archive hash is unchanged. Both new bounded,
CPU/memory-capped broker jobs exited with zero remaining cgroup processes. No
other agent's workload was stopped or source overwritten.

Each native log has zero `error CS`, `Exception:`, CS0618 or CS0612 markers.
Each retains five private CleanEditorControl UAC0005 analyzer warnings and two
headless GTK teardown critical messages. These remain disclosed rather than
claiming warning-free Editor acceptance. Separately, 13 workflow receipt tests,
eight pipeline receipt tests and ten full-archive identity tests pass in Python;
these 31 methods are not additional native Unity gameplay cases.

## Remaining release gates

This evidence does not certify physical keyboard presses, rendered HUD/Inspector
interaction, Player builds, fresh application-process restore, actual legacy-input
gameplay, URP or independent buyer value. Save/load here occurs within the running
scene; previous cold-process and URP results belong to their own archive checksums.
Earlier denied URP operations and the normal graphical software-terms gate were
not retried, rerouted or bypassed.

Commercial release remains **NO-GO** pending changed-archive URP/Player/cold-process
coverage, physical/rendered Editor usability, installer/source reconciliation,
dependency-aware migration/uninstall and independent buyer/comparator validation.
No seller-worktree merge, publication, purchase, outreach, external account change
or reminder occurred.
