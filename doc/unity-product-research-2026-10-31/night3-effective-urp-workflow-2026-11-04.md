# November 4 night three: corrected archive, effective URP selection and full workflow

## Verified milestone

The unchanged night-one corrected archive now passes its own actual native Unity
6000.6.7f1 / URP 17.6.0 / Input System 1.20.1 existing-game workflow with domain
reload both disabled and enabled. Earlier URP results covered the older archive;
those were deliberately not reused to certify this four-source corrected candidate.
No product runtime, GUID, buyer archive or original owner source changed this session.

The opt-in private QA observer reads GraphicsSettings.currentRenderPipeline,
GraphicsSettings.defaultRenderPipeline, QualitySettings.renderPipeline and the
current quality level before scene authoring, during Play, and after returning to
Edit mode. It records native engine/process identity, asset type/path/GUID, default
and override paths, graphics device and optional actual pipeline instance. JSON
is read/written across domain reload; no render or quality setting is changed.

The strict driver requires three ordered observations with actual Boolean Play
states, valid effective URP identity, matching default/quality selection and stable
asset/quality identity. It rejects missing, duplicate, changed or wrong-pipeline
records. The option only supports the full wired same-process workflow; cold-save,
configuration-only and shadow scenarios are rejected before project access. Without
the flag, prior observation contracts are preserved and pipeline acceptance is null.

## Actual native results

| Experiment | Native result | Preservation | Duration |
| --- | --- | --- | --- |
| Corrected archive, URP selected, domain reload off | Full 16-check workflow PASS, all three effective-pipeline observations PASS, native exit 0 | 98 existing files survive native import; 101 staged files unchanged; all 55 product scripts exact | 873.0 seconds |
| Same, domain reload on | Full 16-check workflow PASS, all three selection observations PASS, native exit 0 | Same preservation and exact source identity | 862.5 seconds |
| Built-in project deliberately requested as URP | Native full workflow passes all 16 checks, native exit 0; strict overall result FAIL because selected pipeline is Built-in | 71 protected files unchanged; all 55 product scripts exact | 220.0 seconds |

Both positive cases are genuinely new private project copies with separate actual
native imports of the corrected archive. The negative control reuses an earlier
successful actual import of exactly that corrected archive, verifies all 55 scripts,
and does not replay import. All three rebuild copied script databases and use the
previously verified private settled-startup entry point before authoring/Play.

Each positive observation reports UniversalRenderPipelineAsset at
Assets/HprPrivateUrpQA/HprTestUrp.asset, GUID
`69d351b2add1869f89273ee1e72619c7`, quality level 5 with no quality override. The
before/during/after GUIDs independently match that real imported asset's metadata.
The same native validator source bytes match this source branch and the staged
protected-file hashes. Pipeline settings/assets and original customer files remain
byte-identical throughout each import/workflow phase.

The negative control is specifically useful: compilation, real input, authoritative
health/stamina, HUD binding, cooldown, save/restore, subscription lifecycle and
optional-feature detach all complete successfully. Only the requested URP identity
is absent. Its overall FAIL is retained; it is not counted as a product pass or
misrepresented as a compiler/engine failure. The native Built-in receipt separately
satisfies the Built-in selection contract. A successful gameplay test alone cannot
certify the requested pipeline.

## Evidence boundaries and technical conditions

All native devices are Null; every actual RenderPipeline instance field is empty.
This proves **effective asset selection plus headless functional compatibility**,
not rendered URP frames, shader/material appearance, physical input, external buyer
acceptance, normal graphical Editor usability or a Player build. It does not replace
the pending rendered installer/Inspector or buyer-comparator acceptance tasks.
Unity's first-party docs distinguish the effective asset property from the pipeline
instance, which updates only after rendering. No screenshot/media is fabricated.

Both import and gameplay logs were independently scanned: zero C# error, managed
Exception:, CS0618 or CS0612 markers. Headless GTK/GLib critical teardown messages
remain in all three gameplay logs; the import logs have none of those matched
markers. This is a bounded scan, not a claim that every warning or GUI issue is gone.
Heavy actual host CPU contention was observed during compilation; the two URP builds
made progress and completed within their original twenty-minute native budgets.
No priorities, other owners' services or running workloads were changed.

Eight deterministic pipeline/option-boundary unit tests and thirteen existing
workflow/receipt tests pass. Coverage includes effective quality override semantics,
missing/unordered/duplicate phases, malformed identities/types, changed selection,
wrong requested pipeline and incompatible scenario flags. A new false acceptance
of integer 1 as Boolean true was reproduced before adding strict Boolean validation.
These 21 Python tests remain separate from real native workflow evidence.

## Resource denial and untouched graphical consent

An additional adversarial fixture was prepared in a new private copy with URP 17.6.0
still installed but its default pipeline unassigned and all quality overrides empty.
Only that new copy's GraphicsSettings asset was deliberately changed; its source
project stayed unchanged. The broker denied this extra experiment with
central_reservation_denied_resources_currently_insufficient. **No job started.**
The denial was not retried, reduced, disguised or routed around. PREPARATION.json
and the denied start response are retained; there is no native result for this
installed-but-inactive case. Its native verification remains open. The already
admitted URP jobs continued independently, and the completed Built-in control above
remains distinct evidence.

The earlier normal graphical Unity software-terms prompt was not reopened,
accepted, declined or bypassed. These are independently authorized batch tests;
no normal graphical installer Attach/Undo/Redo result is claimed.

## Preservation, source and remaining release gates

Private runtime:
`/data/var/marketplace-account-setup/hpr-urp-selection-night3-20261104/`.
Final audit: FINAL_NATIVE_AND_PRESERVATION_AUDIT.json. It retains raw-log hashes,
native source/asset-meta comparisons, strict positive/negative checks, all ten
original worktree heads/statuses and all 21 existing dirty-file hashes unchanged.
All three admitted owned jobs are exited with zero remaining cgroup processes.
The extra denied experiment has no running job. The original archive, corrected
candidate and earlier customer save hashes are unchanged.

Corrected candidate SHA-256:
`92cfb2058d32412e28c2da61fe8b93d899140f6a559c9432e072d24cba0870b1`.
Original archive SHA-256:
`1140e9bf5c7a9848003ce0ccd8168c298ced2bf957194364f9f08b3f52974f5e`.
Branch: qa/unity-urp-selection-night3-20261104, based on the completed night-two
native NUnit branch. No merge into dirty original seller work occurred.

Commercial release remains **NO-GO**. Rendered URP/Editor acceptance, actual buyer
workflow comparison/differentiation, full dependency-aware update/uninstall and
original-source/installer-overlay reconciliation remain open. The additional
installed-but-inactive native control remains unrun after its explicit admission
denial. No package was rebuilt, published, submitted, purchased, sent to buyers or
uploaded to a marketplace. Source QA changes and reproducible outcomes are saved
in Git; completed changes must be pushed and remotely verified before final report.

First-party API semantics reviewed:
https://docs.unity3d.com/6000.1/Documentation/Manual/srp-setting-render-pipeline-asset.html
https://docs.unity3d.com/cn/6000.0/ScriptReference/Rendering.RenderPipelineManager-currentPipeline.html
