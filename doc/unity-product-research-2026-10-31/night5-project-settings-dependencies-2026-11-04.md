# November 4 night five: ProjectSettings dependency blind spot fixed

## Verified defect and change

The read-only uninstall dependency preflight scanned Assets and embedded Packages
but completely omitted ProjectSettings. Test-first cases reproduced missed vendor
GUIDs in EditorBuildSettings.asset, GraphicsSettings.asset and QualitySettings.asset.
Oversized, binary/non-UTF8 settings and unsafe settings roots were silently omitted
rather than reported/rejected. The old detector still denied deletion in every
case; the defect was missing dependency/review evidence, not an authorization to
uninstall.

The scanner now includes optional ProjectSettings under the same single traversal
budget, byte ceilings, decoding and symlink safeguards as other project content.
Known vendor GUIDs there have a separate project_settings_vendor_guid finding with
an explicit settings/migration review action. Missing or unrelated settings do not
invent dependencies. Non-directory or symlinked settings roots/children are refused;
unreadable content remains unknown/review-required. All previous asmdef/asmref,
importer metadata and embedded-package behavior remains covered.

Six new regression methods produced nine negative subcase failures before the fix.
Afterward all 40 uninstall/preflight regression methods pass, alongside 13 existing
safe-upgrade preview tests. Four additional output-routing safety tests pass for the
new private native fixture. The helper's original nested-source-output check was
missing; two controlled false acceptances were reproduced before refusing output
inside the original template, including parent symlink aliases. No real source
project was written by those tests or by the native run.

## Actual Unity serialization proof, not hand-authored YAML only

One separately admitted, resource-capped Unity 6000.6.7f1 batch process operated on
a new vendor-only private project copy. It loaded the actual imported SceneAsset
and used public EditorBuildSettings.scenes / EditorBuildSettingsScene APIs to add
that scene to the build list. It exited zero in 96.9 seconds. The resulting native
ProjectSettings/EditorBuildSettings.asset contains:

- enabled scene: Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity
- scene GUID: 4da0644b7fd1cbd7b9f70bd2b208b822

That GUID independently comes from the exact 161-identity private archive, not a
synthetic invented GUID. The before/after detector comparison reads the **same
Unity-saved file**. The frozen previous implementation reports
no_direct_reference_detected with no dependency/unknown findings. The corrected
implementation reports customer_dependencies_found with exactly the build-settings
reference and the expected vendor scene. Both versions retain deletion_permitted
false. All 322 project input files remain byte-identical across those inspections.

Only the new copy's existing EditorBuildSettings.asset was intentionally changed
by Unity's authoring process. The source template's full Assets/Packages/ProjectSettings
inventory is unchanged; all 55 vendor C# files remain exact. No user source, scene
or existing original setting was rewritten. The fixture performs no package import,
removal, Player build, global SaveAssets, graphical interaction or publication.
Unity may create new private importer metadata normally. The native log scan has
zero matching C# error, managed Exception:, CS0618/CS0612 or GTK/GLib critical markers;
this is a bounded log check, not visual acceptance.

## Composed upgrade guard check

The complete read-only safe-upgrade preview was also run on that same native project
with the **same pinned archive on both sides** as an identity-only control. Its
actual vendor verifier confirms all 161 installed identities. Selecting the frozen
old detector produces source_preconditions_verified_editor_acceptance_required;
selecting the corrected detector produces review_required_customer_dependencies,
with exactly one ProjectSettings finding. Both preserve all customer input hashes,
deny automatic upgrade and deny deletion. These are real detector implementations
and file scans, not fabricated dependency lists, but the same-archive identity
control is not a distinct-version upgrade or actual import/migration acceptance.

## Source and preservation

Branch: qa/unity-project-settings-preflight-night5-20261104, based on the completed
lifetime-fix branch. Product runtime and the current private archive are unchanged:
83ea196924d966175c33b07173fa94e69831369df86a71783f9f2a9c20338292.
The earlier 56-case native NUnit and configuration/gameplay evidence therefore
remains scoped to those exact unchanged product bytes. No new gameplay/NUnit/URP
execution is claimed in this continuation.

Private runtime:
/data/var/marketplace-account-setup/hpr-project-settings-preflight-night5-20261104/.
It retains frozen pre-fix source, failing/passing tests, native launch/log/receipt,
Unity-saved fixture, before/after detector reports, identity-only preview reports,
and final preservation audit. All twelve earlier worktree heads/statuses and all
21 original dirty-file hashes match the snapshot. Original archives and earlier
customer save hashes remain unchanged. The one admitted native job is exited with
zero remaining cgroup processes. Python compilation/whitespace checks also pass.

The resource-denied URP and inactive-URP operations were not retried or disguised.
The graphical software-terms gate was not reopened or bypassed. Commercial release
remains **NO-GO** pending the existing new-candidate matrix, rendered Editor/URP
usability, source/installer reconciliation, full dependency-aware migration/uninstall
and independent buyer validation. This narrowly improves dependency review; it
never declares uninstall safe or authorizes deleting any customer/vendor content.

First-party API evidence reviewed:
https://docs.unity3d.com/kr/current/ScriptReference/EditorBuildSettings-scenes.html
https://docs.unity3d.com/cn/current/ScriptReference/EditorBuildSettingsScene.html
