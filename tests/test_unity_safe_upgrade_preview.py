"""Read-only source/asset/consumer preflight for a versioned HPR Unity upgrade.

A PASS means only the SOURCE FILE preconditions were verified. It NEVER
authorizes package import, deletion, or a commercial publication.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_unity_archive_policy import ROOT_FOLDER, SCRIPT, unitypackage
from test_unity_release_export import emit_package

QA=Path(__file__).resolve().parents[1]/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_safe_upgrade_preview as preview


class UpgradePreconditions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="hpr_safe_upgrade_preview_")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.old=self.root/"old.unitypackage"
        self.new=self.root/"new.unitypackage"
        self.old.write_bytes(b"previous exact private vendor Unity package")
        unitypackage(self.new, (ROOT_FOLDER, SCRIPT))
        self.old_sha=hashlib.sha256(self.old.read_bytes()).hexdigest()
        self.new_sha=hashlib.sha256(self.new.read_bytes()).hexdigest()
        self.project=self.root/"real-buyer-game"
        (self.project/"Assets/ExistingCustomerGame").mkdir(parents=True)
        (self.project/"Assets/ExistingCustomerGame/MyController.cs").write_text("class OriginalController {}")
        (self.project/"ProjectSettings").mkdir()
        (self.project/"ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.6.7f1")
        self.old_identity={
            "status":"PASS","asset_paths_verified":161,
            "guid_identities_verified":161,"issues":[],
        }
        self.guid_result={
            "baseline_assets":161,"candidate_assets":161,
            "shared_assets":161,"unchanged_shared_guids":161,
            "changed_shared_guids":[],"removed_reference_guids":[],
            "added_assets":[],"removed_assets":[],
        }
        self.dependencies={
            "classification":"customer_dependencies_found",
            "dependencies":[{"kind":"serialized_vendor_guid",
                             "path":"Assets/ExistingCustomerGame/ExistingScene.unity"}],
            "unknowns":[],"deletion_permitted":False,
        }

    def run_preview(self):
        return preview.inspect(self.project,self.old,self.old_sha,
                               self.new,self.new_sha)

    def patches(self):
        return (
            mock.patch.object(preview,"verify_import",return_value=self.old_identity),
            mock.patch.object(preview,"compare",return_value=self.guid_result),
            mock.patch.object(preview,"inspect_uninstall",return_value=self.dependencies),
            mock.patch.object(preview,"find_customer_guid_collisions",return_value=[]),
        )

    def test_real_user_files_remain_unchanged_and_dependencies_require_review(self):
        original=self.project/"Assets/ExistingCustomerGame/MyController.cs"
        before=original.read_bytes()
        a,b,c,d=self.patches()
        with a,b,c,d:
            result=self.run_preview()
        self.assertEqual("review_required_customer_dependencies",result["decision"])
        self.assertEqual(161,result["current_installed_vendor_guid_identities"])
        self.assertEqual(1,result["customer_dependency_count"])
        self.assertEqual(before,original.read_bytes())
        self.assertTrue(result["read_only"])
        self.assertFalse(result["automatic_upgrade_authorized"])
        self.assertFalse(result["actual_unity_editor_compilation_or_import_verified"])
        self.assertFalse(result["deletion_permitted"])

    def test_no_consumer_findings_still_needs_native_unity_editor(self):
        self.dependencies={"classification":"no_direct_reference_detected",
                           "dependencies":[],"unknowns":[],"deletion_permitted":False}
        a,b,c,d=self.patches()
        with a,b,c,d:r=self.run_preview()
        self.assertEqual("source_preconditions_verified_editor_acceptance_required",r["decision"])
        self.assertFalse(r["automatic_upgrade_authorized"])

    def test_existing_vendor_modifications_block_update(self):
        self.old_identity.update(status="FAIL",
                                 issues=["asset payload differs from exact archive: HPR source"])
        a,b,c,d=self.patches()
        with a,b,c,d:r=self.run_preview()
        self.assertEqual("blocked_modified_or_missing_old_vendor_assets",r["decision"])
        self.assertTrue(r["issues"])

    def test_guids_modified_or_removed_block_update(self):
        self.guid_result["changed_shared_guids"]=["Assets/HPRGameplaySuite/Editor/Installer.cs"]
        a,b,c,d=self.patches()
        with a,b,c,d:r=self.run_preview()
        self.assertEqual("blocked_asset_guid_breaking_update",r["decision"])
        self.assertFalse(r["automatic_upgrade_authorized"])

    def test_embedded_customer_guid_collision_refuses_import(self):
        a,b,c,d=self.patches()
        conflict="Packages/com.customer.game/Runtime/CustomAbility.asmref.meta"
        with a,b,c,d,mock.patch.object(preview,"find_customer_guid_collisions",
                                      return_value=[conflict]):
            result=self.run_preview()
        self.assertEqual("blocked_unrelated_customer_guid_collision",result["decision"])
        self.assertEqual([conflict],result["customer_guid_collisions"])
        self.assertFalse(result["automatic_upgrade_authorized"])

    def test_moved_asset_path_with_stable_guid_still_requires_review(self):
        self.guid_result["removed_assets"]=["Assets/HPRGameplaySuite/Editor/OldTool.cs"]
        self.guid_result["added_assets"]=["Assets/HPRGameplaySuite/Editor/RenamedTool.cs"]
        # Unity references usually use GUIDs, but consumer C# can dynamically
        # load a path and must be reviewed before a rename is accepted.
        a,b,c,d=self.patches()
        with a,b,c,d:r=self.run_preview()
        self.assertEqual("review_required_removed_or_moved_vendor_paths",r["decision"])
        self.assertFalse(r["automatic_upgrade_authorized"])

    def test_vendor_file_changed_during_inspection_blocks_upgrade(self):
        after={"status":"FAIL","asset_paths_verified":160,
               "guid_identities_verified":161,
               "issues":["asset payload differs from exact archive: HPR Installer"]}
        a,b,c,d=self.patches()
        with a,b,c,d,mock.patch.object(preview,"verify_import",
                                   side_effect=[self.old_identity,after]):
            r=self.run_preview()
        self.assertEqual("blocked_old_vendor_changed_during_preflight",r["decision"])
        self.assertEqual("FAIL",r["post_scan_old_import_status"])

    def test_unknown_customer_content_fails_closed(self):
        self.dependencies.update(classification="unknown_project_content_requires_review",
                                 dependencies=[],unknowns=[{"path":"Assets/ExistingCustomerGame/Unknown.asset",
                                                          "reason":"binary"}])
        a,b,c,d=self.patches()
        with a,b,c,d:r=self.run_preview()
        self.assertEqual("review_required_uninspectable_customer_content",r["decision"])
        self.assertFalse(r["automatic_upgrade_authorized"])

    def test_wrong_source_sha_rejected_before_integrity_checks(self):
        with self.assertRaises(ValueError):
            preview.inspect(self.project,self.old,"0"*64,self.new,self.new_sha)
        with self.assertRaises(ValueError):
            preview.inspect(self.project,self.old,self.old_sha,self.new,"0"*64)

    def test_original_customer_files_changing_during_preflight_block(self):
        from customer_integrity import snapshot_customer_project
        base=snapshot_customer_project(self.project)
        controller=self.project/"Assets/ExistingCustomerGame/MyController.cs"
        calls=[base,dict(base)]
        calls[-1]["Assets/ExistingCustomerGame/MyController.cs"]="a"*64
        a,b,c,d=self.patches()
        with a,b,c,d,mock.patch.object(preview,"snapshot_customer_project",
                                    side_effect=calls):
            r=self.run_preview()
        self.assertEqual("blocked_customer_files_changed_during_preflight",r["decision"])

    def test_embedded_customer_source_modified_during_preflight_blocks_update(self):
        # The source-under-test must hash Packages/com.customer.* as buyer
        # files, and must not return a safe upgrade when a foreign process
        # changes an embedded customer C# file during dependency scanning.
        embedded=self.project/"Packages/com.customer.game/Runtime"
        embedded.mkdir(parents=True)
        source=embedded/"CustomerAbilityBridge.cs"
        source.write_text("class CustomerBridge { }\n")
        def concurrent_package_edit(project,old_archive):
            source.write_text("using HPR; class CustomerBridge { }\n")
            return self.dependencies
        a,b,c,d=self.patches()
        with a,b,d,mock.patch.object(preview,"inspect_uninstall",
                                   side_effect=concurrent_package_edit):
            r=self.run_preview()
        self.assertEqual("blocked_customer_files_changed_during_preflight",r["decision"])
        self.assertEqual(["Packages/com.customer.game/Runtime/CustomerAbilityBridge.cs"],
                         r["customer_files_changed_during_preflight"])
        self.assertFalse(r["automatic_upgrade_authorized"])

    def test_pinned_malformed_candidate_fails_before_reading_the_buyer_project(self):
        cases = (
            ((SCRIPT[0], SCRIPT[1], None), "missing non-directory asset payload"),
            ((SCRIPT[0], "Assets/ExistingCustomerGame/MyController.cs", SCRIPT[2]),
             "unsafe, non-suite"),
        )
        for entry, diagnostic in cases:
            with self.subTest(entry=entry[1]):
                unitypackage(self.new, (ROOT_FOLDER, entry))
                self.new_sha = preview.digest_file(self.new)
                with mock.patch.object(preview, "snapshot_customer_project") as snapshot:
                    with self.assertRaisesRegex(ValueError, diagnostic):
                        self.run_preview()
                    snapshot.assert_not_called()

    def test_legacy_archives_preserve_dependency_and_guid_collision_checks(self):
        # Exercise the whole preview with real tar records, metadata and files.
        # The shared GUID comparison expects at least one hundred suite assets.
        self.project = self.root / "legacy-game"
        installed = self.project / "Assets/HPRGameplaySuite"
        installed.mkdir(parents=True)

        def write_meta(path, guid):
            Path(str(path) + ".meta").write_text(f"fileFormatVersion: 2\nguid: {guid}\n")

        write_meta(installed, ROOT_FOLDER[0])
        for index in range(1, 101):
            asset = installed / f"Sample{index}.txt"
            asset.write_text("HPR sample")
            write_meta(asset, f"{index:032x}")

        emit_package(installed.parent, self.old, legacy=True)
        emit_package(installed.parent, self.new, legacy=True)
        self.old_sha, self.new_sha = map(preview.digest_file, (self.old, self.new))
        first_guid = f"{1:032x}"
        customer = self.project / "Assets/ExistingCustomerGame"
        customer.mkdir()
        scene = customer / "Player.prefab"
        scene.write_text(f"%YAML 1.1\nref: {{fileID: 1, guid: {first_guid}, type: 3}}\n")
        report = self.run_preview()
        self.assertEqual(report["decision"], "review_required_customer_dependencies")
        self.assertEqual(report["current_installed_vendor_guid_identities"], 101)
        self.assertTrue(any(dep.get("guid") == first_guid
                            for dep in report["customer_dependency_findings"]))

        write_meta(scene, first_guid)
        report = self.run_preview()
        self.assertEqual(report["decision"], "blocked_unrelated_customer_guid_collision")
        self.assertEqual(report["customer_guid_collisions"],
                         ["Assets/ExistingCustomerGame/Player.prefab.meta"])

    def test_report_destination_cannot_overlap_any_input(self):
        safe=self.root/"out"/"check.json"
        preview.validate_receipt_location(safe,self.project,self.old,self.new)
        for bad in (self.project/"Assets/Preflight.json",
                    self.old,self.new,self.root/"out"/"check.json"):
            if bad==safe:continue
            with self.subTest(bad=bad):
                if bad in (self.old,self.new) or bad.is_relative_to(self.project):
                    with self.assertRaises(ValueError):
                        preview.validate_receipt_location(bad,self.project,self.old,self.new)

    def test_preflight_never_deletes_or_writes_buyer_files(self):
        a,b,c,d=self.patches()
        with a,b,c,d:
            report=self.run_preview()
        before=report["customer_original_sha256"]
        from customer_integrity import snapshot_customer_project
        self.assertEqual(before,snapshot_customer_project(self.project))
        self.assertEqual(set(before),set(["Assets/ExistingCustomerGame/MyController.cs",
                                          "ProjectSettings/ProjectVersion.txt"]))


if __name__=="__main__":unittest.main()
