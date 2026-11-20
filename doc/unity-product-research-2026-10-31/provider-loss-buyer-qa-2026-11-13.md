# Buyer resource-provider loss: fail-closed selection after scene reload

Date: 13 November 2026. Unity version: security-patched `6000.6.8f1`. **No marketplace submission or account action**.

## Real buyer defect, independently reproduced before the patch

The currently verified HPR Gameplay Systems Suite let the buyer choose one of two `IAbilityResourcePool` components on the same player, e.g. `shield` versus `spell`. Selection initially worked: casting a healing ability charged **20 spell stamina** and left shield stamina at **100**. If the buyer removed that specifically selected component, saved the scene and reopened it, Unity deserialized the removed reference as `null`. `AbilityRunnerComponent.RefreshRuntimeBindings()` then silently discovered the surviving shield provider through `GetComponent<IAbilityResourcePool>()`. On the next cast it charged shield stamina from **100 to 80** and returned success.

This was observed in the **actual imported, unpatched customer package** in a disposable native Unity Editor project. The real log contains `HPR_PROVIDER_LOSS_OBSERVED after_loss_cast=True shield_stamina=80` and a deliberate `HPR_PROVIDER_LOSS_UNSAFE_FALLBACK` regression exception. The first attempt had a stale in-memory test asset reference and never reached the scenario; it was preserved as an unrelated test-fixture error. The corrected independent negative reproduction is in `hpr-provider-loss-20261113/retry.unity.log` on Nitro.

## Correction and compatibility

The new release stores a hidden serialized `explicitResourcePoolSelection` flag in the runner and sets it when the HPR installer assigns a selected provider. `BindRuntimeServices` also records live explicit choices. When that chosen component is subsequently absent, runtime binding **fails closed** rather than discovering a different provider, even if only one remains. The status message reports that the resource provider was removed. Explicit rebinding to a living replacement works. Only runners with **no explicit binding** can discover a component automatically, and only if exactly one provider is available. An unconfigured runner facing two providers refuses activation, not silently choosing the first.

The API/UI changes preserve the serialized and editor UX of the current training scene; there is no change to existing Unity asset GUIDs. Existing manually authored Inspector references from older source versions acquire a runtime explicit lock on refresh, but earlier scenes do not retroactively contain the persisted flag until reauthored/saved with it. The new HPR installer is the verified persistence path; do not overclaim automatic migration of every custom Inspector-authored reference.

## Verified current corrected buyer archive

- Exported with the installed patched Unity Editor; builder and release checks passed.
- Compared with the previous package: **161 of 161 asset GUIDs unchanged**, no added or removed archive assets.
- Imported the **new actual `.unitypackage`** in a fresh disposable Unity project; importer native exit zero and exact archive identity PASS across **161 assets, 55 C# scripts and all metadata**.
- Re-ran the original native scene-reload regression, including two providers, explicit selection, deletion, save, reopen, refusal without spending, explicit replacement, sole-provider discovery and ambiguous-provider refusal. All passed with Unity exit zero. The repaired log says `after_loss_cast=False shield_stamina=100`, `HPR_PROVIDER_LOSS_SAFE_AND_EXPLICIT_RECOVERY_PASS` and `HPR_PROVIDER_IMPLICIT_SOLE_AND_AMBIGUOUS_PASS`.
- Added two native NUnit module regressions for the resource-provider lifecycle and unconfigured multiple pools. The native module runner **passed all 62 of 62 cases** across ten assemblies with zero failed/skipped cases, native exit zero and exact package identity. No original protected customer project file changed across the 358-file native QA baseline.
- The independent imported-showcase **real Unity Play Mode** suite passed all eight gameplay checks: lifecycle/bindings, collision movement, enemy pursuit, composition/world, typed combat, stamina/healing, weapons and checkpoint restoration. No native compiler errors or managed exceptions in the acceptance log.
- The complete Python Unity source regression suite passed **391 tests** with no failures.

## Reproduction and evidence

The exact buyer-regression source resides in `unity/tools/release/gameplay_suite/qa/ProviderLoss/ProviderLossVerifier.cs` with `BuyerResourcePool.cs`, staged only into a **new disposable project** already imported from the exact customer archive. From the patched Editor, run the `HPR.Qa.ProviderLoss.ProviderLossVerifier.Run` method in batchmode. It creates only private buyer assets and an independent scene. Do not retry in an existing test project; the fixture requires the target assets not to exist.

The canonical native QA driver is `unity/tools/release/gameplay_suite/qa/NativeEditMode/run_native_editmode.py`, with the **actual imported archive, successful native import receipt, archive SHA-256 and a fresh output path**. The canonical Play Mode driver is `qa/run_verified_playmode.py` with a fresh clone of the imported buyer project. Both refuse ambiguous/old source and receipts.

Private Nitro evidence, outside Git:

- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/retry.unity.log` — negative pre-fix package demonstration.
- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/fixed-native.unity.log` — actual fixed customer package regression.
- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/build-fixed.log`, `release-fixed/` — real patched editor build and archive.
- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/upgrade-guid-check.json`, `fixed-import-identity.json` and `fixed-import.unity.log` — package and actual import identity.
- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/native-nunit/RESULT.json`, `test-results.xml` — native all-module evidence.
- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/release-fixed/actual-playmode-receipt.txt`, `actual-playmode.unity.log` — eight real Play Mode checks.
- `/data/var/marketplace-account-setup/hpr-provider-loss-20261113/complete-python-suite.log` — source Python regressions.

## Remaining release boundaries

This fixes **one real silent wrong-resource debit**, but does not provide customer approval, prove all forms of manual Editor/Inspector assignment, or replace normal graphical Editor UX/accessibility testing. In the normal graphical Unity Editor the previously observed software-terms dialog remains an owner-consent gate and was not retried/bypassed. Standalone URP + new-input-only Player compatibility and buyer-value differentiation need independently scoped evidence; never treat shader compilation or static source tests as a graphical or commercial release. No source data, personal tabs, customer project or external account was modified; the original fourteen dirty seller files remain protected.
