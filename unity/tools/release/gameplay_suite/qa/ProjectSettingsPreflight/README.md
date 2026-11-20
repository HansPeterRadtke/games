# Private native ProjectSettings dependency fixture

This is not a customer uninstall or migration tool. The create-only driver copies
only the exact vendor Assets plus Packages/ProjectSettings/Library from an already
successful native private import, then stages the tiny Editor fixture. Source
projects stay untouched. Launch it through an owned, resource-capped broker job.
Use `run_native_settings_fixture.py --help` for required explicit archive checksum,
installed Editor, successful import receipt, template and fresh private output.

The fixture uses public EditorBuildSettings.scenes and EditorBuildSettingsScene to
select the real imported demonstration SceneAsset in the new disposable project.
Unity saves its own ProjectSettings/EditorBuildSettings.asset. It never starts a
Player build, deletes a package, modifies the original template or globally calls
AssetDatabase.SaveAssets. A successful receipt requires native exit zero, the real
archived scene GUID in Unity's saved file, exactly the intended existing copied
settings-file change, all 55 product scripts exact and the source template's full
Assets/Packages/ProjectSettings inventory unchanged.

The read-only uninstall preflight can then inspect that file against the exact
archive GUID inventory. It should report project_settings_vendor_guid and require
review. Do not treat absent direct references as safe removal. Binary/reflection/
externally resolved references and actual migration still require separate work.

Output must be new and outside the source template, including resolved parent
aliases. Four controlled routing tests cover separate output, refusal to replay,
external symlink escape and accidental nested/aliased writes into the source.
Two nested-output false acceptances were reproduced before the final guard. These
Python routing regressions are separate from actual native serialization evidence.
The first native run already used separate output; this post-launch guard addition
did not rerun or change that native execution or its source-preservation result.

See the dated night-five report for actual positive/negative native-file detector
comparison and the unchanged-archive identity-control upgrade preview. No graphical
Editor/Build Profiles usability, complete uninstall, Player behavior, seller release
or commercial approval is implied.
