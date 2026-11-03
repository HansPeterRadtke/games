# Private existing-game input/health integration experiment

This is QA and customer-integration example code, not a new shipped product.
The representative game is self-authored; it is not an external buyer's project.
No existing owner project is edited. Use the create-only driver in a broker-owned,
CPU/memory-capped process and keep its output below the private marketplace QA
runtime directory. Do not run this against a live game or publish these fixtures.

## What the test observes

`ExistingGameVitals`, `ExistingHealInput`, `ExistingHealthDisplay` and
`ExistingGameSave` define the independent game's health, action, HUD data binding
and explicit save-extension seam. These files have no HPR namespace dependency.
The two HPR-prefixed adapter components explicitly connect those existing APIs
to the packaged runner; they do not introduce another health/stamina store.
Their code and configuration are part of the customer's integration burden.

The private native validator creates and saves an independent original scene,
then authors a separate integrated scene with customer-owned ability/effect
assets. It invokes the actual packaged selected-object installer and reopens the
integrated scene before Play mode. Native InputSystem KeyboardState events drive
the game's action callback; the acceptance checks observe authoritative health,
stamina, cooldown, HUD data, disable/enable subscription lifetime, a real JSON
save/load roundtrip and removal of only the optional runner/input connection.
The original scene stays byte-identical. No physical keyboard or rendered HUD
appearance is certified by a headless test. Save/load currently restores in the
same running scene; a full application restart remains a separate test.

The `shadow` scenario deliberately supplies the older independent QA health
store. It is a valid negative control ONLY if real input reaches the runner and
the test then fails on unchanged authoritative customer health. A compilation
failure or an arbitrary native error is not a successful negative control.
The `wired` scenario uses the explicit existing-vitals adapter. Acceptance
requires every distinct named observation, native exit zero, no failure marker,
all original protected files and all fifty-five exact archive C# files.

## Reproducible run requirements

Use installed Unity 6000.6.7f1 and the existing cached Input System 1.20.1 template.
Pin the exact reviewed archive through the driver's explicit checksum argument.
Every invocation needs a fresh output directory; completed or uncertain output
must be inspected rather than replayed. Driver arguments select the template,
archive, installed Editor, scenario, domain reload on/off and bounded maximum
wall time. Invoke `run_native_workflow.py --help` for the complete interface.
Use a separate invocation for each scenario/reload condition, never concurrent
Editors against one project. Resource admission and the owner's current cutoff
apply independently of this driver's per-process timeout.

The driver first copies only the project's Assets, Packages, ProjectSettings and
Library into its own new project. It explicitly configures domain reload only
in that copy. It launches a native archive import BEFORE copying new probe
scripts, because Unity compiles existing scripts before processing a command-line
import. Before bootstrap import, the driver now hashes every existing nonvendor asset, package and project-setting file after applying the explicitly requested reload flags in its private copy. A changed or missing original file fails the run before probe staging. It then launches the new test without `-quit`; the validator exits after
its asynchronous Play-mode phases finish. The runtime output retains separate
import and gameplay logs, before-file hashes and an independent result receipt.

## Failure evidence and verification levels

The first standalone API compile exposed five missing required default arguments
to SessionState.GetString in the new private fixture. That was corrected and the
sixty-three-source standalone API compilation passed with zero errors and the
same fifteen serialization-field warnings as the prior packaged-code baseline.
This is an API check, not a native Editor result.

The first native staging attempt compiled the probe before the new archive was
imported. Its compiler failure and five old-vendor-source mismatches were retained.
The corrected driver separates import from probe staging rather than mutating or
rerunning that first project. Native scenario receipts are the authority for
whether the corrected experiments actually completed; do not infer their outcome
from this README or a running broker job.

Eight deterministic receipt-classifier tests cover the full positive contract,
every missing observation, duplicated pass lines, contradictory failure evidence,
wrong exit status, unknown scenarios and the specific shadow negative control.
Three genuine classifier false positives were reproduced before the stricter
implementation. Their failing log is retained with the private experiment data.

Production compatibility, a physical device, rendered GUI usability, URP output,
independent expert-user task completion and commercial superiority still require
separate evidence. Nothing here approves a marketplace submission.


The public headless-input configuration additionally sets both IgnoreFocus and AllDeviceInputAlwaysGoesToGameView, plus ProcessEventsManually and the argument-free public InputSystem.Update. Installed Input System 1.20.1 source keeps the update-type overload internal. The fresh-script-cache option preserves the copied source/asset/assembly databases separately and rebuilds them; source template data and downloaded PackageCache remain intact. See the dated native experiment report for actual failures and scenario outcomes.


Final November 3 afternoon observation: the fresh-database wired case passed all sixteen native checks with domain reload enabled, all sixty-seven protected files unchanged and all fifty-five packaged scripts exact. The reused-cache failing case used identical C# fixture bytes. The second continuation completed all sixteen wired checks with domain reload disabled and correctly rejected the shadow-health control after input reached the runner; both new projects preserved seventy-six protected files and all fifty-five packaged scripts. Physical input and rendered GUI remain unverified. See the dated report for the complete evidence boundaries.


The second continuation adds three driver-level controlled-boundary regressions:
a vendor-only import succeeds, while customer-file overwrite and deletion during
bootstrap fail before gameplay. The latter two tests first reproduced real false
PASS receipts in the previous driver. The new pre-import baseline complements the
post-staging fixture baseline; it does not retroactively certify earlier native
receipts or treat controlled fake-Unity tests as actual Editor acceptance.

The corrected driver's fresh Built-in native case also passed actual archive
import followed by all sixteen gameplay observations: forty original nonvendor
files survived bootstrap unchanged, forty-eight protected files survived the
probe, and all fifty-five packaged C# sources remained exact. This native positive
case is separate from the two controlled overwrite/deletion negative tests.

The second-continuation log audit found a UnityEditor.Search startup-index
ArgumentOutOfRangeException in all four native runs, including the passing
Built-in workflows. A functional PASS is not an error-free Editor acceptance.
The first URP-configured run wrote all observations but timed out before a clean
native exit; its strict result remains FAIL. Never promote it from pass-line counts.
See the dated report for the independent retry and unresolved cache/search control.

The fresh URP-configured retry later passed the full named functional contract and
native exit zero in 741.2 seconds, preserving eighty-nine original/staged files
and all fifty-five archive sources. It reused the verified native import; it did
not repeat it. The common Search exception remained, so rendered output and an
error-free clean-project control are still required. All five owned jobs were
confirmed exited without remaining cgroup processes at final audit.
