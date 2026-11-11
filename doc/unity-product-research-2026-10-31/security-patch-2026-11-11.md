# November 11, 2026: Unity eMudhra and Brotli security baseline

Source-of-truth security advisories:
- https://activation.unity3d.com/security/unity-emudhra-compromise
- https://legacy-activation.unity3d.com/security/unity-brotli-decoder-vulnerability
- https://unity.com/releases/editor/whats-new/6000.6.8f1

Unity lists 6000.6.8f1 (released November 3, 2026) as the first
security-patched version for its Unity 6000.6 stream. The earlier
6000.6.7f1 is not security-patched for the October issues. The
historical 6000.4 stream is not listed as a security-fixed release,
so it is unsuitable as a verified patched release baseline.
Official alternatives include patched 6000.3 and 6000.0 LTS releases.

The old editors, Unity 6000.4.0f1 and 6000.6.7f1, remain useful for
deliberate legacy compatibility QA only. They must not silently
serve as the default source of a newly distributed buyer package.

The HPR Gameplay Suite scripts now default to the official, side-by-side
Unity 6000.6.8f1 Editor installation. The internal package builder
runs the qa/editor_security.py security gate before creating output:
it checks the actual executable version, not only the directory name.
Unrecognized release streams fail closed. For intentional historical QA
using a legacy editor, a developer can set the clearly named
HPR_UNPATCHED_EDITOR_INTERNAL_QA=1 override. No internet upload,
Unity Asset Store submission or customer publication is performed
by these scripts.

The release candidate must be rebuilt using the patched editor,
then checked for clean import, runtime integration, and GUID
stability. A cleanroom built with an old editor is not proof that a
new candidate is security-patched. Preserve older Unity installations
and historical release artifacts for exact comparisons.

The two October advisories concern UnityTLS certificate handling
and the Brotli decompression library. A source inspection of this
project found no direct references to BrotliStream, BrotliDecoder,
HttpClient or UnityWebRequest in its shipped runtime/editor modules.
That does not exempt the Editor's own package-management and
dependency transport from the advisory.

## Verification

- Previous candidate v15: static archive inspection passed
  (160 assets, ten modules, no external files), and v14 to v15
  comparison found 160 unchanged asset GUIDs.
- Offline security-gate and gameplay-source tests: 26 passed.
- Official 6000.6.8f1 Linux Editor archive size and download source were
  verified; it was installed side-by-side on Nitro and the actual executable
  returned 6000.6.8f1. Original 6000.4 and 6000.6.7 remain unchanged.
- A new internal release was exported by the patched Editor without
  compiler warnings; 160 Unity assets, ten modules, 52 authored GUIDs and
  22 authored Unity YAML files passed static verification. Comparing the
  old v15 buyer archive to the patched archive showed all 160 shared
  GUIDs unchanged and no asset additions or removals.
- Negative build-preflight test selected installed 6000.6.7f1 and confirmed
  that its version was rejected before a project or release directory was
  created. The existing source tests and new patch-policy tests passed.
- Fresh Unity 6000.6.8f1 cleanroom validation: VERIFIED PASS.
  The rebuilt buyer archive imported into an unused disposable project
  using the patched editor. The imported scene validated all thirteen
  serialized references, all twelve required supporting assets and all
  forty-seven gameplay scripts without overwriting customer assets.
  Ten actual Unity runtime integration checks passed: service registry,
  world data, inventory/doors/pickups, combat and typed damage events,
  healing/stamina/cooldown, area effects, weapon/loot, state restoration,
  real JSON write/read and corrupted-state rejection.
- Evidence is stored privately with the new internal candidate at
  /data/var/marketplace-account-setup/unity-consolidated-securitypatched-20261111/release/.
  The release receipt remains marked INTERNAL_QA_CANDIDATE_NOT_SUBMITTED_NOT_PUBLISHED.
  No live publisher operation was performed.
- No previously approved buyer submission was modified or published.
