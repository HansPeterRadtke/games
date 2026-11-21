
### Safe upgrades and scan responsiveness — development follow-up

The second unpublished candidate increment adds path/GUID identity snapshots,
strict same-root comparison of old versus new versions, and fail-closed
reporting for removed assets, changed GUIDs, moved paths and added assets.
The built-in Unity Editor progress panel is cancelable; canceled or truncated
scans cannot be reported clean. Real prefab/asset rename, deliberate GUID
replacement and negative snapshot fixtures belong to the private native QA
rather than buyer archives. This is a static preflight only, **not** automatic
upgrade repair or certification of runtime/serialized-reference compatibility.

The actual normal GUI layout, keyboard interaction, responsive resizing and
marketing screenshots still need non-batch human-visible native Editor testing.
See `qa/UI_CONTRACT.md`; never use an invented editor capture or claim seller
approval based only on source or batchmode tests.

## Real existing-buyer upgrade acceptance — native, not synthetic

The internal `qa/run_real_buyer_upgrade.sh` recreates a **genuine buyer
existing-project upgrade** from the original November 21 five-asset Unity
package into the later six-asset package. It uses a NEW disposable project
for each run: first import the old archived `.unitypackage`, create a real
buyer-owned runtime `ScriptableObject` referencing the vendor README, save
customer assets, record SHA-256 of every file and original vendor GUIDs,
then import the newer Unity export **into the same project** and verify the
old metadata identities and customer bytes. Finally, the actual exported
`HprBoundaryUpgradeReview.Compare` code must report `ADDITIONS_ONLY`, one new
Editor script, no removals, GUID replacements or unexpected path moves.

Reproduction on authorized Nitro from this source checkout, with exact
private archive evidence already present:

    qa/run_real_buyer_upgrade.sh 2022.3.22f1 NEW_UNIQUE_RUN_LABEL
    qa/run_real_buyer_upgrade.sh 6000.6.8f1 NEW_UNIQUE_RUN_LABEL

The runner refuses to reuse a previous destination and never deletes an
existing project, publishes a product, downloads dependencies, edits a buyer
project or accepts software terms. It operates ONLY in a new private test
project under the owner's marketplace-account-setup QA directory, from
previously built original first-party packages. The original `.unitypackage`
archives are not modified. Internal QA sources must never be included in a
customer release.

November 21 wave forty-nine: both Unity 2022.3.22f1 and Unity 6000.6.8f1
returned independent native `HPR_REAL_PACKAGE_CUSTOMER_UPGRADE_RESULT=PASS`.
Both preserved **five original vendor GUIDs**, **six customer files** and a
real serialized buyer reference; the added script was the **only** vendor
path change. Exact current results are in private directories named
`boundary-upgrade-2022-3-22f1-native2` and
`boundary-upgrade-6000-6-8f1-native1`. An initial `native1` Unity 2022
negative test used an Editor-only test `ScriptableObject`, serialized with
`m_Script: {fileID: 0}`, and could not reliably resolve it after an Editor
restart. The fixture was replaced by a normal customer-side runtime assembly
script, and only that corrected fresh test passed. The failed run is retained
as a warning not to misattribute private QA harness defects to buyer products.

**This demonstrates one exact old-to-new installed archive pair.** It does not
verify all legacy versions, paid UPM migrations, arbitrary customer changes,
UI usability, every Unity Editor update, license/AI disclosure or Asset Store
publisher approval. Actual visual and commercial gates remain separate.
