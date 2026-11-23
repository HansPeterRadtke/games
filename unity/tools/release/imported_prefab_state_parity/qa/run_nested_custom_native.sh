#!/usr/bin/env bash
# Author one genuinely original nested prefab + variant + serialized custom script
# once in disposable Unity2022, then independently import and test in both Editors.
set -euo pipefail
label=${1:?fresh project label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]] || exit 2
base=/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62
work="$base/$label"
qa=$(cd "$(dirname "$0")" && pwd)
source="$qa/../Assets/HPRImportedPrefabParity"
source_meta="$qa/../Assets/HPRImportedPrefabParity.meta"
unity22=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
unity6=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity22" && -x "$unity6" && -d "$source" && -s "$source_meta" && ! -e "$work" ]] || {
 echo 'Original source missing or repeated test effect refused' >&2;exit 3;
}
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ local version=$1 stage=$2;shift 2;echo "NESTED_CUSTOM_REAL_UNITY_STAGE $version $stage";
 local editor="$unity22";[[ "$version" == '6000.6.8f1' ]] && editor="$unity6";
 timeout 490 "$editor" -batchmode -nographics -quit "$@" -logFile "$work/${version//./-}-$stage.unity.log" \
 >"$work/${version//./-}-$stage.stdout" 2>&1 || {
  grep -E 'HPR_NESTED|HPR_PREFAB|error CS[0-9]|Exception' "$work/${version//./-}-$stage.unity.log" |tail -26 >&2 || true;
  exit 5;
 }
}
author="$work/author-original-fixture-project"
run 2022.3.22f1 create-author -createProject "$author"
mkdir -p "$author/Assets/HPRNestedCustomAcceptance/Scripts" "$author/Assets/HPRNestedCustomAcceptance/Prefabs" "$author/Assets/Editor"
cp "$qa/HprNestedCustomSample.cs" "$author/Assets/HPRNestedCustomAcceptance/Scripts/"
cp "$qa/HprNestedCustomFixtureAuthor.cs" "$author/Assets/Editor/"
cp "$qa/HprPrefabParityExporter.cs" "$author/Assets/Editor/"
# Private one-run fixture directory guard; leave the canonical QA runner unchanged.
python3 - "$author/Assets/Editor/HprPrefabParityExporter.cs" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
a='unity-prefab-dependency-20261123-wave61'
b='unity-nested-custom-20261123-wave62'
assert s.count(a)==1
p.write_text(s.replace(a,b))
PY
cp -a "$source" "$source_meta" "$author/Assets/"
export HPR_NESTED_FIXTURE_PACKAGE="$work/HPR_Nested_Real_Prefab_Variant_Test_Original.unitypackage"
run 2022.3.22f1 author-fixture -projectPath "$author" -executeMethod HprNestedCustomFixtureAuthor.Run
grep -q HPR_NESTED_CUSTOM_FIXTURE_AUTHOR_PASS "$work/2022-3-22f1-author-fixture.unity.log"
python3 - "$HPR_NESTED_FIXTURE_PACKAGE" <<'PYFIXTURE'
from pathlib import Path
import sys,tarfile
path=Path(sys.argv[1])
assert path.is_file() and path.stat().st_size>500
with tarfile.open(path,'r:gz') as archive:
    paths={archive.extractfile(item).read().decode('utf-8').strip()
           for item in archive.getmembers() if item.name.endswith('/pathname')}
root='Assets/HPRNestedCustomAcceptance/'
expected={root+'Prefabs/OriginalMachine.prefab',
          root+'Prefabs/OriginalMachineVariant.prefab',
          root+'Prefabs/OriginalMachineAssembly.prefab',
          root+'Scripts/HprNestedCustomSample.cs'}
assert expected.issubset(paths),(expected-paths)
assert len(paths)==7,(len(paths),sorted(paths))
print('HPR_NESTED_CUSTOM_ACTUAL_UNITYPACKAGE_ARCHIVE_PASS original_unique_assets',len(paths))
PYFIXTURE
export HPR_PREFAB_PACKAGE_OUT="$work/HPR_Imported_Prefab_State_Parity_Nested_Original.unitypackage"
run 2022.3.22f1 product-export -projectPath "$author" -executeMethod HprPrefabParityExporter.Run
grep -q HPR_PREFAB_PARITY_ORIGINAL_PACKAGE_EXPORT_PASS "$work/2022-3-22f1-product-export.unity.log"
python3 "$qa/verify_original_archive.py" "$HPR_PREFAB_PACKAGE_OUT" >"$work/product-original-exact-archive-proof.json"
for version in 2022.3.22f1 6000.6.8f1;do
 buyer="$work/${version//./-}-independent-buyer"
 run "$version" create-buyer -createProject "$buyer"
 run "$version" import-original-product -projectPath "$buyer" -importPackage "$HPR_PREFAB_PACKAGE_OUT"
 run "$version" import-original-nested-fixtures -projectPath "$buyer" -importPackage "$HPR_NESTED_FIXTURE_PACKAGE"
 mkdir -p "$buyer/Assets/Editor"
 cp "$qa/HprNestedCustomBuyerQa.cs" "$buyer/Assets/Editor/"
 export HPR_NESTED_BUYER_RECEIPT="$work/${version//./-}-nested-custom-native-receipt.json"
 run "$version" buyer-custom-script-acceptance -projectPath "$buyer" -executeMethod HprNestedCustomBuyerQa.Run
 grep -q HPR_NESTED_CUSTOM_NATIVE_BUYER_PASS "$work/${version//./-}-buyer-custom-script-acceptance.unity.log"
 python3 "$qa/verify_native_prefab_receipt.py" "$buyer" "$HPR_NESTED_BUYER_RECEIPT" \
 >"$work/${version//./-}-exact-original-nested-rehash.json"
 done
python3 "$qa/compare_native_receipts.py" \
 "$work/2022-3-22f1-nested-custom-native-receipt.json" \
 "$work/6000-6-8f1-nested-custom-native-receipt.json" \
 --output "$work/real-two-editors-nested-custom-comparison.json" || rc=$?
python3 - "$work" <<'PY'
import json,sys
from pathlib import Path
w=Path(sys.argv[1]);r=json.loads((w/'real-two-editors-nested-custom-comparison.json').read_text())
assert r['status']=='COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS',r
assert r['unsupported_component_types']>=6
assert not r['dependency_differences'] and not r['source_differences'] and not r['unverified_dependency_paths']
assert not r['changed_keys'] and not r['removed_keys'] and not r['added_keys']
print('HPR_NESTED_CUSTOM_REAL_TWO_EDITORS_PASS','untested_custom_occurrences',r['unsupported_component_types'])
PY
