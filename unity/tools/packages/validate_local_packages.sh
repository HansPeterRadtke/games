#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: validate_local_packages.sh <com.hpr.package> [more packages...]" >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
packages_root="$repo_root/unity/packages"
unity_bin="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
temp_root="${TEMP_ROOT:-/data/tmp/hpr_package_validation}"
project_name="${PROJECT_NAME:-}"
log_dir="${LOG_DIR:-$repo_root/doc/logs/package_validation}"
run_tests="${RUN_TESTS:-0}"
mkdir -p "$temp_root" "$log_dir"

if [[ ! -x "$unity_bin" ]]; then
  echo "Unity editor not found: $unity_bin" >&2
  exit 1
fi

requested=("$@")
if [[ -z "$project_name" ]]; then
  sanitized_packages=$(printf '%s_' "${requested[@]}" | tr -c '[:alnum:]_-' '_')
  project_name="clean_package_project_${sanitized_packages}_$$"
fi
project_path="$temp_root/$project_name"

ensure_editmode_runner() {
  mkdir -p "$project_path/Assets/Editor"
  cat >"$project_path/Assets/Editor/HprPackageEditModeTestRunner.cs" <<'EOF'
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Xml.Linq;
using Stopwatch = System.Diagnostics.Stopwatch;
using UnityEditor;
using UnityEngine;

public static class HprPackageEditModeTestRunner
{
    private const string TestAttributeName = "NUnit.Framework.TestAttribute";
    private const string SetUpAttributeName = "NUnit.Framework.SetUpAttribute";
    private const string TearDownAttributeName = "NUnit.Framework.TearDownAttribute";
    private const string OneTimeSetUpAttributeName = "NUnit.Framework.OneTimeSetUpAttribute";
    private const string OneTimeTearDownAttributeName = "NUnit.Framework.OneTimeTearDownAttribute";

    public static void Run()
    {
        var resultsPath = Environment.GetEnvironmentVariable("HPR_TEST_RESULTS");
        if (string.IsNullOrWhiteSpace(resultsPath))
        {
            UnityEngine.Debug.LogError("HPR_TEST_RESULTS is not set.");
            EditorApplication.Exit(1);
            return;
        }

        Directory.CreateDirectory(Path.GetDirectoryName(resultsPath) ?? ".");

        var assemblies = AppDomain.CurrentDomain
            .GetAssemblies()
            .Where(assembly => !assembly.IsDynamic)
            .Where(assembly =>
            {
                var name = assembly.GetName().Name ?? string.Empty;
                return name.StartsWith("HPR.", StringComparison.Ordinal) && name.Contains(".Tests.", StringComparison.Ordinal);
            })
            .OrderBy(assembly => assembly.GetName().Name, StringComparer.Ordinal)
            .ToArray();

        var results = new List<TestCaseResult>();

        foreach (var assembly in assemblies)
        {
            foreach (var type in assembly.GetTypes().Where(CanContainTests).OrderBy(type => type.FullName, StringComparer.Ordinal))
            {
                RunFixture(type, results);
            }
        }

        var total = results.Count;
        var failed = results.Count(result => !result.Passed);
        var passed = total - failed;
        var root = new XElement("test-run",
            new XAttribute("total", total),
            new XAttribute("passed", passed),
            new XAttribute("failed", failed),
            new XAttribute("result", failed == 0 && total > 0 ? "Passed" : "Failed"));

        foreach (var group in results.GroupBy(result => result.AssemblyName).OrderBy(group => group.Key, StringComparer.Ordinal))
        {
            var suite = new XElement("test-suite", new XAttribute("name", group.Key));
            foreach (var result in group)
            {
                var testCase = new XElement("test-case",
                    new XAttribute("name", result.Name),
                    new XAttribute("result", result.Passed ? "Passed" : "Failed"),
                    new XAttribute("duration", result.DurationSeconds.ToString("0.000", System.Globalization.CultureInfo.InvariantCulture)));
                if (!result.Passed && !string.IsNullOrEmpty(result.Message))
                {
                    testCase.Add(new XElement("failure", new XElement("message", result.Message)));
                }
                suite.Add(testCase);
            }
            root.Add(suite);
        }

        var document = new XDocument(new XDeclaration("1.0", "utf-8", "yes"), root);
        File.WriteAllText(resultsPath, document.ToString());

        if (total <= 0)
        {
            UnityEngine.Debug.LogError("No edit mode tests were discovered in HPR.*.Tests.* assemblies.");
            EditorApplication.Exit(1);
            return;
        }

        if (failed > 0)
        {
            UnityEngine.Debug.LogError($"{failed} edit mode tests failed out of {total}.");
            EditorApplication.Exit(1);
            return;
        }

        UnityEngine.Debug.Log($"All {total} edit mode tests passed. Results: {resultsPath}");
        EditorApplication.Exit(0);
    }

    private static void RunFixture(Type type, List<TestCaseResult> results)
    {
        var allMethods = type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static);
        var tests = allMethods.Where(method => HasAttribute(method, TestAttributeName)).OrderBy(method => method.Name, StringComparer.Ordinal).ToArray();
        if (tests.Length == 0)
        {
            return;
        }

        var setup = allMethods.Where(method => HasAttribute(method, SetUpAttributeName)).OrderBy(method => method.Name, StringComparer.Ordinal).ToArray();
        var tearDown = allMethods.Where(method => HasAttribute(method, TearDownAttributeName)).OrderBy(method => method.Name, StringComparer.Ordinal).ToArray();
        var oneTimeSetUp = allMethods.Where(method => HasAttribute(method, OneTimeSetUpAttributeName)).OrderBy(method => method.Name, StringComparer.Ordinal).ToArray();
        var oneTimeTearDown = allMethods.Where(method => HasAttribute(method, OneTimeTearDownAttributeName)).OrderBy(method => method.Name, StringComparer.Ordinal).ToArray();

        object instance = null;
        if (tests.Any(method => !method.IsStatic) || setup.Any(method => !method.IsStatic) || tearDown.Any(method => !method.IsStatic) || oneTimeSetUp.Any(method => !method.IsStatic) || oneTimeTearDown.Any(method => !method.IsStatic))
        {
            instance = Activator.CreateInstance(type);
        }

        try
        {
            InvokeMethods(oneTimeSetUp, instance);
            foreach (var test in tests)
            {
                var stopwatch = Stopwatch.StartNew();
                try
                {
                    InvokeMethods(setup, instance);
                    test.Invoke(instance, Array.Empty<object>());
                    results.Add(new TestCaseResult(type.Assembly.GetName().Name ?? type.Assembly.FullName ?? "UnknownAssembly", $"{type.FullName}.{test.Name}", true, stopwatch.Elapsed.TotalSeconds, null));
                }
                catch (Exception ex)
                {
                    var root = Unwrap(ex);
                    results.Add(new TestCaseResult(type.Assembly.GetName().Name ?? type.Assembly.FullName ?? "UnknownAssembly", $"{type.FullName}.{test.Name}", false, stopwatch.Elapsed.TotalSeconds, root.ToString()));
                }
                finally
                {
                    try
                    {
                        InvokeMethods(tearDown, instance);
                    }
                    catch (Exception tearDownException)
                    {
                        var root = Unwrap(tearDownException);
                        results.Add(new TestCaseResult(type.Assembly.GetName().Name ?? type.Assembly.FullName ?? "UnknownAssembly", $"{type.FullName}.{test.Name}.TearDown", false, 0d, root.ToString()));
                    }
                }
            }
        }
        catch (Exception fixtureException)
        {
            var root = Unwrap(fixtureException);
            results.Add(new TestCaseResult(type.Assembly.GetName().Name ?? type.Assembly.FullName ?? "UnknownAssembly", $"{type.FullName}.Fixture", false, 0d, root.ToString()));
        }
        finally
        {
            try
            {
                InvokeMethods(oneTimeTearDown, instance);
            }
            catch (Exception oneTimeTearDownException)
            {
                var root = Unwrap(oneTimeTearDownException);
                results.Add(new TestCaseResult(type.Assembly.GetName().Name ?? type.Assembly.FullName ?? "UnknownAssembly", $"{type.FullName}.OneTimeTearDown", false, 0d, root.ToString()));
            }
        }
    }

    private static void InvokeMethods(IEnumerable<MethodInfo> methods, object instance)
    {
        foreach (var method in methods)
        {
            method.Invoke(instance, Array.Empty<object>());
        }
    }

    private static bool CanContainTests(Type type)
    {
        return type.IsClass && !type.IsAbstract && !type.IsGenericTypeDefinition;
    }

    private static bool HasAttribute(MethodInfo method, string attributeFullName)
    {
        return method.GetCustomAttributes(false).Any(attribute => string.Equals(attribute.GetType().FullName, attributeFullName, StringComparison.Ordinal));
    }

    private static Exception Unwrap(Exception exception)
    {
        while (exception is TargetInvocationException tie && tie.InnerException != null)
        {
            exception = tie.InnerException;
        }
        return exception;
    }

    private sealed class TestCaseResult
    {
        public TestCaseResult(string assemblyName, string name, bool passed, double durationSeconds, string message)
        {
            AssemblyName = assemblyName;
            Name = name;
            Passed = passed;
            DurationSeconds = durationSeconds;
            Message = message;
        }

        public string AssemblyName { get; }
        public string Name { get; }
        public bool Passed { get; }
        public double DurationSeconds { get; }
        public string Message { get; }
    }
}
EOF
}

package_list=$(python3 - <<'PY' "$packages_root" "${requested[@]}"
import json, sys
from pathlib import Path

packages_root = Path(sys.argv[1])
requested = sys.argv[2:]
resolved = []
seen = set()

def visit(name):
    if name in seen:
        return
    seen.add(name)
    pkg_dir = packages_root / name
    if not pkg_dir.exists():
        raise SystemExit(f"missing package: {name}")
    manifest = json.loads((pkg_dir / "package.json").read_text())
    for dep_name, dep_value in manifest.get("dependencies", {}).items():
        if dep_name.startswith("com.hpr."):
            visit(dep_name)
    resolved.append(name)

for name in requested:
    visit(name)

print("\n".join(resolved))
PY
)

mapfile -t resolved_packages <<<"$package_list"

if [[ ! -d "$project_path/Assets" ]]; then
  "$unity_bin" -batchmode -nographics -quit -createProject "$project_path" -logFile -
fi

python3 - <<'PY' "$project_path/Packages/manifest.json" "$packages_root" "$run_tests" "${resolved_packages[@]}"
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
packages_root = pathlib.Path(sys.argv[2])
run_tests = sys.argv[3] == "1"
resolved_packages = sys.argv[4:]
obj = json.loads(p.read_text(encoding='utf-8'))
deps = obj.setdefault('dependencies', {})
deps['com.unity.ugui'] = '2.0.0'
for name in list(deps):
    if name.startswith('com.hpr.'):
        deps.pop(name, None)
needs_test_framework = any((packages_root / name / 'Tests').exists() for name in resolved_packages)
if run_tests or needs_test_framework:
    deps['com.unity.test-framework'] = '1.4.6'
    obj['testables'] = sorted(set(resolved_packages))
else:
    deps.pop('com.unity.test-framework', None)
    obj.pop('testables', None)
p.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
PY

python3 - <<'PY' "$project_path/Packages" "$packages_root" "${resolved_packages[@]}"
from pathlib import Path
import shutil
import sys

packages_dir = Path(sys.argv[1])
packages_root = Path(sys.argv[2])
package_names = sys.argv[3:]

for target in packages_dir.glob("com.hpr.*"):
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

for name in package_names:
    source = packages_root / name
    target = packages_dir / name
    shutil.copytree(source, target)
PY

if [[ "$run_tests" == "1" ]]; then
  ensure_editmode_runner
fi

log_file="$log_dir/$(date +%Y%m%d_%H%M%S)_$(printf '%s_' "${requested[@]}" | tr '/.' '__').log"
execute_method="${EXECUTE_METHOD:-}"
execute_log_file=""
tests_log_file=""
test_results_file=""

run_editor() {
  "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -logFile "$log_file"
}

run_execute_method() {
  execute_log_file="${log_dir}/$(date +%Y%m%d_%H%M%S)_$(printf '%s_' "${requested[@]}" | tr '/.' '__')_${execute_method##*.}.log"
  "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -executeMethod "$execute_method" -logFile "$execute_log_file"
}

run_editmode_tests() {
  local test_stamp
  test_stamp="$(date +%Y%m%d_%H%M%S)"
  tests_log_file="${log_dir}/${test_stamp}_$(printf '%s_' "${requested[@]}" | tr '/.' '__')_EditModeTests.log"
  test_results_file="${log_dir}/${test_stamp}_$(printf '%s_' "${requested[@]}" | tr '/.' '__')_EditModeTests.xml"
  HPR_TEST_RESULTS="$test_results_file" "$unity_bin" -batchmode -nographics -quit -projectPath "$project_path" -executeMethod HprPackageEditModeTestRunner.Run -logFile "$tests_log_file"
}

if [[ "$(id -un)" == "hans" ]]; then
  run_editor
  if [[ -n "$execute_method" ]]; then
    run_execute_method
  fi
else
  exec runuser -u hans -- env \
    HOME=/home/hans USER=hans LOGNAME=hans \
    DISPLAY="${DISPLAY:-:1}" \
    XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
    DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
    UNITY_BIN="$unity_bin" TEMP_ROOT="$temp_root" PROJECT_NAME="$project_name" LOG_DIR="$log_dir" EXECUTE_METHOD="$execute_method" RUN_TESTS="$run_tests" \
    bash "$0" "$@"
fi

if rg -n "error CS|: error|Aborting batchmode|NullReferenceException|Exception:" "$log_file" >/dev/null 2>&1; then
  echo "Validation failed. See log: $log_file" >&2
  rg -n "error CS|: error|Aborting batchmode|NullReferenceException|Exception:" "$log_file" >&2 || true
  exit 1
fi

if [[ -n "$execute_method" && -n "$execute_log_file" ]]; then
  if rg -n "error CS|: error|Aborting batchmode|NullReferenceException|Exception:" "$execute_log_file" >/dev/null 2>&1; then
    echo "Validation failed during execute method. See log: $execute_log_file" >&2
    rg -n "error CS|: error|Aborting batchmode|NullReferenceException|Exception:" "$execute_log_file" >&2 || true
    exit 1
  fi
fi

if [[ "$run_tests" == "1" ]]; then
  run_editmode_tests
  if rg -n "error CS|: error|Aborting batchmode|NullReferenceException|Exception:" "$tests_log_file" >/dev/null 2>&1; then
    echo "Validation failed during edit mode tests. See log: $tests_log_file" >&2
    rg -n "error CS|: error|Aborting batchmode|NullReferenceException|Exception:" "$tests_log_file" >&2 || true
    exit 1
  fi
  python3 - <<'PY' "$test_results_file"
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1]
root = ET.parse(path).getroot()
total = int(root.attrib.get("total", "0"))
result = root.attrib.get("result", "")
if total <= 0:
    raise SystemExit("edit mode test run produced zero tests")
if result != "Passed":
    raise SystemExit(f"edit mode tests did not pass: {result}")
PY
fi

warning_pattern='^(Packages|Assets)/com\.hpr\.[^:]+: warning '
for candidate in "$log_file" "$execute_log_file" "$tests_log_file"; do
  if [[ -n "$candidate" && -f "$candidate" ]] && rg -n "$warning_pattern" "$candidate" >/dev/null 2>&1; then
    echo "Validation failed due to package-originated warnings. See log: $candidate" >&2
    rg -n "$warning_pattern" "$candidate" >&2 || true
    exit 1
  fi
done

echo "Validated packages:"
printf ' - %s\n' "${resolved_packages[@]}"
echo "Log: $log_file"
if [[ -n "$execute_method" && -n "$execute_log_file" ]]; then
  echo "Execute log: $execute_log_file"
fi
if [[ "$run_tests" == "1" ]]; then
  echo "Tests log: $tests_log_file"
  echo "Test results: $test_results_file"
fi
