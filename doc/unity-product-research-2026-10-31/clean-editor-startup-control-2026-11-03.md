# Unity 6.6 startup / Play search-index control — November 3, third continuation

## Measured question and boundary

The earlier HPR existing-game functional tests completed their named contracts but
logged ArgumentOutOfRangeException in UnityEditor.Search.SearchDatabase.EnumerateAll,
GetDefaultSearchDatabase and SearchInit.IndexationOnStartup. They were not clean-console
acceptance. This sprint tests whether HPR, copied project caches, the new Input
System or a null graphics device are necessary for that observed exception.

All six controls were genuinely created through the installed Unity 6000.6.7f1
`-createProject` command in unused private folders. No existing Library, HPR source,
HPR archive, scene or material was copied into them. The only Assets C# source was
the private namespaced static Editor observer. Native assembly observations found
zero HPR assemblies. Each Native create and observe process exited zero, and all
24 original project files remained byte-identical after explicit setup. The
Input System case separately configured official package 1.20.1 and new-only input
in its own new project, completed native package resolution, then took its baseline.

`CONTROL_VALID` means the control ran and observed its defined conditions. It does
**not** mean there were no errors: the specific search-exception flag is separate.
The quality regression criterion is no matching Search exception during the observed
startup / two-session sequence. Immediate Play controls violate it; the settled
control passes it. No engine error was hidden, patched or reclassified as harmless.

| Private case | Observed action | Actual graphics API | Input package | Edit wait before Play (s) | Matching Search exception | Native observe exit |
| --- | --- | --- | --- | --- | --- | --- |
| clean-66 | Edit startup | Null | default legacy | 0 | False | 0 |
| clean-66-software-gl | Edit startup | OpenGLCore | default legacy | 0 | False | 0 |
| clean-66-play-off | two Play sessions | Null | default legacy | 0 | True | 0 |
| clean-66-input-play-off | two Play sessions | Null | 1.20.1 | 0 | True | 0 |
| clean-66-gl-play-off | two Play sessions | OpenGLCore | default legacy | 0 | True | 0 |
| clean-66-settled-play-off | two Play sessions | Null | default legacy | 20 | False | 0 |

The software-graphics cases ran in their own Xvfb displays and observed OpenGLCore
with Mesa llvmpipe, not a physical NVIDIA GPU or a human desktop. The startup-only
cases observed twenty seconds of Editor updates and the actual startup-indexing log.
The Play cases completed two sessions with domain reload disabled and scene reload
enabled. Their observed duration was approximately twenty-five seconds; the settled
case measured about twenty seconds in Edit mode before requesting Play and about
forty-two seconds overall. No perceptual UI, screenshot, physical input or Player
build acceptance follows from those observations.

## Interpretation

The same Search exception and source frames reproduce without HPR and without copied
Library caches. Neither HPR, the Input System package nor a Null graphics device is
necessary for this reproduction. This is not proof that those factors can never
contribute to a different issue. Startup-only controls are clean in the observed
window; entering Play immediately from the automation entry point triggers the
observed failure. Draining startup in Edit mode before Play removed it in the
paired fresh-project control. This supports an automation/startup-order interaction,
not a proven universal Unity defect, a known issue ID, or a general engine fix.

The relevant public first-party command-line contract is
https://docs.unity.com/en-us/engine/6000.6/manual/unity-editor/command-line-arguments/editor
It documents empty-project creation, executeMethod and graphics/batch behavior.
The observed delayed-indexing interaction is a local executable finding, not a
claim that the manual promises this particular twenty-second workaround. No exact
matching authoritative issue/fixed-version claim was verified in the search.

## Private QA change and real package follow-up

The existing-game QA validator has an **opt-in** RunAfterStartup entry point selected
by `--settle-editor-startup`. It waits at least twenty Editor seconds and checks
public isCompiling/isUpdating before calling the unchanged scene/health/input/save
workflow. The native gameplay observation contract stays exactly sixteen names.
The product's 55 archived C# files and all runtime behavior are unchanged. This
is not a delay added to customer GUI or gameplay and is not an internal API patch.

A create-only real buyer-archive follow-up completed in a separate copy of the
verified fresh Input System no-HPR project, using rebuilt copied databases, the
same pinned reviewed archive and domain reload disabled. It performs a new native
archive import rather than reusing an old import receipt. Its own native import and gameplay processes both exited zero. All sixteen
named observations passed in 235.2 seconds: queued input reached the existing action,
authoritative existing health/stamina and HUD data changed, cooldown and subscription
lifetime behaved as defined, the save roundtrip restored state, and optional detach
preserved the original action and scene bytes. All 27 original nonvendor files were
unchanged through archive import, all 36 post-staging protected files were unchanged,
and all 55 packaged C# files matched the pinned archive after Play mode.

The complete native import and gameplay logs contain no matching Search exception,
no managed-exception marker, no C# compiler-error marker and no CS0618/CS0612 obsolete
API warning marker in the recorded scan. This is specifically a log/functional result;
it is not proof of a visually reviewed Inspector or all possible Editor warnings.
The first delayed no-product control isolated startup ordering; this package follow-up
also uses a fresh control-derived template rather than the older QA templates. It
therefore does not assign the package result to a single changed variable or certify
all previous templates. The original immediate-Play error evidence is preserved.

## Evidence and release boundary

The reusable private sources are under
`unity/tools/release/gameplay_suite/qa/CleanEditorControl/`.
All raw launch metadata, private broker receipts, native observations, full create,
configure and observe logs and before-file hashes remain outside Git under
`/data/var/marketplace-account-setup/hpr-clean-editor-control-20261103-wave3/`.
Final audits at 15:34–15:35 UTC matched all seven original worktree heads/status
and all 21 dirty-file hashes. All seven owned jobs were exited with zero cgroup
processes. The original private archive checksum remains unchanged. Runtime records
`ORIGINALS_AFTER.json` and `FINAL_PROCESS_ARCHIVE_LOG_AUDIT.json` retain those checks
and both complete log hashes. The isolated source changes are committed and pushed;
no owner dirty file, product archive, account or published asset was changed.

Commercial release remains **NO-GO**: these controls do not establish competitive
differentiation, an external buyer task result, rendered Inspector usability,
physical input, full customer uninstall/migration or approval of the dirty owner
source integration. No marketplace, account or publication operation occurred.
