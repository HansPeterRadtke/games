#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,urllib.error,urllib.request
from pathlib import Path
from PIL import Image,ImageSequence
RETIRED=['flag-in-the-wind.gif','chandelier.gif','cookies.gif','curtains.gif','dining-table.gif','floor-carpet.gif','kitchen-door.gif','mom.gif','player.gif','player--idle.gif','player--walk.gif','player--player_attack.gif','player--player_interact.gif','player--player_use.gif','sideboard.gif','wall-finish.gif']
def fetch(url):
    request=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'player-walk-verifier/1'})
    with urllib.request.urlopen(request,timeout=45) as response:return response.read(),{k.lower():v for k,v in response.headers.items()},response.status
def expect_404(url):
    try:fetch(url)
    except urllib.error.HTTPError as exc:assert exc.code==404,(url,exc.code)
    else:raise AssertionError(f'retired GIF still public: {url}')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='https://nitro.jonnyontherun.org/llm_game/gif_inspector/');parser.add_argument('--local',type=Path,default=Path(__file__).resolve().parents[1]/'web/gif_inspector');args=parser.parse_args();base=args.base.rstrip('/')+'/'
    html_bytes,headers,status=fetch(base);assert status==200 and 'text/html' in headers.get('content-type','');html=html_bytes.decode()
    assert 'Player Walk — Single GIF Test' in html and 'Exactly one GIF' in html and 'No image-generation or video model' in html
    for forbidden in ['.wasm','.pck','<script','index.js','startgame(','godotready','flag-in-the-wind.gif','player.gif','mom.gif']:assert forbidden not in html.lower(),forbidden
    manifest_bytes,headers,status=fetch(base+'manifest.json');assert status==200 and 'application/json' in headers.get('content-type','');public=json.loads(manifest_bytes);local=json.loads((args.local/'manifest.json').read_text());assert public==local
    assert public['count']==1 and len(public['gifs'])==1;item=public['gifs'][0];assert item['slug']=='player-walk'
    payload,headers,status=fetch(base+item['public_path']);assert status==200 and 'image/gif' in headers.get('content-type','');assert len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'] and payload==(args.local/item['public_path']).read_bytes()
    temp=Path('/tmp/verify-player-walk.gif');temp.write_bytes(payload)
    with Image.open(temp) as image:assert image.size==(320,640) and len(list(ImageSequence.Iterator(image)))==32 and image.info.get('duration')==60 and image.info.get('loop')==0
    temp.unlink(missing_ok=True)
    for retired in RETIRED:expect_404(base+'gifs/'+retired)
    print(json.dumps({'ok':True,'base':base,'count':1,'gif':item['public_path'],'sha256':item['sha256'],'retired_404':len(RETIRED)},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
