#!/usr/bin/env bash
# Official Unity Test Framework + InputTestFixture Play Mode acceptance.
# Private, non-shipping test. Requires a disposable Unity project with
# Input System 1.20.1, Test Framework and testable input package enabled.
set -euo pipefail

project=${HPR_INPUT_TEST_PROJECT:-/data/tmp/hpr_suite_input_unitytest_20261101}
output=${HPR_INPUT_TEST_OUTPUT:-/data/var/marketplace-account-setup/unity-suite-quality-research-20261101/official-input-fixture}
unity=${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.6.7f1/Editor/Unity}
test -f "$project/Assets/Tests/PlayMode/HPR.InputQA.PlayMode.Tests.asmdef" || {
    echo "Missing independent Play Mode test assembly" >&2
    exit 3
}
test -f "$project/Packages/manifest.json"
test -x "$unity"
mkdir -p "$output"
result="$output/input-testfixture-results.xml"
log="$output/input-testfixture.unity.log"
test ! -e "$result" || {
    echo "Refusing to overwrite an earlier QA receipt" >&2
    exit 4
}
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:1
export XAUTHORITY=/home/hans/.Xauthority XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
timeout 600 "$unity" -batchmode -nographics -runTests -testPlatform PlayMode     -assemblyNames HPR.InputQA.PlayMode.Tests     -projectPath "$project" -testResults "$result"     -logFile "$log" >/dev/null 2>&1
test -s "$result"
python3 - "$result" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
print("UNITY_INPUT_TEST_FIXTURE_RESULTS",root.attrib)
tests=list(root.iter("test-case"))
failed=[t.attrib for t in tests if t.get("result") not in ("Passed","Success")]
assert len(tests)>=3,(len(tests),"Not all independent input scenarios executed")
assert not failed,failed
print("UNITY_INPUT_TEST_FIXTURE_PASS",len(tests))
PY
