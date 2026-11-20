# HPR Gameplay Systems Suite — package format decision and Unity 6.6 support

Research updated November 1, 2026. This is an engineering choice record; no publisher account, product draft or paid SDK was changed.

## Verified first-party publishing/packaging guidance

- Unity 6.6 identifies two supported package classes: `.unitypackage` assets installed below `Assets/`, and Unity Package Manager (UPM) packages installed below `Packages/`. UPM supports dependency declarations, version switching and package manifests, while `.unitypackage` does not. Unity's own package-format guidance recommends **UPM for code, reusable elements and libraries intended for long-term maintenance**; it recommends `.unitypackage` for more one-time asset imports. Primary source: https://docs.unity.com/en-us/engine/6000.6/manual/packages-list/packages/upm-package-types.
- Unity officially released separate UPM Asset Store Publishing Tools package `com.unity.upm-publishing-tools` (listing version 0.3.1, June 8, 2026), which reports direct validation/upload/publication support for UPM packages. Listing: https://assetstore.unity.com/packages/package/5368745. Reported Unity compatibility includes 6000.0 through 6000.3 and earlier 2023/2022; actual **6000.6** operation and publishing eligibility for this existing owner account are unverified. Do not automatically change format or create another publisher account.
- Unity's ordinary Asset Store Publishing Tools 12.0.0 is the latest public GitHub release visible in November 2026. The tested original source failed to compile in Unity 6000.6 due to Unity API removal; a temporary test-only compatibility edit was required in Unity 6000.4 and the official validator checks then passed. This source edit was **not shipped** or uploaded. Source: https://github.com/Unity-Technologies/com.unity.asset-store-tools/releases .
- In Unity 6.6, Unity adds organization-aware **package signing for exported `.unitypackage` files** as a supported operation. This is an authenticity option, not evidence that our privately built package is signed or that Unity's marketplace has approved it. Official Unity Core Standards announcement: https://discussions.unity.com/t/unity-core-standards-what-s-new-in-6-6-and-6-7-and-looking-ahead-to-unity-7/1740002.
- Existing Unity asset-package creation guidance continues to allow public editor/API CLI export, preserving asset identity. Source: https://docs.unity.com/en-us/engine/6000.6/manual/assets-and-media/asset-packages/create . The HPR candidate's real Unity 6.6 imported archive has been validated with a static GUID audit and scene/code QA.

## Actual current HPR buyer offering

The current v14 release candidate is a source-authored `.unitypackage` with one root `Assets/HPRGameplaySuite`, 47 original runtime C# scripts in ten established assembly definitions, original sample scene/assets with stable `.meta` GUIDs, an optional UI Toolkit Editor guide and engineering docs. It is intentionally dependency-free and does not install an Input System or pipeline package. It is still marked `INTERNAL_QA_CANDIDATE_NOT_SUBMITTED_NOT_PUBLISHED`.

The current buyer guide, Editor menu actions and references expect that exact `Assets/HPRGameplaySuite` path. A naive move into `Packages/com.hpr.gameplay-suite` would break those paths and potentially scene references. Editing the code with hardcoded string replacement would not prove user-project compatibility. The older ten UPM packages have original `com.hpr.*` identifiers, which could conflict with an aggregate package if users install both. The supported archive already avoids a known GUID-regeneration issue, and real independent Unity 6000.4/6000.6 source-level work is documented.

## Choice: do not switch formats inside the current QA/recovery branch yet

UPM is likely a better long-term experience for a **mature C# programming SDK** if this product is ultimately commercially differentiated. However the existing publisher account must be verified and Unity's eligibility for a new consolidated UPM product is not yet confirmed. A format transition would require separate migration and acceptance tests, not a file rename. There is no verified buyer demand or revenue signal showing a UPM format alone is a unique selling proposition.

Retain the current source-authored `.unitypackage` as the technical candidate until the first-phase release test matrix is complete, while preparing a **separate, unsubmitted experimental UPM candidate** only if it has a defined buyer and versioning plan. Do not claim anything is published or signed.

## Explicit UPM migration quality gates (future separate work)

A UPM version must define one unambiguous package identity and version, dependency-minimal `package.json`, distinct runtime and editor `asmdef` references, UPM-safe asset lookup that does not depend on the `Assets/HPRGameplaySuite` path, opt-in `Samples~` instead of auto-modifying a user project, exported API/assembly stability and a migration map from previously installed source packages. It should support opening the demo as a sample, authoring ScriptableObject instances under a **customer-owned** location, and deleting/updating the vendor package without losing user-owned game data.

Acceptance must check: installation from local UPM folder in a populated Unity 6000.6 project; no duplicate or missing assemblies when switching from an older module configuration; no source or GUID mutations outside the package; a complete play/test fixture; old and new Input System as independently exercised; domain reload disabled; and real supported Unity UPM Publishing Tools validator results. Only once these pass and original publisher UPM eligibility is confirmed should the product format decision be revisited.

Market context: UPM long-term source maintainability is an expected ecosystem practice, not a substitute for demonstrable product value compared with mature modular Unity tools.
