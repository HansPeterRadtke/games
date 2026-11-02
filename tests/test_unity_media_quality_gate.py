"""Deterministic nonblack screenshot quality gate (not a human visual review)."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
SPEC=importlib.util.spec_from_file_location("hpr_unity_media_audit",QA/"hpr_unity_media_audit.py")
media=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(media)


class UnityScreenshots(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="hpr_media_quality_")
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)

    def save(self,name,array):
        path=self.dir/name
        Image.fromarray(array.astype(np.uint8),"RGB").save(path)
        return path

    @staticmethod
    def good_scene(seed=0):
        h,w=900,1600
        rng=np.random.default_rng(seed)
        y,x=np.mgrid[0:h,0:w]
        image=np.empty((h,w,3),dtype=np.uint8)
        image[:,:,:]=np.clip(70+90*(y/h)[:,:,None]+30*(x/w)[:,:,None],0,255).astype(np.uint8)
        # Genuine spatial structure, not merely random pixel noise.
        for n in range(14):
            start=45+n*105
            image[200:800,start:start+35,:]=np.array([160+seed%30,75,45],dtype=np.uint8)
            image[300:340,start:start+65,:]=np.array([80,185,80],dtype=np.uint8)
        return image

    def test_black_image_rejected(self):
        image=self.save("black.png",np.zeros((900,1600,3)))
        self.assertEqual("FAIL",media.analyze_image(image)["status"])

    def test_uniform_nonblack_background_rejected(self):
        image=self.save("uniform.png",np.full((900,1600,3),110))
        report=media.analyze_image(image)
        self.assertEqual("FAIL",report["status"])
        self.assertTrue(any("detail" in r or "contrast" in r for r in report["reasons"]))

    def test_meaningful_spatial_scene_accepted(self):
        image=self.save("good.png",self.good_scene())
        report=media.analyze_image(image)
        self.assertEqual("PASS",report["status"])
        self.assertGreaterEqual(report["width"],1280)
        self.assertGreater(report["center_luminance_std"],0.045)

    def test_duplicate_screenshot_pair_rejected(self):
        source=self.save("a.png",self.good_scene())
        duplicate=self.save("b.png",self.good_scene())
        report=media.analyze_gallery([source,duplicate])
        self.assertEqual("FAIL",report["status"])
        self.assertEqual(1,len(report["pairs"]))
        self.assertFalse(report["pairs"][0]["distinct_views"])

    def test_different_views_from_same_scene_accepted(self):
        a=self.good_scene(seed=3)
        b=np.roll(self.good_scene(seed=7),200,axis=1)
        first=self.save("a.png",a)
        second=self.save("b.png",b)
        report=media.analyze_gallery([first,second])
        self.assertEqual("PASS",report["status"])
        self.assertTrue(report["pairs"][0]["distinct_views"])

    def test_invalid_dimensions_fail_without_guessing(self):
        tiny=self.save("tiny.png",np.ones((80,100,3))*110)
        report=media.analyze_image(tiny)
        self.assertEqual("FAIL",report["status"])
        self.assertTrue(any("resolution" in reason for reason in report["reasons"]))

    def test_actual_prior_urp_black_camera_rejected_and_fixed_gallery_accepted(self):
        parent=Path("/data/var/marketplace-account-setup")
        bad=parent/"unity-consolidated-20261101-v14-urp/release/media/01-arena-actual-unity-camera.png"
        fixed=parent/"unity-consolidated-20261101-v14-urp-fixed-media/release/media"
        if not bad.exists() or not fixed.exists():
            self.skipTest("real Unity 6.6 media fixtures are not available on this host")
        self.assertEqual("FAIL",media.analyze_image(bad)["status"])
        accepted=media.analyze_gallery(sorted(fixed.glob("*.png")))
        self.assertEqual("PASS",accepted["status"])


if __name__=="__main__":
    unittest.main()
