# Unity Asset Store release tools

This directory contains the reproducible sale-package validation, export, screenshot, official Asset Store Tools validation, and upload helpers.

## Separate original editor-tool candidates (not approved for storefronts)

`preflight_bundle/` is a third *unpublished internal candidate* that combines the original Input and Animator read-only Editor audit source with an original one-window preflight and create-only JSON report. It exports exactly those three vendor asset roots, with real-import QA and a separate software-terms graphical gate; it is not a general asset validator or authorized Asset Store listing.

`input_readiness_audit/` and `animator_contract_audit/` contain independently tested read-only Editor utilities, each with private QA, exact asset metadata and user documentation. Their `Assets/` folders are the only proposed consumer payloads. Neither is an approved seller release. Unity Editor graphical screenshots and human onboarding remain blocked by the Software Terms consent gate. Never use the generic upload script or an old Publisher Portal package id for these candidates; the single shared sales worker must first verify licensing, actual media and owner publication authority. Native package build/import receipts remain in registered private Nitro project folders, not Git.

`package_boundary_audit/` is an additional **unpublished publisher-facing Editor candidate**. It scans a chosen single export folder for resolved Unity asset dependencies outside that boundary and offers a read-only report with create-only JSON export. The authored source and private native builder/consumer tests are separated; the GUI, real screenshots, seller economic validation, license and publication eligibility remain additional release gates. See its own README and the November 21 market comparison. It does not replace the official Asset Store Validator, discover missing GUIDs or certify dependency manifests.

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
