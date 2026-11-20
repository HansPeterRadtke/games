# Unity URP dependency-compiler timeout — evidence and limited first-party cross-check

Observation date: November 1, 2026. Nitro runs Unity 6000.6.7f1 and
Unity 6000.4.0f1 (and legacy 2022.3). Do not infer this note authorizes
an Editor upgrade, stopping other agents' jobs, clearing caches, or
replaying a failed import on a possibly inconsistent project.

## Measured independent reproductions

One earlier HPR selected-installer candidate URP 17.6/input-only project
copy, with previous Unity Library, timed out after six hundred seconds.
The private Editor was still in bee_backend/Unity.ILPP.Runner while
compiling existing packages; the new HPR Editor script did not yet exist.
Sixty prior customer-owned files remained byte-identical.

A *second, separate fresh Unity project* with the previous known URP
settings and renderer but **no Library, no HPR source and no vendor scenes**
also spent its entire bounded nine-minute invocation in Unity Bee/ILPP.
Its thirty-five original ProjectSettings/Packages/renderer files remained
byte-identical. The frozen exact archive had not been extracted.

The process then exited status 124. No HPR compilation occurred, and
there was no observed C# compiler error from HPR. This is a genuine
**test infrastructure blocker**, NOT a passed exact-archive URP
compatibility test. All failed logs and snapshots are preserved,
including per-process timestamps under the private QA evidence root.

## Measured CPU resources

During the second run Nitro had eight CPU cores in effective affinity.
Linux one-minute runnable load averaged approximately sixty to
seventy-five with CPU some-pressure in the mid-eighties or higher.
Unity and its child compiler processes were scheduled with nice ten.
The Editor's process scheduler statistics showed significant runnable
wait time. Other independent owner jobs were consuming CPU, and none
were killed, reniced, preempted or rescheduled for this test.

A separate deterministic, read-only admission estimator now checks
current affinity, one-minute load, and CPU some avg10 pressure, and
returns **defer** at those conditions. It is not a CPU reservation, and
high load alone cannot identify the precise ILPP cause.

## Primary Unity evidence found in official sources

The official Unity Issue Tracker lists known issue **UUM-142773**,
"Crash on mono_log_write_logfile when more than one copy of bee_backend is
running", applicable to tested Unity 6000.6.7f1 and fixed by Unity
6000.6.8f1 and 6000.7.0b7. It has exact reproduction steps for
interrupted/reopened URP projects, including input-setting changes and
lingering Bee processes. Original first-party Unity issue:
https://issuetracker.unity.com/issues/12297
The Unity 6000.6.7f1 release-notes page also records this as an active
known scripting-build-time blocker:
https://unity.com/releases/editor/whats-new/6000.6.7f1

**Important non-equivalence:** Unity's issue was reproduced on Windows,
and its canonical failure includes an explicit "more than one copy of
bee_backend running" diagnostic. Our current Linux log has NOT shown
that exact signature or a confirmed second Bee process in this project.
We cannot assign our timeouts to UUM-142773 on this evidence alone.
The issue is relevant when planning a different Editor version and
careful single-editor/clean process acceptance, not an established fix.

Unity's separate official Burst Issue Tracker explains that IL
postprocessing adds compilation work even when Burst itself is disabled,
and this is expected (though not ideal). This supports the observation
that URP/postprocessing may require substantial CPU, without explaining
a nine-minute stall by itself:
https://issuetracker.unity.com/issues/15507

A January–March 2026 Unity forum discussion separately reports a
managed InputAction/Entities ILPP hang later corrected in Entities
1.4.5. That example involved Entities assemblies that are NOT part of
our baseline manifest, so it is not evidence that the same codepath
caused the current run:
https://discussions.unity.com/t/unity-editor-hangs-on-compilation-postprocessing-il-for-assembly-csharp/1703453

## Safe next step

Before another real URP test, verify the available Unity Editor
versions and CPU resources, run a *new* unique disposable project when
actual CPU admission is reasonable, and record Unity process exit,
logging, package/engine versions, and hashes. If an owner later elects
to install a patched Unity six point six Editor, compare actual import
behavior in that version **without** assuming the known issue caused the
old failure. Never interrupt active owner processes to manufacture
extra CPU or erase prior negative evidence.

The new selected-installer archive remains technically only partially
qualified for Unity 6.6 URP with new Input System; commercial verdict
remains NO-GO for additional independent buyer/value reasons.
