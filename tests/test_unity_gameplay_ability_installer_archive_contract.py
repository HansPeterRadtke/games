"""Regression for a real Unity buyer upgrade failure from an old mismatched suite archive."""
from pathlib import Path
import importlib.util
import pytest

ROOT=Path(__file__).resolve().parents[1]
VALIDATOR=ROOT/'unity/tools/release/gameplay_suite/validate_release.py'
SOURCE=ROOT/'unity/tools/release/gameplay_suite'
PACKAGES=ROOT/'unity/packages'
spec=importlib.util.spec_from_file_location('hpr_release_validator_ability', VALIDATOR)
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def actual_payloads():
    return {
        v.ROOT+'Editor/HprSelectedAbilityInstaller.cs':
            (SOURCE/'buyer_source_assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs').read_bytes(),
        v.ROOT+'Modules/com.hpr.abilities/Runtime/AbilityData.cs':
            (PACKAGES/'com.hpr.abilities/Runtime/AbilityData.cs').read_bytes(),
        v.ROOT+'Integration/HprSuiteIntegration.cs':(SOURCE/'HprSuiteIntegration.cs').read_bytes(),
    }


def test_current_buyer_payload_contract_is_present():
    v.validate_ability_installer_api_contract(actual_payloads())


def test_archive_missing_selected_ability_installer_is_rejected():
    payloads=actual_payloads()
    payloads.pop(v.ROOT+'Editor/HprSelectedAbilityInstaller.cs')
    with pytest.raises(ValueError,match='missing ability installer/runtime contract'):
        v.validate_ability_installer_api_contract(payloads)


def test_stale_ability_runtime_rejected_pre_export():
    payloads=actual_payloads()
    payloads[v.ROOT+'Modules/com.hpr.abilities/Runtime/AbilityData.cs']=b'public class AbilityData {}'
    with pytest.raises(ValueError,match='missing AbilityData.TryValidateRuntimeSettings'):
        v.validate_ability_installer_api_contract(payloads)


def test_stale_ability_pool_rejected_pre_export():
    payloads=actual_payloads()
    payloads[v.ROOT+'Integration/HprSuiteIntegration.cs']=b'public class HprSuiteAbilityPool {}'
    with pytest.raises(ValueError,match='missing HprSuiteAbilityPool.HasValidStatsSource'):
        v.validate_ability_installer_api_contract(payloads)
