# Private native module NUnit acceptance

This create-only driver runs the canonical ten module EditMode test assemblies
against an exact, previously natively imported private suite archive. It does not
modify a source worktree/template, rebuild or publish the archive, install a second
copy of NUnit, or interact with graphical software terms. Execute only in a bounded,
owned resource-broker job within the authorized owner window.

`run_native_editmode.py --help` documents explicit template/import-receipt/archive
checksum/installed Editor/output arguments. The template must match the selected archive, including all C# sources, other
asset payloads, metadata and GUIDs. The driver repeats this check on the copied
project immediately before launch and after native execution. Its result includes
the final package comparison and the archive checksum. The prior
native import receipt must have successful actual-Editor evidence for that checksum.
Each invocation uses a new directory below the private marketplace QA task runtime.
Copied script databases are retained separately and rebuilt; PackageCache remains.

The driver uses the installed Editor's own bundled Test Framework version, adding
only that dependency in the private copy. This avoids forcing the 6.6 framework into
6.4 or importing a second NUnit assembly. All existing test asmdef names/GUID metadata
are copied unchanged into `Assets/HprProductTests`. It selects these ten assemblies
through public `-runTests -testPlatform EditMode -assemblyNames` arguments, omitting
`-quit` so the native runner controls completion. It records raw XML, Editor log,
launch/source hashes and native exit separately.

Acceptance requires all 56 distinct NUnit cases, exact per-module coverage, no
failed/skipped/inconclusive cases, consistent root counters, all passed assembly
receipts and native exit zero. Missing XML, duplicates or partial runs fail closed.
The protected-file baseline includes every staged canonical test and original asset,
manifest and project setting. A copied packages-lock.json resolution update is
allowed only if it exactly matches the installed first-party Test Framework/NUnit
versions, their declared dependencies and intended dependency depths, preserving
every unrelated lock entry. It is reported separately and never changes the source
template. Lock deletion or unrelated dependency updates fail acceptance, as do all
other original-file changes. Compilation or arbitrary Editor failure is not a successful
old-package negative control: inspect actual failed case identities and assertions.

The ability module has 25 cases: its original three plus 17 malformed-field cases,
one whole-list-before-effects case, two event-only/optional-null-slot maximum saved
cooldown cases, a zero-cost/zero-cooldown negative-offset valid control and one
destroyed-provider/replacement lifetime case. These
exercise public runner APIs and customer callback counters, so the same tests can
run against the pre-fix archive without depending on newly added validation methods.
The other nine module assemblies retain their 31 existing cases unchanged.

Native batch NUnit proves only the observed C# contracts. No test here certifies
rendered Inspector layout, actual mouse/keyboard interaction, URP visuals, Player
builds, independent buyer value, full uninstall/update or commercial approval. The
previously observed normal-Editor terms gate remains untouched.

First-party command documentation:
https://docs.unity.com/en-us/engine/6000.6/manual/programming-environment/test-framework-introduction/running-tests/run-tests-from-command-line
