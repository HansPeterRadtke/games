#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import time
from pathlib import Path

import websocket
from PIL import Image, ImageStat


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
    expression = """JSON.stringify((()=>{const app=document.getElementById('app');const canvas=document.getElementById('canvas');const t=document.createElement('canvas');const gl=t.getContext('webgl2')||t.getContext('webgl');return {readyState:document.readyState,godotReady:app?.dataset?.godotReady||'',canvas:{width:canvas?.width||0,height:canvas?.height||0,clientWidth:canvas?.clientWidth||0,clientHeight:canvas?.clientHeight||0},webgl:!!gl,renderer:gl?gl.getParameter(gl.RENDERER):'',playerName:document.getElementById('player-name')?.textContent||'',controlStatus:document.getElementById('control-status')?.textContent||'',eventText:document.getElementById('event-text')?.textContent||'',loadingHidden:document.getElementById('loading')?.hidden===true,startupComplete:app?.dataset?.startupComplete||'',startupError:app?.dataset?.startupError||'',pageTitle:document.title,loaderText:document.getElementById('loading')?.textContent?.trim()||''};})())"""
    state: dict = {}
    for _ in range(45):
        remote = call('script.evaluate', {'expression': expression, 'target': {'context': context}, 'awaitPromise': True})['result']
        state = json.loads(remote.get('value', '{}'))
        ready = (
            state.get('godotReady') == 'true'
            and state.get('webgl') is True
            and state.get('canvas', {}).get('width', 0) > 0
            and state.get('playerName', '').startswith('Player')
            and 'Thor SDXL animations' in state.get('controlStatus', '')
            and state.get('loadingHidden') is True
            and state.get('startupComplete') == 'true'
            and state.get('startupError', '') == ''
            and state.get('pageTitle') == 'Your Mom'
        )
        if ready:
            break
        time.sleep(1)
    else:
        raise RuntimeError({'generated_scene_not_ready': state})
    screenshot = call('browsingContext.captureScreenshot', {'context': context, 'origin': 'viewport'})
    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
    args.screenshot.write_bytes(base64.b64decode(screenshot['data']))
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
        image_summary = {
            'size': list(image.size),
            'format': image.format,
            'mean': [round(value, 2) for value in ImageStat.Stat(rgb).mean],
            'unique_colors': len(colors) if colors is not None else '>10000000',
            'bytes': args.screenshot.stat().st_size,
        }
    print(json.dumps({'ok': True, 'state': state, 'screenshot': str(args.screenshot), 'image': image_summary, 'log_errors': []}, ensure_ascii=False, sort_keys=True))
    call('session.end', {})
    ws.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
