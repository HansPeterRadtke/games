#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, time, random
from pathlib import Path
from typing import Any
import requests
from PIL import Image

SPRITES = [
    {"id":"player","description":"tiny white explorer body with cyan eye and dark outline"},
    {"id":"spark","description":"glowing cyan crystal collectible with bright core"},
    {"id":"void","description":"red purple dangerous orb with dark center and red rim"},
    {"id":"echo","description":"green memory relic rectangle with bright inner glyph"},
]
PALETTE = {"0":[0,0,0,0],"1":[8,10,18,255],"2":[237,245,255,255],"3":[124,249,255,255],"4":[255,77,141,255],"5":[163,255,143,255],"6":[96,67,255,255],"7":[255,214,102,255]}
SCHEMA: dict[str, Any] = {"type":"object","additionalProperties":False,"required":["sprite"],"properties":{"sprite":{"type":"object","additionalProperties":False,"required":["id","rows"],"properties":{"id":{"type":"string","enum":[s["id"] for s in SPRITES]},"rows":{"type":"array","minItems":16,"maxItems":16,"items":{"type":"string"}}}}}}
TEMPLATES = {
"player":["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000012221000000","0000122222100000","0000121112100000","0000012112000000","0000012002000000","0000120002100000","0000100000100000","0000000000000000"],
"spark":["0000000000000000","0000000300000000","0000003330000000","0000033333000000","0000333233300000","0003332223330000","0033322223333000","0333227222333300","0033322223333000","0003332223330000","0000333233300000","0000033333000000","0000003330000000","0000000300000000","0000000000000000","0000000000000000"],
"void":["0000000000000000","0000004440000000","0000444444400000","0004466666440000","0044661116644000","0046611111664000","0446116661164400","0446116661164400","0446116661164400","0046611111664000","0044661116644000","0004466666440000","0000444444400000","0000004440000000","0000000000000000","0000000000000000"],
"echo":["0000000000000000","0000555555550000","0005111111150000","0005155555150000","0005150005150000","0005150775150000","0005150775150000","0005155555150000","0005111111150000","0005155555150000","0005150005150000","0005155555150000","0005111111150000","0000555555550000","0000000000000000","0000000000000000"]
}

def request_sprite(base_url: str, sprite: dict[str, str], seed: int, attempt: int) -> dict[str, Any]:
    prompt = f"Return JSON only. Create visible 16x16 pixel art for sprite id {sprite['id']}: {sprite['description']}. Use exactly 16 rows, exactly 16 digits per row, digits only 0-7. 0 is transparent alpha and must be used only for background. Use many nonzero digits for the object, at least 45 colored pixels. Keep a one pixel transparent border. Do not output a blank sprite."
    payload = {"prompt": prompt, "n_predict": 620, "temperature": 0.05 + attempt*0.05, "top_p": 0.85, "seed": seed + attempt*1000, "json_schema": SCHEMA}
    started = time.monotonic(); r = requests.post(base_url.rstrip()+"/completion", json=payload, timeout=(10,240)); r.raise_for_status(); body=r.json(); wall=time.monotonic()-started
    parsed=json.loads(body.get("content","{}")); return {"body":body,"parsed":parsed,"wall_seconds":round(wall,3)}

def normalize_rows(rows: list[str]) -> tuple[list[str], list[str]]:
    errors=[]; clean=[]
    for i in range(16):
        raw=rows[i] if i < len(rows) else ""; row=''.join(ch for ch in str(raw) if ch in PALETTE)
        if len(row)!=16: errors.append(f"row {i} length {len(row)}")
        clean.append((row+"0"*16)[:16])
    return clean, errors

def nonzero(rows: list[str]) -> int: return sum(1 for row in rows for ch in row if ch != '0')

def render(rows: list[str], out_png: Path, scale: int) -> None:
    img=Image.new("RGBA",(16,16),(0,0,0,0)); px=img.load()
    for y,row in enumerate(rows):
        for x,ch in enumerate(row): px[x,y]=tuple(PALETTE[ch])
    img=img.resize((16*scale,16*scale), Image.Resampling.NEAREST); out_png.parent.mkdir(parents=True,exist_ok=True); img.save(out_png)

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--base-url",default="http://127.0.0.1:14829"); ap.add_argument("--out",default="LLM_Game/generated_sprites"); ap.add_argument("--web-out",default="LLM_Game/web/assets/sprites"); ap.add_argument("--seed",type=int,default=404); args=ap.parse_args()
    out=Path(args.out); web=Path(args.web_out); manifest=[]; llm_success=0
    for idx,s in enumerate(SPRITES):
        chosen=None; attempts=[]
        for attempt in range(3):
            try:
                result=request_sprite(args.base_url,s,args.seed+idx,attempt); parsed=result["parsed"].get("sprite",{}); rows,errors=normalize_rows(parsed.get("rows",[])); nz=nonzero(rows)
                if parsed.get("id")!=s["id"]: errors.append(f"id mismatch {parsed.get('id')}")
                attempts.append({"attempt":attempt,"errors":errors,"nonzero_pixels":nz,"tokens_predicted":result["body"].get("tokens_predicted"),"wall_seconds":result["wall_seconds"]})
                if not errors and nz >= 45: chosen=("llm",rows,result); llm_success += 1; break
            except Exception as e:
                attempts.append({"attempt":attempt,"error":repr(e)})
        if chosen is None:
            rows=TEMPLATES[s["id"]]; chosen=("procedural_fallback",rows,{"body":{},"wall_seconds":0})
        source,rows,result=chosen; png=out/f"{s['id']}.png"; webpng=web/f"{s['id']}.png"; render(rows,png,4); render(rows,webpng,4)
        spec={"id":s["id"],"source":source,"description":s["description"],"rows":rows,"nonzero_pixels":nonzero(rows),"attempts":attempts,"png":str(png),"web_png":str(webpng),"sha256":hashlib.sha256(png.read_bytes()).hexdigest()}
        (out/f"{s['id']}.json").write_text(json.dumps(spec,indent=2,sort_keys=True)+"\n"); manifest.append(spec)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n"); (web/"manifest.json").write_text(json.dumps([{"id":m["id"],"source":m["source"],"nonzero_pixels":m["nonzero_pixels"],"sha256":m["sha256"]} for m in manifest],indent=2,sort_keys=True)+"\n")
    print(json.dumps({"ok":True,"llm_success":llm_success,"sprites":[{"id":m["id"],"source":m["source"],"nonzero_pixels":m["nonzero_pixels"],"png":m["web_png"]} for m in manifest]},indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
