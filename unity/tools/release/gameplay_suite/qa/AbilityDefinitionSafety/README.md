# Archive-matched installer definition-validation overlay

This complete Editor source starts from the exact reviewed private archive's
HprSelectedAbilityInstaller.cs and changes only its definition-validation call.
It preserves the already tested native HprSuiteAbilityPool.HasValidStatsSource
guard. The older sibling qa/HprSelectedAbilityInstaller.cs prototype lacks that
archived guard; replacing the candidate with that stale file would regress prior
work. It is deliberately left untouched.

The three canonical com.hpr.abilities runtime source files plus this overlay map
to four existing archive payloads. The create-only archive builder preserves all
161 GUID identities, every asset.meta/pathname and every other payload. Runtime
and Editor preview share numeric/effect validation; preview additionally retains
its existing owned, nonempty effect-asset requirement. No original owner dirty
source, original package or publisher draft is changed. The archive is private QA,
not a Unity Editor export, a published product or release approval.
