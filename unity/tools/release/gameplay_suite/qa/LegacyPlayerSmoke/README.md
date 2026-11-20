# Private legacy-only Linux Player smoke

These two fixtures are never included in the buyer archive. Stage the builder in
a fresh private project's Editor folder and the probe outside Editor, using an
exact already-native-imported archive template with activeInputHandler 0 and no
Input System dependency. Run only through a bounded owned resource-broker job.
Never stage into a live buyer project or reuse uncertain/completed output.

Set HPR_INPUT_STANDALONE_EXE to a fresh private Linux executable path and invoke
LegacyInputPlayerBuilder.Build in the installed Editor. The builder saves a new
private empty scene and requires successful BuildReport plus an actual binary.
Both fixtures reject compile paths other than legacy enabled / new input disabled.
Set HPR_LEGACY_PLAYER_RECEIPT to a new private receipt, then run the generated
Player with -batchmode -nographics and a separate log. After ten real game frames,
the probe requires both packaged KeyCode.None queries to remain false, writes its
version plus three PASS observations and exits zero. Failure logs the exception
and exits nonzero; a receipt alone never overrides the actual process exit.

This is package compilation/startup and unbound-key smoke coverage. It does not
simulate or certify physical keys, held/edge transitions, pointer behavior,
rendered output, full gameplay or commercial readiness. Hash protected source,
settings and package files before/after; verify all 55 archive scripts and every
asset/GUID identity. Independently inspect the actual non-Editor Player compiler
response for legacy enabled and new input absent. Preserve all earlier results.
See the dated legacy Player report for the actual Unity 6.4 outcome and retained
private orchestration/evidence. Neither arbitrary prior results nor this README
are permission to launch a new job or alter an owner's input settings.
