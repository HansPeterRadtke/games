# Exact import identity must include importer metadata

The exact-package verifier checked asset bytes and metadata GUIDs, but not the
remaining .meta content. Thus importer customization could be incorrectly reported
as a pristine vendor install before an update. The fix compares every full metadata
payload against the pinned archive, exposes metadata_payloads_verified separately,
and requires payload, metadata and GUID matches for a fully verified asset path.
It is read-only and never restores, normalizes or overwrites customer settings.

Three deterministic regressions first fail on the old verifier: same-GUID script
importer customization, folder importer/userData changes and missing non-GUID
metadata. The baseline fixture now installs the actual archive metadata bytes,
including fileFormatVersion, rather than a previously accepted partial GUID-only
file. All 13 identity, 13 upgrade-preview and 45 uninstall checks pass: 71 methods.
Python compilation and whitespace checks pass. Historical native-import fixtures
also retain exact metadata and continue to pass.

## Actual Unity negative control

Installed Unity 6000.6.7f1 runs the new private MetadataIdentity fixture on a new
copy of the previously verified upgraded project. Public MonoImporter APIs change
the packaged AbilityRunnerComponent execution order from 0 to 123 and save it.
The native process exits zero in 87.5 seconds. Only that existing vendor .meta
changes; the sole new file is the private fixture's own generated .meta. No C#,
customer scene, manifest, project setting or other existing file changes.

The old verifier reports PASS, with all 161 asset paths/GUIDs apparently pristine.
The corrected verifier reports the one metadata difference: all 133 asset payloads
and 161 GUIDs still match, while only 160 metadata payloads/asset paths fully match.
The composed upgrade preview changes from dependency review to
blocked_modified_or_missing_old_vendor_assets. The intentionally customized private
project is retained without repair. This demonstrates a real Unity-generated
metadata edit, not only a hand-written parser fixture.

The unmodified source project still passes all 161 full metadata/GUID/path checks.
All 433 original project file hashes, all 13 other Unity worktree heads/statuses,
all 21 original dirty-file hashes and the pinned product archive are unchanged.
The bounded owned broker job exited with zero remaining cgroup processes. Native
logs contain no C# error, managed exception, obsolete API or GTK/GLib critical
markers; five inherited private CleanEditorControl UAC0005 warnings remain.

## Evidence and limits

Private runtime:
`/data/var/marketplace-account-setup/hpr-metadata-identity-20261109/`.
Retained artifacts include BEFORE.json, original_identity.py, red.log,
green-identity.log, green-upgrade.log, green-uninstall.log, the create-only
run_native_metadata.py, launch.json, unity.log, NATIVE_METADATA_RESULT.json,
PROJECT_BEFORE.json, SOURCE_BEFORE.json, RESULT.json and FINAL_AUDIT.json. The
canonical fixture/README are under qa/MetadataIdentity. Private broker credentials
are excluded from Git. Product archive SHA-256 remains
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.

This deliberately strict byte check can also flag legitimate metadata normalization
by another Unity version; such differences require review, not silent acceptance
or automatic repair. It does not provide semantic importer migration, rollback or
uninstall. No graphical UI, Player, URP or independent buyer acceptance is claimed
for this increment. Earlier denied URP operations and normal graphical software
terms were not retried or bypassed. Commercial release remains NO-GO pending those
wider compatibility, usability, source-reconciliation and buyer-value gates. No
publication, purchase, outreach, account change or reminder occurred.
