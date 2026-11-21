"""Unity release verification cannot silently pass zero tests or mutate shared AST."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/'unity/tools/release/HprAssetStoreToolsValidatorRunner.cs'
SCRIPT=ROOT/'unity/tools/release/run_official_asset_store_validator.sh'


def test_ast_native_runner_counts_results_and_rejects_zero_or_unreadable():
    code=RUNNER.read_text()
    for term in ('testsReturned: {tests.Length}', 'testsPassed: {passedCount}',
                 'testsWithIssues: {issueCount}', 'MISSING_TEST_RESULT',
                 'tests.Length == 0', 'passedCount != tests.Length',
                 'EditorApplication.Exit(1)', 'FileMode.CreateNew'):
        assert term in code
    assert 'object[] tests =' in code
    assert 'File.WriteAllLines(resultsPath, lines)' not in code


def test_wrapper_never_mutates_or_downloads_shared_asset_store_tools():
    s=SCRIPT.read_text()
    assert 'ensure_ast_tools() {' in s
    assert '! -f "$ast_package_dir/package.json"' in s
    helper = s.split('ensure_ast_tools() {', 1)[1].split('resolve_packages() {', 1)[0]
    assert 'git -C "$ast_repo" pull' not in helper
    assert 'git clone --' not in helper
    assert 'path.write_text(' not in helper
    assert 'git clone --' not in s
    assert 'git -C "$ast_repo" pull' not in s
    assert 'HPR_AST_PATHS=' in s
    assert 'HprAssetStoreToolsValidatorRunner.ValidateFromEnvironment' in s
