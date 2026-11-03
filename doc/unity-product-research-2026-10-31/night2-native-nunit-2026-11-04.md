# November 4 night two: actual native NUnit regression milestone

## Result and scope

The unchanged night-one corrected private archive passes all **55 NUnit EditMode
cases across ten module assemblies** in actual Unity 6000.6.7f1 and 6000.4.0f1
processes. The identical tests against the earlier reviewed original archive execute
all 55 cases and fail exactly the 18 intended malformed-definition assertions.
The original 34 tests and three newly added valid compatibility/boundary cases pass
in that old-package control. Its FAIL / native exit 2 is retained, not relabelled as
a product pass. No product runtime or archive payload was changed this session.

Canonical AbilitiesEditModeTests now includes 21 new cases: 17 malformed fields,
one invalid second effect after a valid first effect, two event-only/optional-null
slot compatibility cases, and one valid zero-cost/zero-cooldown negative-offset
case. Its three previous cases are retained. Public runner calls and customer
callback counters test refusal before spending or applying effects; the regression
source compiles against both pre-fix and corrected APIs. Unsupported, negative and
nonfinite built-in data are exercised. Valid zero/maximum bounds remain usable.

The nine other module test sources/asmdefs are unchanged. Existing test GUIDs and
serialized product fields are unchanged. The new tests are canonical module source,
not injected into the immutable buyer archive or a newly exported seller package.

## Actual native results

| Exact imported archive / target | NUnit result / native exit | Protected source/project files | Elapsed |
| --- | --- | --- | --- |
| Earlier original archive; 6000.6.7f1, New Input configured, bundled Test Framework 1.8.0 / NUnit package 2.1.0 | 37 passed, 18 specifically expected failures / exit 2 | 458 unchanged except planned copied package lock resolution; all 55 product C# exact | 233.3 seconds |
| Night-one final candidate; same target/framework | 55 passed, zero failed/skipped/inconclusive / exit 0 | 464 protected, same narrow lock exception; all 55 product C# exact | 208.3 seconds |
| Same candidate; 6000.4.0f1, legacy input configured, bundled Test Framework 1.6.0 / NUnit package 2.0.5 | 55 passed, zero failed/skipped/inconclusive / exit 0 | 452 protected, same narrow lock exception; all 55 product C# exact | 180.2 seconds |

These are fresh private project copies of successful native imports from night one;
their successful import receipts/checksums and all 55 product scripts were verified
before copying. No ImportPackage command was repeated. Copied script databases were
retained separately and rebuilt, with the downloaded/native PackageCache preserved.
The driver stages the canonical tests under a new Assets test directory and runs
public -runTests / -testPlatform EditMode / -assemblyNames / -testResults arguments.
No UPM test discovery, new UPM archive rebuild, PlayMode NUnit, Player build,
physical keyboard or rendered Editor acceptance follows from this result.

The native logs identify the actual engine versions. Both positive XMLs contain
55 unique passed cases and the exact expected ten assembly counts. Raw logs/XML
and launch/staged-source hashes are retained. Independent verification confirms
all staged test bytes match this source revision and their launch hashes.
No C# compiler errors or CS0618/CS0612 markers were found in the three logs.
GTK/GLib critical messages occur around headless widget teardown in all three
runs; these are disclosed, not presented as an entirely warning-free GUI session.
The baseline null-effect-list ArgumentNullException is captured as a failed NUnit
case, alongside the other precise assertion failures.

## Receipt and dependency preservation correction

The new native receipt classifier rejects empty/malformed XML, missing or duplicate
cases, incomplete/unexpected module counts, contradictory failed assembly/root
results, skipped/inconclusive cases and nonzero native exits. A native XML pass
alone is insufficient: archive source identity and protected-file checks also gate
acceptance. Thirteen deterministic Python tests cover these boundaries, including
every individual missing case and installed-framework version resolution.

Initial harness code excluded any copied Packages/packages-lock.json change. Two
regression tests reproduced false acceptance for unrelated dependency mutation and
lock deletion before correcting it. The final gate derives exactly allowed bundled
Test Framework/NUnit entries from the installed Editor's first-party manifests,
checks their dependency versions/depths and preserves every unrelated lock entry.
Even an unchanged but incorrect resolution fails. It does not blindly force the
6.6 framework into 6.4 or copy a second NUnit assembly.

All three native datasets were independently revalidated under this corrected lock
and XML gate. Six-point-six changes are only Test Framework/NUnit depth changes
from transitive to direct dependency. Six-point-four adds only its bundled 1.6.0
framework and 2.0.5 NUnit entries. Unity 6.4's framework declares minimum NUnit 2.0.3,
while its installed resolved bundled package is 2.0.5; the verifier uses both actual
installed manifests rather than inventing an identical-version requirement.

Raw original RESULT.json files remain unchanged. STRICT_REVALIDATION.json is a
read-only reclassification of those actual native results with the tightened gate,
not a fourth Editor execution. The reusable driver also now validates archive path
policy before reading product sources. These narrow post-run harness improvements
are covered separately from the actual native execution described above.

The focused source checks pass: 13 new receipt/preservation tests, 14 archive-policy
tests and 21 existing suite tests; Python compilation and git diff whitespace checks
also pass. These 48 Python tests are separate from the 110 successful native cases
across the two positive processes and the 55-case negative-control execution.

## Provenance, preservation and next milestone

Original archive SHA-256:
`1140e9bf5c7a9848003ce0ccd8168c298ced2bf957194364f9f08b3f52974f5e`.
Unchanged night-one corrected candidate:
`92cfb2058d32412e28c2da61fe8b93d899140f6a559c9432e072d24cba0870b1`.
Private runtime:
`/data/var/marketplace-account-setup/hpr-native-editmode-night2-20261104/`.
Original work is preserved on all nine earlier Unity worktrees: heads, Git statuses
and all 21 original dirty-file hashes match the pre-work snapshot. The original
archive, candidate archive and earlier customer save hashes also match. All three
owned broker jobs are exited with zero remaining cgroup processes. The final
preservation audit was recorded November 3 at 23:31 UTC / November 4 at 00:31 Berlin.

This source branch is qa/unity-native-editmode-night2-20261104, based on the previous
night-one branch. No merge into the dirty original seller worktree occurred. The
work adds durable regressions and closes actual native NUnit execution gaps; it
does not newly fix the already-corrected runtime or certify a new buyer release.

Commercial release remains **NO-GO**. The previously observed normal graphical
Unity 6.6 software-terms prompt was not reopened, accepted, declined or bypassed.
Rendered installer Attach/Undo/Redo, visual Inspector/URP acceptance, dependency-aware
update/uninstall and independent experienced-buyer/comparator validation remain
open. Original-source/installer-overlay reconciliation is also still required
before any seller rebuild. No product publication, upload, account change, purchase
or outreach occurred. The next permitted engineering scope is independent of the
blocked consent action; no uncertain external effect should be replayed.

First-party command reference reviewed:
https://docs.unity.com/en-us/engine/6000.6/manual/programming-environment/test-framework-introduction/running-tests/run-tests-from-command-line
