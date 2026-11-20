"""Offline regression: reject blank, wrong-size and magenta camera captures."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

SRC = Path(__file__).resolve().parents[1] / 'unity/tools/release/gameplay_suite/qa/check_rendered_urp_frames.py'
spec = importlib.util.spec_from_file_location('check_rendered_urp_frames', SRC)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestRenderedUrpFrames(unittest.TestCase):
    @staticmethod
    def fill(folder, *, blank=False, magenta=False, wrong_size=False):
        for name, size in module.EXPECTED.items():
            if wrong_size and name.startswith('02'):
                size = (size[0] - 1, size[1])
            im = Image.new('RGB', size, (0, 0, 0) if blank else (24, 40, 66))
            if magenta:
                im = Image.new('RGB', size, (240, 0, 240))
            elif not blank:
                draw = ImageDraw.Draw(im)
                for i in range(0, size[0], 8):
                    for j in range(0, size[1], 8):
                        draw.rectangle((i, j, min(i+7, size[0]-1), min(j+7, size[1]-1)),
                                       fill=(30+(i*3+j)%120, 70+(i+j*3)%110, 60+(i*2+j*2)%90))
            im.save(folder / name)

    def test_good_frames(self):
        with TemporaryDirectory() as d:
            self.fill(Path(d))
            report = module.check(Path(d))
            self.assertEqual(report['status'], 'PASS', report['errors'])
            self.assertEqual(report['human_artistic_approval'], 'NOT_PERFORMED')

    def test_blank_frames_fail(self):
        with TemporaryDirectory() as d:
            self.fill(Path(d), blank=True)
            self.assertEqual(module.check(Path(d))['status'], 'FAIL')

    def test_magenta_frames_fail(self):
        with TemporaryDirectory() as d:
            self.fill(Path(d), magenta=True)
            self.assertEqual(module.check(Path(d))['status'], 'FAIL')

    def test_wrong_size_fails(self):
        with TemporaryDirectory() as d:
            self.fill(Path(d), wrong_size=True)
            self.assertEqual(module.check(Path(d))['status'], 'FAIL')

    def test_missing_frame_fails(self):
        with TemporaryDirectory() as d:
            self.fill(Path(d))
            (Path(d) / '04-social-actual-unity-camera.png').unlink()
            self.assertEqual(module.check(Path(d))['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
