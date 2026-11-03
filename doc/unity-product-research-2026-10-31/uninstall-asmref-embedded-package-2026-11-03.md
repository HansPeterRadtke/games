# HPR safe-uninstall preflight — Unity assembly references and embedded customer packages

November 3, 2026, shortly after midnight Europe/Berlin. Independent QA only. **No buyer package was uninstalled or published.**

The existing read-only uninstall preflight already detects HPR serialized references in customer scenes, prefabs, assets, importer metadata, C-sharp code, assembly definitions, and Unity Package Manager manifest/lock files. Every report has deletion_permitted false. It is not an automatic uninstall or a guarantee of safe removal.

## A previously missed Unity assembly-reference format

Unity's first-party Assembly Definition File Format reference distinguishes two schemas. A .asmdef uses a references array; a .asmref uses a required singular reference string, which may be an assembly name or GUID followed by a thirty-two-character assembly-definition asset identifier. The previous scanner treated both extensions as .asmdef files and silently read a missing array as empty. An actual customer .asmref binding scripts into HPR's runtime assembly could consequently be reported as no direct reference detected.

Official Unity references:
https://docs.unity.com/en-us/engine/6000.7/manual/programming-environment/script-compilation/assembly-definition-files/file-format
https://docs.unity.com/en-us/engine/6000.6/manual/programming-environment/script-compilation/assembly-definition-files/assembly-definitions-creating

The correction parses the required .asmref reference string and validates its type and GUID syntax. HPR assembly-name or exact vendor-GUID hits are reported as asmref_reference, with actionable Unity Inspector/manual migration guidance. Missing, blank, non-string or malformed references require review and never authorize removal. Malformed entries in a .asmdef references array are also rejected.

Four test-first failures reproduced the old blind spots. Six new assembly-reference tests passed together with the original seventeen regression cases.

## Editable customer packages

The previous scanner traversed only the project Assets tree, plus the top-level Packages manifest and lock. Unity allows customer-authored embedded packages directly inside Packages/com.customer.game; their C-sharp, .asmdef and .asmref files may use HPR even if there are no references in Assets or the manifest.

The corrected preflight traverses both project Assets and embedded Packages under a **single bounded scan budget**. It skips HPR's own embedded package files to avoid self-references, while refusing symlink escapes. It scans customer C-sharp and assembly assets, treats malformed/binary input conservatively, and retains separate schema-aware checks for Packages/manifest.json and Packages/packages-lock.json.

Seven new test cases covered customer embedded C-sharp, .asmdef by name, .asmref by GUID, HPR self-exclusion, symlinks, binary uncertainty and traversal limits. Three more test-first cases reproduced another dangerous omission: a customer embedded package.json file can declare a transitive dependency on com.hpr.abilities without that package appearing in the top-level project manifest. Unity explicitly documents that embedded packages are loaded automatically and package.json stores their own dependencies. The scanner now validates the embedded package.json dependency map, records HPR links under embedded_package_manifest_reference, and treats invalid JSON or non-dictionary dependencies as unknown requiring review. The full focused regression set now passes thirty-three tests. The scanner is not yet shipped in a graphical Unity Editor window.

A later test-first regression found a further false negative: using any com.hpr.* directory name as a reason to skip scanning would hide customer-developed integration packages with names such as com.hpr.customerbridge. Only the ten actual vendor module identifiers from the frozen HPR archive may be self-excluded. The revised uninstall preflight derives them from the selected archive itself. An independent fixture using the actual reviewed archive demonstrated the old scanner's no-direct-reference misclassification and the corrected customer_dependencies_found classification, while preserving all buyer files byte-for-byte.

Additional first-party Unity references:
https://docs.unity.com/en-us/engine/6000.6/manual/packages-list/packages/upm-concepts
https://docs.unity.com/en-us/engine/6000.6/manual/packages-list/cus-pkg-lp/cus-pkg-development/cus-pkg-manifest/cus-edit-manifest
https://docs.unity.com/en-us/engine/6000.6/manual/packages-list/dependencies-lp/upm-embed

## Actual package and customer evidence

The private reviewed HPR archive contains 161 Unity asset and GUID identities. A real package .asmdef for HPR.Abilities.Runtime was identified from that archive, not guessed.

The corrected preflight was run read-only on a preserved populated Unity customer project containing an earlier HPR import. It still found **ten direct customer dependencies** (six C-sharp uses and four serialized vendor GUID references), with no unknown source files and deletion_permitted false. The older scanner found the same ten; the correction did not erase historical findings.

A second, disposable Unity-style customer project was created with an existing unrelated controller and a customer-owned embedded .asmref using the **actual archive's HPR assembly-definition GUID**. The old scanner incorrectly reported no_direct_reference_detected. The corrected scanner reported customer_dependencies_found and correctly identified the embedded .asmref. SHA-256 checks verified that all fixture files were untouched by either scanner.

A separate, newly created package-manifest fixture used the same exact vendor archive and an unrelated existing customer controller, with only a customer embedded package.json declaring com.hpr.abilities. The old scanner again incorrectly reported no_direct_reference_detected; the revised scanner reported the exact embedded_package_manifest_reference and left all input bytes unchanged. The positive, negative and source hash evidence is preserved in a separate private QA receipt rather than replacing the earlier records.

Private evidence is preserved at the owner's marketplace-account-setup QA evidence location, separate from Git and the original customer game. These are genuine parser and archival-source identity checks, not a real Unity Editor compilation, concurrent importer acceptance or graphical buyer workflow test.

**Commercial conclusion: NO-GO.** Safe dependent-game migration/uninstall, genuine Unity Editor UI and Play-mode verification, URP/new-only Input System, human keyboard/visual UX assessment and qualified buyer comparisons remain outstanding. No files were deleted, no marketplace account was changed and no rejected product was resubmitted.
