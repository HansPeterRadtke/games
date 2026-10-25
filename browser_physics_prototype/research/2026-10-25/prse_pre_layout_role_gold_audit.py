#!/usr/bin/env python3
"""POST-FROZEN independent author SceneEval source ON-relationship scoreboard.

Compare native GameCore/Rapier PRE-LAYOUT SOURCE-ROLE ABSTENTION with the prior
frozen native GameCore baseline. Author OORel labels are opened only HERE,
after both physical scenes, original object IDs, contact manifolds and
observer-semantic native save/reentry were frozen. No gold model training.

ON author annotation encodes SUPPORT first, CHILD second. We require upright
source type instances, horizontal footprint, matching vertical contact plane
and a genuine Rapier contact manifold. Score is still optimistic SOURCE TYPE
PAIR existential matching, not exact original entity coreference or a visually
correct 3D asset. Unsupported directional/inside/facing never inferred.
"""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from stat import S_IMODE
import json,csv,io,zipfile,math
R=Path(__file__).parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop')
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset/prse_post_asset_native_baseline_200_raw_v2.json')
NEW=P/'prse_source_syntax_guarded_native_200_raw_v2.json'
GOLD=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
def hash(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert hash(GOLD)=='2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676'
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (NEW,BASE))
with zipfile.ZipFile(GOLD) as z:
 with z.open('annotations.csv') as f:gold=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
assert len(gold)==500
ids=list(range(100))+list(range(100,500,4))
base=read(BASE)['rows'];new=read(NEW)['results']
source=read(FROZEN)['proposalsAll500']
assert [a['id'] for a in base]==[x['sourceId'] for x in new]==ids
def norm(s):
 a=s.lower().replace(' ','_')
 return {'television':'tv','bunk_bed':'bed','refrigerator':'fridge','bedside_lamp':'lamp'}.get(a,a)
def upright(body):
 q=body['rotation'];return 2*math.acos(max(-1,min(1,abs(q['w']))))<.10
def supported(a,b,contacts):
 if a['id']==b['id'] or not upright(a) or not upright(b):return False
 if any(abs(a['position'][axis]-b['position'][axis])+b['size'][axis]/2>
        a['size'][axis]/2+.03 for axis in ('x','z')):return False
 if abs((b['position']['y']-b['size']['y']/2)-(a['position']['y']+a['size']['y']/2))>.08:
  return False
 return frozenset((a['id'],b['id'])) in contacts
def world_on_count(bodies,pairs,parent,child):
 by=defaultdict(list)
 for e in bodies:by[norm(e['kind'])].append(e)
 supports={frozenset((x['a'],x['b'])) for x in pairs if x.get('contactCount',x.get('contactPointCount',0))>0}
 a=by[parent];b=by[child]
 matched=set()
 for x in a:
  for y in b:
   if supported(x,y,supports):matched.add(y['id'])
 return len(matched),bool(a) and bool(b)
def gold_on(row):
 for t in row['OORel'].split(';'):
  p=[v.strip() for v in t.split(',')]
  if len(p)<6 or p[2]!='on':continue
  try:n=int(p[1])
  except ValueError:continue
  if p[0] not in ('eq','ge','gt'):continue
  yield {'support':norm(p[4]),'child':norm(p[5]),
   'required':n+(1 if p[0]=='gt' else 0),
   'annotationOperator':p[0]}
counter=Counter();per=[]
for i,row in enumerate(new):
 id=ids[i];baseline=base[i]
 if baseline['status']!='native_simulated':
  assert row['status']=='original_scene_not_physically_valid'
  continue
 assert row['status']=='native_valid_source_guarded',id
 assert row['originalBodyIDsPreserved'] and row['fullOriginalLiterarySourcePreserved']
 assert row['exactCurrentTextAfterNativeReentry'] and row['unchangedSemanticRecordDoesNotRepeat']
 counter['acceptedScenes']+=1
 x=baseline['bodyStates'];xb=baseline['nativeContactPairs']
 y=row['initialBodyStates'];yb=row['initialNativeContactPairs']
 assert {z['id'] for z in x}=={z['id'] for z in y}
 g=list(gold_on(gold[id]))
 details=[]
 for clause in g:
  old,typesOld=world_on_count(x,xb,clause['support'],clause['child'])
  newValue,typesNew=world_on_count(y,yb,clause['support'],clause['child'])
  oldOK=old>=clause['required'] and clause['required']>0
  newOK=newValue>=clause['required'] and clause['required']>0
  counter['authorOnClauses']+=1
  counter['bothTypesBaselinePresent']+=int(typesOld)
  counter['bothTypesGuardedPresent']+=int(typesNew)
  counter['authorOnPhysicallyConfirmedBaseline']+=int(oldOK)
  counter['authorOnPhysicallyConfirmedGuarded']+=int(newOK)
  counter['newlyGainedPhysicalAuthorOn']+=int(newOK and not oldOK)
  counter['previouslyVerifiedAuthorOnNowLost']+=int(oldOK and not newOK)
  details.append({'originalGold':clause,
   'baselineRealContactCount':old,'guardedRealContactCount':newValue,
   'baselineSatisfied':oldOK,'guardedSatisfied':newOK})
 per.append({'id':id,'originalProposedOn':row['sourceOnClaims'],
  'syntaxApprovedOn':row['sourceRoleAcceptedOnClaims'],
  'nativeOriginalOnContacts':sum(z['physical']=='true' for z in row['sourceOnOutcomes']),
  'independentAuthorOn':details})
assert counter['acceptedScenes']==197
post=P/'prse_pre_layout_role_guard_on_gold_200_raw_v1.json'
with post.open('x') as f:json.dump({'metadata':{
 'frozenAuthorSource':'SceneEval v250610 OORel only opened after physical save',
 'scope':'Source type-pair upright support/contact scoring, not exact scene entailment'},
 'counters':dict(counter),'rows':per},f,indent=2);f.write('\n')
post.chmod(0o600)
publication=R/'prse_pre_layout_source_role_gold_200_aggregate_v1.json'
with publication.open('x') as f:json.dump({'metadata':{
 'authorSceneEvalSHA256':hash(GOLD),
 'frozenNativeBaselineSHA256':hash(BASE),
 'frozenRoleGuardNativeSHA256':hash(NEW),
 'privateOfficialPerCaseSHA256':hash(post),
 'goldNeverEnteredPhysicalCompiler':True,
 'metric':'Native Rapier contact + upright object top support type pair author ON only',
 'sourceTypePairNotProvenInstanceGrounding':True},
 'counter':dict(counter)},f,indent=2);f.write('\n')
print('SOURCE_GATED_NATIVE_INDEPENDENT_AUTHOR_ON',dict(counter))
