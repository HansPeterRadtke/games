#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/HeadlessPhase1Validation"

dotnet run --project "${PROJECT_DIR}/HeadlessPhase1Validation.csproj" --configuration Release
