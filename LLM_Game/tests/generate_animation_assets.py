#!/usr/bin/env python3
from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from typing import Any
import requests
from PIL import Image

BASE='http://127.0.0.1:14829'
WEB=Path('/data/src/github/games/LLM_Game/web/assets/animations')
GEN=Path('/data/src/github/games/LLM_Game/generated_sprites')
WEB.mkdir(parents=True, exist_ok=True); GEN.mkdir(parents=True, exist_ok=True)
PALETTE={"0":(0,0,0,0),"1":(8,10,18,255),"2":(237,245,255,255),"3":(124,249,255,255),"4":(255,77,141,255),"5":(163,255,143,255),"6":(96,67,255,255),"7":(255,214,102,255)}
SCHEMA: dict[str, Any] = {"type":"object","additionalProperties":False,"required":["animations"],"properties":{"animations":{"type":"array","minItems":2,"maxItems":2,"items":{"type":"object","additionalProperties":False,"required":["id","frames"],"properties":{"id":{"type":"string","enum":["player_idle","player_walk"]},"frames":{"type":"array","minItems":2,"maxItems":4,"items":{"type":"object","additionalProperties":False,"required":["rows"],"properties":{"rows":{"type":"array","minItems":16,"maxItems":16,"items":{"type":"string","pattern":"^[0-7]{16}$"}}}}}}}}}}
FALLBACK={
"player_idle":[
["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000012221000000","0000122222100000","0000121112100000","0000012112000000","0000012002000000","0000120002100000","0000100000100000","0000000000000000"],
["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000002220000000","0000012221000000","0000121112100000","0000012112000000","0000012002000000","0000012002100000","0000100000000000","0000000000000000"]],
"player_walk":[
["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000012221000000","0000122222100000","0000121112100000","0001212112000000","0000102002000000","0000100002100000","0001000000100000","0000000000000000"],
["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000002220000000","0000012221000000","0000121112100000","0000012112000000","0000012002000000","0000120002100000","0000100000100000","0000000000000000"],
["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000012221000000","0000122222100000","0000121112100000","0000012112120000","0000012002010000","0000120000100000","0000100000010000","0000000000000000"],
["0000000000000000","0000000110000000","0000001221000000","0000012222100000","0000012322100000","0000012222100000","0000001221000000","0000001110000000","0000002220000000","0000012221000000","0000121112100000","0000012112000000","0000012002000000","0000120002100000","0000100000100000","0000000000000000"]]
}
OBJECT_ANIMS={
"spark_spin":[
["0000000000000000","0000000300000000","0000003330000000","0000033333000000","0000333233300000","0003332223330000","0033322223333000","0333227222333300","0033322223333000","0003332223330000","0000333233300000","0000033333000000","0000003330000000","0000000300000000","0000000000000000","0000000000000000"],
["0000000000000000","0000000300000000","0000033330000000","0000332233000000","0003322223300000","0033227222330000","0332222222233000","0033222222330000","0003322223300000","0000332233000000","0000033330000000","0000000300000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000"],
["0000000000000000","0000000000000000","0000003030000000","0000033333000000","0000332223300000","0003322722330000","0033222222333000","0332222222223300","0033222222333000","0003322722330000","0000332223300000","0000033333000000","0000003030000000","0000000000000000","0000000000000000","0000000000000000"]],
"void_pulse":[
["0000000000000000","0000004440000000","0000444444400000","0004466666440000","0044661116644000","0046611111664000","0446116661164400","0446116661164400","0446116661164400","0046611111664000","0044661116644000","0004466666440000","0000444444400000","0000004440000000","0000000000000000","0000000000000000"],
["0000004444000000","0000444444440000","0004466666640000","0044661111664000","0446611111664400","0446116661164400","4461166666116440","4461166666116440","4461166666116440","0446116661164400","0446611111664400","0044661111664000","0004466666640000","0000444444440000","0000004444000000","0000000000000000"]],
"gate_shimmer":[
["0000000000000000","0000066666600000","0000663333660000","0006630003660000","0066300000366000","0063000770036000","0063007770036000","0063007770036000","0063007770036000","0063000770036000","0066300000366000","0006630003660000","0000663333660000","0000066666600000","0000000000000000","0000000000000000"],
["0000000000000000","0000033333300000","0000336666330000","0003360006330000","0033600000633000","0036000770063000","0036007770063000","0036007770063000","0036007770063000","0036000770063000","0033600000633000","0003360006330000","0000336666330000","0000033333300000","0000000000000000","0000000000000000"]]
}

def call_llm() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    prompt=("Return JSON only. Create pixel animation data. Need exactly two animations: player_idle with 2 frames, player_walk with 4 frames. Each frame is 16 rows, each row exactly 16 digits 0-7. 0 is transparent. Use many nonzero pixels, visible body, tiny white explorer with cyan eye, moving legs in walk frames. Do not output blank frames.")
    payload={"prompt":prompt,"n_predict":1800,"temperature":0.05,"top_p":0.85,"seed":606,"json_schema":SCHEMA}
    start=time.monotonic()
    try:
        r=requests.post(BASE+'/completion', json=payload, timeout=(10,300)); r.raise_for_status(); body=r.json(); wall=round(time.monotonic()-start,3)
        parsed=json.loads(body.get('content','{}'))
        return parsed,{"ok":True,"wall_seconds":wall,"tokens_predicted":body.get('tokens_predicted')}
    except Exception as e:
        return None,{"ok":False,"error":repr(e),"wall_seconds":round(time.monotonic()-start,3)}

def validate(rows: list[str]) -> list[str]:
    errors=[]
    if len(rows)!=16: errors.append(f'rows {len(rows)}')
    for i,row in enumerate(rows[:16]):
        if not isinstance(row,str) or len(row)!=16 or any(ch not in PALETTE for ch in row): errors.append(f'row {i} invalid')
    if sum(1 for row in rows for ch in row if ch!='0') < 35: errors.append('too few opaque pixels')
    return errors

def frame_image(rows: list[str], scale=4) -> Image.Image:
    img=Image.new('RGBA',(16,16),(0,0,0,0)); px=img.load()
    for y,row in enumerate(rows):
        for x,ch in enumerate(row): px[x,y]=PALETTE[ch]
    return img.resize((16*scale,16*scale), Image.Resampling.NEAREST)

def save_anim(name: str, frames: list[list[str]], source: str) -> dict[str, Any]:
    imgs=[frame_image(rows,4) for rows in frames]
    gif=WEB/f'{name}.gif'; sheet=WEB/f'{name}.png'; gen_gif=GEN/f'{name}.gif'; gen_sheet=GEN/f'{name}.png'
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=140, loop=0, disposal=2, transparency=0)
    imgs[0].save(gen_gif, save_all=True, append_images=imgs[1:], duration=140, loop=0, disposal=2, transparency=0)
    sheet_img=Image.new('RGBA',(64*len(imgs),64),(0,0,0,0))
    for i,img in enumerate(imgs): sheet_img.paste(img,(64*i,0),img)
    sheet_img.save(sheet); sheet_img.save(gen_sheet)
    opaque=[sum(1 for v in img.getchannel('A').getdata() if v>0) for img in imgs]
    return {"id":name,"source":source,"frames":len(frames),"frame_size":[64,64],"sheet_size":list(sheet_img.size),"opaque_pixels_per_frame":opaque,"gif_sha256":hashlib.sha256(gif.read_bytes()).hexdigest(),"sheet_sha256":hashlib.sha256(sheet.read_bytes()).hexdigest()}

def main():
    parsed,llm=call_llm(); manifest=[]; source='fallback_after_llm_validation'
    anims={k:v for k,v in FALLBACK.items()}
    llm_errors=[]
    if parsed and isinstance(parsed.get('animations'), list):
        got={}
        for anim in parsed['animations']:
            aid=anim.get('id'); frames=[f.get('rows',[]) for f in anim.get('frames',[])]
            errs=[]
            if aid=='player_idle' and len(frames)!=2: errs.append(f'idle frames {len(frames)}')
            if aid=='player_walk' and len(frames)!=4: errs.append(f'walk frames {len(frames)}')
            for fi,rows in enumerate(frames): errs += [f'{aid} frame {fi}: {e}' for e in validate(rows)]
            if errs: llm_errors += errs
            elif aid in ('player_idle','player_walk'): got[aid]=frames
        if set(got)=={'player_idle','player_walk'}:
            anims=got; source='llm_validated'
    else:
        llm_errors.append('no usable parsed animations')
    for name,frames in anims.items(): manifest.append(save_anim(name,frames,source))
    for name,frames in OBJECT_ANIMS.items(): manifest.append(save_anim(name,frames,'handmade_test_animation'))
    result={"ok":True,"llm":llm,"llm_errors":llm_errors,"player_animation_source":source,"assets":manifest}
    (WEB/'animation_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    (GEN/'animation_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    (Path('/data/src/github/games/LLM_Game/results')/'animation_test_20260705.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({"ok":True,"player_animation_source":source,"llm":llm,"llm_errors":llm_errors[:8],"assets":[{"id":a['id'],"frames":a['frames'],"frame_size":a['frame_size'],"sheet_size":a['sheet_size']} for a in manifest]},indent=2))
if __name__=='__main__': main()
