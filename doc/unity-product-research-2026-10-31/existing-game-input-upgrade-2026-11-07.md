# Existing integrated game: native input-fix package upgrade

## November 7 actual upgrade result

A fresh clone of the previously tested lifetime-fixed game successfully upgrades
through actual Unity **6000.6.7f1 ImportPackage** to the corrected input archive.
All **139** protected customer assets, embedded-package files and project settings
remain byte-identical. Across the complete Assets/Packages/ProjectSettings file
inventory, including vendor files and metadata, **exactly one file changes**:
`Assets/HPRGameplaySuite/Integration/HprSuiteInput.cs`. Native import exits **0**
in **92.2 seconds**. Full new archive identity passes all **161** asset paths,
**133** payloads and **161** GUID identities.

A separate fresh process/copy of this upgraded project then passes all **15**
cold-save observations, exits **0** in **128.9 seconds**, and preserves all **140**
staged protected files and all **55** exact packaged scripts. Total import,
post-upgrade cold workflow and preservation checks take **222.8 seconds**. The
existing scene, customer-created ability/effect assets, input bindings and disk
save are reused; no replacement integration scene or settings are generated to
make the test pass. The representative game is self-authored QA, not a purchaser
project or independent buyer study.

## Exact transition and preconditions

Old private lifetime archive SHA-256:
`83ea196924d966175c33b07173fa94e69831369df86a71783f9f2a9c20338292`.
New private input archive SHA-256:
`3a3e2170680fc2c73730e39dacfdfb266b86727dc5751093b09aa01ba609a3bb`.
The old source is `green-66-workflow/project` under the night-four lifetime task,
which already has successful actual native import and full workflow receipts.
All old asset payloads/GUIDs are independently verified before cloning/import.
The exact integrated scene is selected as the unique scene created after that
workflow's staged baseline, rather than guessing among historical scenes.

The existing read-only upgrade preflight returns
`review_required_customer_dependencies`, finding **47** HPR dependencies with no
foreign GUID collision and exact old installation before/after its scan. This is
an appropriate review gate, not a failed native import or automatic permission.
The owner-authorized experiment uses only disposable private copies; it never
upgrades a live game or changes the report's automatic-upgrade prohibition.

A create-only broker-owned script clones the old native project, saves both the
customer inventory and complete file baseline, performs native import, then
requires zero customer changes and exactly the one expected vendor source delta.
If that gate fails, it stops before gameplay. Only after passing does it call the
existing cold-workflow driver with the newly upgraded project/import receipt,
exact new checksum and existing old scene/save. The cold test operates in a further
fresh copy so the upgraded proof project itself remains unchanged.

The save restores health **60**, stamina **80** and **30 seconds** remaining
cooldown. Input during cooldown causes no extra charge; a malformed snapshot is
rejected without changing state. After about **30.2 game seconds**, cooldown
expires, the existing input activates, health becomes **80**, stamina **60** and
HUD data updates. Original scene and source/copy save bytes stay identical. This
is relative game-clock restoration with offline time paused, not wall-clock expiry.
The cold process ID matches an independent live OS observation and differs from
both the original workflow and the upgrade-import process.

## Retained evidence and preservation

Private runtime:
`/data/var/marketplace-account-setup/hpr-input-upgrade-20261107-serial1/`.
`run_upgrade.py` is the retained create-only orchestration. SELECTION.json pins
source/scene/save and both archives. READ_ONLY_PREFLIGHT.json preserves the review
findings; SOURCE_TEMPLATE_BEFORE.json, CUSTOMER_BEFORE.json and
ALL_PROJECT_BEFORE.json preserve before hashes. IMPORT_LAUNCH.json,
UPGRADE_IMPORT_RESULT.json and upgrade-import.log preserve the actual transition.
COLD_LAUNCH.json and `cold-after-upgrade/` retain the actual fresh-process commands,
raw observations, native result/log, copy and protected baseline.

FINAL_AUDIT.json records exact native results, evidence/script hashes, the observed
cold process, ownership and preservation. FULL_IDENTITIES.json independently
verifies the unchanged old installation, upgraded project and cold project against
their respective archive checksums: every target passes all 161 asset/GUID checks.
All **433** original source-template file hashes and the source scene/save remain
unchanged. All **13** earlier Unity worktree heads/statuses and **21** original
dirty-file hashes remain unchanged. Both original archives retain their pinned
hashes. The owned job exited with zero cgroup processes. Broker control receipts
stay private and are not committed. No production/source/archive code changed in
this continuation; the owned repository changes are this report and its index.

The import log has zero scanned C# errors, managed-exception, obsolete-warning,
private UAC0005, GTK-critical or GLib-critical markers. The cold log has zero C#,
managed-exception or obsolete-warning markers, but retains five private
CleanEditorControl UAC0005 warnings and two headless GTK teardown critical messages.
These are disclosed rather than calling the entire Editor warning-free.
The existing **13** upgrade-preview tests and **13** workflow receipt tests pass
separately; the private script compiles and tracked edits pass whitespace checks.
Those Python methods are not additional native upgrade/gameplay cases.

## Remaining gates

This is one real, single-payload private package transition on one self-authored
Built-in/new-input integration fixture. It does not prove arbitrary customer
upgrades, rollback, uninstall, source/installer reconciliation, full Player
migration, rendered Inspector/HUD usability, URP or independent buyer value.
No earlier denied URP operation or graphical software-terms gate was retried or
bypassed. The preflight continues to require dependency review; this result is
not blanket automatic-upgrade approval.

Commercial release remains **NO-GO** until those compatibility, migration,
usability and buyer/comparator gates are resolved. No seller-source merge,
marketplace publication, purchase, outreach, account change or reminder occurred.
