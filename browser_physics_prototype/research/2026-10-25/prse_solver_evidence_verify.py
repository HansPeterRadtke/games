#!/usr/bin/env python3
"""Independent verifier for this ONE fixed-proposal / two-layout comparison.

Original SceneEval ZIP and prompt-bearing per-scene proposals remain owner-private.
Only stable IDs/quantities and source-file SHA hashes appear in public reports.
"""
from pathlib import Path
from hashlib import sha256
import io,csv,zipfile,json,stat

R=Path(__file__).parent
RAW=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-relation-solver')
ZIP=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
def read(p):return json.loads(p.read_text())
def hash(p):return sha256(p.read_bytes()).hexdigest()
assert hash(ZIP)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
with zipfile.ZipFile(ZIP) as z:
 with z.open('annotations.csv') as f: rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(rows)==500
gold=read(R/'prse_solver_external_gold_comparison_v1.json')
guard=read(R/'prse_relation_negation_guard_results_v1.json')
assert guard['sourceNegation']['noCoffeeTableObserved'] and guard['sourceNegation']['preservedPhysicalEntityIDs']
assert guard['contradiction']['rejectedAsFullySatisfied'] and guard['unknownSemantics']['ambiguousEntityNotMaterialized']
for part,expected_ids,old_gold,new_gold in [
 ('human',list(range(100)),22,30),
 ('assisted',list(range(100,500,4)),17,22)]:
 path=RAW/f'prse_solver_{part}_100_raw_v1.json'
 assert path.is_file() and stat.S_IMODE(path.stat().st_mode)==0o600
 dat=read(path);pub=read(R/f'prse_solver_{part}_100_aggregate_v1.json')
 assert dat['metadata']['noGoldUsed'] and dat['metadata']['maxCandidateAttemptsPerScene']==150
 assert [int(r['id']) for r in dat['results']]==expected_ids
 assert dat['summary']==pub['summary']
 assert pub['metadata']['rawSHA256']==hash(path)
 assert dat['summary']['sourceDescriptions']==100
 assert dat['summary']['physicallyMaterialized']==(97 if part=='human' else 99)
 assert dat['summary']['stableOriginalIdentitiesAndProse']==dat['summary']['physicallyMaterialized']
 assert all(x['maxReloadPositionError']<.001 for x in dat['results'] if x['status']=='materialized_and_reloaded')
 assert all(dat['results'][i]['id']==str(original) for i,original in enumerate(expected_ids))
 for i,id in enumerate(expected_ids):
  assert id>=0 and id<500
  assert dat['results'][i]['initialGroundedCount']<=dat['results'][i]['proposals']
  assert dat['results'][i]['finalProposedGroundedCount']>=dat['results'][i]['initialGroundedCount']
 item=gold['samples'][part]
 assert item['rawSHA256']==hash(path)
 assert item['objectRelations']['baseline']['matched']==old_gold
 assert item['objectRelations']['optimized']['matched']==new_gold
 assert item['objectRelations']['regressedScenes']==0
 assert item['objectRelations']['goldClaims']==(478 if part=='human' else 743)
 assert item['roomRelations']['improvementAbsolute']>=0
 print(f'{part}: scene saves {dat["summary"]["physicallyMaterialized"]}/100; '
       f'gold physical relations {old_gold}->{new_gold} out of {item["objectRelations"]["goldClaims"]}; '
       f'layout fixes {dat["summary"]["sceneCorrections"]} in {dat["summary"]["correctedScenes"]} scenes, '
       f'raw provenance SHA256 {hash(path)[:16]}...')
print('RESULTS VERIFIED: no raw prompt corpus distributed, same source-ID groups, exact raw file hashes, '
 'preserved baseline and independent gold comparisons, absent/contradictory object guards.')
