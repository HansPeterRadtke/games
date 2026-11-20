# Private native buyer provider-loss regression

These sources are **not** included in the buyer Unity package. Stage `BuyerResourcePool.cs`
under `Assets/BuyerLossQA/` and `ProviderLossVerifier.cs` under `Assets/BuyerLossQA/Editor/`
in a **new disposable Unity Editor project** that actually imported the exact
HPR `.unitypackage` and has no existing `BuyerLostProvider*` files. Invoke
`HPR.Qa.ProviderLoss.ProviderLossVerifier.Run` in patched Unity batchmode.

The test selects the spell pool, casts once to verify the selection, deletes it,
saves and reloads the scene, asserts no silent shield debit, explicitly rebinds
and casts, and tests single versus ambiguous implicit discovery. Inspect native
exit, named log markers, and the original archive identity before accepting.
The negative run must show an actual incorrect debit, not merely a different
fixture or compilation failure. No graphical/editor-consent or publisher action.
