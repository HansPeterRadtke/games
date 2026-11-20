# Unity buyer-project preservation — independent QA and commercial gate

Scope: private November 1, 2026 reproducibility record on Nitro, branch
`qa/unity-customer-integrity-20261101`. No publisher operations,
customer projects, or source in the concurrently dirty integration worktree were
modified. The snapshot helper and its tests are QA-only and are **not** new
commercial product features.

## Question and risk

Can an HPR archive be imported or upgraded in an existing project with an
independent buyer-owned controller, scene, prefab, ScriptableObject settings,
and unrelated ProjectSettings/Packages files without destructive changes?

A clean Unity project is insufficient to answer this. Existing upgrade QA on
the product branch had checked only a generated customer text file and one C#
file. It did not check serialized scenes, prefabs, Unity GUID metadata, custom
ScriptableObject values, or existing input/graphics/editor settings.

## New independent guard

The Python checker at
`unity/tools/release/gameplay_suite/qa/customer_integrity.py`
hashes **all existing non-vendor Assets files** (including .meta), **all
existing ProjectSettings files**, and the Packages manifest/lock files using
SHA-256 by default. An explicit --customer-root narrows the watched Assets
scope only; ProjectSettings/Packages remain protected. It records only relative paths and digests and refuses
to overwrite an existing baseline. After an import it fails on *added,
removed or byte-modified* protected assets. It independently checks candidate
Unity archive GUIDs against unrelated customer-owned .meta GUIDs before
import. The existing vendor root and its root .meta are deliberately excluded
from unrelated-customer collision warnings; customer edits *inside* that
vendor-owned root are **not** proven safe.

The watcher refuses symlinked Assets ancestors, customer files and project
settings, preventing accidental traversal outside the specified project.
Capture is meant for a **disposable copied game**, not a real customer's
project. Only a Unity Editor invocation, with logged output, can prove
imported C# compiles and an actual authored scene still works.

Test-first record: the initial test module failed at import because the
checker did not exist; six foundational cases passed after implementation.
A new symlinked-Assets-parent test then failed and motivated an ancestor
check. An actual pre-import v13-to-v14 project exposed a false-positive
collision at `Assets/HPRGameplaySuite.meta`; a regression test
reproduced it and the source was corrected. The initial nine checker cases
passed. Three additional test-first cases identified two missing defaults:
files in other customer Assets folders and less-common ProjectSettings. The
broadened checker now passes **twelve focused cases**, including those
previously failing cases, and **thirty-three total Python tests** when combined
with the original suite. The scoped live v13-to-v14 upgrade described below
was first captured with the initial narrower checker; do **not** retroactively
claim the broadened file coverage for that original successful import.

## Real Unity acceptance scenario

Private scratch root: `/data/tmp/hpr-caltask33-20261101-0903`.
The copied release archive matches the original v14 package byte for byte.
Unity 6000.6.7f1 completed a clean project creation and import, with thirteen
of thirteen serialized scene references and twelve of twelve related asset
checks. Its ten independent runtime smoke checks also passed, including a
JSON disk round trip and corrupt-state rejection. These are *fresh actual*
Unity Editor logs and receipts, not Python stand-ins.

For customer preservation, a copy of the previously imported real Unity 6.6
v13 project was seeded using a private Unity Editor method. The buyer fixture
uses its own independent MonoBehaviour controller and ScriptableObject settings.
The Editor created an authored scene, prefab, and their GUID metadata, and
set domain reload disabled. Seed verification passed in the actual Editor.

The private pre-import digest baseline protects twenty-one files: one Unity
scene, one prefab, eight metadata files, seven ProjectSettings files, one
Packages manifest and other buyer-owned source/settings files. Initial
unrelated-GUID preflight passed after correcting the vendor-root collision
classification. The v14 upgrade now **passed** in a real Unity 6.6 Editor,
with a zero process exit and no C# compiler errors or warnings in its
separate log. The after-import SHA-256 gate reported all twenty-one original
customer files preserved, and the separate private Unity Editor
`HprCustomerFixture.Verify` reported the same original scene, controller,
prefab, serialized settings and Editor domain-reload-disabled setting.
Evidence: scratch receipts `customer-baseline.json`,
`customer-import-v14-unity.log` and
`customer-post-upgrade-actual-unity.txt`. This is one fully specified customer
fixture, **not** a general guarantee over arbitrary third-party projects.

The broadened checker now inventories **forty-six** protected files in the
already-upgraded private test project: twenty-one non-vendor Assets files,
twenty-three ProjectSettings files, and two package-management files. The
post-uninstall scratch project currently has forty-two protected files; the
four-file difference is expected because its private HPR-dependent QA scripts
and scratch fixture differ. These are **current read-only inventories**, not
forty-six-file before/after import acceptance; a fresh full-scope pre-import
baseline is still needed to upgrade the strength of that claim.

A separately isolated actual Unity 6.6 invocation tested the **latest
uncommitted integration guide** frozen into a disposable copy of the older
v14 buyer archive. The private customer-sample-copy validator passed: copying
a weapon and healing ability, rebinding the copied effect, generating
independent IDs/GUIDs, safely rejecting an occupied destination and forbidden
paths, and retaining vendor original asset bytes/GUIDs. See private
`customer-sample-copy-new-guide-receipt-20261101.txt` and its Unity log.
That test does **not** mean the newer guide code has already been included
in the actual commercially distributable v14 archive.

A **separate disposable copy** was used for an Editor-initiated uninstall.
The real Unity 6.6 Editor reported it removed the entire original
`Assets/HPRGameplaySuite` directory and the private HPR-dependent QA scripts.
After removal, an independent full repeat of the original twenty-one-file
SHA-256 gate passed. A **separate, fresh Unity 6.6 Editor process** then
completed a clean C# compile and invoked
`HprCustomerFixture.VerifyWithoutVendor` successfully. Its private receipt
`customer-after-uninstall-actual-unity.txt` confirms the original customer
controller, scene, prefab, serialized settings and Editor settings remain
valid and the entire HPR vendor source is absent. The real Editor uninstall
and re-open logs show no C# compiler errors or warnings. This validates
uninstall **only for a game with no HPR-dependent customer code**; an actual
consumer of vendor interfaces would require migration or intentional manual
integration change and is not yet supported.

The independent real Unity 6.6 Editor UI Toolkit fixture also passed: it
constructed the HPR Integration Guide EditorWindow, found a responsive
scroll container and eight native action buttons, and checked that the window
reported Unity version, package-file status, and the fact that file-presence
checks are not runtime acceptance. Evidence: private `editor-ui-actual-unity.txt`
and `editor-ui-unity.log`. This proves Editor structure, **not** screen
legibility, keyboard navigation, task completion or real buyer adoption.

## Reproduce and interpret

Run:
`python3 -m pytest -q tests/test_unity_customer_integrity.py tests/test_unity_gameplay_suite.py`

The isolated external-process acceptance sequence is: clone the **already
imported v13 test game** to a new scratch path, seed buyer-owned assets through
the Unity Editor's private `HprCustomerFixture.Seed` method, run
`customer_integrity.py --project <scratch> --capture <new-json> --archive <v14-unitypackage>`,
import the newer archive with the actual Unity 6.6 Editor, run
`customer_integrity.py --project <scratch> --verify <saved-json> --archive <same-package>`,
then execute the private Editor method `HprCustomerFixture.Verify` to inspect the
serialized customer controller, scene, prefab and settings after import.
Keep source original and existing release evidence immutable. All external
QA logs and buyer fixtures remain in the private scratch directory, outside
Git.

## Measured discrepancy: latest source versus tested release archive

Do **not** treat successful v14 acceptance as evidence for the worktree's
currently uncommitted guide changes. A read-only asset-byte comparison found
that the tested v14 Unity archive's integration guide C# source is 9,604 bytes,
whereas the currently edited worktree source is 21,860 bytes. The archive
README, QUICKSTART and ARCHITECTURE are also different from today's edited
files. The archived HprGameplaySuiteSceneBuilder.cs and HprSuiteInput.cs
were byte-identical to the live worktree. Thus the latest customer-copy
features in the dirty guide have **not** been validated as buyer-archive
content by this pass. Wait for its owning agent's edits to settle, create a
new versioned release candidate in a fresh private output directory, and
repeat all cleanroom, existing-game and uninstall quality gates. Do not
claim test or publication readiness on the basis of the old archive.

## Commercial context and remaining gates

The official Unity Asset Store Submission Guidelines require unique buyer
value and AI-use disclosure, compatible scripts, no obsolete API warnings,
and safe domain-reload-disabled Play mode on Unity 6.6:
https://assetstore.unity.com/publishing/submission-guidelines

A **free direct competitor**, PackageLens, already offers .unitypackage
preview, path/GUID collision reports, text/YAML comparisons and pre-import
snapshots:
https://assetstore.unity.com/packages/tools/utilities/packagelens-package-import-review-tool-375592

Focused ability workflows also already exist in:
https://assetstore.unity.com/packages/tools/game-toolkits/ability-system-kit-385772
and
https://marketplace.unity.com/packages/tools/game-toolkits/abilities-game-creator-2-206589

These are descriptions from actual listings, **not** verified purchases,
download counts, comparative usability benchmarks or proof of market demand.

The passing update and removal byte-integrity gates do not establish
preservation of buyer edits **inside the vendor-owned HPR root**, reliable
uninstall for projects that actually depend on HPR services, real end-user
Inspector completion time, keyboard-accessible/dark/light/high-DPI Editor
usability, the entire old/new-input plus URP matrix, or willingness to pay. The separate dirty integration branch may contain later
unsynced changes that are not included in the tested v14 archive. No submission
or publication is authorized. **Commercial verdict remains NO-GO** pending
differentiation, complete release matrix, and real user-value validation.
