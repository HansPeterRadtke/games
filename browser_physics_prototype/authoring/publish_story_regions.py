#!/usr/bin/env python3
"""Atomic, non-executable literal pack for importing LLM scene facts in a browser."""
import json,pathlib,os,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/'generated/story-region-bank.json'
TARGET=ROOT/'generated/story-region-bank.js'

def main():
    bank=json.loads(SOURCE.read_text()) if SOURCE.is_file() else {'version':1,'model':'unavailable','scenes':[]}
    if bank.get('version')!=1 or not isinstance(bank.get('scenes'),list) or len(bank['scenes'])>32:raise ValueError('Invalid narrative pack')
    for s in bank['scenes']:
        if not isinstance(s,dict) or not isinstance(s.get('description'),str) or not isinstance(s.get('objects'),list) or not isinstance(s.get('region'),int) or not isinstance(s.get('anchor'),(float,int)):raise ValueError('Invalid scene')
    # JSON is a JavaScript expression; escape U+2028/U+2029 and HTML tag markers.
    literal=json.dumps(bank,ensure_ascii=True,separators=(',',':'))
    output='// Pre-generated, source-tracked local LLM narrative content. No runtime model call.\nexport const storyRegionBank='+literal+';\n'
    temp=TARGET.with_suffix('.js.tmp');temp.write_text(output);os.replace(temp,TARGET)
    print('BROWSER_STORY_BANK',len(bank['scenes']),'scenes',TARGET.stat().st_size,'bytes',TARGET)
if __name__=='__main__':main()
