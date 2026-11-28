#!/usr/bin/env python3
"""Replay real saved Unity assembly definitions in an isolated disposable copy."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hpr_asmdef_preflight import inspect


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(original: Path, evidence: Path):
    if evidence.exists() or not str(evidence).startswith('/data/var/marketplace-account-setup/'):
        raise ValueError('New private evidence directory required, overwrite refused')
    if not original.is_dir() or original.is_symlink():
        raise ValueError('Original project path must be a real directory')
    files = sorted(p for p in (original/'Assets').rglob('*.asmdef'))
    if not files:
        raise ValueError('Actual saved project contains no assembly definitions')
    version = original/'ProjectSettings/ProjectVersion.txt'
    original_files = [version]
    for p in files:
        m = Path(str(p)+'.meta')
        if not p.is_file() or p.is_symlink() or not m.is_file() or m.is_symlink():
            raise ValueError('Unsafe or unversioned saved first-party assembly file')
        original_files.extend((p,m))
    before = {str(p):sha(p) for p in original_files}
    good = inspect(original)
    if good['status'] != 'CLEAR_WITH_LIMITS':
        raise ValueError('Original source does not have a clear local reference result')
    evidence.mkdir(parents=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='hpr-asmdef-real-replay-',dir='/data/tmp') as temp:
        copied = Path(temp)/'project'
        for source in original_files:
            destination = copied/source.relative_to(original)
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
        candidate = next((p for p in files if '/Runtime/' in p.as_posix()),files[0])
        copied_candidate = copied/candidate.relative_to(original)
        name = json.loads(candidate.read_text())['name']
        injected = copied/'Assets/HPR_AssembyDiagnostic_TestOnly/LocalCollision.asmdef'
        injected.parent.mkdir(parents=True)
        injected.write_text(json.dumps({'name':name})+'\n')
        Path(str(injected)+'.meta').write_text('fileFormatVersion: 2\nguid: '+'f'*32+'\n')
        conflict = inspect(copied)
        if conflict['status'] != 'FAIL' or not any(x['code']=='DUPLICATE_ASSEMBLY_NAME' for x in conflict['findings']):
            raise AssertionError('Deliberate private-copy assembly collision not detected')
        injected.unlink()
        Path(str(injected)+'.meta').unlink()
        modified = json.loads(copied_candidate.read_text())
        modified['defineConstraints']=['UNITY_INCLUDE_TESTS']
        copied_candidate.write_text(json.dumps(modified,indent=2)+'\n')
        missing_in_player = inspect(copied)
        if missing_in_player['status']!='REVIEW' or not any(x['code']=='TEST_ONLY_CONSTRAINT' for x in missing_in_player['findings']):
            raise AssertionError('Deliberate private-copy runtime test-only constraint not reported')
        for filename,receipt in [('real-project-positive.json',good),('private-copy-duplicate.json',conflict),
                                 ('private-copy-test-constraint.json',missing_in_player)]:
            (evidence/filename).write_text(json.dumps(receipt,indent=2)+'\n')
    assert before == {str(p):sha(p) for p in original_files},'Original saved Unity data changed'
    result={'result':'PASS_SAVED_UNITY_SOURCE_ONLY','saved_project':str(original),
            'real_asmdef_files':len(files),'saved_originals_unchanged':True,
            'duplicate_detected_in_private_copy':True,'test_only_constraint_detected_in_private_copy':True,
            'scratch_project_removed':True,'unity_editor_invoked':False,'buyer_native_accepted':False,
            'original_file_hashes':before}
    (evidence/'source-preservation-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'original_file_hashes'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original',type=Path)
    p.add_argument('new_evidence_dir',type=Path)
    a=p.parse_args()
    main(a.original,a.new_evidence_dir)
