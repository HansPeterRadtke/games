# Exact reviewed HPR package: offline API matrix and buyer upgrade staging

November 2, 2026, Nitro. This is evidence for a PRIVATE, non-published QA candidate and does NOT replace genuine Unity Editor import/Play-mode acceptance.

The reviewed copy-race private package is preserved at /data/var/marketplace-account-setup/hpr-unity-copy-race-reviewed-private-archive-20261102/internal-not-tested-in-unity.unitypackage, SHA-256 1140e9bf5c7a9848003ce0ccd8168c298ced2bf957194364f9f08b3f52974f5e. It has 161 asset identities and ten valid assembly definitions. The frozen original archive and all original GUID metadata bytes remain unchanged. A previously reviewed deterministic repacker replaced only seven authorized source and buyer-guide payloads. The two independent GUID/structure validators passed. This candidate has not yet been imported into a real Unity Editor.

## Exact source extracted from the new archive, not an inferred proposal

A new tested, create-only QA script under unity/tools/release/gameplay_suite/qa/unity_packaged_source_compile.py reads the SHA-pinned candidate .unitypackage, applies the prior archive path safety policy, and stages each C-sharp asset body byte-for-byte in a NEW private output folder. It creates an explicit source-to-SHA manifest, and an offline .NET compilation project referencing installed Unity API assemblies. It never executes product code, changes the original archive, creates Unity Asset Store uploads, or launches the Unity Editor. Six new deterministic staging tests passed (source identity, SHA refusal, no output overwrite, new-input DLL requirement, input immutability, and refusing writes inside the installed Editor directory).

Actual reviewed candidate: exactly 55 C-sharp files extracted and hashed, without any shipped tests/QA source. Three separate low-priority offline .NET 8 compiler runs using source from the EXACT new candidate passed:

- Unity 6000.6.7f1 managed API assemblies, Built-in input branch: 55 C-sharp files, 167 API references, zero C-sharp errors and 15 private serialized-field warnings.
- Unity 6000.4.0f1 managed API assemblies, older input branch: the same 55 C-sharp bytes, 146 API references, zero errors and 15 serialized-field warnings.
- Unity 6000.6.7f1 managed APIs with ENABLE_INPUT_SYSTEM and a concrete Unity.InputSystem.dll from an earlier Unity project: the same 55 packaged C-sharp bytes, 168 references, zero errors and 15 serialized-field warnings.

The warnings are reported by standalone .NET because inspector-serialized private fields are not assigned by ordinary C-sharp source constructors. Real Unity Editor warnings may differ. These runs do not exercise Unity asmdef compilation isolation, native serialization, scene rendering, actual InputAction updates or gameplay.

The generated source manifests and original compiler logs are in three isolated Nitro scratch directories: /data/tmp/hpr-exact-reviewed-package-api-6000-6-20261102, /data/tmp/hpr-exact-reviewed-package-api-6000-4-20261102 and /data/tmp/hpr-exact-reviewed-package-api-6000-6-newinput-20261102.

## Original buyer-game upgrade fixture

A new disposable copy of an actually imported, populated Unity 6000.6.7f1 customer game is staged at /data/tmp/hpr-reviewed-raceguard-customer-upgrade-20261102/customer-project. Only Assets, Packages and ProjectSettings were copied, not the historical Unity Library/Temp build caches. The original source project was never changed.

The old frozen 161-asset Unity candidate matched every original vendor payload and GUID in the source game before staging, and again in its new disposable copy. An independent snapshot protects **63 original nonvendor customer Assets/Packages/ProjectSettings files**, including controllers, scenes, prefabs, code, settings and .meta identities. The new reviewed archive, not yet imported, correctly reports exactly seven expected source/document content mismatches against the old imported version and all 161 GUID identities still matching. This proves the test fixture is an OLD-package customer upgrade scenario, not a passed NEW-package import. A create-only staging receipt and protected customer file hashes are outside the staged Unity project.

A later genuine Unity Editor upgrade must import the exact new binary into that disposable game, show a real zero-exit Unity process and compile log, verify all 161 new package payloads/GUIDs, and independently confirm all 63 original customer file hashes unchanged. It must also run native Stats scene serialization, real healing/stamina and cooldown, and the staged dirty customer asset-copy/material conversion tests. Do not treat a clean package archive or fake Unity simulation as that acceptance.

## Current blocker and release decision

The previously authorized resource-broker-managed URP worker was still waiting under roughly eighty-percent Nitro CPU scheduling pressure and had started zero Unity import attempts. It was configured with the older frozen archive, not this reviewed new package. The worker was not interrupted or replaced, no other owner's computations were preempted, and no new post-cutoff automation was created.

The exact new package also needs actual URP 17.6 with the new-only Input System, a Built-in old-input customer test, domain reload disabled, accessible/visual Editor checks, safe dependent-game migration/uninstall and an independent experienced-developer benchmark against existing paid ability toolkits. The seller has no measured unique value or approved publisher submission. Current commercial status remains NO-GO.
