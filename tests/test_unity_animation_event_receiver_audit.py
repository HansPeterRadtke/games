"""Offline source and package contract tests, not native Unity acceptance."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'unity/tools/release/animation_event_receiver_audit'
ASSETS = TOOL / 'Assets/HPRAnimationEventAudit'
EDITOR = ASSETS / 'Editor/HprAnimationEventAudit.cs'

class AnimationEventAuditSourceContract(unittest.TestCase):
    def test_stable_unique_meta_identities_and_only_editor_assets(self):
        found = set()
        for source in (ASSETS, *ASSETS.rglob('*')):
            if source.name.endswith('.meta'):
                continue
            meta = Path(str(source)+'.meta')
            self.assertTrue(meta.is_file(),str(meta))
            match = re.search(r'(?m)^guid: ([0-9a-f]{32})$',meta.read_text())
            self.assertIsNotNone(match,str(meta))
            self.assertNotIn(match.group(1),found)
            found.add(match.group(1))
        self.assertEqual(len(found),6)
        self.assertFalse(list(ASSETS.rglob('HprEventAuditNativeQa.cs')))
        self.assertFalse(list(ASSETS.rglob('HprEventAuditFixtureReceiver.cs')))

    def test_scanner_is_read_only_with_explicit_actual_asset_scope(self):
        text = EDITOR.read_text()
        for token in ('#if UNITY_EDITOR', 'AnimationUtility.GetAnimationEvents(clip)',
                      'AssetDatabase.FindAssets("t:Prefab"', 'GetComponents<MonoBehaviour>()',
                      'animationClips', 'ReceiverSignatureStatus',
                      'OVERLAPPING_EVENT_MARKERS', 'NO_RECEIVER_METHOD', 'INVALID_RECEIVER_SIGNATURE',
                      'INCOMPLETE', 'CLEAR_WITH_LIMITS', 't:Prefab', 'MaxPrefabs', 'MaxClips',
                      'MaxEvents', 'MaxFindings', 'EditorApplication.isCompiling',
                      'No changes, automatic fixes'):
            self.assertIn(token,text)
        for prohibited in ('AssetDatabase.DeleteAsset(', 'AssetDatabase.CreateAsset(',
                           'AnimationUtility.SetAnimationEvents(', 'EditorUtility.SetDirty(',
                           'AssetDatabase.ImportPackage(', 'PrefabUtility.SaveAsPrefabAsset(',
                           'SetActiveBuildProfile(', 'WebRequest', 'HttpClient('):
            self.assertNotIn(prohibited,text)

    def test_report_has_serializable_findings_and_create_only_safe_export(self):
        text=EDITOR.read_text()
        for token in ('[Serializable]', 'public List<HprEventFinding> findings',
                      'JsonUtility.ToJson(report, true)', 'FileMode.CreateNew',
                      'outside the Unity project', 'Audit report exceeds',
                      'MessageType.Warning', 'MenuItem("Tools/HPR/Animation Event Receiver Audit")'):
            self.assertIn(token,text)
        self.assertNotIn('public readonly List<HprEventFinding>',text)
        self.assertNotIn('GetInstanceID()',text)
        self.assertIn('new HashSet<AnimationClip>()',text)
        self.assertIn('parameter.FullName == "UnityEngine.AnimationEventInfo"',text)
        self.assertIn('new Dictionary<float, string>()',text)
        self.assertIn('AssetDatabase.IsValidFolder(folder)',text)
        self.assertIn('Scan folder (optional)',text)

    def test_real_native_qa_is_separate_and_explicit(self):
        qa = (TOOL/'qa/HprEventAuditNativeQa.cs').read_text()
        shell=(TOOL/'qa/run_native_acceptance.sh').read_text()
        for token in ('HPR_ANIMATION_EVENT_REAL_NATIVE_PASS', 'NO_RECEIVER_METHOD',
                      'INVALID_RECEIVER_SIGNATURE','OVERLAPPING_EVENT_MARKERS',
                      'HprEventAuditFixtureReceiver', 'AnimatorController.CreateAnimatorControllerAtPath',
                      'AnimationUtility.SetAnimationEvents', 'PrefabUtility.SaveAsPrefabAsset',
                      'real_asset_hashes_and_manifest_unchanged=PASS'):
            self.assertIn(token,qa)
        for token in ('-createProject','-importPackage', 'verify_archive.py',
                      'HprEventAuditNativeQa.Run','HPR_ANIMATION_EVENT_NATIVE_ACCEPTANCE_PASS'):
            self.assertIn(token,shell)
        self.assertTrue((TOOL/'qa/HprEventAuditPreview.cs').is_file())
        self.assertIn('HPR_EVENT_UI_SCREENSHOT_RETAINED_BUT_BUTTON_INTERACTION_FAILED',
                      (TOOL/'qa/capture_native_preview.sh').read_text())
        self.assertIn('actual-event-audit-scrolled-details.png',
                      (TOOL/'qa/capture_native_preview.sh').read_text())
        self.assertNotIn('cp -a "$qa"',shell)
        self.assertIn('current_unity_event_info_receiver=PASS',qa)
        self.assertIn('current_unity_event_info_receiver=NOT_APPLICABLE_ON_THIS_EDITOR',qa)
        self.assertIn('new FileInfo(archive).Length > 4000',qa)
        verifier = (TOOL/'qa/verify_archive.py').read_text()
        self.assertIn('item.isdir()',verifier)
        self.assertIn('item.isfile()',verifier)
        self.assertIn('Unexpected link/non-file archive member',verifier)
        self.assertIn('Unexpected archive directory',verifier)
        self.assertIn('HiddenOtherName',qa)
        self.assertIn('folderReport',qa)
        self.assertIn('non_assets_scope_rejected=PASS',qa)
        self.assertNotIn("SAME_TIME_DUPLICATE_EVENT",qa)
        self.assertIn("current.failures == 3 && current.reviews == 2",qa)

    def test_private_rights_and_scope_disclosed(self):
        for name in ('README.md','LICENSE.md','ThirdPartyNotices.md'):
            self.assertTrue((ASSETS/name).is_file())
        readme=(ASSETS/'README.md').read_text()
        for term in ('NOT PUBLISHED','no runtime', 'legacy `Animation`',
                     'scene-only', 'INCOMPLETE','duplicate', 'Asset Store'):
            self.assertIn(term.lower(),readme.lower())

if __name__=='__main__': unittest.main()
