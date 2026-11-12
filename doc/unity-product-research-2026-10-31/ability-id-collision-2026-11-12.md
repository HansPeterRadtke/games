# Two ability definitions sharing one gameplay ID

Unity 6000.6.8f1 reproduced an incorrect cast in the private package built from `1fe2558`, SHA-256 `9640f2a08a0b3e4db3e6abd68fdcdbc6ccc51134e7cc9c3c5bdeb717f2aea533`. The native runner verified the imported archive before and after the test. The two sample abilities in the supplied showcase have distinct IDs. This defect affects a buyer loadout that gives different definitions the same ID.

The fixture places Ward, Sprint and Heal in that order. Ward and Heal have the same ID. Ward costs five stamina and has no healing effect. Heal costs twenty-five and heals twenty. Activating slot zero returned success, spent twenty-five stamina and raised health from fifty to seventy. This happened with both the public configuration API and a list set through the serialized Inspector field. The slot looks up its definition again by ID, and the runner overwrites the earlier definition when it builds that lookup.

The regression covers the expected refusal by ID and by either conflicting slot, the HUD, resource callback counts, cooldowns, save and restore, the independent middle slot and recovery after the buyer assigns a unique ID. Both cases stopped at the first assertion on the current product. The other fifty-six native cases passed. The reference copy of the imported project retained all of its protected files.

## Buyer workaround

Give distinct abilities on the same runner distinct gameplay IDs. Check the **Id** field when authoring a loadout, including after duplicating a ScriptableObject. Changing the file name or display name leaves the gameplay ID in place. The Integration Guide assigns new IDs when copying its samples. The retained customer fixture has independent IDs for both its copied healing ability and its effect. Keep IDs stable after using them for saved unlocks and cooldowns.

## Verification checkpoint

The QA branch contains the reproducer and buyer guidance. The native XML is in `/data/var/marketplace-account-setup/hpr-ability-id-collision-20261112/baseline/test-results.xml` on Nitro. `baseline-confirmed.json` records the two failing assertions. The candidate runtime correction is preserved in the same directory as `proposed-runtime.patch`. It detects conflicting definitions, keeps their original slot positions and reports the ID when activation is refused.

Nitro's central resource broker declined the candidate native run and a separate compiler and archive audit for insufficient capacity. Neither job started. The candidate still needs a successful managed compile, a native run of all fifty-eight tests and validation in a freshly exported package. The native Test Runner command is documented in `unity/tools/release/gameplay_suite/qa/NativeEditMode/README.md`.
