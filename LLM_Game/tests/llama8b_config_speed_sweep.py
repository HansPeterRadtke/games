#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, time, requests, pathlib, statistics

BASE = os.environ.get('LLAMA_BASE_URL', 'http://127.0.0.1:14829')
START = ['/data/infra/bin/llama.sh']
PROMPT = ('You are testing output speed. Write exactly 10 concise numbered bullets about why a perception-oriented LLM game engine needs deterministic validation. Do not include any preface.')
CONFIGS = [
    {'name':'ctx2048_b24_u24_gl31','ctx':'2048','batch':'24','ubatch':'24','gpu_layers':'31'},
    {'name':'ctx4096_b24_u24_gl31','ctx':'4096','batch':'24','ubatch':'24','gpu_layers':'31'},
    {'name':'ctx8192_b24_u24_gl31','ctx':'8192','batch':'24','ubatch':'24','gpu_layers':'31'},
    {'name':'ctx8192_b64_u64_gl31','ctx':'8192','batch':'64','ubatch':'64','gpu_layers':'31'},
    {'name':'ctx8192_b128_u64_gl31','ctx':'8192','batch':'128','ubatch':'64','gpu_layers':'31'},
    {'name':'ctx12000_b64_u64_gl31','ctx':'12000','batch':'64','ubatch':'64','gpu_layers':'31'},
]

def run(cmd, env=None, timeout=120):
    return subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)

def nvidia():
    p = run(['nvidia-smi','--query-gpu=memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'], timeout=10)
    vals = [v.strip() for v in (p.stdout.strip().splitlines()[0] if p.stdout.strip() else '').split(',')]
    return {'total_mb':int(vals[0]),'used_mb':int(vals[1]),'free_mb':int(vals[2]),'util_percent':int(vals[3])} if len(vals) >= 4 else {'raw': p.stdout.strip()}

def curl_json(path):
    r = requests.get(BASE + path, timeout=(5, 15)); r.raise_for_status(); return r.json()

def completion(n_predict=128, seed=1):
    payload = {'prompt': PROMPT, 'n_predict': n_predict, 'temperature': 0.0, 'top_p': 0.95, 'seed': seed, 'stop': ['</s>']}
    t = time.monotonic()
    r = requests.post(BASE + '/completion', json=payload, timeout=(10, 240)); r.raise_for_status()
    wall = time.monotonic() - t
    body = r.json(); toks = body.get('tokens_predicted') or 0
    return {'wall_seconds': round(wall, 3), 'completion_tokens': toks, 'prompt_tokens': body.get('tokens_evaluated'), 'tokens_per_second': round(toks / wall, 3) if wall else None, 'stop': body.get('stop')}

def main() -> int:
    out = pathlib.Path(os.environ.get('SWEEP_OUT', 'LLM_Game/results/llama8b_config_speed_sweep_manual.json'))
    out.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for cfg in CONFIGS:
        env = os.environ.copy()
        env.update({'LLAMA_CTX': cfg['ctx'], 'LLAMA_BATCH': cfg['batch'], 'LLAMA_UBATCH': cfg['ubatch'], 'LLAMA_GPU_LAYERS': cfg['gpu_layers'], 'LLAMA_PARALLEL': '1', 'LLAMA_KVT': 'q4_0', 'LLAMA_KVV': 'q4_0'})
        start = run(START, env=env, timeout=120)
        ready = False
        for _ in range(20):
            try:
                curl_json('/health'); ready = True; break
            except Exception:
                time.sleep(1)
        mem_after_start = nvidia()
        warm = completion(n_predict=16, seed=100) if ready else {'error': 'not ready'}
        measurements = [completion(n_predict=128, seed=200+i) for i in range(2)] if ready else []
        tps = [m['tokens_per_second'] for m in measurements if isinstance(m.get('tokens_per_second'), (int, float))]
        results.append({'config': cfg, 'ready': ready, 'start_exit': start.returncode, 'gpu_after_start': mem_after_start, 'warmup': warm, 'measurements': measurements, 'median_tps': round(statistics.median(tps), 3) if tps else None, 'mean_tps': round(statistics.mean(tps), 3) if tps else None, 'start_output_tail': '\n'.join(start.stdout.splitlines()[-24:])})
    out.write_text(json.dumps(results, indent=2, sort_keys=True) + '\n')
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
