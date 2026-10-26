#!/usr/bin/env python3
"""Read-only cross-check of frozen NEW-300 physical evidence and later gold.
No new physics, no oracle placements, no repeat of denied parent-placebo.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
from stat import S_IMODE
import csv
import io
import json
import zipfile

R = Path(__file__).parent
D = Path('/data/var/games/prse_semantic_research/runs/2026-10-26-new-physical-300')
Z = Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
SOURCE = Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
P = D / 'prse_source_only_on_nounchunk_300_raw_v1.json'
N = D / 'prse_source_only_same_budget_native_300_raw_v1.json'
G = D / 'prse_new300_independent_author_gold_percase_v1.json'
C = D / 'prse_new300_author_quantity_percase_v1.json'
def sha(path):
    return sha256(path.read_bytes()).hexdigest()
def data(path):
    return json.loads(path.read_text())
assert S_IMODE(D.stat().st_mode) == 0o700
assert all(S_IMODE(f.stat().st_mode) == 0o600 for f in (P, N, G, C))
assert sha(Z) == '2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(Z) as zip_file:
    with zip_file.open('annotations.csv') as f:
        authors = list(csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig')))
assert len(authors) == 500
source = data(SOURCE)['proposalsAll500']
props = data(P)
native = data(N)
gold = data(R / 'prse_new300_matched_native_independent_gold_aggregate_v1.json')
count = data(R / 'prse_new300_source_count_geometry_author_aggregate_v1.json')
safe_native = data(R / 'prse_source_only_same_budget_native_300_aggregate_v1.json')
safe_props = data(R / 'prse_source_only_on_nounchunk_300_aggregate_v1.json')
expected = [id for id in range(100, 500) if (id - 100) % 4 != 0]
prior = set(range(100)) | set(range(100, 500, 4))
assert len(expected) == 300 and not (prior & set(expected))
assert [r['sourceId'] for r in native['rows']] == expected
assert [r['sourceId'] for r in props['cases']] == expected
assert safe_native['metadata']['rawSHA256'] == sha(N)
assert safe_props['metadata']['completePrivateSourceOnlyRawSHA256'] == sha(P)
assert gold['metadata']['frozenPhysicsSHA256'] == sha(N)
assert gold['metadata']['frozenSourceOnlyParserSHA256'] == sha(P)
assert gold['metadata']['privateGoldPerCaseSHA256'] == sha(G)
assert count['metadata']['newNativeRawSHA256'] == sha(N)
assert count['metadata']['privateGoldPerCaseSHA256'] == sha(C)

native_total = Counter()
attempt_status = Counter()
for index, (row, proposal) in enumerate(zip(native['rows'], props['cases'])):
    id = expected[index]
    text = source[id]['text']
    assert authors[id]['Description'] == text
    assert sha256(text.encode()).hexdigest() == proposal['sourceHash'] == row['sourceHash']
    assert row['candidateCount'] == len(proposal['proposedOn'])
    native_total['descriptions'] += 1
    if row['status'] != 'same_body_real_native_matched':
        assert row['status'] == 'original_scene_not_physically_accepted'
        native_total['originalRejected'] += 1
        continue
    native_total['accepted'] += 1
    old_body = {x['id']: x for x in row['oldBodyStates']}
    new_body = {x['id']: x for x in row['newBodyStates']}
    assert old_body.keys() == new_body.keys()
    native_total['bodies'] += len(old_body)
    for id, x in old_body.items():
        y = new_body[id]
        assert (x['kind'], x['shape'], x['body']) == (y['kind'], y['shape'], y['body'])
        assert x['size'] == y['size']
    contact_keys = lambda records: {tuple(sorted((p['a'], p['b']))) for p in records}
    older = contact_keys(row['oldNativeContactPairs'])
    newer = contact_keys(row['newNativeContactPairs'])
    assert older.issubset(newer), 'unexpected existing true contact loss'
    native_total['baselineContacts'] += len(older)
    native_total['newContacts'] += len(newer)
    native_total['gainedContacts'] += len(newer - older)
    native_total['lostContacts'] += len(older - newer)
    attempts = row['attempts']
    attempt_status.update(a['status'] for a in attempts)
    plans = {tuple(sorted((a['childId'], a['supportId'])))
             for a in attempts if a['status'] == 'nominally_valid_prephysics_source_on'}
    assert len(plans) == row['placed']
    assert len(plans & newer) == row['actualNewSourcePairs']
    native_total['placed'] += row['placed']
    if not plans:
        assert older == newer
        native_total['zeroMoveControls'] += 1
    assert row['savedNativeSourceAndContacts'] and row['identicalSourceAndNativeEntityBudget']
assert native_total == Counter({
    'descriptions': 300, 'accepted': 293, 'originalRejected': 7, 'bodies': 3528,
    'baselineContacts': 21, 'newContacts': 54, 'gainedContacts': 33,
    'lostContacts': 0, 'placed': 33, 'zeroMoveControls': 263
})
assert native['summary']['preplannedAbstentions'] == dict(attempt_status)
assert native['summary']['actualNativeSaveAndSameBodies'] == native_total['accepted']
t = gold['total']; q = count['total']
assert (t['goldONPhysicallyEvaluable'], t['goldONPhysicallySupportedBaseline'],
        t['goldONPhysicallySupportedSourceOnly'], t['goldONTrueGained'],
        t['goldONTrueLost']) == (698, 5, 15, 10, 0)
assert t['newRelationsUnannotatedAtTypePairLevel'] == 22
assert (q['independentAuthorObjectCountClauses'], q['authorObjectCountSatisfied'],
        q['authorObjectCountFailed'], q['genericFallbackSmallPlaceholderBoxes']) == (2148, 1588, 560, 2165)
assert q['missingObjectType'] + q['underCountWithTypePresent'] + q['overCountWhenExact'] == q['authorObjectCountFailed']
assert sum(1 for x in data(G)['perCase'] if x['oldTrue']) == 5
assert sum(1 for x in data(G)['perCase'] if x['newTrue']) == 15
assert len(data(C)['cases']) == 2148
print('VERIFIED NEW PHYSICAL-300 source identity, exact native IDs and geometry,')
print('all real contact sets, all 263 zero-move controls, source-scene separation,')
print('independent post-frozen author metrics, raw hashes and mode-0600 privacy.')
print('NATIVE:', dict(native_total))
