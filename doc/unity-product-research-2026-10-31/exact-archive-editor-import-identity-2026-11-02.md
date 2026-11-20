# Exact HPR Unity archive import and Play-mode identity — November 2

This is a private, independently tested acceptance gate for the new
seven-change buyer candidate. **It is not a passed Unity Editor test of
that new archive, not a marketplace submission, and not a commercial GO.**

## Concrete previously missed failure modes

The previously running broker worker was pinned to an older
161-asset selected-installer archive. It checked only that Unity exited
with code zero, original buyer/project file hashes were unchanged
*immediately after import*, and the installer source pathname existed.
That was insufficient to establish that the exact new binary had
actually been imported: a residual/older installer source could exist
and all old asset GUIDs could still match.

It also reused the pre-Play-mode original-file integrity result when
claiming customer preservation AFTER Play mode. A private unit fixture
demonstrated a false PASS even after intentionally altering a buyer
ProjectSettings file or an imported vendor script during a fabricated
Unity Play-mode stage. Both tests failed on the original worker and
passed after the correction.

## Exact version pinning

The worker now accepts an optional separately specified
\`--expected-archive-sha256\` alongside \`--archive\`. The previous
frozen release retains its original default SHA-256 and path. Any
**different** archive path without its exact new expected hash fails
closed, before any broker reservation or Unity launch. The seven-change
new candidate has SHA-256:

\`1d565d600baefa1decf62ea44452f5976706e15b93effbbfa63beafef8c22ad0\`

A real read-only invocation of the worker's report mode accepted this
hash, reported CPU admission **wait_for_cpu**, and made no reservation.
Another read-only invocation without a new hash correctly refused
the candidate, while the old default candidate continued to pass
its existing checksum. These commands did not run Unity.

## Real asset and GUID-by-GUID verifier

New QA code:
\`unity/tools/release/gameplay_suite/qa/unity_imported_archive_identity.py\`

The verifier refuses an invalid archive/pin, unsafe/unknown tar entries,
symlinks in imported paths and missing or extraneous HPR source files.
It examines every .unitypackage pathname/asset/.meta identity without
extracting it and checks against an actual Unity project's installed
asset tree. It independently compares **every asset payload byte hash**
and **every GUID**. A valid root folder and folder .meta files are
required, and a failed asset/path is explicitly named. It cannot
establish Unity compilation by itself.

Historical actual positive and negative checks against the real prior
Unity 6000.6.7f1 populated-customer import:

- Previous exact archive: **161/161 imported paths and GUIDs passed**,
  zero payload differences, zero added vendor files.
- New seven-change archive compared against that same older
  installation: correctly **FAILED** with exactly seven content
  mismatches, while all 161 GUID identities still match. The seven
  mismatches are exactly the intended three updated source files, the
  demo scene builder source, and the three buyer documents.
- The current new archive has still not been installed in the actual
  Unity Editor. The previous real Unity result must **not** be recycled
  as acceptance of the new binary.

The positive and negative JSON receipts are stored privately under
\`/data/var/marketplace-account-setup/hpr-unity-internal-selected-installer-20261101/qa-evidence/import-identity-20261102\`.
No original Unity project was modified.

## Orchestration acceptance is stricter now

The revised QA worker's explicit new-archive version is verified
before creating a disposable project, again before import, and again
after import. After Unity returns success, it requires a genuine
\`import-identity.json\` read-only receipt with every archived asset
body and GUID matching the imported project; merely having an
HprSelectedAbilityInstaller.cs file is insufficient.

**After** the genuine Unity Play-mode stage, it now recomputes the
pre-existing customer asset/ProjectSettings/Packages hashes and reruns
the entire archive identity comparison. The final status becomes
\`failed_playmode_requires_review\` if a protected buyer file or vendor
asset changed, even if fabricated stage receipts claim PASS.

Private mock-process tests first reproduced a false success for an
older installer and both post-Play-mode mutation cases. The corrected
worker rejects them and still passes the intact simulated case. The
synthetic tests are not described as Unity Editor tests.

## Existing running worker and next verified work

The already registered \`hpr-unity-urp-broker-retry-20261102-v3\`
systemd job is **older code already loaded into memory**, currently
monitoring high Nitro CPU load and testing the previous frozen binary.
It was not interrupted, restarted, or replaced in this scheduled
continuation. If it eventually reports an old-style COMPLETE, that
receipt alone does **not** establish all the new full-byte and
post-Play-mode gates. Run the independent read-only archive and buyer
file audits on its actual project/receipts before trusting it.

For the seven-change candidate, the new worker code is **ready for
a later separately authorized, broker-managed exact-archive run**.
No new long-running automation was created after this event's cutoff.
Its clean URP 17.6 / modern-only Input System test, Built-in
customer import, actual healing and scoped-save Editor QA, visual
accessibility and independent buyer-value comparison remain incomplete.

Commercial release decision is **NO-GO**. No public publication,
purchase, provider-account action, user file deletion or trade occurred.
