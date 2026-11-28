#!/usr/bin/env bash
set -euo pipefail
out=${1:?New private output directory required}
[[ "$out" = /data/var/marketplace-account-setup/* && ! -e "$out" ]] || { echo 'New exact private output path required'; exit 3; }
qa=$(cd -- "$(dirname "$0")" && pwd)
assets=$(cd "$qa/../Assets" && pwd)
unity=${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity}
[[ -x "$unity" && -f "$assets/HPRAnimationEventAudit/Editor/HprAnimationEventAudit.cs" ]]
mkdir -p "$out";chmod 0700 "$out"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=${DISPLAY:-:1} XAUTHORITY=${XAUTHORITY:-/home/hans/.Xauthority}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000} DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus} LP_NUM_THREADS=2
export HPR_EVENT_AUDIT_ARCHIVE="$out/HPR_Animation_Event_Receiver_Audit_PRIVATE.unitypackage" HPR_EVENT_AUDIT_RECEIPT="$out/real-native-event-receipt.txt"
run(){
 stage=$1;shift;echo "HPR_EVENT_STAGE $stage"
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
   grep -E 'error CS[0-9]|Exception|HPR_ANIMATION_EVENT' "$out/$stage.unity.log" | tail -24 >&2 || true
   exit 4
 }
}
run author-create -createProject "$out/author"
cp -a "$assets/HPRAnimationEventAudit" "$assets/HPRAnimationEventAudit.meta" "$out/author/Assets/"
mkdir -p "$out/author/Assets/Editor"
cp "$qa/HprEventAuditNativeQa.cs" "$out/author/Assets/Editor/"
cp "$qa/HprEventAuditFixtureReceiver.cs" "$out/author/Assets/"
run author-export -projectPath "$out/author" -executeMethod HprEventAuditNativeQa.Export
grep -q HPR_ANIMATION_EVENT_EXPORT_PASS "$out/author-export.unity.log"
python3 "$qa/verify_archive.py" "$HPR_EVENT_AUDIT_ARCHIVE" "$assets" > "$out/archive-identity.json"
run buyer-create -createProject "$out/buyer"
run buyer-import -projectPath "$out/buyer" -importPackage "$HPR_EVENT_AUDIT_ARCHIVE"
mkdir -p "$out/buyer/Assets/Editor"
cp "$qa/HprEventAuditNativeQa.cs" "$out/buyer/Assets/Editor/"
cp "$qa/HprEventAuditFixtureReceiver.cs" "$out/buyer/Assets/"
run buyer-native -projectPath "$out/buyer" -executeMethod HprEventAuditNativeQa.Run
grep -q HPR_ANIMATION_EVENT_REAL_NATIVE_PASS "$HPR_EVENT_AUDIT_RECEIPT"
cat "$HPR_EVENT_AUDIT_RECEIPT"
echo HPR_ANIMATION_EVENT_NATIVE_ACCEPTANCE_PASS
