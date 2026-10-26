#!/usr/bin/env python3
"""SOURCE-ONLY frozen external Nr3D one-per-independent-ScanNet-scene cohort.
Allowed source inputs: index, scan_id, utterance ONLY. CSV target_id, target
instance_type, entity 3D ID human labels and all gold fields remain unread by
this experiment. Predictions are frozen before independent scorer opens gold.
"""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import csv,importlib.util,re,json,sys,time
import spacy

ROOT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-nr3d-independent-r7')
SOURCE=ROOT/'ScanEnts3D_Nr3D_official_raw.csv'
PRE=ROOT/'PREREG_ORIGINAL_FROZEN_BEFORE_GOLD.md'
PROG=Path(__file__).resolve().parent
OLD=PROG.parent/'2026-10-24/prse_semantic_constraints.py'
MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/extracted/en_core_web_sm/en_core_web_sm-3.8.0')
def dig(p):return sha256(p.read_bytes()).hexdigest()
def digest_text(s):return sha256(s.encode('utf-8')).hexdigest()
assert dig(SOURCE)=='f6b437e2bfc15c69c2b497c755e9a5b42eec110dccc25deb29594e3734a31f5b'
assert dig(PRE)=='688fc6d8199b30617a481460386de87a329f8ceeea1f255d2774b7416d06076f'
spec=importlib.util.spec_from_file_location('old_frozen_prse_parser_crossgenre',OLD)
parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
nlp=spacy.load(MODEL,disable=['ner'])
def canon(s):
 s=re.sub(r'[^a-z0-9]+','_',s.casefold()).strip('_')
 return parser.canon(s)
# No dataset-specific kinds or ontology labels are added to PRSE.
GENERIC={'side','right','left','end','corner','back','front','area','room','scene',
         'top','bottom','middle','one','thing','object','it','part','person','way',
         'edge','place','floor','ceiling','wall','direction','distance','angle',
         'view','background','foreground','center','centre','rest','other','another',
         'group','set','pair','row','line','bit','piece','kind','type'}
def choose_baseline(t):
 ms=[m for m in parser.mentions(t) if parser.quantify(t,m)[0]>0]
 ms=[m for m in ms if canon(m['type']) not in GENERIC]
 return None if not ms else {'kind':canon(ms[0]['type']),
  'start':ms[0]['start'],'end':ms[0]['end'],'proof':'previously_frozen_source_lexicon_first_nonnegated_physical_kind'}
def choose_open(doc,baseline):
 for np in doc.noun_chunks:
  root=np.root
  if root.pos_ not in ('NOUN','PROPN'):continue
  lemma=canon(root.lemma_)
  if lemma in GENERIC or not lemma:continue
  if any(t.dep_=='neg' for t in root.children):continue
  if not re.fullmatch(r'[a-z][a-z0-9_]{1,45}',lemma):continue
  label=lemma
  # Exact pre-existing lexical source span and ontology mapping has higher
  # priority only when grammatical noun head overlaps that source span.
  ms=[m for m in parser.mentions(doc.text)
      if m['start']<=root.idx<=(m['end']-len(root.text)) and
        parser.quantify(doc.text,m)[0]>0]
  if ms:
   ms.sort(key=lambda x:(-(x['end']-x['start']),x['start']))
   label=canon(ms[0]['type'])
  return {'kind':label,'start':root.idx,'end':root.idx+len(root.text),
          'proof':'pretrained_general_spacy_first_concrete_nominal_head'}
 return None
def source_relation(doc):
# Conservative directed top support grammar. A distinct noun support must
# exist in the same human source; reject "on the left/right/side".
 relations=[]
 for preposition in doc:
  if preposition.lower_ not in ('on','atop','upon') or preposition.dep_ not in ('prep','agent'):continue
  head=preposition.head
  subj=[head] if head.pos_ in ('NOUN','PROPN') else [
   x for x in head.children if x.pos_ in ('NOUN','PROPN') and x.dep_ in ('nsubj','nsubjpass')]
  target=[x for x in preposition.children if x.pos_ in ('NOUN','PROPN') and x.dep_ in ('pobj','pcomp')]
  if not subj or not target:continue
  a,b=subj[0],target[0]
  if a.lemma_.lower() in GENERIC or b.lemma_.lower() in GENERIC:continue
  if any(x.dep_=='neg' for x in preposition.head.children):continue
  roles=[]
  for t in (a,b):
   cand=[m for m in parser.mentions(doc.text)
         if m['start']<=t.idx and t.idx+len(t.text)<=m['end']
         and parser.quantify(doc.text,m)[0]>0]
   if cand:
    cand.sort(key=lambda v:(-(v['end']-v['start']),v['start']))
    roles.append(canon(cand[0]['type']))
   else:roles.append(canon(t.lemma_))
  if roles[0]!=roles[1]:
   relations.append({'child':roles[0],'parent':roles[1],
     'prepositionOffset':preposition.idx,
     'childRootOffset':a.idx,'parentRootOffset':b.idx,
     'sourceOnlyPretrained':True,
     'trueSourceSupportNotEstablished':True})
 return relations

# The source-only extraction whitelist is enforced by indexing only three
# approved fields, not extracting the full DictReader record (which would
# materialize target and 3D gold labels).
by_scan={}
counter=Counter()
with SOURCE.open(newline='',encoding='utf-8') as f:
 reader=csv.reader(f);header=next(reader)
 pos={col:header.index(col) for col in ('index','scan_id','utterance')}
 for r in reader:
  counter['allRows']+=1
  ix,scan,text=(r[pos[c]] for c in ('index','scan_id','utterance'))
  assert ix.isdigit() and scan.startswith('scene') and 0<len(text)<3000
  rank=digest_text(scan+'|'+ix+'|'+text)
  if scan not in by_scan or rank<by_scan[scan][0]:
   by_scan[scan]=(rank,{'datasetIndex':int(ix),'scanId':scan,
                           'text':text,'sourceHash':digest_text(text)})
assert counter['allRows']==37842 and len(by_scan)==641
by_scene=sorted(by_scan,key=lambda s:digest_text('PRSE-r7-external-scene|'+s))
chosen=[by_scan[scene][1] for scene in by_scene[:480]]
assert len(chosen)==480 and len({x['scanId'] for x in chosen})==480
# Cohort freeze is exclusive before ANY annotations are opened.
cohort=ROOT/'nr3d_one_per_scene_480_sourceonly_frozen_v1.json'
with cohort.open('x') as f:
 json.dump({'metadata':{'officialNr3dScanEntsRawSHA256':dig(SOURCE),
 'preRegistrationSHA256':dig(PRE),
 'sourceColumnsRead':['index','scan_id','utterance'],
 'sourceColumnsDeliberatelyNotRead':['correct_guess','instance_type','target_id','entities','stimulus_id'],
 'allSourceRows':counter['allRows'],'distinctSourceScenes':len(by_scan),'selectedIndependentScenes':480},
 'sourceCohort':chosen},f,indent=2)
 f.write('\n')
cohort.chmod(0o600)
start=time.perf_counter()
results=[];counts=Counter()
for row,doc in zip(chosen,nlp.pipe((x['text'] for x in chosen),batch_size=32,n_process=1)):
 assert doc.text==row['text']
 literal=choose_baseline(doc.text)
 trained=choose_open(doc,literal)
 relations=source_relation(doc)
 # Specific idiom negative controls: count only literal original source
 # phrases, and relations overlapping exact on-keyword.
 negative=list(re.finditer(r'\b(?:on\s+(?:the\s+)?(?:left|right|side|front|back|end|edge)\b|not\s+on\b)',doc.text,re.I))
 bad=[]
 for rel in relations:
  at=rel['prepositionOffset']
  if any(m.start()<=at<m.end() for m in negative):bad.append(rel)
 result={'datasetIndex':row['datasetIndex'],'scanId':row['scanId'],'sourceHash':row['sourceHash'],
 'text':row['text'],'baselineTargetType':literal,'sourceOnlyPretrainedTargetType':trained,
 'sourceOnlyOnTopProposal':relations,'explicitNaturalNontopCases':[(m.start(),m.end(),m.group(0)) for m in negative],
 'badSupportProposalOverlap':bad}
 results.append(result)
 counts['cases']+=1
 counts['baselinePredictions']+=literal is not None
 counts['pretrainedPredictions']+=trained is not None
 counts['sourceOnlyOnProposals']+=len(relations)
 counts['negativeIdioms']+=len(negative)
 counts['negativeCases']+=bool(negative)
 counts['overlapErrors']+=len(bad)
assert len(results)==480
raw=ROOT/'nr3d_source_only_predictions_480_frozen_v1.json'
with raw.open('x') as f:
 json.dump({'metadata':{'preregSHA256':dig(PRE),'sourceOnlyFrozenCohortSHA256':dig(cohort),
 'noHumanGroundTruthFieldsOpened':True,'previouslyFrozenLexiconSHA256':dig(OLD),
 'pretrainedGeneralSpacy':'en_core_web_sm 3.8, no Nr3D training',
 'ScanNetPointCloud3DGeometryUnavailable':True,
 'sourceModelNoTargetObjectIDs':True},'summary':dict(counts),'records':results,
 'parserWallSeconds':round(time.perf_counter()-start,3)},f,indent=2)
 f.write('\n')
raw.chmod(0o600)
print('FROZEN_NR3D_SOURCE_ONLY_TRANSFER',dict(counts),
 'predictionSHA256',dig(raw),'cohortSHA256',dig(cohort),
 'elapsedSeconds',round(time.perf_counter()-start,3),flush=True)
