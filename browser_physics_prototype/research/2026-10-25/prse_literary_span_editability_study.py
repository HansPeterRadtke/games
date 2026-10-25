#!/usr/bin/env python3
"""Audit exact literary source-span editability of PREVIOUSLY FROZEN relation
proposals, separately from their physical validity.

This does NOT rewrite any third-party text or pass external annotation labels
into any interpreter. A sourceText snippet being a substring is NOT enough to
make it a safe grammar/meaning-preserving replacement. Measure unique full
sentence boundaries, ambiguity, quotation/conditional/negation scope, and
multi-relation sentences before proposing an automated literary patch.

Only aggregate counts and hashes go to public Games Git; original descriptions
and per-span excerpts remain owner-private in Nitro research storage.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter,defaultdict
import json,re,stat
ROOT=Path(__file__).parent
PRIVATE=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-literary-revision')
FROZEN=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints/prse_semantic_constraints_eval_all500_v3.json')
SYNTAX=Path('/data/var/games/prse_semantic_research/runs/2026-10-25-syntax-model/prse_spacy_sceneeval_500_union_v1.json')
PRIVATE.mkdir(parents=True,exist_ok=True,mode=0o700)
def hash(path):return sha256(path.read_bytes()).hexdigest()
def row_source_sentences(text):
 # Deliberately a conservative naive segmentation; abbreviation, dotted
 # numbers and dialogue quotes are potential failures, not silently trusted.
 return [x.strip() for x in re.split(r'(?<=[.!?])\s+',text.strip()) if x.strip()]
def candidate_positions(text,snippet):
 result=[]
 if not snippet:return result
 start=0
 while True:
  x=text.find(snippet,start)
  if x<0:break
  result.append((x,x+len(snippet)))
  start=x+1
 return result
def unsafe_context(snippet):
 return bool(re.search(r'\b(if|unless|when|might|perhaps|possibly|could|would|should|not|never|without|no)\b|["“”‘’]',snippet,re.I))
summary={}
for method,file in [('deterministic',FROZEN),('union',SYNTAX)]:
 props=json.loads(file.read_text())['proposalsAll500']
 assert len(props)==500
 raw=[]
 metrics=Counter()
 split_metrics={s:Counter() for s in ('human100','assisted400')}
 for i,p in enumerate(props):
  text=p['text']
  sentences=row_source_sentences(text)
  sources=p['relations']
  method_group='human100' if i<100 else 'assisted400'
  for r in sources:
   snippet=r.get('sourceText') or ''
   trimmed=snippet.strip()
   places=candidate_positions(text,trimmed)
   unique=len(places)==1
   whole=unique and trimmed in sentences
   # Count all source relations whose exact matching string appears in the
   # same textual sentence, to avoid replacing one sentence that expresses
   # more than one independent physical relation.
   nested=[rr for rr in sources if whole and rr.get('sourceText','').strip()==trimmed]
   standalone=whole and len(nested)==1
   one_per_type=(sum(m['type']==r['a'] and m['quantity']>0 for m in p['mentions'])==1
                 and sum(m['type']==r.get('b') and m['quantity']>0 for m in p['mentions'])==1)
   flags={'sourceStringFound':bool(places),'uniqueSubstring':unique,
    'exactFullSentence':whole,'onlyOneRelInFullSentence':standalone,
    'uniqueSourceAndTargetMentions':one_per_type,
    'conditionalNegatedOrQuotedSpan':unsafe_context(trimmed),
    'potentialControlledSentenceCandidate':bool(standalone and one_per_type and not unsafe_context(trimmed)
       and r['kind']=='object')}
   for k,v in flags.items():
    if v:metrics[k]+=1;split_metrics[method_group][k]+=1
   metrics['totalRelations']+=1;split_metrics[method_group]['totalRelations']+=1
   if not trimmed:metrics['emptySnippet']+=1;split_metrics[method_group]['emptySnippet']+=1
   raw.append({'sourceId':i,'relationKind':r['kind'],'relationType':r['type'],
      'sourceString':trimmed,'sourceSpanOffsets':places,
      'originalDescription':text,'flags':flags})
 report={k:int(v) for k,v in metrics.items()}
 report['sceneCount']=500
 report['sourceSHA256']=hash(file)
 report['bySourceGroup']={k:dict(v) for k,v in split_metrics.items()}
 path=PRIVATE/f'prse_source_span_editability_{method}_500_raw_v1.json'
 with path.open('x') as f:json.dump({'metadata':{
  'parser':method,'frozenProposalSHA256':hash(file),
  'method':'Conservative literal-sentence source span editability, NOT a grammar proof',
  'noGoldAnnotationsRead':True},'report':report,'records':raw},f,indent=2);f.write('\n')
 path.chmod(0o600)
 summary[method]={**report,'privateFileSHA256':hash(path),'privateFile':str(path)}
 print(method,'relations',report['totalRelations'],'substringMatched',
  report.get('sourceStringFound',0),'fullSentence',
  report.get('exactFullSentence',0),'unambiguousControlledCandidates',
  report.get('potentialControlledSentenceCandidate',0))
out=ROOT/'prse_literary_source_span_editability_aggregate_v1.json'
with out.open('x') as f:json.dump({'metadata':{
 'source':'Official SceneEval-500 external descriptions, frozen deterministic and CPU syntax-union proposals',
 'noRewritingPerformed':True,'sourceGoldNotRead':True,
 'limit':'Literal split into sentences and unique substring are necessary but not sufficient for correct literary editing',
 'meaning':'Unsafe spans explain why a current physically correct fact cannot simply replace arbitrary fragments of historical source prose'},
 'variants':summary},f,indent=2);f.write('\n')
