#!/usr/bin/env python3
"""Source-ONLY pretrained grammar candidate extraction for 3D ON relations.

Fixed existing SceneEval source texts, the previously frozen lexicon/counts
and open-vocabulary noun candidates. NEVER import official OORel annotations
or access gold data paths here.

spaCy dependency parser proposes literal grammatical noun PREP on/upon/atop
attachments and explicit verb subjects. Output original source offsets,
types, source span and abstain reasons. Multiple ambiguous classes remain
unresolved and are NOT multiplied into fake independent instances.

Only a subsequent GameCore/Rapier experiment can establish ACTUAL physical
support/contact. Grammar parser accuracy must be evaluated independently
after 3D candidate scenes are frozen.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import json,spacy,re
ROOT=Path(__file__).parent
RAW=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-source-only-placement')
RAW.mkdir(parents=True,exist_ok=True,mode=0o700);RAW.chmod(0o700)
INPUT=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
EXTRA=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery/prse_spacy_open_vocab_500_proposals_raw_v1.json')
MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/extracted/en_core_web_sm/en_core_web_sm-3.8.0')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
old=json.loads(INPUT.read_text())['proposalsAll500']
proposed=json.loads(EXTRA.read_text())['records']
assert len(old)==len(proposed)==500
ids=list(range(100))+list(range(100,500,4))
parser=spacy.load(MODEL,disable=['ner'])
def get_candidate(word,scene,new):
 types=[]
 if word.pos_ not in ('NOUN','PROPN'):return []
 # Frozen old source mention parser: exact lemma root lies inside span.
 for m in scene['mentions']:
  if m['quantity']<=0:continue
  if m['start']<=word.idx and word.idx+len(word.text)<=m['end']:
   types.append((m['type'],'lexical_existing_mention'))
 # Frozen source-only new noun-chunk: exact root occurs in source phrase.
 for m in new['candidates']:
  a,b=m['sourceOffsets']
  if m['count']<=0:continue
  if a<=word.idx and word.idx+len(word.text)<=b:
   types.append((m['type'],'source_only_pretrained_noun'))
 # Explicit exact lemma when old source parser already has this kind.
 single=norm(word.lemma_)
 if single in scene['quantities'] and scene['quantities'][single]['count']>0:
  types.append((single,'literal_root_known_kind'))
 seen=set()
 return [(typ,reason) for typ,reason in types if not (typ in seen or seen.add(typ))]
def targets_for(prep):
 return [c for c in prep.children if c.dep_ in ('pobj','pcomp') and c.pos_ in ('NOUN','PROPN')]
def children_for(prep):
 head=prep.head
 if head.pos_ in ('NOUN','PROPN'):
  return [head]+[x for x in head.children if x.dep_=='conj' and x.pos_ in ('NOUN','PROPN')]
 if head.pos_ in ('VERB','AUX'):
  nouns=[x for x in head.children if x.dep_ in ('nsubj','nsubjpass') and x.pos_ in ('NOUN','PROPN')]
  return nouns + [child for noun in nouns for child in noun.children if child.dep_=='conj' and child.pos_ in ('NOUN','PROPN')]
 return []
skipheads={'side','top','front','back','end','corner','left','right','middle','one','part','edge','area','bottom'}
cases=[];count=Counter()
for id,doc in zip(ids,parser.pipe((old[i]['text'] for i in ids),batch_size=32,n_process=1)):
 s=old[id];n=proposed[id]
 assert s['text']==n['sourceText']
 candidates=[];abstentions=[]
 for prep in doc:
  if prep.lower_ not in ('on','atop','upon') or prep.dep_ not in ('prep','agent'):continue
  parents=targets_for(prep)
  childs=children_for(prep)
  if not parents or not childs:
   abstentions.append({'offset':prep.idx,'reason':'no_unique_nominal_subject_or_prepositional_object'})
   continue
  for child in childs:
   for parent in parents:
    if parent.lemma_.lower() in skipheads or child.lemma_.lower() in skipheads:
     abstentions.append({'offset':prep.idx,'reason':'part_or_location_not_physical_support'});continue
    left=get_candidate(child,s,n);right=get_candidate(parent,s,n)
    if not left or not right:
     abstentions.append({'offset':prep.idx,'reason':'no_source_linked_entity_candidate'});continue
    for a,originA in left:
     for b,originB in right:
      if a==b:continue
      phrase=str(prep.sent)
      e={'a':a,'b':b,'kind':'object','type':'on',
       'sourceSnippet':phrase[:230],
       'grammaticalChildRoot':child.text,'grammaticalParentRoot':parent.text,
       'sourceCharPositions':[child.idx,parent.idx,prep.idx],
       'provenanceA':originA,'provenanceB':originB,
       'confidence':'pretrained_dependency_attached_on_not_author_entailed'}
      if not any(x['a']==a and x['b']==b for x in candidates):
       candidates.append(e)
 if len(candidates)>128:raise ValueError('Abnormally many unresolved relations in one source scene')
 count['sources']+=1
 count['onRelationshipCandidates']+=len(candidates)
 count['sourceScenesWithCandidates']+=bool(candidates)
 count['abstentions']+=len(abstentions)
 cases.append({'sourceId':id,'sourceHash':sha256(s['text'].encode()).hexdigest(),
               'proposedOn':candidates,'abstentions':abstentions})
assert len(cases)==200
summary=dict(count)
file=RAW/'prse_source_only_on_nounchunk_200_raw_v1.json'
with file.open('x') as f:json.dump({'metadata':{
 'method':'spaCy 3.8 pretrained source noun chunk/dependency only, old frozen lexicon and earlier frozen open-vocab source noun candidates',
 'noGoldInput':True,'sourceParserSHA256':sha(INPUT),'frozenNounCandidatesSHA256':sha(EXTRA)},
 'summary':summary,'cases':cases},f,indent=2);f.write('\n')
file.chmod(0o600)
with (ROOT/'prse_source_only_on_nounchunk_200_aggregate_v1.json').open('x') as f:
 json.dump({'metadata':{'sourceParserSHA256':sha(INPUT),'frozenSourceNounCandidatesSHA256':sha(EXTRA),
 'completePrivateSourceOnlyRawSHA256':sha(file),
 'notIndependentOriginalAuthorEntailment':True,'noGoldUsed':True},'summary':summary,
 'perScene':[{'sourceId':r['sourceId'],'count':len(r['proposedOn']),
              'abstentions':len(r['abstentions'])} for r in cases]},f,indent=2);f.write('\n')
print('FROZEN_SOURCE_ONLY_PRETRAINED_GRAMMAR_ON',summary)
