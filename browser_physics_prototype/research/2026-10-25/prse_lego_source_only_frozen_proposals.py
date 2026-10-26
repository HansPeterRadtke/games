#!/usr/bin/env python3
"""Prepare source-only LEGO-Bench human-curated instructions with frozen PRSE
lexicon and pre-trained dependency syntax. No LEGO constraints, author labels,
reference scene JSON, objects, asset metadata or oracle geometry are read.
Do not rerun on existing immutable output. Complete source stays private.
"""
import hashlib, importlib.util, json, re
from pathlib import Path
from collections import Counter
import spacy
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'2026-10-24'/'prse_semantic_constraints.py'
RAW=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
DATA=RAW/'lego_full_data_public_human_gold.json'
MODEL=Path('/data/var/games/prse_semantic_research/models/spacy-english-3.8.0/extracted/en_core_web_sm/en_core_web_sm-3.8.0')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def hash_text(text):return hashlib.sha256(text.encode()).hexdigest()
spec=importlib.util.spec_from_file_location('prse_frozen_source_only', BASE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
nlp=spacy.load(MODEL,disable=['ner'])
records=json.loads(DATA.read_text())
assert len(records)==130
# Critical no-gold boundary: ONLY 'instruction' field is ever accessed below.
text_only=[{'id':i,'sourceId':f'lego-{i:03d}','text':record['instruction']}
           for i,record in enumerate(records)]
assert all(40<=len(item['text'])<=6000 for item in text_only)
SCORE=Counter(); result=[]
for item,doc in zip(text_only,nlp.pipe((x['text'] for x in text_only),batch_size=16,n_process=1)):
    parsed=module.interpret(item['text'], item['sourceId'])
    candidates=[]; abstained=[]
    def source_kind(token):
        kinds={m['type'] for m in parsed['mentions']
               if m['quantity']>0 and m['start']<=token.idx and
               token.idx+len(token.text)<=m['end']}
        return sorted(kinds)
    for prep in doc:
        if prep.lower_ not in ('on','atop','upon') or prep.dep_ not in ('prep','agent'):
            continue
        parents=[c for c in prep.children if c.dep_ in ('pobj','pcomp') and
                 c.pos_ in ('NOUN','PROPN')]
        head=prep.head
        if head.pos_ in ('NOUN','PROPN'):
            children=[head]
        elif head.pos_ in ('VERB','AUX'):
            children=[c for c in head.children if c.dep_ in ('nsubj','nsubjpass') and
                      c.pos_ in ('NOUN','PROPN')]
        else:
            children=[]
        if not parents or not children:
            abstained.append({'sourceOffset':prep.idx,'reason':'unresolved_syntax_roles'})
            continue
        for c in children:
            for p in parents:
                kinds_a=source_kind(c);kinds_b=source_kind(p)
                if len(kinds_a)!=1 or len(kinds_b)!=1 or kinds_a[0]==kinds_b[0]:
                    abstained.append({'sourceOffset':prep.idx,'reason':'missing_ambiguous_or_same_lexicon_kind'})
                    continue
                rec={'a':kinds_a[0],'b':kinds_b[0],'kind':'object','type':'on',
                     'sourceCharPositions':[c.idx,p.idx,prep.idx],
                     'sourceGrammar':'frozen_pretrained_spacy_dependency',
                     'sourceHash':hash_text(item['text'])}
                if not any(a['a']==rec['a'] and a['b']==rec['b'] for a in candidates):
                    candidates.append(rec)
    if len(candidates)>64:raise ValueError('Too many source-only relations')
    result.append({'sourceId':item['sourceId'],'sourceIndex':item['id'],
                   'sourceText':item['text'],'sourceHash':hash_text(item['text']),
                   'lexicalProposal':parsed,'pretrainedOn':candidates,'pretrainedAbstentions':abstained})
    SCORE['descriptions']+=1
    SCORE['sourceLexicalKinds']+=len(parsed['quantities'])
    SCORE['sourceOnlyLexicalOnProposals']+=sum(r['kind']=='object' and r['type']=='on'
                                              for r in parsed['relations'])
    SCORE['sourceOnlyPretrainedOnProposals']+=len(candidates)
    SCORE['sourceDescriptionsWithPretrainedOn']+=bool(candidates)
    SCORE['pretrainedOnAbstentions']+=len(abstained)
assert len(result)==130
output=RAW/'lego_source_only_frozen_130_raw_v1.json'
with output.open('x') as f:json.dump({'metadata':{
   'source':'LEGO-Eval/LEGO_Bench public source instructions 130, separate external corpus',
   'rawFullDataSHA256':sha(DATA),'preexistingFrozenSourceLexiconSHA256':sha(BASE),
   'pretrainedSpacyModel':'en_core_web_sm 3.8.0 local CPU pretrained',
   'neverAccessedHumanConstraintsOrReferencesInThisPhase':True,
   'corpusHumanCuratedNotProvenIndividualInstructionsHumanWritten':True},
 'summary':dict(SCORE),'scenes':result},f,indent=2);f.write('\n')
output.chmod(0o600)
print('SOURCE_ONLY_FROZEN',dict(SCORE),'sha256',sha(output),'bytes',output.stat().st_size)
