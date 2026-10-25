#!/usr/bin/env python3
"""PRSE source-text relation proposals with a genuine pretrained CPU syntax model.

Uses *only* the description string and the already-fixed noun/count/attribute
lexicon (same as deterministic comparator). spaCy en_core_web_sm v3.8.0 parses
dependencies; a transparent, bounded constraint mapper converts syntactic
prepositional/verb arcs to source-linked spatial relation candidates.

There is no dataset annotation access here, no learned fine tuning on SceneEval,
and no claim that dependency parsing alone resolves world commonsense.
"""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).parent.parent/"2026-10-24"))
import spacy
from prse_semantic_constraints import interpret as lexical_interpret

DEFAULT_MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/extracted/en_core_web_sm/en_core_web_sm-3.8.0')
PREPS={'on':'on','under':'under','beneath':'under','above':'above','over':'above',
       'near':'near','beside':'next','behind':'behind','against':'against',
       'around':'surround','inside':'inside','within':'inside','in':'in',
       'by':'near','opposite':'opposite','across':'across','along':'along',
       'next':'next','between':'between','adjacent':'adjacent','below':'under'}
COMPOSITES={
 ('of','top'):'on',('of','front'):'front',('of','back'):'behind',
 ('of','side'):'side_of',('of','left'):'left',('of','right'):'right',
 ('to','next'):'next',('to','close'):'near',('to','adjacent'):'adjacent',
 ('from','across'):'across',('to','opposite'):'opposite'}
VERBS={'surround':'surround','face':'face','flank':'side_of'}
ROOM={'room','wall','walls','floor','ceiling','corner','door','window','windows'}
SUBJ={'nsubj','nsubjpass','attr','dobj','obj','oprd','appos'}
def load_model(path=DEFAULT_MODEL):
 model=spacy.load(str(path),disable=['ner'])
 if 'parser' not in model.pipe_names:raise RuntimeError('Real dependency parser not loaded')
 model.max_length=6000
 return model

def mentions_as_tokens(doc,claims):
 out=[]
 for m in claims['mentions']:
  if m['quantity']<=0:continue
  span=doc.char_span(m['start'],m['end'],alignment_mode='expand')
  if span is not None and len(span)>0:
   out.append({'type':m['type'],'span':span,'head':span.root,'start':span.start,'end':span.end})
 return out

def is_inside(token,span):
 return span.start<=token.i<span.end
def mention_token(tok,matches):
 for m in matches:
  if is_inside(tok,m['span']):return m
 return None

def find_entity_in_subtree(prep,mentions):
 candidates=[]
 for m in mentions:
  token=m['head']
  if prep==token or prep in list(token.ancestors):
   candidates.append(m)
 return sorted(candidates,key=lambda m:(m['start'],m['end']))
def child_subject(verb,mentions):
 # Prefer the actual subject/attribute attached to this predicate, not
 # another independent clause's most recent noun.
 subject=[]
 for c in verb.children:
  if c.dep_ in SUBJ:
   m=mention_token(c,mentions)
   if m:subject.append((0,m))
   for descendant in c.subtree:
    m=mention_token(descendant,mentions)
    if m:subject.append((1,m))
 if subject:
  subject.sort(key=lambda x:(x[0],x[1]['start']))
  return subject[0][1]
 return None

def find_source(prep,mentions):
 head=prep.head
 for i,node in enumerate([head,*list(head.ancestors)]):
  m=mention_token(node,mentions)
  if m and not is_inside(prep,m['span']):return m
  if node.pos_ in ('VERB','AUX') or node.dep_ in ('relcl','ROOT'):
   m=child_subject(node,mentions)
   if m:return m
  # Relative clause refers back to an explicit preceding entity: "TV,
  # which is placed on a console." Do not resolve arbitrary pronouns.
  if node.dep_=='relcl':
   m=mention_token(node.head,mentions)
   if m:return m
 return None

def find_targets(prep,mentions):
 subtree=list(prep.subtree)
 candidates=[m for m in mentions
   if m['head'] in subtree and not is_inside(prep,m['span'])]
 candidates.sort(key=lambda m:(m['start'],m['end']))
 return candidates

def clause_text(doc,left,preposition,right):
 start=max(left['span'].start,preposition.sent.start)
 end=min(right['span'].end,preposition.sent.end)
 return doc[start:end].text.strip()[:170]

def normalized_preposition(token):
 root=(token.head.lemma_ or token.head.text).lower()
 name=token.lower_
 composite=COMPOSITES.get((name,root))
 if composite:return composite
 if name=='in':
  nested=[c for c in token.children if c.dep_ in ('pobj','pcomp')]
  for c in nested:
   if c.lower_ in ('front','center','middle','corner'):
    return {'front':'front','center':'center','middle':'middle','corner':'corner'}[c.lower_]
 if name=='on':
  nested=[c for c in token.children if c.dep_=='pobj']
  if nested and nested[0].lower_ in ('side','sides'):return 'side_of'
 return PREPS.get(name)

def infer_relation(doc,prep,mentions):
 kind=normalized_preposition(prep)
 if not kind:return None
 src=find_source(prep,mentions)
 targets=find_targets(prep,mentions)
 # Ancestor relation can point to an intermediate prepositional noun "front"
 # or "top". Only concrete recognized target mentions are permitted.
 target=next((m for m in targets if src is None or m['type']!=src['type']),None)
 # Some spatial expressions use structural room nouns rather than an object.
 structural=[tok for tok in prep.subtree if tok.lower_ in ROOM and
             tok.dep_ in ('pobj','pcomp','dobj','nmod')]
 room_target=structural[0].lower_ if structural else None
 if not src:
  return None
 if target is not None:
  if room_target is not None and room_target in ROOM and not target['span'].start<=structural[0].i<target['span'].end:
   # "against the wall with a lamp": honor wall rather than the later lamp.
   if structural[0].i<target['start']:target=None
 if kind in ('corner','middle','center'):
  return {'kind':'room','type':kind,'a':src['type'],'b':'room',
    'sourceText':clause_text(doc,src,prep,src),'confidence':'parsed_dependency'}
 if target:
  return {'kind':'object','type':kind,'a':src['type'],'b':target['type'],
   'sourceText':clause_text(doc,src,prep,target),
   'confidence':'parsed_dependency'}
 if room_target:
  return {'kind':'room','type':kind,'a':src['type'],'b':room_target,
   'sourceText':doc[max(0,prep.i-5):min(len(doc),prep.i+10)].text,
   'confidence':'parsed_dependency'}
 return None

def verb_relation(token,mentions):
 verb=VERBS.get(token.lemma_.lower())
 if not verb or token.pos_!='VERB':return None
 subj=child_subject(token,mentions)
 targets=[]
 for c in token.children:
  if c.dep_ in ('dobj','obj','pobj','attr','oprd'):
   targets.extend([m for m in mentions if m['head'] in list(c.subtree)])
 if subj and targets:
  target=next((m for m in targets if m['type']!=subj['type']),None)
  if target:return {'kind':'object','type':verb,'a':subj['type'],'b':target['type'],
    'sourceText':token.sent.text[:200],'confidence':'parsed_dependency'}
 return None

def dependency_relations(doc,base):
 matches=mentions_as_tokens(doc,base)
 results=[]
 for tok in doc:
  rel=None
  if tok.dep_ in ('prep','agent','advmod') and (tok.pos_=='ADP' or tok.lower_ in ('next','close','opposite')):
   rel=infer_relation(doc,tok,matches)
  elif tok.pos_=='VERB':
   rel=verb_relation(tok,matches)
  if rel and rel['a']!=rel['b']:
   if not any(x['kind']==rel['kind'] and x['type']==rel['type'] and
      x['a']==rel['a'] and x['b']==rel['b'] for x in results):
    results.append(rel)
 return results

def combine(base,parsed,method='dependency'):
 base={**base}
 if method=='dependency':base['relations']=parsed
 elif method=='union':
  result=base['relations'][:]
  for r in parsed:
   if not any(x['kind']==r['kind'] and x['type']==r['type'] and x['a']==r['a'] and x['b']==r['b'] for x in result):
    result.append(r)
  base['relations']=result
 else:raise ValueError('Unknown comparison')
 base['unresolved']={**base['unresolved'],
   'sourceModel':'spaCy en_core_web_sm 3.8.0 CPU pretrained parser, NOT trained on this SceneEval benchmark',
   'syntaxLimitations':'No implicit relation guarantee, no full reference/coreference resolution, no frame/geometry grounding'}
 return base

def infer_one(text,model,source_id='unknown',method='dependency'):
 base=lexical_interpret(text,source_id)
 doc=model(text)
 proposals=dependency_relations(doc,base)
 return combine(base,proposals,method=method)
if __name__=='__main__':
 m=load_model()
 for text in ['A sofa is placed across from a TV which stands on a console.',
  'A lamp is on top of a nightstand in a bedroom.',
  'Two chairs are next to a wooden dining table.',
  'A bookshelf with two books sits against the wall.',
  'The bed has a lamp beside it, and a sofa behind the table.']:
  x=infer_one(text,m)
  print(text,[(r['type'],r['a'],r['b']) for r in x['relations']])
