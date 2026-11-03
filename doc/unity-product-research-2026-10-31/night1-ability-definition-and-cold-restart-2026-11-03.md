# November 3 night: ability-definition safety and fresh-process save acceptance

## Actual result and source scope

Real Unity tests reproduced eleven invalid-definition failures in the unchanged
reviewed package. The isolated fix validates the whole built-in ability definition
before spending resources. Three canonical com.hpr.abilities runtime files are
updated; an archive-matched private installer overlay delegates numeric/effect
validation to the same rule. Serialized field names/types and all existing GUIDs
are preserved. The original owner product worktree is not modified or merged.

Cost and effect values must be finite and nonnegative. Cooldown is finite and
0–86400 seconds, matching the existing snapshot validator's one-day maximum.
Unsupported built-in effect types, a null effect list, invalid area-damage radius
or nonfinite effect offset are rejected before charging. Status text gives the
reason. Valid empty lists and optional null slots retain runtime compatibility for
event-only integrations. The installer separately retains its existing requirement
for owned, nonempty effect assets. Custom resource/event callbacks remain responsible
for their own behavior; this is not general transactional rollback across arbitrary
customer code.

## Native failing cases before the fix

The exact original archive's configuration run exited 3 / FAIL, with eleven failures
among sixteen actual API/Editor-preview cases. Observed examples:

- Cooldown 86401 seconds: activation accepted, health healed and stamina spent,
  but its own captured snapshot was rejected as unrestorable.
- Negative cost: activation accepted and healing was free.
- Null effect list: ArgumentNullException after stamina fell from 100 to 80.
- NaN effect value: ArgumentOutOfRangeException after the same partial charge.
- Negative/NaN/infinite cooldown, negative effect value, unsupported effect type,
  negative damage radius and infinite forward offset also activated or mutated
  state despite invalid definitions. Preview accepted several of them.

The first four-payload private candidate passed all sixteen cases. Review of the
existing AbilitiesEditModeTests then identified an important compatibility control:
its snapshot test intentionally uses a zero-effect runtime ability. The final
candidate preserves that API behavior and adds a seventeenth native case exercising
its unlock/cooldown snapshot restore and second-activation rejection. The original
bad-run logs and the intermediate candidate were retained; neither was overwritten.

## Final-candidate verification matrix

| Native target / task | Actual result | Preservation and boundary |
| --- | --- | --- |
| Unity 6000.6.7f1, Input System 1.20.1, Built-in; definition + actual preview API matrix | 17/17 PASS, process exit 0 | 56 import / 59 staged original files unchanged; all 55 archived C# exact |
| Same target; existing-game input/health/HUD/save/detach workflow, domain reload disabled | 16/16 PASS, process exit 0 | Same protected counts and exact source identity |
| Same target; older package's disk save restored in a new process | 15/15 PASS, process exit 0 | Save and integrated scene byte-identical; same protected/source checks |
| Unity 6000.4.0f1, Built-in, legacy input configured; native import + configuration matrix | 17/17 PASS, process exit 0 | 25 import / 37 staged original files unchanged; all 55 C# exact; input handler 0, no Input System dependency |
| Unity 6000.4 managed API / old-input offline assembly build | Build exit 0, zero errors, fifteen existing serialization-field warnings | API-only result; separate from the actual native 6.4 run |
| Unity 6000.6.7f1, full workflow with domain reload enabled | 16/16 PASS, process exit 0 | 56 import / 59 staged originals unchanged; all 55 C# exact |

All native imports are actual Editor processes. The original package and a new
candidate each have their own checksum and receipts. The old package's earlier
URP result does not certify the changed candidate. No new rendered URP claim is made.
Native configuration tests run the real runtime classes and public installer
validation in Edit mode; they do not draw or click the installer window.

## Fresh-process save behavior

The source save was produced by the afternoon package workflow and remained
unchanged. The first new-process test of the original archive passed fifteen checks;
the final candidate repeated them against that older save, not a regenerated fixture.
It began with serialized health 40/stamina 100 and restored health 60/stamina 80,
including the existing HUD binding. Input reached the existing action once, but the
restored active cooldown rejected activation without charging. An invalid NaN
snapshot was rejected without changing restored vitals or cooldown.

The test then waited for the saved thirty-second cooldown to expire on the new
engine's game clock. The same queued action activated once and produced health
80/stamina 60 with HUD agreement. Process identity, engine version and elapsed
clock were recorded. This verifies relative cooldown persistence: offline time
does not consume the stored cooldown. It is not wall-clock cooldown, a Player
build, physical-keyboard evidence, or an external buyer's game.

## Private archive and preserved earlier engineering

The final create-only private archive is SHA-256
`92cfb2058d32412e28c2da61fe8b93d899140f6a559c9432e072d24cba0870b1`.
Its original is
`1140e9bf5c7a9848003ce0ccd8168c298ced2bf957194364f9f08b3f52974f5e`.
The retained first-fix intermediate is
`2d1c63beacad1ebd00d01c44ce0d20213831028dead148062b6b9dba0c3c5933`.
The final candidate changes four existing source payloads only.
All 161 GUID asset identities, every asset.meta/pathname and all 451 other tar
members remain byte-identical to the reviewed original. There are still 55 C#
files and ten runtime assembly definitions. This is a tar-format internal QA
candidate, not a Unity Editor export, publication or approval.

The older sibling qa/HprSelectedAbilityInstaller.cs prototype lacks the archived
native-stats-source guard. It was deliberately not substituted into the candidate.
The new AbilityDefinitionSafety overlay starts from the actual archived source,
preserves HasValidStatsSource validation and changes only the definition gate.
The three canonical runtime files byte-matched the archive before editing. Frozen
four-file original/proposed snapshots and an explicit source-to-asset mapping are
retained privately. Do not lose those earlier fixes when reconciling seller source.

## Graphical Editor consent gate and truthful UI boundary

The normal graphical Unity 6.6 process was launched in its own authenticated Xvfb
with software OpenGL. It displayed Unity Editor Software Terms (updated June 30,
2026) before the installer opened. The genuine screenshot is retained. No checkbox,
Accept, Decline, installer button or Undo/Redo was clicked. Only this owned GUI job
was stopped through its own broker capability; zero child processes remained.
No acceptance flag or Editor preference was edited to bypass the prompt.

The screen contract and create-only interaction observer are prepared. Their
receipt gate requires all eighteen ordered observations and screenshots of narrow,
wide, Attach, Undo and Redo stages; twenty-four missing/empty cases reproduced the
presence-only gate's false positives before tightening it. Five unit tests pass.
The observer compiles in the native 6.6 batch projects, but full GUI execution,
readability, real mouse/shortcut behavior, themes/DPI and expert comprehension remain
UNTESTED. Owner acceptance of the displayed terms in normal Unity 6.6 is needed
before that graphical step can continue. Existing independently available batch
compilation/runtime tests continued; no blocked GUI action was rerouted or claimed.

## Durable evidence and next release gates

Private runtime: `/data/var/marketplace-account-setup/hpr-editor-usability-night1-20261103/`.
It holds the observed consent gate, native imports, all configuration case JSON,
old/new cold-state observations, native result files, offline API manifests, exact
source snapshots, archive-build receipts and original-worktree preservation hashes.
The final candidate is selected by DEFINITION_COMPATIBLE_ARCHIVE_RESULT.json;
DEFINITION_ARCHIVE_RESULT.json identifies the retained intermediate candidate.

Source-level checks passed: thirteen workflow/receipt tests, five interaction
receipt tests, fourteen archive-policy tests, twenty-one suite tests and eleven
private archive-builder tests. These sixty-four Python tests are not substitutions
for the native runs listed above. No actual NUnit runner is claimed; the event-only
compatibility test was traced from the existing module tests and exercised natively.

Commercial release remains NO-GO. Required work includes original-source integration
review, actual rendered Editor/Inspector and URP acceptance, human buyer workflow
comparison/differentiation, physical input and full dependency-aware uninstall/update.
No package was published, submitted, priced, purchased or uploaded to a marketplace.
Final Git/source/process verification and the reload-enabled result follow below.


## Final checkpoint, November 3 at 22:49 UTC

All final-candidate matrix entries above completed successfully. The configuration
matrix took 368.0 seconds in native 6.6 and 232.4 seconds in native 6.4. The full
workflow took 346.1 seconds with reload disabled and 351.3 with reload enabled.
The old-save fresh-process test took 369.9 seconds. The final candidate's native
import/gameplay/configuration logs were independently scanned: no managed-exception,
C# compiler-error, CS0618 or CS0612 markers were found. This is a specific scan,
not a claim of all possible warning/perceptual issues being absent.

All eleven owned broker jobs were exited/stopped with zero remaining cgroup
processes, including the consent-gated GUI job. All eight original worktree heads,
Git statuses and all 21 existing dirty-file hashes matched the pre-work snapshot.
The original reviewed archive and original afternoon save hashes also matched.
FINAL_PRESERVATION_AND_LOG_AUDIT.json retains native log hashes, job states and
those checks. No original private candidate or uncertain effect was replayed in
place. Each native run used a new separate copied project; the 6.4 target began
from an actual newly created 6.4 project rather than a downgraded 6.6 template.

The isolated branch is qa/unity-editor-usability-night1-20261103. Canonical runtime
changes and the exact archived-Editor overlay require source reconciliation before
any seller rebuild. Native full-graphical usability remains blocked on the owner's
software-terms consent; the dialog was left untouched. The next useful permitted
engineering milestone after that consent is the prepared rendered installer
Attach/Undo/Redo task, followed by real buyer comparison. No commercial readiness
or marketplace approval follows from these tests.
