# Native HPR Stats adapter: real customer scene persistence gap

Date: November 2, 2026, Nitro. **Independent QA-only proposal.**
Source worktree: qa/unity-customer-integrity-20261101; original owner
commercial worktree unchanged. No publisher submission.

## Concrete buyer-facing problem

The current compiled seller candidate includes a runtime
HprSuiteAbilityPool implementing IAbilityResourcePool, but its
ActorStatsComponent source is an ordinary *non-serialized* private
field. The included training arena explicitly calls Bind(stats) on
startup, so that runtime demo works. A customer who adds the HPR
Stats component and the resource pool to an existing controller with
Unity's Inspector, and then uses the selected-object Editor ability
installer, has no persisted Stats source unless they author and run
their own C# Bind call each session. The previous selected-object
Editor preflight checks only the IAbilityResourcePool interface, so it
could accept such a nonfunctional pool. Its Health/Stamina would read
as zero, and healing/cost calls would do nothing or fail.

This is a **source-confirmed integration bug and usability weakness**.
It was not inferred from screenshots and is not yet a real Editor
runtime failure reproduction on the original immutable package.

## Isolated proposed correction

A second private **source-only** proposal was staged from the earlier
scoped-save and reversible-detach source candidate, not from or into
the owner's concurrent dirty product branch:

/data/var/marketplace-account-setup/hpr-unity-stats-native-source-only-20261102

The runtime adapter now serializes the ActorStatsComponent reference
with Unity SerializeField, exposes StatsSource and HasValidStatsSource,
and uses a same-GameObject GetComponent fallback when a customer has
explicitly installed an HPR Stats component. Reset binds a same-object
Stats reference when the pool is manually created in the Editor. A
runtime Bind() refuses a Stats instance belonging to another player
object rather than silently wiring the wrong customer's health.
Health/stamina reads and writes resolve the same validated source.

The selected-object Editor installer now rejects an HprSuiteAbilityPool
that has no usable ActorStatsComponent with a specific actionable
message. It does not create Stats or controllers or rewrite customer
settings. Buyers with their own non-HPR stats implementation still
need an independent IAbilityResourcePool bridge; no universal
zero-code third-party health compatibility is claimed.

Two minimal reviewable source patches are in the independent QA branch:
patches/hpr-native-stats-binding-2026-11-02.patch and
patches/hpr-editor-check-native-stats-2026-11-02.patch.

The separate source snapshot has exactly **five** changes versus its
immediate predecessor: these two C# sources and the README, QUICKSTART
and ARCHITECTURE explanatory documents. All **1,093** paths, all
**516** Unity metadata GUID identities and the pre-existing symlinks
were preserved, with the original frozen 161-asset buyer archive
untouched. This is source-only, not a build to a new buyer .unitypackage.

## Completed and pending verification

Four deterministic Python source/fixture contracts passed after an
initial red test because the new validation fixture did not exist.
An independent low-priority **offline .NET8 compiler check** compiled
all 47 actual HPR runtime source files, the new HprSuiteIntegration and
selected-object Editor source, the customer controller C# source and a
private real Unity Editor test probe against the actual installed
Unity 6000.6.7f1 managed API assemblies. It passed with zero errors
and three expected CS0649 warnings from fields Unity serializes
automatically. The standalone compiler included one explicit
test-only HprGameplaySuitePlayground type stub to avoid loading demo
scene infrastructure. **This is not a Unity Editor compilation or
a genuine Play-mode acceptance.**

The private real Unity fixture is
unity/tools/release/gameplay_suite/qa/HprCustomerStatsAdapterValidator.cs.
It exercises a NEW copy of a representative existing-customer scene,
preserves the controller, refuses a native pool without HPR Stats,
rejects cross-GameObject Stats bindings, checks auto-discovery,
persists the typed serialized Inspector source across save/reopen,
explicitly attaches the independent healing ability through the
customer Editor installer, verifies Undo/Redo, and checks the original
buyer scenes/prefab/source/settings/ability bytes and GUIDs. Its
second real Play-mode phase verifies twenty health restored, twenty
stamina consumed and cooldown. This fixture **has been staged but
has not yet run** in the overloaded Unity Editor environment.

A fresh private copy of the populated Unity 6.6 customer project
has been staged at:
/data/tmp/hpr-unity-native-stats-customer-20261102/customer-project

Only the two optional HPR sources and one private QA Editor script
were overlaid into that disposable project. **64 original nonvendor
customer Assets/ProjectSettings/Packages files** were independently
baselined. Source and destination original customer scene SHA-256
values matched at staging time; no original user project was changed.

## Release blockers and next correct test

The owner resource broker is supervising a separate priority URP/
new-only Input System test, currently waiting because Nitro's CPU
load is sustained above safe admission levels. Run this native Stats
fixture through its own authorized admission window once CPU is
available, without competing with the existing URP job.

If the real Editor checks pass, reconcile this narrow source patch
with current owner/other-agent edits and build an entirely new
immutable buyer package. Repeat real install, scene persistence,
Play-mode, domain reload, URP and input tests on that exact archive.
Also verify that a customer's independent health system is not
silently replaced, editor messages are readable, and a buyer can
complete the task without modifying vendor source.

The commercial decision remains **NO-GO** without demonstrated
experienced developer advantage against real competitors and
publisher authorization. No publication, purchase, account mutation
or false sales claim occurred.
