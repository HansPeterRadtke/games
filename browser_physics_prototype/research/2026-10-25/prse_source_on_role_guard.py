#!/usr/bin/env python3
"""PRSE exploratory SOURCE-SYNTAX guard for 'on' relationships.

NO SceneEval gold labels, no 3D physics truth and no benchmarks are opened in
this parser. Actual source text and previously frozen proposed relations are
its only inputs. The pretrained en_core_web_sm dependency model is fixed and
already installed. The guard accepts only literal noun/PP attachment when
the source head describes the proposed CHILD and the PP object names the
proposed SUPPORT. 'On the right side of a TV stand' is not physical support
on the stand; nor is a magazine on a sofa evidence a VASE is on the sofa.

A pass means positive syntactic support evidence, NOT independent source
entailment, complete coreference, sense disambiguation, scene calibration, or
physical validity. Every abstention and failure remains visible.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import json,spacy,re

DIR=Path(__file__).parent
SOURCE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/extracted/en_core_web_sm/en_core_web_sm-3.8.0')
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-support-loop')
PRIVATE.mkdir(parents=True,exist_ok=True,mode=0o700);PRIVATE.chmod(0o700)
def sha(x):return sha256(x.read_bytes()).hexdigest()
def norm(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def name_of(tok):
 compounds=sorted((c for c in tok.children if c.dep_=='compound'),key=lambda t:t.i)
 return norm('_'.join([c.lemma_ for c in compounds]+[tok.lemma_]))
def matches_type(tok,typ):
 a=norm(typ)
 if not tok:return False
 if name_of(tok)==a:return True
 # Singular roots when the source label uses a literal composite class.
 return norm(tok.lemma_)==a
def physical_supported_pp(p):
 return p.text.lower() in ('on','upon','atop') and p.dep_ in ('prep','agent')
def resolved_roles(prep):
 pobj=[c for c in prep.children if c.dep_ in ('pobj','pcomp') and c.pos_ in ('NOUN','PROPN','PRON','NUM')]
 if not pobj:return []
 pp=pobj[0]
 # A PP about the "side", "end", "top", "foot", or "region" can denote
 # lateral/relative positions; without modeled surfaces and part-whole
 # meaning it is not safe to turn into actual support. Abstain.
 if pp.lemma_.lower() in ('side','front','back','region','foot','top','bottom','end','corner','middle',
                          'centre','center','part','area','edge','half','surface','one'):return []
 head=prep.head
 if head.pos_ in ('NOUN','PROPN'):return [(head,pp,'nominal_prepositional_attachment')]
 if head.pos_ in ('VERB','AUX'):
  subjects=[t for t in head.children if t.dep_ in ('nsubj','nsubjpass') and t.pos_ in ('NOUN','PROPN')]
  # If multiple subjects are possible, do NOT arbitrarily select one.
  return [(s,pp,'verb_subject_prepositional_attachment') for s in subjects]
 return []
def test_relation(doc,sourceText,ra,rb,original):
 starts=[]
 start=0
 while True:
  i=original.find(sourceText,start)
  if i<0:break
  starts.append(i);start=i+1
 if len(starts)!=1:return {'pass':False,'reason':'missing_or_ambiguous_exact_source_span','evidence':[]}
 start=starts[0];end=start+len(sourceText)
 roleEvidence=[];why=Counter()
 for prep in doc:
  if not physical_supported_pp(prep) or not (start<=prep.idx<end):continue
  links=resolved_roles(prep)
  if not links:why['pp_without_unambiguous_supported_object_roles']+=1;continue
  for child,support,kind in links:
   childOK=matches_type(child,ra)
   parentOK=matches_type(support,rb)
   if childOK and parentOK:
    roleEvidence.append({'prepStart':prep.idx,'relationKind':kind,
      'childRoot':child.text,'supportRoot':support.text,
      'sourceWords':str(prep.sent)[:250]})
   else:why['wrong_child_or_support_in_actual_source_syntax']+=1
 if roleEvidence:return {'pass':True,'reason':'explicit_same_clause_source_roles','evidence':roleEvidence}
 if why:return {'pass':False,'reason':why.most_common(1)[0][0],'evidence':[]}
 return {'pass':False,'reason':'no_source_supported_on_preposition','evidence':[]}

samples=json.loads(SOURCE.read_text())['proposalsAll500']
ids=list(range(100))+list(range(100,500,4))
nlp=spacy.load(MODEL,disable=['ner'])
rows=[]
for id,doc in zip(ids,nlp.pipe((samples[i]['text'] for i in ids),batch_size=32,n_process=1)):
 p=samples[id]
 for index,r in enumerate(p['relations']):
  if r['kind']!='object' or r['type']!='on':continue
  checked=test_relation(doc,r.get('sourceText',''),r['a'],r['b'],p['text'])
  rows.append({'sourceId':id,'sourceRelationIndex':index,
   'parsedChild':r['a'],'parsedSupport':r['b'],
   'literalSourceSpan':r.get('sourceText',''),
   'status':'source_syntax_role_candidate' if checked['pass'] else 'abstain',
   'reason':checked['reason'],'evidence':checked['evidence']})
assert len(rows)>=45
stats=Counter(r['status'] for r in rows)
reason=Counter(r['reason'] for r in rows)
summary={'sourceSceneCount':len(ids),'extractedOnSourceClaims':len(rows),
 'syntaxRoleCandidates':stats['source_syntax_role_candidate'],
 'roleNotSourceConfirmedAbstentions':stats['abstain'],
 'abstentionReasons':dict(reason),
 'pretrainedGrammarOnly':True,'authorGoldLabelsNotRead':True,
 'unknownPhysicalTruthAndCoreference':True}
file=PRIVATE/'prse_source_role_on_200_raw_v1.json'
with file.open('x') as f:json.dump({'metadata':{
 'sourceSHA256':sha(SOURCE),'modelVersion':'spacy en_core_web_sm 3.8.0',
 'method':'Source text spans, syntax PP roles; positive lexical evidence is NOT full sentence entailment'},
 'summary':summary,'records':rows},f,indent=2);f.write('\n')
file.chmod(0o600)
with (DIR/'prse_source_role_on_200_aggregate_v1.json').open('x') as f:
 json.dump({'metadata':{'sourceSHA256':sha(SOURCE),
 'privateSourceRolesSHA256':sha(file),'noGold':True},
 'summary':summary,'examplesBySourceId':[{'id':r['sourceId'],'role':r['status'],
  'child':r['parsedChild'],'support':r['parsedSupport'],'reason':r['reason']}
  for r in rows]},f,indent=2);f.write('\n')
print('SOURCE_ROLE_GATE',json.dumps(summary))
