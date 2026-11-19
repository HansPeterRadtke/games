# HPR Input Compatibility Audit — separate Unity editor-tool candidate

Purpose: detect *potential* Unity input-backend mismatches **without modifying project files**. This is a new original Editor-only product, independent of the ten-module Gameplay Systems Suite; it is not part of that buyer archive.

Private source: `Assets/HPRInputReadiness/Editor/HprInputReadinessAudit.cs` with stable, source-controlled `.meta` GUIDs. The project source includes `Assets/HPRInputReadiness/README.md`. QA-only `qa/HprInputReadinessQa.cs` and `qa/HprInputReadinessExporter.cs` **must not be shipped** in this product package. The latter exports the product root only. The read-only QA `qa/check_package_identity.py` independently checks exact archived path/payload/meta bytes and GUIDs against a fresh Unity import.

A genuine private native Unity project is created from scratch; QA sources are staged separately under private `Assets/Editor` and tests run with `-executeMethod HprInputReadinessQa.Run`. The package is exported with `-executeMethod HprInputReadinessExporter.Build` to a fresh path. A separately created buyer project must import the archive with `-importPackage`. Re-run native QA in that separate project, verify unchanged project settings and imported bytes, and retain the raw logs. Tests under the games repo verify non-mutating API usage, source safety and package identity.

Scope and limitations are in the buyer README. Not covered: automated code conversion, scene UI EventSystem components, all composite C# preprocessor expressions, embedded UPM source or real Player runtime behavior. This is a **candidate**, not human screen-reviewed, priced, licensed or approved for publication. No external publisher workflow is authorized by this README.
