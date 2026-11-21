"""Guard native Unity test cleanup after the real 6.6 Search/Mono crash."""
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/'unity/tools/release/gameplay_suite/qa/HprSuiteFastPlaymodeValidator.cs'


def test_wait_for_unity_asset_database_before_batch_exit():
    text=PATH.read_text()
    assert 'HPR_SUITE_FAST_PLAY_EDITOR_DRAIN_STARTED' in text
    assert 'EditorApplication.isCompiling || EditorApplication.isUpdating' in text
    assert 'EditorApplication.timeSinceStartup + 8.0' in text
    assert 'if (++frames < 120 || EditorApplication.timeSinceStartup < exitReadyAfter)' in text
    assert 'HPR_SUITE_FAST_PLAY_EDITOR_IDLE_EXIT_REQUESTED' in text
    assert 'RestoreOriginalEditorSettings();' in text
    assert 'EditorApplication.delayCall += () => EditorApplication.Exit(0)' in text
