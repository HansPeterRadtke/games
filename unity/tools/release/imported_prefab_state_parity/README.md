# Original HPR Imported Prefab State Parity — private separate Unity tool

This is a separate product from the Publisher Version Matrix: it snapshots selected **loaded prefab object values**, not just imported source byte paths and GUID/dependencies. Use public Unity Editor PrefabUtility APIs to load isolated source prefabs and unload without writing; compare results from real installed Editors. Unsupported component fields are counted and disclosed rather than pretending full serialization parity. The buyer source is the single `Assets/HPRImportedPrefabParity` folder; `qa/` is private and must not be shipped in `.unitypackage`. Do not publish without genuine native QA, visual screenshots, licensing, disclosure and market evidence.

## Dependency input fidelity revision, 23 November 2026

The newer receipt schema two also fingerprints physical source and importer metadata for the recursively referenced `Assets/` dependencies of each selected prefab. A changed FBX/material/script or `.meta` file now prevents attributing selected loaded-value differences to Unity alone, even if the prefab source bytes match. Nonphysical built-in or package dependencies are recorded explicitly and prevent a clean verdict. Earlier schema-one native receipts are intentionally rejected for new comparisons. All private QA and native buyer evidence are versioned separately under the new wave61 test root. No external storefront or customer action is authorized by this revision.

## Uninspected custom fields — strict verdict

A separate original nested-prefab/variant acceptance test uses a genuine custom MonoBehaviour carrying serialized fields. Even with identical source and covered imported values, the comparison must return `COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS` whenever either native receipt reports uninspected component occurrences. The tool does not silently label unknown custom-script serialization as matching. Full-script parity, custom importer effects and Player behavior are outside current verified scope.

## Additional common physics geometry coverage

A correctness correction prevents an obvious silent omission in Collider subclasses: selected capsule collider shape fields and character-controller dimensions/limits are captured, while other unhandled collider subclasses explicitly report uninspected fields. This affects only new schema-two snapshots and requires native buyer revalidation of the changed source before a new candidate can be handed to the sole seller; do not reuse older binary package evidence for this revision.
