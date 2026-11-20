# Migration preflight: package metadata validation, November 9

The read-only uninstall/dependency checker could report `no_direct_reference_detected`
for malformed manifest version values, malformed resolved lock entries, and an HPR
reference present only in a customer lock entry's dependency map. Its two special
metadata readers also used unbounded read_text after a file-size check, unlike the
bounded general asset reader: a growing file could bypass the intended read limit.
These were diagnostic gaps, not prior permission to delete or auto-import anything.

The checker now validates nonempty string dependency names/versions, resolved lock
entry objects/versions/dependency maps, and reports transitive HPR lock references.
Both metadata files use a byte-bounded JSON reader and flag growth past the ceiling
as unknown content requiring review. This is basic schema/type validation, not full
UPM version-resolution or package-ID validation. No package is downloaded or resolved.
All read-only, deletion-prohibited and manual-review semantics remain intact.

Five new deterministic regression methods exercise malformed manifest and lock
values, a transitive HPR edge, valid unrelated registry/local/Git strings, an exact
128-byte boundary and simulated growth of each metadata file. The original checker
fails 19 observations across four methods while the valid control passes; the same
cases pass after the fix. All 45 uninstall checks and 13 upgrade-preview checks pass
(58 methods total). Python compilation and whitespace checks also pass.

Read-only verification on the saved actual Unity-upgraded project retains all 47
original dependency findings and leaves all 433 source/settings/asset hashes intact.
A disposable copy with a null manifest version demonstrates full upgrade-preview
propagation: the original helper returns dependency review with no metadata unknown;
the corrected helper explicitly requires uninspectable-content review. A separate
ordinary-controller fixture isolates the lost transitive lock edge: the original
reports no direct reference, while the corrected helper reports an HPR dependency.
Neither result grants deletion or automatic upgrade permission.

Private evidence is retained under
`/data/var/marketplace-account-setup/hpr-package-metadata-preflight-20261109/`:
BEFORE.json, original_uninstall_preflight.py, red-tests.log,
red-counterfactual.log, green-uninstall.log, green-upgrade.log,
VALID_SAVED_PROJECT.json, MALFORMED_UPGRADE_PREVIEW.json and
TRANSITIVE_LOCK_COMPARISON.json. Only disposable private fixtures were edited;
original project/runtime/package data and concurrent worktrees remain preserved.

This increment changes QA migration tooling/tests and documentation only. No Unity
Editor or Player was run; no new native compatibility or graphical usability result
is claimed. The private product archive is unchanged. Commercial release remains
NO-GO pending wider migration/uninstall coverage, source/installer reconciliation,
URP/rendered usability and independent buyer/comparator validation. Earlier denied
URP operations and graphical software terms were not retried or bypassed. No product
was published and no account, outreach, purchase or reminder action occurred.
