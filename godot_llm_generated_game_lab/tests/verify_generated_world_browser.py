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
    expression = """JSON.stringify((()=>{const app=document.getElementById('app');const canvas=document.getElementById('canvas');const t=document.createElement('canvas');const gl=t.getContext('webgl2')||t.getContext('webgl');const r=canvas?.getBoundingClientRect?.()||{left:0,top:0,width:0,height:0};let visibleObjects=[];try{visibleObjects=JSON.parse(app?.dataset?.visibleObjects||'[]')}catch(e){}return {readyState:document.readyState,godotReady:app?.dataset?.godotReady||'',canvas:{width:canvas?.width||0,height:canvas?.height||0,clientWidth:canvas?.clientWidth||0,clientHeight:canvas?.clientHeight||0,left:r.left,top:r.top,rectWidth:r.width,rectHeight:r.height},devicePixelRatio:window.devicePixelRatio||1,webgl:!!gl,renderer:gl?gl.getParameter(gl.RENDERER):'',playerName:document.getElementById('player-name')?.textContent||'',controlStatus:document.getElementById('control-status')?.textContent||'',eventText:document.getElementById('event-text')?.textContent||'',loadingHidden:document.getElementById('loading')?.hidden===true,startupComplete:app?.dataset?.startupComplete||'',startupError:app?.dataset?.startupError||'',pageTitle:document.title,loaderText:document.getElementById('loading')?.textContent?.trim()||'',playerX:Number(app?.dataset?.playerX||0),playerY:Number(app?.dataset?.playerY||0),animationFrame:Number(app?.dataset?.animationFrame??-1),internalWidth:Number(app?.dataset?.internalWidth||0),internalHeight:Number(app?.dataset?.internalHeight||0),visibleObjects};})())"""

    def state() -> dict:
        remote = call('script.evaluate', {'expression': expression, 'target': {'context': context}, 'awaitPromise': True})['result']
        return json.loads(remote.get('value', '{}'))

    current: dict = {}
    for _ in range(45):
        current = state()
        ready = (
            current.get('godotReady') == 'true'
            and current.get('webgl') is True
            and current.get('canvas', {}).get('width', 0) > 0
            and current.get('playerName', '').startswith('Player')
            and 'Thor SDXL animations' in current.get('controlStatus', '')
            and current.get('loadingHidden') is True
            and current.get('startupComplete') == 'true'
            and current.get('startupError', '') == ''
            and current.get('pageTitle') == 'Your Mom'
            and current.get('animationFrame', -1) >= 0
            and len(current.get('visibleObjects', [])) == 10
            and current.get('internalWidth', 0) > 0
            and current.get('internalHeight', 0) > 0
        )
        if ready:
            break
        time.sleep(1)
    else:
        raise RuntimeError({'generated_scene_not_ready': current})

    expected_object_ids = {
        'player', 'mom', 'dining_table', 'chandelier', 'sideboard',
        'curtains', 'wall_finish', 'floor_carpet', 'kitchen_door', 'cookies',
    }
    objects = {str(item.get('id')): item for item in current.get('visibleObjects', [])}
    if set(objects) != expected_object_ids:
        raise RuntimeError({'rendered_object_ids': sorted(objects), 'expected': sorted(expected_object_ids)})
    internal_width = float(current['internalWidth'])
    internal_height = float(current['internalHeight'])
    object_state_summary: dict[str, dict] = {}
    for object_id, item in objects.items():
        width = float(item.get('width', 0.0))
        height = float(item.get('height', 0.0))
        x = float(item.get('x', 0.0))
        y = float(item.get('y', 0.0))
        visible_width = max(0.0, min(internal_width, x + width) - max(0.0, x))
        visible_height = max(0.0, min(internal_height, y + height) - max(0.0, y))
        visible_ratio = (visible_width * visible_height) / max(1.0, width * height)
        if width < 28.0 or height < 28.0:
            raise RuntimeError({'rendered_object_too_small': object_id, 'rect': [x, y, width, height]})
        if visible_ratio < 0.60:
            raise RuntimeError({'rendered_object_offscreen': object_id, 'visible_ratio': visible_ratio, 'rect': [x, y, width, height], 'viewport': [internal_width, internal_height]})
        if item.get('texture_loaded') is not True or item.get('visible') is not True:
            raise RuntimeError({'rendered_object_not_visible': object_id, 'state': item})
        if item.get('playing') is not True or int(item.get('frame_count', 0)) < 6:
            raise RuntimeError({'rendered_object_not_animated': object_id, 'state': item})
        object_state_summary[object_id] = {
            'rect': [round(x, 2), round(y, 2), round(width, 2), round(height, 2)],
            'visible_ratio': round(visible_ratio, 4),
            'frame': int(item.get('frame', -1)),
            'frame_count': int(item.get('frame_count', 0)),
            'usage': item.get('usage'),
        }

    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
    before_path = args.screenshot.with_name(args.screenshot.stem + '-before.png')
    before_shot = call('browsingContext.captureScreenshot', {'context': context, 'origin': 'viewport'})
    before_path.write_bytes(base64.b64decode(before_shot['data']))
    initial_frame = current['animationFrame']
    for _ in range(20):
        time.sleep(0.12)
        current = state()
        if current.get('animationFrame') != initial_frame:
            break
    else:
        raise RuntimeError({'animation_frame_did_not_change': initial_frame, 'state': current})
    after_shot = call('browsingContext.captureScreenshot', {'context': context, 'origin': 'viewport'})
    args.screenshot.write_bytes(base64.b64decode(after_shot['data']))

    with Image.open(before_path) as first, Image.open(args.screenshot) as second:
        first_rgb = first.convert('RGB')
        second_rgb = second.convert('RGB')
        difference = ImageChops.difference(first_rgb, second_rgb)
        changed = sum(1 for pixel in difference.getdata() if max(pixel) > 6)
        animation_changed_ratio = changed / float(first_rgb.width * first_rgb.height)
        if animation_changed_ratio < 0.0005:
            raise RuntimeError({'animation_not_visibly_rendered': animation_changed_ratio})

    initial_position = (float(current.get('playerX', 0.0)), float(current.get('playerY', 0.0)))
    call('input.performActions', {
        'context': context,
        'actions': [{
            'type': 'key',
            'id': 'keyboard',
            'actions': [
                {'type': 'keyDown', 'value': 'w'},
                {'type': 'pause', 'duration': 700},
                {'type': 'keyUp', 'value': 'w'},
            ],
        }],
    })
    call('input.releaseActions', {'context': context})
    moved_state = state()
    moved_position = (float(moved_state.get('playerX', 0.0)), float(moved_state.get('playerY', 0.0)))
    moved_distance = math.dist(initial_position, moved_position)
    if moved_distance < 5.0:
        raise RuntimeError({'physical_wasd_failed': {'before': initial_position, 'after': moved_position, 'distance': moved_distance}})

    ws.settimeout(0.2)
    try:
        while True:
            events.append(json.loads(ws.recv()))
    except Exception:
        pass
    failures: list[dict] = []
    for event in events:
        if event.get('method') != 'log.entryAdded':
            continue
        entry = event.get('params', {}).get('entry', {})
        level = entry.get('level', '')
        text = entry.get('text', '')
        if level == 'error' or any(token in text for token in ('SCRIPT ERROR', 'Parse Error', 'Failed to load', 'Generated world manifest is missing')):
            failures.append({'level': level, 'text': text})
    if failures:
        raise RuntimeError({'browser_errors': failures})

    with Image.open(args.screenshot) as image:
        rgb = image.convert('RGB')
        colors = rgb.getcolors(maxcolors=10_000_000)
        if image.size[0] < 1000 or image.size[1] < 700:
            raise RuntimeError(f'viewport screenshot is too small: {image.size}')
        if colors is not None and len(colors) <= 1000:
            raise RuntimeError('rendered screenshot lacks visual complexity')
        dpr = float(current.get('devicePixelRatio', 1.0) or 1.0)
        canvas = current['canvas']
        canvas_left = int(round(float(canvas.get('left', 0.0)) * dpr))
        canvas_top = int(round(float(canvas.get('top', 0.0)) * dpr))
        canvas_width = int(round(float(canvas.get('rectWidth', canvas.get('clientWidth', 0.0))) * dpr))
        canvas_height = int(round(float(canvas.get('rectHeight', canvas.get('clientHeight', 0.0))) * dpr))
        canvas_box = (
            max(0, canvas_left),
            max(0, canvas_top),
            min(rgb.width, canvas_left + canvas_width),
            min(rgb.height, canvas_top + canvas_height),
        )
        canvas_image = rgb.crop(canvas_box)
        if canvas_image.width < 500 or canvas_image.height < 500:
            raise RuntimeError({'canvas_crop_too_small': canvas_box, 'screenshot': image.size})
        strict_white = [[min(canvas_image.getpixel((x, y))) > 245 for x in range(canvas_image.width)] for y in range(canvas_image.height)]
        row_white = [sum(row) / canvas_image.width for row in strict_white]
        col_white = [sum(strict_white[y][x] for y in range(canvas_image.height)) / canvas_image.height for x in range(canvas_image.width)]
        if max(row_white) > 0.25 or max(col_white) > 0.25:
            raise RuntimeError({'white_bar_detected': {'max_row': max(row_white), 'max_column': max(col_white)}})

        scale_x = canvas_image.width / internal_width
        scale_y = canvas_image.height / internal_height
        roi_summary: dict[str, dict] = {}
        for object_id, item in objects.items():
            x0 = max(0, int(math.floor(float(item['x']) * scale_x)))
            y0 = max(0, int(math.floor(float(item['y']) * scale_y)))
            x1 = min(canvas_image.width, int(math.ceil((float(item['x']) + float(item['width'])) * scale_x)))
            y1 = min(canvas_image.height, int(math.ceil((float(item['y']) + float(item['height'])) * scale_y)))
            if x1 - x0 < 4 or y1 - y0 < 4:
                raise RuntimeError({'rendered_object_empty_roi': object_id, 'roi': [x0, y0, x1, y1]})
            roi = canvas_image.crop((x0, y0, x1, y1))
            roi_colors = roi.getcolors(maxcolors=1_000_000)
            unique_colors = len(roi_colors) if roi_colors is not None else 1_000_001
            channel_std = ImageStat.Stat(roi).stddev
            if unique_colors < 18 or max(channel_std) < 3.0:
                raise RuntimeError({'rendered_object_has_no_visible_pixels': object_id, 'unique_colors': unique_colors, 'stddev': channel_std, 'roi': [x0, y0, x1, y1]})
            roi_summary[object_id] = {
                'roi': [x0, y0, x1, y1],
                'unique_colors': unique_colors,
                'max_stddev': round(max(channel_std), 3),
            }
        image_summary = {
            'size': list(image.size),
            'canvas_size': list(canvas_image.size),
            'format': image.format,
            'mean': [round(value, 2) for value in ImageStat.Stat(canvas_image).mean],
            'unique_colors': len(colors) if colors is not None else '>10000000',
            'bytes': args.screenshot.stat().st_size,
            'max_white_row': round(max(row_white), 5),
            'max_white_column': round(max(col_white), 5),
            'object_rois': roi_summary,
        }
    print(json.dumps({
        'ok': True,
        'state': moved_state,
        'screenshot': str(args.screenshot),
        'image': image_summary,
        'animation_changed_ratio': round(animation_changed_ratio, 6),
        'wasd_distance': round(moved_distance, 3),
        'rendered_objects': object_state_summary,
        'log_errors': [],
    }, ensure_ascii=False, sort_keys=True))
    call('session.end', {})
    ws.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
