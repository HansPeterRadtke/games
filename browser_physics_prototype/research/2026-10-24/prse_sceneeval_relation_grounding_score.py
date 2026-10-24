#!/usr/bin/env python3
"""Independent annotation-to-materialized-scene audit.

Consumes official gold only AFTER text-only parser proposals and GameCore
physical placements have been frozen. Scores typed pair relationship
grounding, NOT orientation precision, aesthetics, enjoyment or general NLP.
"""
from pathlib import Path
import csv,zipfile,io,json,collections,sys,re
ROOT=Path(__file__).parent
CORPUS=Path('/data/var/games/prse_semantic_research/SceneEval-500_v250610.zip')
with zipfile.ZipFile(CORPUS) as z:
    with z.open('annotations.csv') as f: rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
inputName=next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith('--physics=')),'prse_sceneeval_constraint_physics_v1.json')
if not re.fullmatch(r'[a-z][a-z0-9_.-]*\.json',inputName):raise ValueError('Unsafe input result name')
source=(ROOT/inputName)
if not source.is_file():source=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints')/inputName
results=json.loads(source.read_text())['results']
resultById={int(r['id']):r for r in results}
rel_alias={'next_to':'next','adjacent':'next','beside':'next','facing':'face','opposite':'across',
           'beneath':'under','side_by_side':'next','around':'surround'}
noun_alias={'television':'tv','refrigerator':'fridge','bunk_bed':'bed'}
def noun(n):
    n=n.split(':')[0].lower().strip().replace(' ','_')
    return noun_alias.get(n,n)
def rel(r):return rel_alias.get(r.lower(),r.lower())
def key(kind,a,b):
    return (rel(kind),tuple(sorted((noun(a),noun(b)))))
def annotations(row):
    expected=collections.Counter()
    for raw in row['OORel'].split(';'):
        v=[x.strip() for x in raw.strip().split(',')]
        if len(v)<6:continue
        try:n=int(v[1])
        except ValueError:continue
        if v[0]=='gt':n+=1
        if v[0] not in ('eq','ge','gt'):continue
        k=key(v[2],v[4],v[5])
        expected[k]=max(expected[k],n)
    return expected
def metrics(indices):
    expected_total=matched_extracted=matched_physically=0
    predicted_all=predicted_grounded=0
    fail=[]
    statuses=collections.Counter()
    for idx in indices:
        row=rows[idx];record=resultById[idx];statuses[record['status']]+=1
        gold=annotations(row)
        extracted=collections.Counter()
        grounded=collections.Counter()
        for rr in record.get('relationPredictions',[]):
            if rr['kind']!='object':continue
            k=key(rr['type'],rr['a'],rr['b'])
            extracted[k]=max(extracted[k],1)
            if rr.get('grounded') is True and record['status']=='materialized_and_reloaded':
                grounded[k]=max(grounded[k],1)
        # Use the final post-physics body relation check when available; anything
        # not actually grounded after stepping is NOT credited.
        grounded=collections.Counter()
        for rr in record.get('physicalRelationOutcomes',[]):
            if rr['kind']!='object' or rr['result'] is not True:continue
            grounded[key(rr['type'],rr['a'],rr['b'])]=1
        expected_total+=sum(gold.values())
        matched_extracted+=sum(min(v,extracted.get(k,0)) for k,v in gold.items())
        matched_physically+=sum(min(v,grounded.get(k,0)) for k,v in gold.items())
        predicted_all+=sum(extracted.values())
        predicted_grounded+=sum(grounded.values())
        if sum(min(v,grounded.get(k,0)) for k,v in gold.items())<sum(gold.values()) and len(fail)<12:
            fail.append({'id':idx,'description':row['Description'][:220],
                'missing':[str(k) for k,v in gold.items() if grounded.get(k,0)<v][:6],
                'grounded':[str(k) for k in grounded][:6]})
    recall=matched_physically/expected_total if expected_total else None
    precision=matched_physically/predicted_grounded if predicted_grounded else 0
    return {'scenes':len(indices),'statuses':dict(statuses),
       'goldAnnotatedTypedPairRelations':expected_total,
       'extractedMatchedGold':matched_extracted,
       'physicallyGroundedMatchedGold':matched_physically,
       'groundedPrecisionIgnoringDirection':precision,
       'groundedRecallIgnoringDirection':recall,
       'groundedF1':2*precision*recall/(precision+recall) if precision+recall else 0,
       'predictedRelations':predicted_all,
       'predictedRelationsPhysicallyTrue':predicted_grounded,
       'directionNotEvaluated':True,'missingFirst12':fail}
sampleIds=sorted(resultById)
subsets=({'development_first35':range(35),'later65':range(35,100),'originalHuman100':range(100)}
 if all(i in resultById for i in range(100))
 else {'machine_assisted_sampled_100':sampleIds})
out={'metadata':{
 'benchmark':'SceneEval-500 original first 100 human-authored descriptions; official annotated relation types and participant classes',
 'noAnnotationLeak':'Text constraints and Rapier placements were compiled without reading evaluation annotations. Gold consumed only in this separate scorer.',
 'limits':'Pair type orientation ignored; duplicate exact relation ground truth may require multiple distinct participants; hand-authored source ontology/heuristics; not untouched scientifically blind outer holdout.',
 'noLLM':'No new neural generator invocation'},
 'results':{k:metrics(v) for k,v in subsets.items()}}
nameArg=next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith('--output=')),'prse_sceneeval_relation_grounding_score_v1.json')
if not re.fullmatch(r'[a-z][a-z0-9_.-]*\.json',nameArg):raise ValueError('Unsafe output result name')
name=ROOT/nameArg
with name.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for k,v in out['results'].items():
    print(k,{x:v[x] for x in ('scenes','goldAnnotatedTypedPairRelations','extractedMatchedGold',
     'physicallyGroundedMatchedGold','groundedPrecisionIgnoringDirection',
     'groundedRecallIgnoringDirection','groundedF1','predictedRelationsPhysicallyTrue')})
