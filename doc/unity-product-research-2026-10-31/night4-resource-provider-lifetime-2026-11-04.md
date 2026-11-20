# November 4 night four: destroyed resource-provider regression and fix

## Actual defect and resulting behavior

An actual Unity 6000.6.7f1 NUnit test reproduced a lifecycle defect in the previously
corrected private archive: after DestroyImmediate removed the native resource
provider component, AbilityRunnerComponent.TryActivate still returned true. Its
cached IAbilityResourcePool interface retained the detached managed object, so the
existing interface-null check did not recognize Unity's destroyed native component.
The native-object-null assertion passed before the activation assertion failed;
this is not a mocked C# lifetime or a failed compiler/startup control.

The unchanged pre-fix archive executes all 56 module tests: 55 pass and exactly
DestroyedResourcePool_RejectsUntilLiveReplacementIsBound fails. Native exit is 2
and the raw FAIL/XML is retained. The new test uses public APIs and the same source
bytes before and after the fix. It additionally requires no destroyed-provider
callbacks, unchanged vitals, no new cooldown, successful use of a live replacement,
and normal cooldown refusal after that successful activation.

The narrow canonical runner fix checks both ordinary null and UnityEngine.Object
native lifetime before calling SpendAbilityCost. A missing/removed provider returns
false with a clear status reason. It does not charge, apply effects or start a new
cooldown through that removed provider. Binding a live replacement restores normal
use without replacing the loadout or unlocking state. No serialized field names,
types, GUIDs or public signatures changed. Arbitrary customer callbacks remain
responsible for their own behavior; this is not transaction rollback or protection
against a provider destroying itself midway through its own callback.

## New exact private candidate

A create-only internal archive changes only the existing runner payload relative
to the prior corrected candidate. All 161 GUID asset identities and metadata are
unchanged, all 454 other tar members are unchanged, and there remain 55 product C#
files and ten runtime asmdefs. The archive-matched installer and earlier numeric/
definition/data-preservation fixes remain intact. Frozen original/proposed source
snapshots contain this one file, not a purported full source-worktree snapshot.
SOURCE_MAP.json records its exact source-to-archive mapping. The final canonical
runner bytes independently match the payload actually imported and tested.

Previous corrected archive:
`92cfb2058d32412e28c2da61fe8b93d899140f6a559c9432e072d24cba0870b1`.
New lifetime candidate:
`83ea196924d966175c33b07173fa94e69831369df86a71783f9f2a9c20338292`.
This is deterministic internal tar-format QA, not a Unity Editor export, saleable
package, published submission or approval. Original archives are not overwritten.

## Actual native acceptance of this new candidate

| Target and distinct task | Actual result | Protected data / boundary |
| --- | --- | --- |
| Unity 6000.6.7f1, New Input 1.20.1, Built-in, domain reload off; new archive import + existing-game workflow | Native import and gameplay exit 0, all 16 workflow observations PASS, all three effective Built-in selection phases PASS; 332.1 seconds | 131 existing/staged protected files unchanged; all 55 archived C# exact |
| Same new candidate, native module NUnit with bundled Test Framework 1.8.0 | 56/56 PASS, zero failed/skipped/inconclusive, native exit 0; 162.3 seconds | 473 protected files unchanged except exact planned bundled lock resolution; all 55 product scripts exact |
| Unity 6000.4.0f1, legacy input configured; native new archive import + configuration matrix | Native import and configuration exit 0, all 17 cases PASS; 251.7 seconds | 119 protected files unchanged; all 55 archived C# exact; configuration/API checks, not keyboard gameplay |
| Same 6.4 candidate, native NUnit with bundled Test Framework 1.6.0 | 56/56 PASS, zero failed/skipped/inconclusive, native exit 0; 140.4 seconds | 521 protected files unchanged except exact planned bundled lock resolution; all 55 product scripts exact |

The pre-fix red run took 145.4 seconds, preserved 464 files except the same exact
planned bundled lock resolution and retained all 55 original candidate scripts.
NUnit results require native exit and the complete exact ten-assembly test contract,
now 25 ability cases plus the other nine modules' unchanged 31 cases. All staged
canonical test source hashes match this branch and the launch-source hashes.
The installed bundled-framework lock guard remains enforced; no customer dependency
or second NUnit assembly is silently substituted.

Native import/configuration/gameplay/NUnit logs were separately scanned: zero
C# error, managed Exception:, CS0618 or CS0612 markers. Headless GTK/GLib critical
teardown messages remain in execution logs, so this is not an entirely warning-free
GUI claim. The lifetime test uses real EditMode DestroyImmediate semantics; ordinary
end-of-frame Destroy scheduling, rendered UI, physical keyboard, Player builds and
external buyer behavior are not certified by that test. The separate 6.6 native
workflow verifies existing input/health/HUD/save/detach functionality still works.

Thirteen receipt/preservation unit tests and eleven private archive-builder tests
pass; Python/NUnit counts are separate. The receipt test now checks missing-case
coverage using the updated exact assembly manifest, rather than retaining the stale
55-case loop bound. Archive/code whitespace checks also pass.

## Explicit denial and evidence not transferred between archives

An additional selected-URP existing-project check for this new archive was denied
by the central resource broker with
central_reservation_denied_resources_currently_insufficient. No job started; the
response is retained. It was not retried, reduced or routed elsewhere. This is
separate from the previous night's denied installed-but-inactive URP control, which
was also not retried. The already admitted 6.4/6.6 lifecycle targets continued and
finished independently.

The prior candidate's successful URP reload-on/off and cold-restart results remain
historical evidence for its own exact checksum. They do not certify the new lifetime
archive. New-candidate URP, reload-enabled full gameplay and cold-restart checks
remain open. The normal graphical software-terms gate was not reopened, accepted,
declined or bypassed. No rendered installer/Inspector acceptance is claimed.

## Preservation and commercial state

Private runtime:
`/data/var/marketplace-account-setup/hpr-resource-lifetime-night4-20261104/`.
ARCHIVE_RESULT.json selects the new candidate. FINAL_NATIVE_AND_PRESERVATION_AUDIT.json
retains raw log/XML hashes, strict native positive/specific negative results, source
matches, unchanged earlier archives/save, and all eleven original worktree heads,
Git statuses and all 21 original dirty-file hashes unchanged. All three admitted
owned jobs have exited with zero cgroup processes; the extra denied check has no
job. The original seller worktree and other agents' edits were not merged or changed.

Branch: qa/unity-resource-lifetime-night4-20261104. This is a real tested runtime
fix plus regression, not a new commercial feature or marketplace submission.
Commercial release remains **NO-GO** pending the new-candidate matrix above, normal
rendered Editor/URP usability, original-source/installer-overlay reconciliation,
full dependency-aware update/uninstall and independent buyer/comparator validation.
No marketplace publication/upload, purchase, outreach or account change occurred.

First-party lifetime semantics reviewed:
https://docs.unity3d.com/ja/6000.0/ScriptReference/Object-operator_eq.html
https://docs.unity3d.com/cn/6000.0/ScriptReference/Object.html
