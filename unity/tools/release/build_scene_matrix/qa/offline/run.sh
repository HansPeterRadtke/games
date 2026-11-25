#!/usr/bin/env bash
# No Unity invocation, engine assemblies, network package sources, or native acceptance claim.
set -euo pipefail
ulimit -c 0
out=${1:?new isolated output directory}
prior_csv=${2:-}
[[ "$out" = /data/var/marketplace-account-setup/* && ! -e "$out" ]]
here=$(cd "$(dirname "$0")" && pwd)
src=$(cd "$here/../../Assets/HPRBuildSceneMatrix/Editor" && pwd)
mkdir -p "$out/harness"
cp -a "$here"/core "$here"/tests "$here"/NuGet.Config "$out/harness/"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
export DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true
export DOTNET_CLI_HOME="$out/dotnet-home" NUGET_PACKAGES="$out/nuget"
dotnet restore "$out/harness/tests/HprSceneTests.csproj" --configfile "$out/harness/NuGet.Config" -p:HprSourceRoot="$src" -p:NuGetAudit=false
dotnet build "$out/harness/tests/HprSceneTests.csproj" --no-restore -c Release -m:1 -p:HprSourceRoot="$src" -p:UseSharedCompilation=false
dotnet "$out/harness/tests/bin/Release/net10.0/HprSceneTests.dll" "$out/test-data" "$src/HprBuildSceneMatrix.cs" "$prior_csv" "$here/../HprBuildSceneMatrixQa.cs"
sha256sum "$src"/HprSceneMatrixCore.cs "$src"/HprSceneBaseline.cs "$src"/HprBuildSceneMatrix.cs
