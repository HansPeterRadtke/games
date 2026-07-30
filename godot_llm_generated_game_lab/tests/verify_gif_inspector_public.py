#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,urllib.error,urllib.request
from pathlib import Path
from PIL import Image,ImageSequence
RETIRED=['flag-in-the-wind.gif','chandelier.gif','cookies.gif','curtains.gif','dining-table.gif','floor-carpet.gif','kitchen-door.gif','mom.gif','player.gif','player--idle.gif','player--walk.gif','player--player_attack.gif','player--player_interact.gif','player--player_use.gif','sideboard.gif','wall-finish.gif']
def fetch(url):
 req=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'articulated-walk-verifier/1'})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read(),{k.lower():v for k,v in r.headers.items()},r.status
def expect_404(url):
 try:fetch(url)
 except urllib.error.HTTPError as e:assert e.code==404,(url,e.code)
 else:raise AssertionError(f'retired GIF still public: {url}')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base',default='https://nitro.jonnyontherun.org/llm_game/gif_inspector/');ap.add_argument('--local',type=Path,default=Path(__file__).resolve().parents[1]/'web/gif_inspector');a=ap.parse_args();base=a.base.rstrip('/')+'/'
 page,h,status=fetch(base);assert status==200 and 'text/html' in h.get('content-type','');html=page.decode();assert 'Player Walk — Articulated BVH Test' in html and 'Exactly one looping GIF' in html and 'No model generates these frames' in html
 for forbidden in ['.wasm','.pck','<script','index.js','startgame(','godotready','mimicmotion','nonlooping']:assert forbidden not in html.lower(),forbidden
 raw,h,status=fetch(base+'manifest.json');assert status==200 and 'application/json' in h.get('content-type','');public=json.loads(raw);local=json.loads((a.local/'manifest.json').read_text());assert public==local
 assert public['count']==1 and public['looping'] is True and public['frame_generation_model_used'] is False;item=public['gifs'][0];assert item['slug']=='player-walk' and item['looping'] is True
 payload,h,status=fetch(base+item['public_path']);assert status==200 and 'image/gif' in h.get('content-type','');assert len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'] and payload==(a.local/item['public_path']).read_bytes()
 tmp=Path('/tmp/verify-articulated-player-walk.gif');tmp.write_bytes(payload)
 with Image.open(tmp) as im:assert im.size==(512,768) and len(list(ImageSequence.Iterator(im)))==32 and im.info.get('duration')==50 and im.info.get('loop')==0
 tmp.unlink(missing_ok=True)
 for retired in RETIRED:expect_404(base+'gifs/'+retired)
 print(json.dumps({'ok':True,'base':base,'count':1,'gif':item['public_path'],'sha256':item['sha256'],'loop':0,'retired_404':len(RETIRED)},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
