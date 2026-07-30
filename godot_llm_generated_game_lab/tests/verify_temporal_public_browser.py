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

ENGINE = 'sdxl-reviewed-scene-assets+stableanimator-pose-driven-player'
EXPECTED_CLIPS = {'idle', 'walk', 'player_interact', 'player_attack', 'player_use'}


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
    expression = """JSON.stringify((()=>{const app=document.getElementById('app');const canvas=document.getElementById('canvas');const t=document.createElement('canvas');const gl=t.getContext('webgl2')||t.getContext('webgl');const r=canvas?.getBoundingClientRect?.()||{left:0,top:0,width:0,height:0};const parse=(value,fallback)=>{try{return JSON.parse(value||'')}catch(e){return fallback}};const visibleObjects=parse(app?.dataset?.visibleObjects,[]);return {readyState:document.readyState,godotReady:app?.dataset?.godotReady||'',loadingHidden:document.getElementById('loading')?.hidden===true,startupComplete:app?.dataset?.startupComplete||'',startupError:app?.dataset?.startupError||'',pageTitle:document.title,assetEngine:app?.dataset?.assetEngine||'',lastActionId:app?.dataset?.lastActionId||'',playerClip:app?.dataset?.playerClip||'',playerX:Number(app?.dataset?.playerX||0),playerY:Number(app?.dataset?.playerY||0),animationFrame:Number(app?.dataset?.animationFrame??-1),inventory:parse(app?.dataset?.inventory,{}),gameStats:parse(app?.dataset?.gameStats,{}),objectStates:parse(app?.dataset?.objectStates,{}),visibleObjects,canvas:{width:canvas?.width||0,height:canvas?.height||0,clientWidth:canvas?.clientWidth||0,clientHeight:canvas?.clientHeight||0,left:r.left,top:r.top,rectWidth:r.width,rectHeight:r.height},webgl:!!gl,renderer:gl?gl.getParameter(gl.RENDERER):'',controlStatus:document.getElementById('control-status')?.textContent||'',eventText:document.getElementById('event-text')?.textContent||''};})())"""

    def state() -> dict:
        result = call('script.evaluate', {'expression': expression, 'target': {'context': context}, 'awaitPromise': True})['result']
        if result.get('type') == 'exception':
            raise RuntimeError(result)
        return json.loads(result.get('value', '{}'))

    def evaluate(expression_text: str) -> dict:
        result = call('script.evaluate', {
            'expression': expression_text,
            'target': {'context': context},
            'awaitPromise': True,
        })['result']
        if result.get('type') == 'exception':
            raise RuntimeError(result)
        return result

    def godot_move(x: float, y: float) -> None:
        evaluate(f"(()=>{{if(typeof window.llmGameGodotMove!=='function')throw new Error('move bridge unavailable');window.llmGameGodotMove({x:.8f},{y:.8f});return true;}})()")

    def godot_action(action: str) -> None:
        evaluate(f"(()=>{{if(typeof window.llmGameGodotAction!=='function')throw new Error('action bridge unavailable');window.llmGameGodotAction({json.dumps(action)});return true;}})()")

    def move_to(target_x: float, target_y: float, *, tolerance: float = 36.0, timeout_seconds: float = 12.0) -> dict:
        deadline = time.time() + timeout_seconds
        last = state()
        try:
            while time.time() < deadline:
                last = state()
                dx = target_x - float(last.get('playerX', 0.0))
                dy = target_y - float(last.get('playerY', 0.0))
                distance = math.hypot(dx, dy)
                if distance <= tolerance:
                    return last
                godot_move(dx / max(distance, 1.0), dy / max(distance, 1.0))
                time.sleep(0.08)
        finally:
            godot_move(0.0, 0.0)
        raise RuntimeError({'move_to_timeout': {'target': [target_x, target_y], 'last': last}})

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
            and player.get('frame_count') == 13
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

    def key_down(key: str) -> None:
        call('input.performActions', {
            'context': context,
            'actions': [{
                'type': 'key', 'id': 'held-keyboard',
                'actions': [{'type': 'keyDown', 'value': key}],
            }],
        })

    def release_keys() -> None:
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
    key_down('w')
    walk_state = wait_clip('walk', 3.0)
    walk_player = next((item for item in walk_state.get('visibleObjects', []) if item.get('id') == 'player'), {})
    if walk_player.get('frame_count') != 17 or walk_player.get('playing') is not True:
        release_keys()
        raise RuntimeError({'walk_clip_not_loaded': walk_state})
    walk_initial_frame = int(walk_state.get('animationFrame', -1))
    walk_frame_state = walk_state
    for _ in range(24):
        time.sleep(0.08)
        walk_frame_state = state()
        if walk_frame_state.get('playerClip') == 'walk' and int(walk_frame_state.get('animationFrame', -1)) != walk_initial_frame:
            break
    else:
        release_keys()
        raise RuntimeError({'walk_frame_did_not_advance': {'initial': walk_initial_frame, 'last': walk_frame_state}})
    walk_frame_advanced_to = int(walk_frame_state.get('animationFrame', -1))
    time.sleep(0.55)
    moving_state = state()
    release_keys()
    idle_after_walk = wait_clip('idle', 3.0)
    moved_position = (float(moving_state.get('playerX', 0.0)), float(moving_state.get('playerY', 0.0)))
    moved_distance = math.dist(initial_position, moved_position)
    if moved_distance < 5.0:
        raise RuntimeError({'wasd_failed': {'before': initial_position, 'after': moved_position, 'distance': moved_distance}})

    cookie_object = next((item for item in moving_state.get('visibleObjects', []) if item.get('id') == 'cookies'), None)
    if not cookie_object:
        raise RuntimeError({'cookies_missing_from_runtime': moving_state})
    cookie_x = float(cookie_object.get('node_x', 0.0))
    cookie_y = float(cookie_object.get('node_y', 0.0))
    viewport_height = float(moving_state.get('canvas', {}).get('height', 725.0))
    safe_y = min(viewport_height - 70.0, max(float(moving_state.get('playerY', 0.0)), cookie_y) + 150.0)
    move_to(float(moving_state.get('playerX', 0.0)), safe_y, tolerance=30.0)
    move_to(cookie_x, safe_y, tolerance=30.0)
    near_cookies = move_to(cookie_x, cookie_y, tolerance=34.0)
    godot_action('interact')
    pickup_state = wait_clip('player_interact', 3.0)
    if pickup_state.get('lastActionId') != 'interact_cookies':
        raise RuntimeError({'cookie_pickup_action_failed': {'near': near_cookies, 'after': pickup_state}})
    cookie_count_after_pickup = int(pickup_state.get('inventory', {}).get('cookies', 0))
    if cookie_count_after_pickup < 1:
        raise RuntimeError({'cookie_inventory_not_added': pickup_state})
    wait_clip('idle', 3.0)
    godot_action('use')
    use_state = wait_clip('player_use', 3.0)
    if use_state.get('lastActionId') != 'player_eat_cookie':
        raise RuntimeError({'cookie_use_action_failed': use_state})
    cookie_count_after_use = int(use_state.get('inventory', {}).get('cookies', 0))
    if cookie_count_after_use != cookie_count_after_pickup - 1:
        raise RuntimeError({'cookie_inventory_not_consumed': {'pickup': cookie_count_after_pickup, 'use': cookie_count_after_use, 'state': use_state}})
    idle_after_use = wait_clip('idle', 3.0)

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
        'walk_clip': walk_state.get('playerClip'),
        'walk_frame_count': walk_player.get('frame_count'),
        'walk_frame_advanced_from': walk_initial_frame,
        'walk_frame_advanced_to': walk_frame_advanced_to,
        'idle_after_walk': idle_after_walk.get('playerClip'),
        'wasd_distance': round(moved_distance, 3),
        'cookie_pickup_action_id': pickup_state.get('lastActionId'),
        'cookie_count_after_pickup': cookie_count_after_pickup,
        'use_action_id': use_state.get('lastActionId'),
        'use_clip': use_state.get('playerClip'),
        'cookie_count_after_use': cookie_count_after_use,
        'idle_after_use': idle_after_use.get('playerClip'),
        'screenshot': str(args.screenshot),
        'image': image_summary,
        'log_errors': [],
    }, ensure_ascii=False, sort_keys=True))
    call('session.end', {})
    ws.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
