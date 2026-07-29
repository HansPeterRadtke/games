#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import math
import time
from pathlib import Path

import websocket
from PIL import Image, ImageChops, ImageStat

ENGINE = 'sdxl-reviewed-canonical+ltx-video-temporal+birefnet-matting'
EXPECTED_CLIPS = {'idle', 'player_interact', 'player_attack', 'player_use'}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--websocket', required=True)
    parser.add_argument('--screenshot', type=Path, required=True)
    args = parser.parse_args()
    ws = websocket.create_connection(args.websocket, timeout=15, suppress_origin=True)
    sequence = 0
    events: list[dict] = []

    def call(method: str, params: dict, timeout: float = 25.0) -> dict:
        nonlocal sequence
        sequence += 1
        ident = sequence
        ws.send(json.dumps({'id': ident, 'method': method, 'params': params}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = json.loads(ws.recv())
            if message.get('id') == ident:
                if message.get('type') == 'error' or 'error' in message:
                    raise RuntimeError(message)
                return message.get('result', message)
            events.append(message)
        raise TimeoutError(method)

    call('session.new', {'capabilities': {'alwaysMatch': {'browserName': 'firefox'}}})
    call('session.subscribe', {'events': ['log.entryAdded']})
    contexts = call('browsingContext.getTree', {}).get('contexts', [])
    context = next(item for item in contexts if '/llm_game/' in item.get('url', ''))['context']
    expression = """JSON.stringify((()=>{const app=document.getElementById('app');const canvas=document.getElementById('canvas');const t=document.createElement('canvas');const gl=t.getContext('webgl2')||t.getContext('webgl');const r=canvas?.getBoundingClientRect?.()||{left:0,top:0,width:0,height:0};let visibleObjects=[];try{visibleObjects=JSON.parse(app?.dataset?.visibleObjects||'[]')}catch(e){}return {readyState:document.readyState,godotReady:app?.dataset?.godotReady||'',loadingHidden:document.getElementById('loading')?.hidden===true,startupComplete:app?.dataset?.startupComplete||'',startupError:app?.dataset?.startupError||'',pageTitle:document.title,assetEngine:app?.dataset?.assetEngine||'',lastActionId:app?.dataset?.lastActionId||'',playerClip:app?.dataset?.playerClip||'',playerX:Number(app?.dataset?.playerX||0),playerY:Number(app?.dataset?.playerY||0),animationFrame:Number(app?.dataset?.animationFrame??-1),visibleObjects,canvas:{width:canvas?.width||0,height:canvas?.height||0,clientWidth:canvas?.clientWidth||0,clientHeight:canvas?.clientHeight||0,left:r.left,top:r.top,rectWidth:r.width,rectHeight:r.height},webgl:!!gl,renderer:gl?gl.getParameter(gl.RENDERER):'',controlStatus:document.getElementById('control-status')?.textContent||'',eventText:document.getElementById('event-text')?.textContent||''};})())"""

    def state() -> dict:
        result = call('script.evaluate', {'expression': expression, 'target': {'context': context}, 'awaitPromise': True})['result']
        if result.get('type') == 'exception':
            raise RuntimeError(result)
        return json.loads(result.get('value', '{}'))

    current: dict = {}
    started = time.monotonic()
    for _ in range(45):
        current = state()
        player = next((item for item in current.get('visibleObjects', []) if item.get('id') == 'player'), {})
        clips = set(player.get('available_clips', []))
        ready = (
            current.get('godotReady') == 'true'
            and current.get('loadingHidden') is True
            and current.get('startupComplete') == 'true'
            and current.get('startupError', '') == ''
            and current.get('pageTitle') == 'Your Mom'
            and current.get('assetEngine') == ENGINE
            and current.get('webgl') is True
            and current.get('canvas', {}).get('width', 0) > 0
            and current.get('playerClip') == 'idle'
            and clips == EXPECTED_CLIPS
            and player.get('texture_loaded') is True
            and player.get('frame_count') == 9
            and player.get('playing') is True
        )
        if ready:
            break
        time.sleep(1)
    else:
        raise RuntimeError({'temporal_scene_not_ready': current})
    startup_seconds = time.monotonic() - started
    if startup_seconds >= 45:
        raise RuntimeError({'startup_too_slow': startup_seconds})

    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
    before = args.screenshot.with_name(args.screenshot.stem + '-idle-before.png')
    shot = call('browsingContext.captureScreenshot', {'context': context, 'origin': 'viewport'})
    before.write_bytes(base64.b64decode(shot['data']))
    initial_frame = current['animationFrame']
    for _ in range(20):
        time.sleep(0.12)
        current = state()
        if current.get('animationFrame') != initial_frame:
            break
    else:
        raise RuntimeError({'idle_animation_frame_did_not_change': initial_frame})
    shot = call('browsingContext.captureScreenshot', {'context': context, 'origin': 'viewport'})
    args.screenshot.write_bytes(base64.b64decode(shot['data']))
    with Image.open(before) as first, Image.open(args.screenshot) as second:
        diff = ImageChops.difference(first.convert('RGB'), second.convert('RGB'))
        changed_ratio = sum(1 for px in diff.getdata() if max(px) > 6) / float(diff.width * diff.height)
        if changed_ratio < 0.0005:
            raise RuntimeError({'idle_not_visibly_animated': changed_ratio})

    def press(key: str, duration: int = 120) -> None:
        call('input.performActions', {
            'context': context,
            'actions': [{
                'type': 'key', 'id': 'keyboard',
                'actions': [
                    {'type': 'keyDown', 'value': key},
                    {'type': 'pause', 'duration': duration},
                    {'type': 'keyUp', 'value': key},
                ],
            }],
        })
        call('input.releaseActions', {'context': context})

    def wait_clip(expected: str, timeout_seconds: float) -> dict:
        deadline = time.time() + timeout_seconds
        last = {}
        while time.time() < deadline:
            last = state()
            if last.get('playerClip') == expected:
                return last
            time.sleep(0.08)
        raise RuntimeError({'clip_transition_failed': {'expected': expected, 'last': last}})

    press('f')
    attack_state = wait_clip('player_attack', 3.0)
    if not attack_state.get('lastActionId'):
        raise RuntimeError({'attack_action_id_missing': attack_state})
    idle_after_attack = wait_clip('idle', 3.0)

    press('e')
    interact_state = wait_clip('player_interact', 3.0)
    if not interact_state.get('lastActionId'):
        raise RuntimeError({'interact_action_id_missing': interact_state})
    idle_after_interact = wait_clip('idle', 3.0)

    initial_position = (float(idle_after_interact.get('playerX', 0.0)), float(idle_after_interact.get('playerY', 0.0)))
    press('w', 700)
    moved = state()
    moved_position = (float(moved.get('playerX', 0.0)), float(moved.get('playerY', 0.0)))
    moved_distance = math.dist(initial_position, moved_position)
    if moved_distance < 5.0:
        raise RuntimeError({'wasd_failed': {'before': initial_position, 'after': moved_position, 'distance': moved_distance}})

    ws.settimeout(0.2)
    try:
        while True:
            events.append(json.loads(ws.recv()))
    except Exception:
        pass
    errors = []
    for event in events:
        if event.get('method') != 'log.entryAdded':
            continue
        entry = event.get('params', {}).get('entry', {})
        level, text = entry.get('level', ''), entry.get('text', '')
        if level == 'error' or any(token in text for token in ('SCRIPT ERROR', 'Parse Error', 'Failed to load', 'Generated world manifest is missing')):
            errors.append({'level': level, 'text': text})
    if errors:
        raise RuntimeError({'browser_errors': errors})

    with Image.open(args.screenshot) as image:
        rgb = image.convert('RGB')
        stats = ImageStat.Stat(rgb)
        colors = rgb.getcolors(maxcolors=10_000_000)
        if image.width < 1000 or image.height < 700 or (colors is not None and len(colors) < 1000):
            raise RuntimeError({'invalid_screenshot': {'size': image.size, 'colors': len(colors) if colors else None}})
        image_summary = {'size': list(image.size), 'bytes': args.screenshot.stat().st_size, 'mean': [round(x, 2) for x in stats.mean], 'unique_colors': len(colors) if colors is not None else '>10000000'}

    print(json.dumps({
        'ok': True,
        'startup_seconds': round(startup_seconds, 3),
        'asset_engine': ENGINE,
        'idle_changed_ratio': round(changed_ratio, 6),
        'attack_action_id': attack_state.get('lastActionId'),
        'attack_clip': attack_state.get('playerClip'),
        'idle_after_attack': idle_after_attack.get('playerClip'),
        'interact_action_id': interact_state.get('lastActionId'),
        'interact_clip': interact_state.get('playerClip'),
        'idle_after_interact': idle_after_interact.get('playerClip'),
        'wasd_distance': round(moved_distance, 3),
        'screenshot': str(args.screenshot),
        'image': image_summary,
        'log_errors': [],
    }, ensure_ascii=False, sort_keys=True))
    call('session.end', {})
    ws.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
