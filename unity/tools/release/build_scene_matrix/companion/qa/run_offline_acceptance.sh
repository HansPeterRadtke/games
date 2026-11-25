#!/usr/bin/env bash
# Independent original-source compilation and actual process-level acceptance.
# No Unity invocation or network package retrieval; only isolated private output.
set -euo pipefail
ulimit -c 0
out=${1:?new private output directory required}
[[ "$out" = /data/var/marketplace-account-setup/* && ! -e "$out" ]]
here=$(cd "$(dirname "$0")" && pwd)
product=$(cd "$here/.." && pwd)
core=$(cd "$product/../Assets/HPRBuildSceneMatrix/Editor" && pwd)
mkdir -p "$out/build" "$out/fixtures-source"
cp "$product"/{HprSceneGate.csproj,Program.cs,SavedUnitySceneLists.cs,NuGet.Config} "$out/build/"
cp "$here"/fixtures/{Fixtures.csproj,Program.cs} "$out/fixtures-source/"
cp "$product/NuGet.Config" "$out/fixtures-source/"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
export DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true
export DOTNET_CLI_HOME="$out/dotnet-home" NUGET_PACKAGES="$out/nuget"
dotnet --list-sdks
dotnet --list-runtimes
build() {
    local project=$1
    dotnet restore "$project" --configfile "$(dirname "$project")/NuGet.Config" -p:HprSourceRoot="$core" -p:NuGetAudit=false
    dotnet build "$project" --no-restore -c Release -m:1 -p:HprSourceRoot="$core" -p:UseSharedCompilation=false
}
build "$out/build/HprSceneGate.csproj"
build "$out/fixtures-source/Fixtures.csproj"
dotnet "$out/fixtures-source/bin/Release/net10.0/Fixtures.dll" "$out/fixtures"
python3 "$here/test_command.py" "$out/build/bin/Release/net10.0/HprSceneGate.dll" "$out/fixtures"
sha256sum "$core/HprSceneMatrixCore.cs" "$core/HprSceneBaseline.cs" "$product/Program.cs" "$product/SavedUnitySceneLists.cs"
