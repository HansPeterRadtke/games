# Unity customer-copy safety: orphan .meta overwrite reproduced and fixed

Date: November 1, 2026. All experiments were run **only** on actual Unity
6000.6.7f1 in private disposable project copies on Nitro. The live dirty
product worktree and released buyer archive were not modified. This source
bug affects the **uncommitted new customer-copy function** from the latest
worktree, **not** a claimed published Asset Store product.

## Verified failure

The new `HprSuiteIntegrationGuide.CopySampleToCustomerPath` checks the target
asset path for an existing Unity main asset, a physical file and a physical
directory. Before this experiment it did **not** check for a pre-existing
`.meta` file when the associated Unity `.asset` file was absent.

Private test fixture:
`unity/tools/release/gameplay_suite/qa/HprSampleMetaCollisionValidator.cs`.
The disposable Editor created a new test folder under `Assets`, wrote a
reserved `ReservedIdentity.asset.meta` with a chosen identity, and **did not**
create its matching `.asset`. It then tried to copy an HPR sample asset
to that target through the unmodified latest guide.

The real Unity Editor completed the asset copy instead of refusing it.
Observed result in `customer-meta-collision-20261101.txt`:

- `copy_rejected=False`
- `preexisting_metadata_preserved=False`
- `target_asset_was_created=True`

Independent file inspection after the run verified the exact original GUID
had been replaced by a Unity-generated GUID. The real Editor threw the QA
validator's deliberate acceptance exception and exited nonzero. All error
logs and changed scratch assets are retained outside Git, not cleaned up
or rewritten as a successful test.

## Minimal safe fix and independently verified result

The isolated, reviewable patch is
`patches/hpr-guide-reject-orphan-meta-2026-11-01.patch`.
It adds two destination preflight checks to the existing conditional:
`File.Exists(physical + ".meta")` and
`Directory.Exists(physical + ".meta")`.

The original guide source was frozen into a **different fresh scratch project**
and only that scratch file was patched. A full Unity six point six compile and
Editor invocation of the same safety validator completed with exit zero,
using fresh logs/receipts. The exact independent receipt
`customer-meta-collision-fixed-20261101.txt` says:

- `copy_rejected=True`
- `rejection_type=IOException`
- `preexisting_metadata_preserved=True`
- `target_asset_was_created=False`

The positive QA result is not a false simulation: the real Unity Editor
executed the actual updated `CopySampleToCustomerPath` method and validated
the original metadata bytes. The patch includes only that precise
preflight change. The original uncommitted owner/agent guide had source
SHA-256 beginning `c0b1dfec`, the scratch patch source `8d841806`,
and the diff was generated only after proving the latter differs by the
two guarded `.meta` conditions.

## Integration, scope and remaining limitations

The patch has **not** been applied to the other agent's dirty worktree;
the approved next step is for that worktree's owner to reconcile the patch,
add a failing-then-passing Unity EditMode regression there, and build a new
immutable release archive. The last verified v14 archive still has the
older Editor integration guide, without this new customer copy action.
Do not submit either package or claim the patched feature is shipped.

This gate protects a reserved orphan metadata file in a single destination
and the test demonstrates it actually works. Additional cases to test before
commercial release: directory symlinks, read-only paths, import refresh
races, multiple ScriptableObject dependencies with conflicting
`.meta` paths, intentional update of an existing user-owned asset,
rollback under partial write, and links to user-owned objects. A paid tool
requires a non-destructive preview and an explicit consent workflow.
