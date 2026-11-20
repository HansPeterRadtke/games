# Unity installer resource-pool selection verification — November 13, 2026

The earlier buyer installer silently selected the first `IAbilityResourcePool` component when a player had two. In the buyer reproduction, casting a healing ability drained the shield pool even though the intended pool was the spell pool. The updated installer requires an explicit choice if there are multiple candidates, retains automatic selection for exactly one, and refreshes validation immediately before Attach to guard against newly introduced provider ambiguity. The buyer Quickstart now explains the explicit selection requirement.

The original commercial worktree and prior isolated candidate were not modified. The fixed source was copied into a separate new worktree and tested with Unity 6000.6.8f1 on Nitro. A disposable, separately copied Editor project verified zero, one and multiple pools; rejected a stale single-pool preview; accepted an explicit spell-pool selection; preserved the selected resource reference across a manually saved scene and reload; and cast healing with spell stamina 100 -> 80 while shield stamina stayed at 100. The relevant Unity log states `HPR_POOL_CHOICE_PASS`. The same verification was repeated in a fresh project **importing the actual newly built Unity package**, whose installer source bytes matched the candidate source. The first fixture failures were due to copying an already populated test project and to referencing a stale Unity asset object after import. The corrected disposable fixture reloads the copied ability from AssetDatabase and uses explicit Editor state refresh for detached headless controls. Therefore this is native Editor and packaged runtime verification, not proof of mouse-driven visual buyer interaction.

Evidence (private local runtime, not committed):

- `/data/tmp/hpr-pool-rollover-20261113/unity-retry6.log` — corrected isolated-source native regression.
- `/data/tmp/hpr-pool-rollover-20261113/package-build.log` — Unity export succeeded.
- `/data/tmp/hpr-pool-rollover-20261113/package-guid-identity.json` — all 161 previous asset GUIDs preserved.
- `/data/tmp/hpr-pool-rollover-20261113/package-import.unity.log` — clean buyer-project archive import.
- `/data/tmp/hpr-pool-rollover-20261113/final-buyer-qa.unity.log` — actual imported package passed resource choice, activation, save/reopen.
- `/data/tmp/hpr-pool-rollover-20261113/package-release/hpr-gameplay-systems-suite-candidate.unitypackage` — private build, not published.

Release remains gated by visual installer and URP checks and unrelated duplicate ability-ID research. No marketplace publication was performed.
