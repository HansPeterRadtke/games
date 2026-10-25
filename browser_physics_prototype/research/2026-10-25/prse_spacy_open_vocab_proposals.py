#!/usr/bin/env python3
"""PRSE exploratory open-vocabulary noun discovery using an OFFICIAL PRETRAINED
spaCy dependency parser on frozen SceneEval source prose only.

NO gold annotations are opened, used for noun vocabulary, rule tuning, count
selection or any other proposal generation. This is a controlled CPU-only
candidate mechanism, NOT a validated object ontology, reliable coreference
resolver, 3D shape generator, multimodal detector or general LLM.

Keep every tentative unknown noun, quantifier clue, and exact source text span
with its uncertainty. Repeated mention != distinct object instance.

Complete original descriptions and per-source predictions stay private on
Nitro. Only source hashes and safe aggregate counts are committed to Games.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json,os,re
from prse_spacy_relation_interpreter import load_model

HERE=Path(__file__).parent
INPUT=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/extracted/en_core_web_sm/en_core_web_sm-3.8.0')
OUT=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-open-noun-discovery')
OUT.mkdir(mode=0o700,parents=True,exist_ok=True)
OUT.chmod(0o700)
assert INPUT.exists() and MODEL.exists()
def sha(p):return sha256(p.read_bytes()).hexdigest()
numbers={'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,
 'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12}
generic={'room','floor','ceiling','wall','space','area','corner','center',
 'side','front','back','middle','view','part','arrangement','layout','design',
 'style','interior','decor','decoration','furniture','item','thing','object',
 'number','group','pair','set','collection','piece','end','edge','top','bottom',
 'home','house','kitchen','bedroom','bathroom','living_room','office','dining_room',
 'scene','color','shade','contrast','mixture','tone','way','sense','effect',
 'surface','background','foreground','theme','feeling','light','lighting',
 'size','room_s','left','right','aspect','kind','type','location','direction',
 'addition','variety','touch','feel','look','flooring','setting','place',
 'position','function','purpose'}
# These are generic logical/scene-location nouns, NOT benchmark annotation
# classes; note that genuinely physical "light" is intentionally missed.
structural={'window','door','stairs','floor','wall','ceiling'}
def norm(s):return re.sub(r'[^a-z0-9]+','_',s.strip().lower()).strip('_')
def quantifier(chunk):
 root=chunk.root
 depend=[x for x in chunk if x.head==root]
 ds=[x.lower_ for x in depend if x.dep_ in ('det','nummod','quantmod') or x.pos_=='NUM']
 if 'no' in ds or 'zero' in ds or any(x.text.lower()=='without' for x in root.ancestors):
  return 0,'explicit_negation'
 for x in depend:
  key=x.lower_.replace(',','')
  if key in numbers:return min(12,numbers[key]),'explicit_numeral'
  if x.like_num:
   try:return min(12,int(x.text)),'explicit_numeral'
   except ValueError:pass
 if root.tag_ in ('NNS','NNPS') or root.morph.get('Number')==['Plur']:
  return 2,'plural_lower_bound_no_coreference'
 if 'a' in ds or 'an' in ds:return 1,'indefinite_singular_mention'
 return 1,'unquantified_singular_lower_bound'
def candidate(chunk,base):
 root=chunk.root
 if root.pos_ not in ('NOUN','PROPN'):return None
 if not root.is_alpha or len(root.text)>32:return None
 compounds=sorted([x for x in chunk if x.head==root and x.dep_=='compound' and
  x.pos_ in ('NOUN','PROPN')],key=lambda x:x.i)
 label=norm('_'.join([x.lemma_ for x in compounds]+[root.lemma_]))
 if not label or len(label)>60 or label in generic or label in structural:return None
 if root.lemma_.lower() in generic:return None
 # A previously recognized noun phrase is retained unchanged. A competing
 # "side table" versus "table" is a proposal, NOT silently adjudicated.
 m=next((m for m in base['mentions'] if
   m['start']<=root.idx and m['end']>=root.idx+len(root.text)),None)
 if m and norm(m['type'])==label:return None
 amount,reason=quantifier(chunk)
 if amount==0:return {'type':label,'count':0,'quantityBasis':'explicit_negation',
   'sourceOffsets':[chunk.start_char,chunk.end_char],'sourceText':chunk.text,
   'rootLemma':root.lemma_,'compounds':[x.lemma_ for x in compounds],
   'previousLexiconOverlap':m['type'] if m else None,
   'materialize':False,'reason':'Absent source object never materialized'}
 return {'type':label,'count':amount,'quantityBasis':reason,
  'sourceOffsets':[chunk.start_char,chunk.end_char],'sourceText':chunk.text,
  'rootLemma':root.lemma_,'compounds':[x.lemma_ for x in compounds],
  'previousLexiconOverlap':m['type'] if m else None,
  'materialize':True,
  'reason':'PRETRAINED_GRAMMATICAL_NOUN_CANDIDATE_UNKNOWN_COREf_AND_3D_DIMENSIONS'}

frozen=json.loads(INPUT.read_text())['proposalsAll500']
assert len(frozen)==500
nlp=load_model()
records=[]
for doc,p in zip(nlp.pipe((x['text'] for x in frozen),batch_size=32,n_process=1),frozen):
 found=[]
 for chunk in doc.noun_chunks:
  c=candidate(chunk,p)
  if c:found.append(c)
 # Repeated noun mentions are NOT added together because they may refer to
 # one prior object. Use max local mention count as a scene-level lower bound;
 # completely exact instance counts require independent discourse resolution.
 by={}
 for c in found:
  typ=c['type']
  if typ not in by:by[typ]={'type':typ,'count':c['count'],
   'basis':c['quantityBasis'],'mentionCount':0,'sourceSpans':[],
   'overlapsKnownType':[],
   'confidence':'pretrained_syntax_candidate_not_verified_source_entity'}
  d=by[typ]
  d['mentionCount']+=1
  d['count']=max(d['count'],c['count'])
  d['sourceSpans'].append(c['sourceOffsets'])
  if c['previousLexiconOverlap']:d['overlapsKnownType'].append(c['previousLexiconOverlap'])
 pos=[q for q in by.values() if q['count']>0]
 selected=pos[:24] # bounded full 3D candidate budget, preserve excluded
 record={'id':p['sourceId'],'sourceText':p['text'],'baseTypes':list(p['quantities'].keys()),
  'candidates':found,'candidateTypes':list(by.values()),'boundedNewTypes':selected,
  'typesOverflow':len(pos)-len(selected) if len(pos)>len(selected) else 0,
  'originalParserQuantities':p['quantities']}
 records.append(record)
assert len(records)==500
summary={
 'input500Sources':len(records),
 'sourceSHA256':sha(INPUT),
 'modelVersion':nlp.meta['version'],
 'spaCyPretrainedModelName':nlp.meta['name'],
 'newNounTokenMentionCandidates':sum(len(x['candidates']) for x in records),
 'distinctExtraSourceTypeCandidates':sum(len(x['candidateTypes']) for x in records),
 'boundedPhysicallyEligibleExtraTypes':sum(len(x['boundedNewTypes']) for x in records),
 'extraTypeCountOverflow':sum(x['typesOverflow'] for x in records),
 'sourceScenesWithAdditionalCandidate':sum(bool(x['boundedNewTypes']) for x in records),
 'compoundCandidateMentions':sum(bool(c['compounds']) for x in records for c in x['candidates']),
 'overlappingEarlierTypeMentions':sum(bool(c['previousLexiconOverlap']) for x in records for c in x['candidates']),
 'sourceScenesWithPotentialUnrecognizedNewNouns':sum(any(c['previousLexiconOverlap'] is None for c in x['candidates']) for x in records),
 'goldAnnotationsNotReadOrImported':True,
 'existingBaselineNotMutated':True}
path=OUT/'prse_spacy_open_vocab_500_proposals_raw_v1.json'
with path.open('x') as f:json.dump({'meta':{
 'experimentalMethod':'spaCy noun chunks with generic grammatical compounds and conservative max local source numeral; source spans with no external gold',
 'model':'en_core_web_sm 3.8.0 pretrained dependency parser CPU, not generative LLM',
 'limitations':'Generic noun candidates can be abstractions and incorrect type names; no coreference, visual/physical asset types, scale or meaning entailment'},'summary':summary,'records':records},f,indent=2);f.write('\n')
path.chmod(0o600)
public=HERE/'prse_spacy_open_vocab_proposal_500_aggregate_v1.json'
with public.open('x') as f:json.dump({'meta':{
 'frozenSourceSHA256':sha(INPUT),
 'model':'Official pretrained spaCy en_core_web_sm 3.8.0',
 'data':'SceneEval v250610 ORIGINAL TEXT ONLY, no official annotations',
 'independentlyValidatedSourceMeaning':False,
 'notA3DModelAndNotCoreferenceSolver':True,
 'ownerPrivateRawSHA256':sha(path)},'summary':summary},f,indent=2);f.write('\n')
print('FROZEN PRETRAINED GRAMMAR CANDIDATES',json.dumps(summary))
