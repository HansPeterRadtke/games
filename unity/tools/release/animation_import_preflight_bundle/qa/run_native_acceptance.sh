#!/usr/bin/env bash
# Genuine first-party 3-root Unity Editor author/export, independent buyer
# archive import and two-module sample-only and real private customer checks.
set -euo pipefail
version=${1:?installed Unity version}
label=${2:?fresh unique label}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
[[ "$label" =~ ^[a-z0-9_-]{2,30}$ ]] || exit 2
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
base=/data/var/marketplace-account-setup/unity-20261122-wave55
root=$base/combined-animation-native-${version//./-}-$label
pkg=$root/HPR_Combined_Animation_Import_Preflight_Candidate.unitypackage
draft=$(cd "$(dirname "$0")/.." && pwd)
repo=$(dirname "$draft")
fixture=$repo/fbx_source_take_visibility/Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx
[[ -x "$unity" && -s "$fixture" && ! -e "$root" ]] || { echo 'Missing Unity or repeated exact QA effect' >&2;exit 3; }
mkdir -p "$root"
author="$root/author-project"
buyer="$root/independent-buyer-project"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "REAL_UNITY_COMBINED_ANIMATION $version $stage"
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$root/$stage.unity.log" > "$root/$stage.stdout" 2>&1 || {
  grep -E -C2 'error CS|Exception|HPR_COMBINED' "$root/$stage.unity.log" | tail -35 >&2 || true
  exit 5
 }
}
install_vendor(){
 project=$1
 for pair in 'fbx_clip_identity_audit HPRFbxClipIdentity' 'fbx_source_take_visibility HPRFbxSourceTakes'; do
  read -r product vendor <<< "$pair"
  cp -a "$repo/$product/Assets/$vendor" "$project/Assets/"
  cp -a "$repo/$product/Assets/$vendor.meta" "$project/Assets/"
 done
 cp -a "$draft/Assets/HPRAnimationImportPreflight" "$project/Assets/"
 cp -a "$draft/Assets/HPRAnimationImportPreflight.meta" "$project/Assets/"
}
qa(){ target=$1;mkdir -p "$target/Assets/Editor";cp "$draft/qa/HprCombinedAnimationNativeQa.cs" "$target/Assets/Editor/"; }
run create-author -createProject "$author"
install_vendor "$author"
qa "$author"
cp "$draft/qa/HprCombinedAnimationExporter.cs" "$author/Assets/Editor/"
export HPR_COMBINED_ANIM_QA_DIR="$root/author-vendor-only-QA"
mkdir -p "$HPR_COMBINED_ANIM_QA_DIR"
run original-vendor-only-author -projectPath "$author" -executeMethod HprCombinedAnimationNativeQa.SamplesOnly
grep -q HPR_COMBINED_ANIMATION_VENDOR_ONLY_NATIVE_PASS "$root/original-vendor-only-author.unity.log"
export HPR_COMBINED_ANIM_PACKAGE_OUT="$pkg"
run author-export -projectPath "$author" -executeMethod HprCombinedAnimationExporter.Run
grep -q HPR_COMBINED_ANIMATION_NATIVE_EXPORT_PASS "$root/author-export.unity.log"
python3 "$draft/qa/verify_combined_archive.py" --archive "$pkg" > "$root/strict-original-first-party-package.json"
mkdir -p "$author/Assets/HPRCombinedPrivateCustomer"
cp -- "$fixture" "$author/Assets/HPRCombinedPrivateCustomer/OriginalTwoTake.fbx"
export HPR_COMBINED_ANIM_QA_DIR="$root/author-customer-QA"
mkdir -p "$HPR_COMBINED_ANIM_QA_DIR"
run author-real-customer-healthy -projectPath "$author" -executeMethod HprCombinedAnimationNativeQa.CustomerUnmodified
grep -q HPR_COMBINED_ANIMATION_CUSTOMER_HEALTHY_NATIVE_PASS "$root/author-real-customer-healthy.unity.log"
run author-real-customer-warning -projectPath "$author" -executeMethod HprCombinedAnimationNativeQa.CustomerOneTakeMissing
grep -q HPR_COMBINED_ANIMATION_CUSTOMER_WARNING_NATIVE_PASS "$root/author-real-customer-warning.unity.log"
run create-buyer -createProject "$buyer"
run buyer-import-exact-archive -projectPath "$buyer" -importPackage "$pkg"
qa "$buyer"
export HPR_COMBINED_ANIM_QA_DIR="$root/buyer-vendor-only-QA"
mkdir -p "$HPR_COMBINED_ANIM_QA_DIR"
run buyer-original-vendor-only -projectPath "$buyer" -executeMethod HprCombinedAnimationNativeQa.SamplesOnly
grep -q HPR_COMBINED_ANIMATION_VENDOR_ONLY_NATIVE_PASS "$root/buyer-original-vendor-only.unity.log"
mkdir -p "$buyer/Assets/HPRCombinedPrivateCustomer"
cp -- "$fixture" "$buyer/Assets/HPRCombinedPrivateCustomer/OriginalTwoTake.fbx"
export HPR_COMBINED_ANIM_QA_DIR="$root/buyer-customer-QA"
mkdir -p "$HPR_COMBINED_ANIM_QA_DIR"
run buyer-real-customer-healthy -projectPath "$buyer" -executeMethod HprCombinedAnimationNativeQa.CustomerUnmodified
grep -q HPR_COMBINED_ANIMATION_CUSTOMER_HEALTHY_NATIVE_PASS "$root/buyer-real-customer-healthy.unity.log"
run buyer-real-customer-warning -projectPath "$buyer" -executeMethod HprCombinedAnimationNativeQa.CustomerOneTakeMissing
grep -q HPR_COMBINED_ANIMATION_CUSTOMER_WARNING_NATIVE_PASS "$root/buyer-real-customer-warning.unity.log"
python3 - "$root" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);v=json.loads((p/'strict-original-first-party-package.json').read_text())
assert v['result']=='PASS' and v['exact_source_meta_and_guid_preserved']
for group,name in [('vendor-only-QA','original-vendor-only-receipt.txt'),('vendor-only-QA','original-vendor-only-both-scans.json'),('customer-QA','real-customer-original-receipt.txt'),('customer-QA','combined-original-customer-warning.txt'),('customer-QA','combined-original-customer-warning.json')]:
 a=(p/('author-'+group)/name).read_bytes();b=(p/('buyer-'+group)/name).read_bytes()
 assert a==b,(group,name)
assert 'combined_vendor_examples_excluded=PASS' in (p/'buyer-vendor-only-QA/original-vendor-only-receipt.txt').read_text()
assert 'real_combined_customer_warning_detected=PASS' in (p/'buyer-customer-QA/combined-original-customer-warning.txt').read_text()
print('GENUINE_ORIGINAL_THREE_ROOT_UNITY_AUTHOR_AND_INDEPENDENT_BUYER=PASS')
print('EXACT_UNITY_ASSETS',v['actual_original_unity_asset_paths'])
PY
