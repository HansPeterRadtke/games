# Unity Asset Store release tools

This directory contains the reproducible sale-package validation, export, screenshot, official Asset Store Tools validation, and upload helpers.

## Typical package flow

For one sellable package, run the package-specific pipeline rather than the all-package default:

```sh
unity/tools/release/prepare_sale_packages.sh com.hpr.eventbus
unity/tools/release/validate_release_candidate.sh com.hpr.eventbus
unity/tools/release/run_official_asset_store_validator.sh com.hpr.eventbus
```

The release scripts always inject the `hans` GUI/session environment (`DISPLAY`, `XAUTHORITY`, `XDG_RUNTIME_DIR`, and DBus address), even when the caller is already `hans`. This is required because Unity AssetImportWorkers can otherwise fail with `Error opening default X display` and leave the parent Editor waiting indefinitely.

Package-specific preparation is non-destructive at the reporting layer: `doc/package-sale-prep.md` is rebuilt from all sale artifacts currently present under `dist/package_sale_artifacts`, not just the package names supplied to the latest command. `generate_sale_listing_drafts.py` also preserves the maintained `doc/human-only-final-steps.md`; it creates the generic checklist only when that document is missing.

## Asset Store upload/status command

`upload_asset_store_package.sh` uses Unity's installed Asset Store Publishing Tools API through `HprAssetStoreUploaderRunner.cs`.

Dry-run is the default. It authenticates, fetches publisher packages, matches the exact package name plus Publisher Portal id, and reports the current server status without uploading:

```sh
unity/tools/release/upload_asset_store_package.sh \
  --portal-id 1506320 \
  --name 'HPR Typed Event Bus' \
  --expected-login multiverse3dhpr@gmail.com \
  com.hpr.eventbus
```

A real upload requires the explicit `--execute` switch:

```sh
unity/tools/release/upload_asset_store_package.sh \
  --execute \
  --portal-id 1506320 \
  --name 'HPR Typed Event Bus' \
  --expected-login multiverse3dhpr@gmail.com \
  com.hpr.eventbus
```

The runner refuses a real upload unless the exact server-side package/version status is `draft`. Status inspection still works for `pendingReview`, published, rejected, or other non-draft states. This prevents accidentally replacing a submission that is already in review.

Authentication prefers Unity cloud authentication when `CloudProjectSettings` exposes a usable signed-in account. Otherwise it reads the local credential file at execution time and calls the Asset Store Tools `CredentialsAuthentication` API. The default credential path is `/data/infra/secrets/unity3d.txt`; override it with `--credential-file` or `HPR_UPLOAD_CREDENTIAL_FILE`. The credential file must remain private runtime/infra state and must never be committed, copied into the sale project, printed, or placed in command arguments.

The accepted local credential-file layout is:

```text
login:
<unity-login>
<unity-password>
```

Use `--expected-login` so the runner rejects a credential file belonging to a different Unity account before authenticating.

The uploader is intentionally asynchronous. Do not add Unity's `-quit` command-line switch: the runner awaits authentication/package/upload tasks and calls `EditorApplication.Exit(0/1)` itself when the operation has actually completed. Blocking the Editor main thread with `Task.GetAwaiter().GetResult()` deadlocks the Asset Store Tools async API.

Result and Unity log files are written under `doc/logs/asset_store_tools_upload/`. Result files contain package ids, server status, uploadability and upload outcome, but never credentials or session/access tokens.
