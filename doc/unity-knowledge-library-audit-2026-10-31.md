# Unity Gameplay Suite: Raspi Knowledge Library evidence audit

October 31, 2026. Scoped to original KnowMoreDiRT FileDB and the isolated Unity integration worktree. This is a targeted source review, not a claim that all twelve thousand documents were read.

## Inventory and native FileDB

On host raspi, the downloaded library contains 12,365 present originals, approximately 66.5 GiB. Native FileDB reported all originals accounted for with correct sizes, zero scan/hash errors, SQLite integrity okay, 10,117 readable PDF page-count records and 168 nonfatal metadata warnings. The native semantic content index was actively building: first check showed 8,626 complete text extractions, 305 originals with genuine vectors and 2,057 embedded content chunks. The metadata database and native semantic database are separate.

Three genuine native semantic searches for gameplay architecture, persistent save states, and physically based rendering were run. Several results had high numerical similarity while being demonstrably irrelevant. Therefore the search was used for candidate discovery, supplemented with title-filtered catalog search and direct reading of original files. Do not treat vector scores or current incomplete indexing as whole-library knowledge.

## Reviewed primary-source material and direct changes

MaterialX Physically Based Shading Nodes v1.39 (June 5, 2026) at graphics/materials-color/materialx-pbr-spec.md and OpenPBR Surface v1.1.1 (April 17, 2026) at graphics/materials-color/openpbr-spec.html provide microfacet-roughness, dielectric versus metallic, and color-management definitions. These are platform-independent specifications; do not claim Unity Standard implements the complete OpenPBR surface model. The integrated demo's Unity material author now explicitly defines metallic and roughness and translates roughness into Standard/URP smoothness, with bounds and source regression testing. Existing scene materials remain synthetic/stylized, not photorealistic.

Adobe/Allegorithmic PBR Guide, Wes McDermott (third edition February 2018, 104 pages) and Ray Tracing in One Weekend v4.0.2 (April 25, 2025, 93 pages): inspected originals, copyright/edition, early pages and rendering contents. They provide general color/reflection and shading principles; neither authorizes embedding figures or book pages in the Unity product.

The locally archived official Unity Asset Store Submission Guidelines were opened at money-and-business/2026-platform-operations/digital-products/unity-asset-store-official-current-submission-requirements-f4b794ff30.html. Material rules: sections 1.1.m (submission quotas), 1.6 (AI transparency and differentiated value), 2.1.h (do not resubmit unchanged rejected packages), 2.3.a (complete local code docs), 2.5.a/d/e/g (readable source, user namespaces, consistent style and no private Editor API reflection), and 2.5.h (domain-reload-disabled Play Mode compatibility starting with Unity Editor 6.6). The current sample has been validated on Unity 6000.4 only; 6.6 support MUST remain unclaimed until independently tested.

GameDevBench, 2026, original PDF in ai-agents/agent-reliability-and-automation, 29 pages: inspected paper opening/abstract. Its executable and visual feedback recommendations support retaining real imported-archive Play Mode checks and genuine Unity camera screenshots, rather than equating source compilation with actual gameplay or commercial quality.

Additional located original references: the complete Blender 5.2 offline API/manual ZIPs; two Architecture of Open Source Applications volumes including Battle for Wesnoth, Continuous Integration and Python packaging; glTF 2.0, current Vulkan reference; OpenColorIO and other rendering textbooks and current papers. These are mapped for specific future use rather than indiscriminately included in the buyer product. Blender manuals are not evidence that the installed Blender version matches 5.2.

## Next validation priorities

After the PBR-sample authoring change, rebuild actual buyer archive and rerun fresh import, runtime and playmode tests. Require real separate tests for Unity 6.6 disabled-domain-reload behavior, URP/HDRP before claiming compatibility, especially considering original package differences. Add richer buyer-facing visuals and workflow tests before commercial submission. Retain accurate AI disclosures. Preserve all original knowledge texts on Raspi outside Git, and keep generated Unity packages outside Git.
