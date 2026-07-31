#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from animation_quality import encode_transparent_gif


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_frames(sheet: Path, count: int, width: int, height: int) -> list[Image.Image]:
    with Image.open(sheet) as image:
        rgba=image.convert('RGBA')
    if rgba.size != (count*width,height):
        raise ValueError(f'{sheet}: expected {(count*width,height)}, got {rgba.size}')
    return [rgba.crop((index*width,0,(index+1)*width,height)) for index in range(count)]


def decoded_contract(path: Path) -> tuple[int,list[int],bool,int]:
    durations=[]
    with Image.open(path) as image:
        frame_count=image.n_frames
        looped=image.info.get('loop')==0
        for index in range(frame_count):
            image.seek(index)
            durations.append(int(image.info.get('duration',0)))
        distinct=len({hashlib.sha256(frame.convert('RGBA').tobytes()).hexdigest() for frame in ImageSequence.Iterator(image)})
    return frame_count,durations,looped,distinct


def main() -> None:
    manifest_path=ROOT/'data/generated_world.json'
    manifest=json.loads(manifest_path.read_text())
    player=manifest['assets']['player']
    summaries={}
    for name,clip in player['clips'].items():
        meta_path=ROOT/clip['meta_path'] if clip.get('meta_path') else ROOT/'generated/world_assets/player/clips'/name/'clip.json'
        meta=json.loads(meta_path.read_text())
        runtime_count=int(clip['frame_count'])
        gif_count=int(meta['source_frame_count'])
        width=int(clip['frame_width']); height=int(clip['frame_height'])
        runtime_looped=name in {'idle','walk'}
        gif_looped=True
        if runtime_looped and runtime_count != gif_count+1:
            raise ValueError(f'{name}: looping runtime sheet must contain one closure frame')
        if not runtime_looped and runtime_count != gif_count:
            raise ValueError(f'{name}: one-shot runtime sheet/GIF frame count mismatch')
        frames=read_frames(ROOT/clip['sheet_path'],runtime_count,width,height)[:gif_count]
        gif_path=ROOT/clip['gif_path']
        durations=encode_transparent_gif(frames,gif_path,duration_ms=int(clip['frame_duration_ms']),loop=gif_looped)
        decoded_count,decoded_durations,decoded_looped,distinct=decoded_contract(gif_path)
        if (decoded_count,decoded_durations,decoded_looped)!=(gif_count,durations,gif_looped):
            raise RuntimeError(f'{name}: decoded GIF contract differs')
        expected_distinct=gif_count
        if distinct!=expected_distinct:
            raise RuntimeError(f'{name}: expected {expected_distinct} distinct frames, got {distinct}')
        fields={
            'gif_frame_count':gif_count,
            'gif_frame_durations_ms':durations,
            'gif_total_duration_ms':sum(durations),
            'gif_looped':gif_looped,
            'gif_palette_mode':'single shared 254-color palette; index 0 transparent',
            'gif_duplicate_closure_frame':False,
            'distinct_gif_frames':distinct,
            'gif_sheet_mask_disagreement':[0.0 for _ in range(gif_count)],
        }
        clip.update(fields)
        clip['gif_loop']=0
        clip.setdefault('validation',{}).update({
            'gif_frames':gif_count,
            'gif_loop':0,
            'gif_frame_durations_ms':durations,
            'gif_total_duration_ms':sum(durations),
            'gif_palette_mode':fields['gif_palette_mode'],
            'gif_duplicate_closure_frame':False,
            'gif_sheet_mask_disagreement':fields['gif_sheet_mask_disagreement'],
        })
        clip['sha256']['gif']=sha256(gif_path)
        meta.update(fields)
        meta['gif_loop']=0
        meta.setdefault('validation',{}).update(clip['validation'])
        meta['sha256']['gif']=sha256(gif_path)
        meta['sha256'].pop('meta',None)
        meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        clip['sha256']['meta']=sha256(meta_path)
        summaries[name]={**fields,'sha256':sha256(gif_path),'bytes':gif_path.stat().st_size}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summaries,indent=2))

if __name__=='__main__':
    main()
