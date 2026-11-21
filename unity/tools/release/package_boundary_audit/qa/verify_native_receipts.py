#!/usr/bin/env python3
"""Independent read-only check of *actual* old/new native buyer-upgrade evidence.

A Unity-created receipt alone cannot prove a successful upgrade. Recheck
archive GUID identities and the unchanged customer files on disk.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

LEGACY=Path('/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-cleanmeta1/hpr-package-boundary-candidate.unitypackage')
UPDATED=Path('/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-upgrade-final1/hpr-package-boundary-candidate.unitypackage')
ALLOWED_BASE=Path('/data/var/marketplace-account-setup/unity-20261121-wave49')
EXPECTED_ROOT='Assets/HPRPackageBoundary'


def archive_guids(path:Path)->dict[str,str]:
    result={};used_guids=set()
    with tarfile.open(path, 'r:gz') as tar:
        for item in tar:
            if not item.isfile() or not item.name.endswith('/pathname'):continue
            guid=item.name.removeprefix('./').split('/')[0]
            if not re.fullmatch(r'[0-9a-f]{32}',guid) or guid in used_guids:
                raise ValueError('Duplicate/invalid Unity archive GUID')
            data=tar.extractfile(item)
            if data is None or item.size>4096:raise ValueError('Invalid pathname content')
            target=data.read().decode('utf-8').strip()
            if not (target==EXPECTED_ROOT or target.startswith(EXPECTED_ROOT+'/')) or target in result:
                raise ValueError('Invalid/duplicated/unexpected Unity archive target path')
            result[target]=guid;used_guids.add(guid)
    if not result:raise ValueError('No Unity path metadata present')
    return result


def verify(evidence:Path)->dict:
    evidence=evidence.resolve(strict=True)
    if evidence.parent != ALLOWED_BASE or not evidence.name.startswith('boundary-upgrade-'):
        raise ValueError('Only a producer-owned, disposable Unity native QA directory is permitted')
    snap=json.loads((evidence/'before-native-vendor-identity.json').read_text())
    diff=json.loads((evidence/'actual-native-upgrade-diff.json').read_text())
    receipt=(evidence/'after-native-upgrade-receipt.txt').read_text()
    original=archive_guids(LEGACY);updated=archive_guids(UPDATED)
    before={x['path']:x['guid'] for x in snap['vendor']}
    if original != before or len(before)!=5 or len(updated)!=6:
        raise AssertionError('Saved original vendor GUIDs disagree with actual prior archive')
    if not all(updated.get(path)==guid for path,guid in before.items()):
        raise AssertionError('New vendor archive does not preserve legacy path and GUID')
    added=set(updated)-set(before)
    if added != {'Assets/HPRPackageBoundary/Editor/HprBoundaryUpgradeReview.cs'}:
        raise AssertionError('Unexpected newer vendor release path changes')
    if not (diff.get('status')=='ADDITIONS_ONLY' and not diff.get('incomplete') and
        diff.get('addedAssets')==1 and diff.get('removedAssets')==0 and
        diff.get('replacedGuids')==0 and diff.get('movedPaths')==0):
        raise AssertionError('Native actual UpgradeReview result not accurately clean')
    customer_root=evidence/'independent-existing-buyer'
    all_customer=list((customer_root/'Assets/HprBoundaryUpgradeCustomerFixture').rglob('*'))
    customer={str(p.relative_to(customer_root)).replace('\\','/'):p for p in all_customer if p.is_file()}
    expected={x['path']:x['sha256'] for x in snap['customerFiles']}
    if set(customer)!=set(expected) or len(expected)<6:
        raise AssertionError('Customer files were added, dropped or miscounted')
    for path,file in customer.items():
        if hashlib.sha256(file.read_bytes()).hexdigest().upper()!=expected[path].upper():
            raise AssertionError('Unexpected changed buyer asset hash: '+path)
    asset=(customer_root/'Assets/HprBoundaryUpgradeCustomerFixture/BuyerReferences.asset').read_text()
    document_guid=before['Assets/HPRPackageBoundary/README.md']
    if (f'guid: {document_guid}' not in asset or 'vendorReadme:' not in asset or
        not re.search(r'm_Script: \{fileID: 11500000, guid: [0-9a-f]{32}, type: 3\}',asset)):
        raise AssertionError('Serialized customer MonoScript or vendor reference missing')
    expected_checks=('exact_old_new_archives_installed_in_same_real_buyer_project=PASS',
        'five_old_vendor_guids_unchanged=PASS',
        'all_customer_file_sha256_and_inventory_unchanged=PASS',
        'serialized_customer_reference_to_vendor_document_resolves=PASS',
        'upgrade_comparison_additions_only=PASS')
    if not all(s in receipt for s in expected_checks):
        raise AssertionError('Native buyer acceptance receipt incomplete')
    if (snap.get('unityVersion') not in ('2022.3.22f1','6000.6.8f1') or
        ('unity_version='+snap['unityVersion']) not in receipt):
        raise AssertionError('Editor-version mismatch')
    log=(evidence/'upgraded-v2-buyer-check.unity.log').read_text(errors='replace')
    if ('HPR_REAL_BUYER_UPGRADE_NATIVE_PASS' not in log or
        'HPR_REAL_UPGRADE_AFTER_FAIL' in log or 'error CS' in log):
        raise AssertionError('Real native Unity buyer run missing or contained failures')
    return {'result':'PASS','editor':snap['unityVersion'],
        'legacy_assets':len(original),'updated_assets':len(updated),
        'customer_files_unchanged':len(expected),'serialized_runtime_reference':'PASS',
        'one_new_vendor_script_only':'PASS'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--evidence',type=Path,required=True)
    a=parser.parse_args()
    print(json.dumps(verify(a.evidence),indent=2))

if __name__=='__main__':main()
