# Serial customer Unity Editor acceptance after URP — owner-broker QA draft

Date: November 2, 2026. Nitro. **This is a TESTED PURE-PYTHON
FOLLOW-UP WORKER SOURCE, not an activated new broker job, and not a
completed native Unity Editor acceptance.** The already registered
separate URP broker worker remains running and monitoring real CPU.

## Three distinct genuine acceptance objectives

The frozen 161-asset seller candidate has previous genuine Unity 6.6
cleanroom/Play-mode and existing-customer tests. The following newer
source-only improvements still need actual Editor tests:
- `stats_build`: In a private copy of an actual
  customer-authored Unity scene, configure HPR-native ActorStats +
  HprSuiteAbilityPool without replacing the existing controller.
  Save and reopen the scene, verify the serialized Stats reference,
  reject missing or wrong-object Stats, attach independent healing
  ability, verify Undo/Redo, and preserve original buyer data/GUIDs.
- `stats_playmode`: Enter genuine Unity 6.6 Play mode
  from that newly saved scene; confirm twenty health healed, twenty
  stamina spent, second cast blocked by cooldown, native serialized
  provider still functional, and customer controller preserved.
- `dirty_asset_copy`: In an entirely DIFFERENT disposable
  buyer project, leave an unrelated customer-owned ScriptableObject
  unsaved in the Inspector, invoke the patched HPR sample-copier, and
  confirm only the new customer-owned ability/effect are saved while
  original customer asset and scene SHA-256 bytes remain unchanged.
  `AssetDatabase.SaveAssetIfDirty` does bypass
  `OnWillSaveAssets`; editor/VCS integration still needs
  further real-world testing.

These are genuine Unity test methods with unique private file receipts,
not synthetic gameplay screenshots. Both staged private projects already
exist with **64** original nonvendor file hashes captured each. The
currently proposed C# sources are pinned by SHA-256, and the selected
HPR vendor .meta files are also pinned. The test methods were compiled
separately in a .NET8 offline Unity managed-reference check with zero
C# errors, but this does NOT replace actual Unity Editor execution.

## Read-only upstream coordination and actual broker usage

The source at
`unity/tools/release/gameplay_suite/qa/unity_customer_followon.py`
is designed to become a SEPARATE, owner-registered Nitro
`resource-broker-job` process if it is independently
accepted. It does not start Unity while the existing upstream URP
worker is active. It watches the upstream owner's publicly readable
job identity/status and requires a verified terminal result plus
stopped systemd job and no remaining broker lease. A manual stop
without a final source receipt is an explicit HALT, not an invitation
to race another agent's process.

After upstream completion it checks actual CPU pressure and load,
requires two consecutive acceptable samples and no existing Unity
Editor process, verifies broker health, then requests an actual
short-lived secure CPU/RAM lease. The worker would execute the three
independent Unity stages serially within its OWN resource-broker cgroup.
Each phase writes separate create-only logs/receipts, checks protected
original user files and verifies new paths are exactly allowlisted.
If a source/receipt, CPU/broker status or lease is uncertain, it does
not repeat unknown effects in place. A true authorization/resource
denial is NOT retried under a different owner, endpoint or identity.
Ordinary read-only transport timeouts are rechecked.

The worker includes process-group cleanup for its OWN Unity Editor
children, and a hardened broker lease finalizer: failed secure lease
release is never reported as a successful test. If private disk
storage fails at the same time, the status explicitly records that
the control credential could not be preserved and the real broker
lease must expire normally. The worker does not kill, renice or
reschedule unrelated Unity, trading, graphics or AI processes.
Source/output path overlap with any customer or upstream project is
refused. The original vendor C# source and .meta identities are pinned.

## Evidence and limitations

The worker's initial Python unit/mocked-broker tests were created RED
first and now pass. They cover an active URP worker, a correct terminal
result, malformed/manual-stopped upstream, source guard conditions,
stale output rejection, exact Editor method and quit flags, secure
reservation/release, denial, failed credential write, failed test
release, read-only timeout recovery, and output path overlap.
These mock tests do NOT start Unity or request a real resource lease.

A separate synthetic fake-Editor full-sequence test script was written
to test real child-process orchestration end to end. The platform
safety checker REJECTED execution of that specific test. The test
was NOT rerun or routed around the refusal. Its source and the failed
invocation record were preserved privately under the owner's QA
evidence, and no PASS claim is made. Consequently this NEW downstream
worker is **NOT DEPLOYED**. Only the previous tested upstream URP
worker is actually running.

Once permitted full orchestration validation and broker authorization
are available, a distinct unique output directory can be used for
the real downstream tasks, without editing or replaying the original
customer projects and evidence. No new Unity package, customer scene,
publisher account or other provider was modified by this draft.

## Product decision

Commercial status remains **NO-GO**. Native Stats persistence and
scoped customer asset-saving must pass genuine Unity Editor
scene/save/Play-mode tests, then a new immutable buyer archive needs
the full input/pipeline matrix. Independent developer value, accessible
GUI screenshots, safe dependent-game migration and marketing artwork
approval remain open.

Do not confuse a waiting broker job, a mocked receipt, an offline
C# compilation or a paper workflow with a passed Unity product.
