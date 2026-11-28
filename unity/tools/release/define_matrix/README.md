# HPR Define Matrix — independent original Unity 6 Editor extension

This package is **NEW**, distinct from the existing Build Scene Matrix and Scene Gate: it compares profile-specific *scripting compile defines*, whereas Build Scene Matrix compares *scene lists and launch order*. The tools may eventually be bundled if sales evidence supports bundling; do not create duplicate storefront listings.

Only `Assets/HPRDefineMatrix/` is buyer deliverable. `qa/` is developer-only and must NEVER ship. Unity 6.1 API needed; actual native tests in installed patched Unity 6000.6.8f1 only. `qa/run_native_acceptance.sh` creates an author project, exports a private .unitypackage with genuine stable `.meta` identities, imports into a clean buyer project and verifies real BuildProfile defines, read-only scanning, create-only export and EditorWindow construction. No automatic UPM operations or profiles in the buyer archive.

Native interactive visual acceptance and customer usability (not merely batch Editor window construction) should additionally be verified before claiming buyer-ready marketplace screenshots. No external upload/publication is authorized. Sale income unknown. The current licence is private evaluation, not permission to distribute.
