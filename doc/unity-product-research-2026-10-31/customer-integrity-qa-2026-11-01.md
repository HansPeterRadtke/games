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
hashes customer-owned assets (including .meta) and selected persistent Unity
settings using SHA-256. It records only relative paths and digests and refuses
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
reproduced it and the source was corrected. Nine deterministic checker cases
now pass, including adverse mutations and GUID conflicts.

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
classification. The v14 upgrade is a separate Unity Editor operation; do not
claim preservation until its actual import process exits and the digest and
scene/Inspector-value checks both pass.

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

Even a passing update gate does not establish non-destructive vendor-root
modification preservation, safe uninstall, UI Toolkit onboarding, actual
end-user Inspector completion time, new-input + URP combinations, or human
willingness to pay. The separate dirty integration branch may contain later
unsynced changes that are not included in the tested v14 archive. No submission
or publication is authorized. **Commercial verdict remains NO-GO** pending
differentiation, complete release matrix, and real user-value validation.
