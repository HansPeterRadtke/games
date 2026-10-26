#!/usr/bin/env python3
"""Research-only, HIGH-PRECISION room-scoped source contract from ORIGINAL
independently human-written LEGO text, not from released constraint labels or
reference 3D scenes. Sample ids 20, 26, 40 are POSTHOC chosen and have been
previously inspected; do not describe as unseen or an unbiased test.

Freeze this manifest separately BEFORE new native PRSE materialization, then
verify physics separately against official independently authored clauses.
No narrator/observer experiment, random feasible parent placebo or production
game service is accessed here.
"""
from pathlib import Path
import re, json, hashlib, time
from collections import Counter
from stat import S_IMODE

HERE=Path(__file__).resolve().parent
PRIV=Path('/data/var/games/prse_semantic_research/runs/2026-10-27-prse-round9-room-contract')
PRIV.mkdir(parents=True,exist_ok=True,mode=0o700);PRIV.chmod(0o700)
BASE=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
SOURCE=BASE/'lego_full_data_public_human_gold.json'
assert S_IMODE(SOURCE.stat().st_mode)==0o600
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def txtsha(s):return hashlib.sha256(s.encode()).hexdigest()
def normalize(s):return re.sub(r'[^a-z0-9]+','_',s.casefold()).strip('_')
def canon(s):
    s=normalize(s)
    if s.endswith('ies'):s=s[:-3]+'y'
    elif s.endswith('s') and not s.endswith(('ss','us')):s=s[:-1]
    return {'refrigerator':'fridge','television':'tv'}.get(s,s)
# Structural categories are not false primitive "objects on the ground":
# the real asset/room topology is unknown, and requires a separate adapter.
STRUCTURAL={'wall','walls','floor','floors','ceiling','ceilings','door','doors',
            'window','windows','stairs','staircase','roof','gate','archway',
            'pillar','pillars'}
UNTRUSTED_MODIFIER_TOKENS={'that','with','painted','connected','leads','lead','of','to'}
COUNT={'a':1,'an':1,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,
       'seven':7,'eight':8,'nine':9,'ten':10}
COUNT_RE=r'(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)'
def phrases(s):
    # The comma + final-and list grammar, only. No arbitrary clause inference.
    return [x.strip(' ,') for x in re.split(r',\s*(?:and\s+)?|\s+and\s+',s)
            if x.strip(' ,')]
def quantified(s):
    match=re.fullmatch(rf'({COUNT_RE})\s+([a-z][a-z\s-]+)',s.strip(),re.I)
    if not match:return None
    countword,raw=match.groups()
    n=int(countword) if countword.isdigit() else COUNT.get(countword.casefold())
    if not n or n>8:return None
    kind=canon(raw)
    return (kind,n)
def spans(text):
    start=0
    for match in re.finditer(r'[^.!?]+[.!?]',text):
        source=match.group().strip()
        if not source:continue
        base=match.start()+len(match.group())-len(match.group().lstrip())
        yield source,base,base+len(source)
# More general fallback than the exact intro: split text BEFORE lexical
# name checks and require each constituent count to be independently explicit.
room_intro_general=re.compile(r'^There is (.+) in the (?:apartment|prison building)\.$',re.I)
negative=re.compile(r'^There (?:is|are) no ([a-z-]+) in the ([a-z][a-z\s-]+)\.$',re.I)
positive_a=re.compile(r'^In the ([a-z][a-z\s-]+), there (?:is|are) (.+)\.$',re.I)
positive_b=re.compile(r'^There (?:is|are) (.+) in the ([a-z][a-z\s-]+)\.$',re.I)
positive_c=re.compile(r'^The ([a-z][a-z\s-]+) has (.+)\.$',re.I)
gold=json.loads(SOURCE.read_text())
assert len(gold)==130
SELECTED=[20,26,40]
cases=[]
total=Counter()
start=time.perf_counter()
for idx in SELECTED:
    text=gold[idx]['instruction']  # NO .labels, NO official reference JSON
    assert len(text)>=300
    rooms=[]; roomEvents=[]; sentenceRows=list(spans(text))
    for sent,a,b in sentenceRows:
        m=room_intro_general.fullmatch(sent)
        if not m:continue
        components=phrases(m.group(1))
        proposed=[quantified(x) for x in components]
        if len(proposed)<2 or any(x is None for x in proposed):continue
        if len({name for name,n in proposed})!=len(proposed):continue
        if sum(n for _,n in proposed)>8:continue
        for room,n in proposed:
            if n!=1:raise ValueError('Repeated room kinds lack distinct source instance IDs: reject')
            rooms.append(room)
        roomEvents.append({'sourceCharOffsets':[a,b], 'sourceHash':txtsha(sent),
          'roomNames':rooms[:]})
    if not rooms or len(rooms)>6:raise ValueError('no unambiguous author room list')
    reqs=[];prohibitions=[];unresolved=[];parseSeen=set()
    for sent,a,b in sentenceRows:
        if any(sent==text[x['sourceCharOffsets'][0]:x['sourceCharOffsets'][1]]
               for x in roomEvents):continue
        neg=negative.fullmatch(sent)
        if neg:
            kind,room=neg.groups();kind=canon(kind);room=normalize(room)
            if room not in rooms:raise ValueError('Author negative unrecognized room')
            prohibitions.append({'kind':kind,'roomId':room,
                'sourceCharOffsets':[a,b],'sourceClauseSHA256':txtsha(sent)})
            parseSeen.add((a,b))
            continue
        pos=positive_a.fullmatch(sent)
        if pos:room,items=pos.groups()
        else:
            pos=positive_b.fullmatch(sent)
            if pos:items,room=pos.groups()
            else:
                pos=positive_c.fullmatch(sent)
                if pos:room,items=pos.groups()
                else:continue
        room=normalize(room)
        if room not in rooms:continue
        constituents=phrases(items)
        parsed=[quantified(x) for x in constituents]
        for part_i,part in enumerate(constituents):
            if parsed[part_i] is None:
                unresolved.append({'reason':'unquantified_or_ambiguous_noun_list',
                 'sourceCharOffsets':[a,b],'sourceClauseSHA256':txtsha(sent)})
                continue
            kind,amount=parsed[part_i]
            tokens=kind.split('_')
            if len(tokens)>3 or any(t in STRUCTURAL or t in UNTRUSTED_MODIFIER_TOKENS for t in tokens):
                unresolved.append({'reason':'unapproved_architectural_physical_asset',
                   'kind':kind,'roomId':room,'sourceCharOffsets':[a,b],
                   'sourceClauseSHA256':txtsha(sent)})
                continue
            key=(room,kind)
            if key in parseSeen:raise ValueError('Duplicate source object assertion would create duplicate')
            reqs.append({'kind':kind,'roomId':room,'count':amount,
              'sourceCharOffsets':[a,b],
              'sourceClauseSHA256':txtsha(sent),
              'geometryCertified':False,'sourceRoomIdentityCertifiedByExactText':True})
            parseSeen.add(key)
    for pos in reqs:
        if any(pos['kind']==neg['kind'] and pos['roomId']==neg['roomId']
               for neg in prohibitions):
            raise ValueError('Contradictory source positive and negative within one room')
    if not reqs or not prohibitions:raise ValueError('No room-qualified source positives and negatives')
    assert not any(any(t in STRUCTURAL or t in UNTRUSTED_MODIFIER_TOKENS for t in x['kind'].split('_')) for x in reqs)
    assert not any(len(x['kind'].split('_'))>3 for x in reqs)
    cases.append({'sceneIndex':idx,'sourceText':text,'sourceTextSHA256':txtsha(text),
      'roomNames':rooms,'sourceRoomEvents':roomEvents,
      'positiveRoomKinds':reqs,'explicitNegativeRoomKinds':prohibitions,
      'recognizedButUnmaterializableClauses':unresolved,
      'FULL_AUTHOR_SCENE_APPROVED':False,
      'reasonFullSceneNotApproved':'Only explicit enumerative clauses and simple rooms are currently interpreted; asset meshes, visual materials, causal story, observer narration, doors/windows/room topology are NOT source-grounded'})
    total['scenes']+=1
    total['sourceRooms']+=len(rooms)
    total['sourcePositiveKindGroups']+=len(reqs)
    total['sourcePositiveNativeObjectInstancesPlanned']+=sum(p['count'] for p in reqs)
    total['sourceExplicitRoomNegations']+=len(prohibitions)
    total['sourceAssetOrAmbiguityAbstentions']+=len(unresolved)
assert total['scenes']==3
assert total['sourceRooms']==8
assert total['sourceExplicitRoomNegations']==4
assert [c['sceneIndex'] for c in cases]==SELECTED
assert all(c['sourceTextSHA256']==txtsha(gold[c['sceneIndex']]['instruction']) for c in cases)
out=PRIV/'source_original_strict_room_proposal_frozen_v3.json'
with out.open('x') as f:
    json.dump({'metadata':{'originalOfficialHumanInstructionCSV_SHA256':sha(SOURCE),
        'readOnlyInputFields':['instruction'],
        'humanOfficialLabelsAndReferenceRoomsNeverReadBySourceProposals':True,
        'posthocKnownHumanScenesNotIndependentHeldout':True,
        'ALL_PROVISIONAL_UNCALIBRATED_3D_ASSETS':True,
        'FULL_SCENE_ACCEPTANCE_ALWAYS_FALSE_UNTIL_INDEPENDENT_COMPLETE_GOLD':True,
        'noDeniedObserverCycleOrRandomParentPlacebo':True},
        'summary':dict(total),'cases':cases,
        'elapsedSourceOnlySeconds':round(time.perf_counter()-start,4)},f,indent=2)
    f.write('\n')
out.chmod(0o600)
print('ROUND9_SOURCE_ONLY_STRICT_ROOM_MANIFEST_FROZEN',dict(total),'SHA',sha(out))
for c in cases:print('SCENE',c['sceneIndex'],'ROOMS',c['roomNames'],
 'POSITIVE',[(x['roomId'],x['kind'],x['count']) for x in c['positiveRoomKinds']],
 'NEGATIVE',[(x['roomId'],x['kind']) for x in c['explicitNegativeRoomKinds']],
 'UNRESOLVED',len(c['recognizedButUnmaterializableClauses']))
