"""Source contract for safe selection of demo shaders by ACTIVE render pipeline.

Independent compiled C# source-harness evidence is produced separately by
unity/tools/release/gameplay_suite/qa/verify_pipeline_shader_offline.py.
Neither test route starts Unity or approves marketplace publication.
"""
from pathlib import Path
import ast
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"unity/tools/release/gameplay_suite"
BUILDER=SOURCE/"HprGameplaySuiteSceneBuilder.cs"
HARNESS=SOURCE/"qa/verify_pipeline_shader_offline.py"


class GameplaySuiteShaderChoice(unittest.TestCase):
    def setUp(self):
        self.source=BUILDER.read_text()

    def test_real_pipeline_type_names_and_scoped_shaders(self):
        names=re.findall(
            r'DemoShaderNameForPipelineType\(string activePipelineType\).*?'
            r'private static Shader RequireActiveDemoShader\(\)',
            self.source,re.DOTALL
        )
        self.assertEqual(len(names),1)
        selector=names[0]
        for value in ('UniversalRenderPipelineAsset','HDRenderPipelineAsset',
                      'Universal Render Pipeline/Lit','HDRP/Lit','Standard'):
            self.assertIn(value,selector)
        self.assertIn('StringComparison.Ordinal',selector)
        self.assertIn('throw new InvalidOperationException',selector)
        self.assertNotIn('activePipelineType.Contains(',selector)

    def test_creation_and_adaptation_use_same_real_shader_selection(self):
        self.assertEqual(self.source.count('Shader target = RequireActiveDemoShader();'),1)
        self.assertEqual(self.source.count('Shader shader = RequireActiveDemoShader();'),1)
        self.assertIn('GraphicsSettings.currentRenderPipeline;',self.source)
        self.assertIn('Shader.Find(name)',self.source)
        self.assertIn('shader == null || !shader.isSupported',self.source)
        self.assertNotIn('Shader.Find("Universal Render Pipeline/Lit") ??',self.source)
        self.assertNotIn('if (shader == null) shader = Shader.Find("Unlit/Color")',self.source)

    def test_color_of_active_hdrp_urp_material_uses_its_real_property(self):
        self.assertIn('SetDemoMaterialColor(Material material, Color color)',self.source)
        self.assertIn('material.HasProperty("_BaseColor")',self.source)
        self.assertIn('material.SetColor("_BaseColor", color)',self.source)
        self.assertIn('material.HasProperty("_Color")',self.source)
        self.assertIn('material.SetColor("_Color", color)',self.source)
        self.assertNotIn('material.color = color;',self.source)
        creation=self.source.split('private static Material CreateMaterial(',1)[1].split('private static GameObject Shape(',1)[0]
        conversion=self.source.split('public static void AdaptDemoMaterials()',1)[1].split('public static void BuildAndExport()',1)[0]
        self.assertEqual(creation.count('SetDemoMaterialColor(material, color);'),2)
        self.assertEqual(conversion.count('SetDemoMaterialColor(material, color);'),1)
        self.assertLess(creation.index('SetDemoMaterialColor(material, color);'),
                        creation.index('AssetDatabase.CreateAsset(material, path);'))
        self.assertIn('AssetDatabase.SaveAssetIfDirty(material)',conversion)
        self.assertNotIn('AssetDatabase.SaveAssets()',conversion)

    def test_independent_real_csharp_source_harness_is_reproducible(self):
        script=HARNESS.read_text()
        ast.parse(script)
        for value in ('extract_method(original,"DemoShaderNameForPipelineType")',
                      'extract_method(original,"RequireActiveDemoShader")',
                      'extract_method(original,"SetDemoMaterialColor")',
                      'dotnet','HPR_PIPELINE_SHADER_SOURCE_PASS assertions=22',
                      'Shader.Available.Remove("HDRP/Lit")',
                      'Shader.Available.Remove("Universal Render Pipeline/Lit")',
                      'both.colors["Color"]' if False else 'both.colors["_Color"]',
                      'Unsupported HDRP shader fails closed'):
            with self.subTest(value=value):
                self.assertIn(value,script)
        self.assertIn('CSharpSyntaxTree.ParseText',script)
        self.assertIn('UNITY_6000_6_OR_NEWER',script)
        self.assertNotIn('UnityEditor.exe',script)

    def test_explicit_scope_does_not_claim_new_unity_acceptance(self):
        readme=(SOURCE/"README.md").read_text()
        self.assertIn('Exact-current',readme)
        self.assertIn('URP/HDRP',readme)
        self.assertIn('have not yet been accepted',readme)


if __name__=="__main__":
    unittest.main()
