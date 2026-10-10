#!/usr/bin/env python3
"""Audited known geometry/narrative corrections; never represent them as raw LLM output."""
import json,pathlib,os,datetime
root=pathlib.Path(__file__).resolve().parents[1]
p=root/'generated/story-region-bank.json';bank=json.loads(p.read_text());count=0
corrections={
 'bridge_repaired':('The Split-Stone Arch','An arch-shaped crack divides a mossy boulder beside the old trail. Fresh cart tracks suggest the repaired crossing is used again.','On the stone, a faded mason mark resembles the one carved on the original bridge.','Corrected nonexistent second stream, implausible contact with distant timber and impossible arch shape.'),
 'bridge_unrepaired':('The Split Oak','A lightning-split oak stands beside an overgrown path. No new cart tracks cross the valley since the footbridge failed.','Deep in the bark lies a rusty nail, probably older than the broken crossing.','Corrected roots touching a bridge 20 metres away and stranded travelers appearing across the river.'),
 'mechanism_open':('The Humming Gate','A rusted iron shelter stands on the valley edge. It hums faintly whenever the distant lifting gate rises, although no wires are visible.','The humming grows clearer when the wind changes direction.','Clarified a small shelter/cuboid representation for a previously impossible open iron arch.')
}
for s in bank['scenes']:
 if s['branch'] not in corrections or s.get('reconciliation'):continue
 name,description,clue,reason=corrections[s['branch']]
 s['raw_model_title']=s['title'];s['raw_model_description']=s['description'];s['raw_model_clue']=s['objects'][0]['interaction_clue'];s['title']=name;s['description']=description;s['objects'][0]['description']=description;s['objects'][0]['interaction_clue']=clue;s['reconciliation']={'kind':'independent-spatial-audit','reason':reason,'date':'2026-10-10'};s['source']+=':reviewed';count+=1
q=p.with_suffix('.json.tmp');q.write_text(json.dumps(bank,ensure_ascii=False,indent=2));os.replace(q,p)
print('RECONCILED',count,'out of',len(bank['scenes']),'LLM-authored region scenes; originals preserved in raw_model fields')
