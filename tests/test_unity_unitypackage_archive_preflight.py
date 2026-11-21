"""Private original Unitypackage pre-import upgrade scan QA/publishing guards.

Source and synthetic TAR tests are not substitutes for the installed Unity
Editor author/export/fresh buyer negative fixture acceptance.
"""
from pathlib import Path
import importlib.util
import io
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'unity/tools/release/unitypackage_archive_preflight'
VENDOR=PACKAGE/'Assets/HPRArchivePreflight'
ALLOWED={
 'Assets/HPRArchivePreflight',
 'Assets/HPRArchivePreflight/Editor',
 'Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveReader.cs',
 'Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveWindow.cs',
 'Assets/HPRArchivePreflight/README.md',
 'Assets/HPRArchivePreflight/LICENSE.md'
}


def _verifier():
    spec=importlib.util.spec_from_file_location('hpr_archive_verifier',PACKAGE/'qa/verify_archive.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic_package(path:Path,tamper=False,extra=False):
    with tarfile.open(path,'w:gz') as archive:
        for sourcepath in sorted(ALLOWED):
            local=PACKAGE/'Assets'/Path(sourcepath).relative_to('Assets')
            meta=Path(str(local)+'.meta')
            guid=re.search(r'(?m)^guid:\s*([0-9a-f]{32})',meta.read_text()).group(1)
            for suffix,payload in [('pathname',sourcepath.encode()),('asset.meta',meta.read_bytes())]:
                m=tarfile.TarInfo(guid+'/'+suffix);m.size=len(payload)
                archive.addfile(m,io.BytesIO(payload))
            if local.is_file():
                raw=local.read_bytes()
                if tamper and local.name=='HprUnitypackageArchiveReader.cs':raw+=b'USER_SOURCE_MUTATION'
                m=tarfile.TarInfo(guid+'/asset');m.size=len(raw)
                archive.addfile(m,io.BytesIO(raw))
        if extra:
            raw=b'Assets/Unrelated/Injected.cs'
            m=tarfile.TarInfo('f'*32+'/pathname');m.size=len(raw)
            archive.addfile(m,io.BytesIO(raw))


def test_distinct_first_party_sources_and_metadata():
    ids=[]
    for relative in ['', 'Editor','Editor/HprUnitypackageArchiveReader.cs',
                     'Editor/HprUnitypackageArchiveWindow.cs','README.md','LICENSE.md']:
        source=VENDOR/relative if relative else VENDOR
        meta=Path(str(source)+'.meta')
        assert source.exists() and meta.exists()
        guid=re.search(r'(?m)^guid:\s*([a-f0-9]{32})',meta.read_text())
        assert guid
        ids.append(guid.group(1))
    assert len(ids)==len(set(ids))==6
    assert not list(VENDOR.rglob('*.dll'))
    assert set(ALLOWED)==_verifier().ALLOWED


def test_read_only_parser_covers_tar_checksum_footer_sha_crc_unsafe_inputs():
    source=(VENDOR/'Editor/HprUnitypackageArchiveReader.cs').read_text()
    for contract in ('GZipStream(', 'CheckHeaderChecksum(header)',
                     'Invalid Unity package member GUID or path',
                     'Unsafe/unsupported TAR entry type',
                     'Truncated TAR', 'MetaGuid.Matches(meta)',
                     'MaxDecompressedBytes', 'MaxHeaders', 'MaxAssets',
                     'input.FinalCrc', 'input.SizeModulo32',
                     'ReadExactly(file, trailer, 0, 8, false)',
                     'GUID_REPLACED_AT_PATH', 'SOURCE_BYTES_CHANGED',
                     'IMPORT_SETTINGS_CHANGED', 'REVIEW_POTENTIAL_REFERENCE_BREAKAGE',
                     'REVIEW_CONTENT_OR_IMPORT_CHANGES', 'FileMode.CreateNew'):
        assert contract in source
    forbidden=('AssetDatabase.ImportPackage(', 'SaveAndReimport(',
               'FileMode.Create,', 'File.Delete(', 'UnityWebRequest',
               'System.Diagnostics.Process', 'AssetDatabase.DeleteAsset(')
    for keyword in forbidden:
        assert keyword not in source
    ui=(VENDOR/'Editor/HprUnitypackageArchiveWindow.cs').read_text()
    for contract in ('MenuItem(', 'DisplayCancelableProgressBar',
                     'OpenFilePanel(', 'Compare without importing',
                     'Export result to a NEW JSON file', 'INCOMPLETE'):
        assert contract in ui
    for keyword in ('AssetDatabase.ImportPackage(', 'AssetDatabase.DeleteAsset(', 'SaveAndReimport('):
        assert keyword not in ui


def test_strict_verifier_rejects_wrong_source_or_added_package_paths(tmp_path):
    verify=_verifier().verify
    good=tmp_path/'good.unitypackage';_synthetic_package(good)
    assert verify(good)['verified_vendor_paths']==6
    tamper=tmp_path/'tamper.unitypackage';_synthetic_package(tamper,tamper=True)
    try:verify(tamper)
    except ValueError as e:assert 'source bytes' in str(e)
    else:raise AssertionError('Source tamper accepted')
    expanded=tmp_path/'expanded.unitypackage';_synthetic_package(expanded,extra=True)
    try:verify(expanded)
    except ValueError as e:assert 'vendor path' in str(e) or 'Extra' in str(e)
    else:raise AssertionError('Extra injected asset accepted')


def test_native_qa_requires_genuine_archives_corruption_and_fresh_buyer():
    qa=(PACKAGE/'qa/HprArchivePreflightNativeQa.cs').read_text()
    for name in ('real_Unity_packages_strict_readable',
                 'real_existing_buyer_upgrade_exposes_content_changes_not_just_GUIDs',
                 'metadata_GUID_mismatch_fails_closed',
                 'genuine_archive_GUID_change_warns_before_import',
                 'path_traversal_fails_closed', 'truncated_gzip_tar_fails_closed',
                 'symlink_tar_member_rejected', 'user_cancelled_scan_cannot_pass',
                 'both_archives_unchanged_by_scanning', 'HPR_ARCHIVE_PREFLIGHT_NATIVE_PASS'):
        assert name in qa
    run=(PACKAGE/'qa/run_native_acceptance.sh').read_text()
    assert 'Refusing replay of existing native QA project' in run
    assert 'buyer-create' in run and 'buyer-real-import' in run and 'buyer-native-qa' in run
    assert 'verified-buyer-archive.json' in run
    assert 'HprArchivePreflightExporter.Run' in run


def test_actual_buyer_documentation_explains_statuses_and_limits():
    readme=(VENDOR/'README.md').read_text()
    for term in ('documentation', 'existing', 'proposed', 'INCOMPLETE',
                 'REVIEW_POTENTIAL_REFERENCE_BREAKAGE', 'REVIEW_PATH_MIGRATION',
                 'REVIEW_CONTENT_OR_IMPORT_CHANGES', 'ADDITIONS_ONLY',
                 'real buyer project', 'serialized references', 'No archive is imported'):
        assert term in readme
