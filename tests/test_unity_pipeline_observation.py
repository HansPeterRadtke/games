import copy
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/ExistingGameWorkflow/run_native_workflow.py"
spec = importlib.util.spec_from_file_location("workflow", path)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def receipt(kind="urp", override=False):
    path = "Assets/URP/CustomerPipeline.asset" if kind == "urp" else ""
    rows = []
    for phase, playing in (("before_scene_authoring", False), ("during_play", True), ("after_play", False)):
        rows.append(dict(phase=phase, playing=playing,
            assetType="UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset" if path else "",
            assetPath=path, assetGuid="abc123de" * 4 if path else "",
            defaultAssetPath="Assets/URP/Default.asset" if override else path,
            qualityOverridePath=path if override else "", qualityLevel=2,
            pipelineInstanceType="", graphicsDevice="Null"))
    return dict(schema=1, engineVersion="6000.6.7f1", processId=123, observations=rows)


class PipelineObservationTests(unittest.TestCase):
    def test_real_selection_shapes_and_quality_override(self):
        for kind in ("urp", "builtin"):
            self.assertTrue(qa.classify_pipeline_observation(kind, receipt(kind)))
        self.assertTrue(qa.classify_pipeline_observation("urp", receipt(override=True)))

    def test_installed_package_does_not_certify_selected_pipeline(self):
        self.assertFalse(qa.classify_pipeline_observation("urp", receipt("builtin")))
        self.assertFalse(qa.classify_pipeline_observation("builtin", receipt("urp")))

    def test_every_missing_duplicate_or_unordered_phase_rejected(self):
        for index in range(3):
            data = receipt(); data["observations"].pop(index)
            self.assertFalse(qa.classify_pipeline_observation("urp", data))
        data = receipt(); data["observations"][1] = copy.deepcopy(data["observations"][0])
        self.assertFalse(qa.classify_pipeline_observation("urp", data))
        data = receipt(); data["observations"].reverse()
        self.assertFalse(qa.classify_pipeline_observation("urp", data))

    def test_pipeline_or_quality_changes_rejected(self):
        for key, value in (("assetGuid", "f" * 32), ("assetType", "OtherPipeline"), ("qualityLevel", 3), ("defaultAssetPath", "Assets/Other.asset"), ("assetPath", "Assets/Other.asset")):
            data = receipt(); data["observations"][1][key] = value
            with self.subTest(key=key): self.assertFalse(qa.classify_pipeline_observation("urp", data))

    def test_missing_wrong_typed_and_malformed_fields_rejected(self):
        for key, value in (("assetGuid", ""), ("assetGuid", "not-a-guid"), ("assetPath", "../outside.asset"), ("playing", 1), ("graphicsDevice", "OpenGLCore"), ("qualityLevel", True), ("pipelineInstanceType", "OtherPipeline"), ("assetType", None)):
            data = receipt(); data["observations"][1][key] = value
            with self.subTest(key=key, value=value): self.assertFalse(qa.classify_pipeline_observation("urp", data))
        for value in (None, {}, [], {"observations": None}):
            self.assertFalse(qa.classify_pipeline_observation("urp", value))

    def test_bad_identity_schema_and_process_rejected(self):
        for key, value in (("schema", True), ("schema", 0), ("engineVersion", ""), ("engineVersion", None), ("processId", True), ("processId", 0), ("processId", -1)):
            data = receipt(); data[key] = value
            with self.subTest(key=key, value=value): self.assertFalse(qa.classify_pipeline_observation("urp", data))
        self.assertFalse(qa.classify_pipeline_observation("unknown", receipt()))
        data = receipt(); data["observations"][1] = None
        self.assertFalse(qa.classify_pipeline_observation("urp", data))

    def test_optional_native_instance_does_not_imply_rendered_frame(self):
        data = receipt(); data["observations"][1]["pipelineInstanceType"] = "UnityEngine.Rendering.Universal.UniversalRenderPipeline"
        self.assertTrue(qa.classify_pipeline_observation("urp", data))
        self.assertTrue(qa.classify_pipeline_observation("urp", receipt()))


class PipelineModeBoundaryTests(unittest.TestCase):
    def test_incompatible_modes_are_rejected_before_project_or_archive_access(self):
        from unittest.mock import patch
        import sys
        base = ["qa", "--template", "/unused-template", "--archive", "/unused-archive", "--archive-sha256", "unused", "--editor", "/unused-editor", "--output", "/unused-output", "--domain-reload", "off", "--expected-render-pipeline", "urp"]
        for extra in (("--scenario", "wired", "--configuration-matrix"), ("--scenario", "shadow"), ("--scenario", "wired", "--cold-save-source", "/unused-save")):
            with self.subTest(extra=extra), patch.object(sys, "argv", base + list(extra)):
                with self.assertRaisesRegex(ValueError, "full wired same-process"):
                    qa.main()
