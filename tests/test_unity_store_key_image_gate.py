"""Verify fixed-size Unity Asset Store promotional key image requirements.

Pixel/dimension checks are separate from the actual Unity-rendered gameplay
screenshots and from professional marketing visual signoff.
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

QA=Path(__file__).resolve().parents[1]/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
SPEC=importlib.util.spec_from_file_location("unity_store_key_image_gate",QA/"hpr_unity_store_key_image_gate.py")
gate=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class KeyArtRequirements(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="hpr_store_key_art_")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def image(self,name,dimensions):
        image=Image.new("RGB",dimensions,(42,87,114))
        path=self.root/name
        image.save(path)
        return path

    def test_role_dimensions_are_explicit_and_validated(self):
        expected={"icon":(160,160),"card":(420,280),
                  "cover":(1950,1300),"social":(1200,630)}
        self.assertEqual(expected,gate.KEY_IMAGE_SIZES)
        for role,size in expected.items():
            good=self.image(role+".png",size)
            self.assertEqual("PASS",gate.verify_image(good,role)["status"])
            wrong=self.image(role+"-wrong.png",(1600,900))
            self.assertEqual("FAIL",gate.verify_image(wrong,role)["status"])

    def test_gallery_requires_all_four_distinct_roles(self):
        correct={role:self.image(role+".png",size)
                 for role,size in gate.KEY_IMAGE_SIZES.items()}
        self.assertEqual("PASS",gate.verify_set(correct)["status"])
        self.assertEqual("FAIL",gate.verify_set({"cover":correct["cover"]})["status"])

    def test_invalid_role_rejected_not_guessed(self):
        with self.assertRaises(ValueError):
            gate.verify_image(self.image("unknown.png",(160,160)),"fake")

    def test_image_can_pass_dimensions_without_human_marketing_approval(self):
        report=gate.verify_image(self.image("cover.png",(1950,1300)),"cover")
        self.assertEqual("PASS",report["status"])
        self.assertFalse(report["human_visual_content_review_completed"])
        self.assertFalse(report["verified_origin_from_unity_editor"])

    def test_historical_store_cover_is_not_a_compliant_1950x1300_key_cover(self):
        path=Path("/data/var/marketplace-account-setup/unity-consolidated-20261101-v14-urp-fixed-media/release/media/store/01-store-cover.png")
        if not path.is_file():
            self.skipTest("Historical actual Unity screenshot is not on this host")
        report=gate.verify_image(path,"cover")
        self.assertEqual("FAIL",report["status"])
        self.assertEqual([1600,900],report["observed_dimensions"])


if __name__=="__main__":
    unittest.main()
