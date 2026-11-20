# November 7 recovery: undefined integrated-suite keyboard bindings

## Actual bug and implementation

The integrated suite's new Input System adapter converted KeyCode.ToString() through
Enum.TryParse. Undefined serialized KeyCode values stringify as integer strings;
parsing accepts those integers as a different Key value without proving enum
membership. Actual native Unity 6000.6.7f1 / Input System 1.20.1 Play-mode cases
confirmed value 18 activates D, while 50000 and -1 throw ArgumentOutOfRangeException
when the adapter indexes the keyboard. Six ordinary mappings work in the same run,
and the raw simulated device held/edge controls are active throughout.

The canonical HprSuiteInput.cs now rejects values not defined by KeyCode before
parsing an uncached binding. It returns Key.None, so both public queries safely
return false for these invalid bindings. Existing cached valid bindings keep their
fast path. Valid names/mismatch mappings and intentional mouse/joystick keyboard
exclusions remain intact. The legacy-input and no-input branches are byte-identical.
No serialized setting, public signature, user binding, scene or asset GUID is rewritten.

A new create-only internal archive changes only the existing Input source payload
relative to the lifetime-fixed archive. All 161 GUID identities/metadata, 454 other
tar members, 55 product C# paths and ten runtime asmdefs are retained. Its exact
canonical source matches the imported payload. This is private tar-format QA,
not a Unity Editor export, publisher upload or release approval.

Prior lifetime archive:
`83ea196924d966175c33b07173fa94e69831369df86a71783f9f2a9c20338292`.
Input-key corrected archive:
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.

## Reconciled interrupted work and actual native outcomes

The November 5 owner work was interrupted by the explicit no-tools reliability
canary. Its response was the requested acknowledgement only. Read-only inspection
on November 7 found the already-started green job completed successfully; neither
its package build nor test was blindly repeated. The completed native receipts,
exact staged probe bytes, archive identity and process state were independently
checked before continuing. Existing failed attempts were retained.

| Actual target / task | Native result and scope |
| --- | --- |
| First November 5 Edit-mode probe | Positive device controls fail; retained as inadequate harness evidence, not a complete negative control |
| Corrected November 5 Play-mode probe, prior lifetime archive | Twelve observations, nine pass and exactly three invalid-value failures; native exit 3; no project/source file changes |
| Same final Play-mode probe, corrected input archive | All 12 cases PASS, native exit 0; actual native device held/edge controls active in every case; no project/source changes; 107.6 seconds including native import |
| New November 7 Unity 6000.4.0f1 legacy-input project import + configuration matrix | Native import/configuration exit 0, all 17 cases PASS; 188 protected files unchanged; 99.2 seconds |

Both imported positive projects pass the full read-only package identity verifier:
all 161 asset paths and all 161 GUID identities match, with no issues. The focused
new-input test also verifies all 55 archived scripts exactly. The 6.4 project has
activeInputHandler 0 and no com.unity.inputsystem dependency. Its new import and
configuration check prove legacy-branch compilation/package compatibility; they
are not physical or simulated legacy keyboard event tests.

The new private driver/receipt gate requires all distinct cases and fixed expected
outcomes, real device state, no exception and native exit zero. Five regression
methods pass, including every missing case and rejection of a false all-negative
receipt that initially passed the first classifier. The existing 21 suite, 11
archive-builder and 14 archive-policy tests also pass: 51 Python methods total,
separate from the actual native executions. Python compilation and whitespace
checks pass. No new actual module NUnit run is claimed for this changed archive.

## Evidence limits and preservation

The valid red/green Play-mode log scans have no C# error, managed Exception:,
CS0618 or CS0612 markers. Expected range exceptions are captured in the old probe's
JSON cases rather than logged as uncaught engine failures. Inherited private
CleanEditorControl assembly-enumeration analyzer UAC0005 warnings and headless
GTK/GLib teardown critical messages remain; no warning-free Editor claim is made.
The tests use a simulated Keyboard in an unsaved empty Play scene, not physical
key presses, all international layouts, gamepad support or rendered UI.

Private runtime:
`/data/var/marketplace-account-setup/hpr-invalid-input-key-20261105/`.
ARCHIVE_RESULT.json and SOURCE_MAP.json select the package/source mapping.
FINAL_INPUT_AND_PRESERVATION_AUDIT_20261107.json records the strict native red/green
comparison, source/log hashes, full package identity, legacy compatibility and all
four owned jobs exited with zero cgroup processes. All thirteen earlier Unity
worktree heads/statuses and all 21 original dirty-file hashes are unchanged both
from the November 5 checkpoint and the November 7 resume snapshot. No other agent's
work was overwritten. Original archives and failed test projects remain intact.

The branch is qa/unity-invalid-input-key-20261105. Its canonical source edits and
reproducible focused QA are finalized on November 7. No merge into the dirty owner
seller worktree occurred. The earlier denied URP/inactive-URP operations and normal
graphical software-terms gate were not retried, disguised or bypassed.

Commercial release remains **NO-GO**. This changed archive still requires its wider
pipeline/gameplay/Player matrix, physical/rendered Editor acceptance, original
installer/source reconciliation, dependency-aware migration/uninstall and real
buyer/comparator validation. Earlier broader results apply to their own archive
checksums and are not silently transferred. No product was published, purchased,
sent to buyers or submitted to a marketplace; no reminder was created.
