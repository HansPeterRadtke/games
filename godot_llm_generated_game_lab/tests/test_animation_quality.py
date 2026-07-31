#!/usr/bin/env python3
from __future__ import annotations
import sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from animation_quality import analyze_animation,validate_animation,encode_transparent_gif,_frames_from_gif,_gif_frame_durations

def write_assets(directory: Path, frames: list[Image.Image]) -> tuple[Path,Path]:
    width,height=frames[0].size
    sheet=Image.new('RGBA',(width*len(frames),height),(0,0,0,0))
    for i,frame in enumerate(frames):sheet.alpha_composite(frame,(i*width,0))
    sheet_path=directory/'sheet.png';gif_path=directory/'animation.gif'
    sheet.save(sheet_path)
    frames[0].save(gif_path,format='GIF',save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=2,transparency=0,optimize=False)
    return sheet_path,gif_path

with tempfile.TemporaryDirectory() as raw:
    root=Path(raw);frames=[]
    for i in range(9):
        frame=Image.new('RGBA',(96,128),(0,0,0,0))
        phase=np.sin(2*np.pi*i/8)
        x=int(round(38+phase*5));y=int(round(25-abs(phase)*2))
        for yy in range(y,y+80):
            for xx in range(x,x+20):frame.putpixel((xx,yy),(70,120,180,255))
        frames.append(frame)
    frames[-1]=frames[0].copy()
    sheet,gif=write_assets(root,frames)
    quality=analyze_animation(sheet,gif,9,96,128)
    errors=validate_animation(quality,transparent=True,loop_required=True,action_clip=False,clip_name='idle')
    assert not errors,errors

with tempfile.TemporaryDirectory() as raw:
    root=Path(raw);frames=[]
    for i in range(9):
        frame=Image.new('RGBA',(96,128),(20+i*15,30,40,255))
        frames.append(frame)
    sheet,gif=write_assets(root,frames)
    quality=analyze_animation(sheet,gif,9,96,128)
    errors=validate_animation(quality,transparent=True,loop_required=True,action_clip=False,clip_name='idle')
    assert any('occupies too much' in error for error in errors),errors
    assert any('frame border' in error for error in errors),errors
    assert any('starting frame' in error for error in errors),errors

with tempfile.TemporaryDirectory() as raw:
    root=Path(raw);frames=[]
    for i in range(16):
        phase=2*np.pi*i/16
        frame=Image.new('RGBA',(128,160),(0,0,0,0))
        body_x=54+int(round(np.sin(phase)*2))
        for yy in range(20,90):
            for xx in range(body_x,body_x+20):frame.putpixel((xx,yy),(80,120,180,255))
        left=body_x-8+int(round(np.sin(phase)*10));right=body_x+20-int(round(np.sin(phase)*10))
        pelvis_left=min(left,body_x);pelvis_right=max(right+8,body_x+20)
        for yy in range(84,100):
            for xx in range(pelvis_left,pelvis_right):frame.putpixel((xx,yy),(75,110,170,255))
        for yy in range(92,145):
            for xx in range(left,left+8):frame.putpixel((xx,yy),(70,100,160,255))
            for xx in range(right,right+8):frame.putpixel((xx,yy),(70,100,160,255))
        frames.append(frame)
    frames[-1]=frames[0].copy()
    sheet,gif=write_assets(root,frames)
    quality=analyze_animation(sheet,gif,16,128,160)
    errors=validate_animation(quality,transparent=True,loop_required=True,action_clip=False,clip_name='walk')
    assert not errors,errors

with tempfile.TemporaryDirectory() as raw:
    root=Path(raw);frame=Image.new('RGBA',(128,160),(0,0,0,0))
    for yy in range(20,145):
        for xx in range(54,74):frame.putpixel((xx,yy),(80,120,180,255))
    frames=[frame.copy() for _ in range(16)]
    sheet,gif=write_assets(root,frames)
    try:
        quality=analyze_animation(sheet,gif,16,128,160)
    except ValueError as exc:
        assert 'GIF has 1 frames' in str(exc),exc
    else:
        errors=validate_animation(quality,transparent=True,loop_required=True,action_clip=False,clip_name='walk')
        assert any('walk cycle' in error or 'gait' in error or 'leg motion' in error or 'static' in error for error in errors),errors

with tempfile.TemporaryDirectory() as raw:
    root=Path(raw)
    frames=[]
    for i in range(6):
        frame=Image.new('RGBA',(96,128),(0,0,0,0))
        for yy in range(18,110):
            for xx in range(32+i,62+i):
                frame.putpixel((xx,yy),(20+i*20,80,160,255))
        frames.append(frame)
    gif=root/'reserved-alpha.gif'
    durations=encode_transparent_gif(frames,gif,duration_ms=125,loop=True)
    assert durations==_gif_frame_durations(len(frames),125)
    assert durations==[120,130,120,130,120,130]
    decoded,looped=_frames_from_gif(gif)
    assert looped and len(decoded)==len(frames)
    with Image.open(gif) as image:
        decoded_durations=[]; palette_tables=[]
        for index in range(image.n_frames):
            image.seek(index)
            decoded_durations.append(image.info.get('duration'))
            palette=image.getpalette()
            if palette:palette_tables.append(tuple(palette))
        assert decoded_durations==durations
        assert len(palette_tables)==1 and len(set(palette_tables))==1
    for source,target in zip(frames,decoded):
        source_coverage=np.asarray(source.getchannel('A'))>16
        target_coverage=np.asarray(target.getchannel('A'))>16
        assert abs(float(source_coverage.mean())-float(target_coverage.mean()))<0.002
        assert float(target_coverage.mean())<0.40
    one_shot=root/'one-shot.gif'
    one_shot_durations=encode_transparent_gif(frames,one_shot,duration_ms=125,loop=False)
    decoded,looped=_frames_from_gif(one_shot)
    assert not looped and len(decoded)==len(frames)
    with Image.open(one_shot) as image:
        assert image.info.get('loop') is None
        actual=[]
        for index in range(image.n_frames):
            image.seek(index);actual.append(image.info.get('duration'))
        assert actual==one_shot_durations
print('animation quality contracts passed')
