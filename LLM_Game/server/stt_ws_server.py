#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, argparse, asyncio, json, math, os, re, tempfile, time, wave, subprocess, threading, unicodedata
from pathlib import Path
from typing import Any
import numpy as np
import requests
import websockets
from aiohttp import web
from PIL import Image, ImageDraw
from faster_whisper import WhisperModel
from game_llm import install_routes as install_game_llm_routes

MODEL_PATH = os.environ.get('LLM_GAME_STT_MODEL', '/data/src/external/whisper.cpp/models/ggml-base.en.bin')
SAMPLE_RATE = 16000
BYTES_PER_SECOND = SAMPLE_RATE * 2
MIN_WINDOW_SECONDS = float(os.environ.get('LLM_GAME_STT_MIN_WINDOW', '0.6'))
MAX_WINDOW_SECONDS = float(os.environ.get('LLM_GAME_STT_MAX_WINDOW', '1.6'))
TRANSCRIBE_EVERY_SECONDS = float(os.environ.get('LLM_GAME_STT_INTERVAL', '0.9'))
TOPIC_EXTRACT_EVERY_SECONDS = float(os.environ.get('LLM_GAME_TOPIC_INTERVAL', '10.0'))
LLAMA_URL = os.environ.get('LLM_GAME_LLAMA_URL', 'http://127.0.0.1:14829')
THOR_STT_URL = os.environ.get('LLM_GAME_THOR_STT_URL', 'http://10.8.0.7:15201/stt')
ALLOW_LOCAL_STT_FALLBACK = os.environ.get('LLM_GAME_ALLOW_LOCAL_STT_FALLBACK','1').strip().lower() in {'1','true','yes'}
DEFAULT_STT_LANGUAGE = os.environ.get('LLM_GAME_STT_LANGUAGE', 'en').strip().lower() or 'en'
STT_BACKEND = os.environ.get('LLM_GAME_STT_BACKEND', 'local-first').strip().lower() or 'local-first'
LOCAL_FAST_MODEL_PATH = Path(os.environ.get('LLM_GAME_LOCAL_FAST_MODEL', '/data/models/faster_whisper/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356'))
LOCAL_FAST_DEVICE = os.environ.get('LLM_GAME_LOCAL_FAST_DEVICE', 'cpu').strip().lower() or 'cpu'
LOCAL_FAST_COMPUTE_TYPE = os.environ.get('LLM_GAME_LOCAL_FAST_COMPUTE_TYPE', 'int8').strip() or 'int8'
THOR_STT_CONNECT_TIMEOUT = float(os.environ.get('LLM_GAME_THOR_STT_CONNECT_TIMEOUT', '2'))
THOR_STT_READ_TIMEOUT = float(os.environ.get('LLM_GAME_THOR_STT_READ_TIMEOUT', '45'))
DEBUG_LOG_MAX_BYTES = int(os.environ.get('LLM_GAME_DEBUG_LOG_MAX_BYTES', str(8 * 1024 * 1024)))
DEBUG_LOG_BACKUPS = max(1, int(os.environ.get('LLM_GAME_DEBUG_LOG_BACKUPS', '3')))
PIXEL_LLAMA_URL = os.environ.get('LLM_GAME_PIXEL_LLAMA_URL', os.environ.get('LLM_GAME_THOR_14B_URL', 'http://10.8.0.7:14830'))
RMS_THRESHOLD = float(os.environ.get('LLM_GAME_STT_RMS_THRESHOLD', '0.0015'))
UTTERANCE_START_RMS = float(os.environ.get('LLM_GAME_UTTERANCE_START_RMS', '0.008'))
UTTERANCE_CONTINUE_RMS = float(os.environ.get('LLM_GAME_UTTERANCE_CONTINUE_RMS', '0.003'))
UTTERANCE_END_SILENCE_SECONDS = float(os.environ.get('LLM_GAME_UTTERANCE_END_SILENCE', '0.75'))
UTTERANCE_MIN_SECONDS = float(os.environ.get('LLM_GAME_UTTERANCE_MIN_SECONDS', '0.75'))
UTTERANCE_MAX_SECONDS = float(os.environ.get('LLM_GAME_UTTERANCE_MAX_SECONDS', '7.0'))
UTTERANCE_PREROLL_SECONDS = float(os.environ.get('LLM_GAME_UTTERANCE_PREROLL_SECONDS', '0.24'))
OUT_DIR = Path(os.environ.get('LLM_GAME_STT_OUT_DIR', '/data/var/llm_game/stt'))
OUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_LOG = OUT_DIR / 'debug.jsonl'
GIF_DIR = Path(os.environ.get('LLM_GAME_GIF_DIR', '/data/var/llm_game/topic_gifs'))
GIF_DIR.mkdir(parents=True, exist_ok=True)
OPENAI_IMAGE_MODEL = os.environ.get('LLM_GAME_OPENAI_IMAGE_MODEL', 'gpt-image-1')
OPENAI_IMAGE_SIZE = os.environ.get('LLM_GAME_OPENAI_IMAGE_SIZE', '1024x1024')
OPENAI_IMAGE_ENV_FILES = [Path('/data/var/swe_agent/.env'), Path('/data/.env')]
THOR_IMAGE_URL = os.environ.get('LLM_GAME_THOR_IMAGE_URL', 'http://10.8.0.7:15310/generate')
LOG_LOCK = threading.Lock()

def rotate_debug_log() -> None:
    try:
        if not DEBUG_LOG.exists() or DEBUG_LOG.stat().st_size < DEBUG_LOG_MAX_BYTES:
            return
        oldest = DEBUG_LOG.with_name(DEBUG_LOG.name + f'.{DEBUG_LOG_BACKUPS}')
        oldest.unlink(missing_ok=True)
        for index in range(DEBUG_LOG_BACKUPS - 1, 0, -1):
            src = DEBUG_LOG.with_name(DEBUG_LOG.name + f'.{index}')
            dst = DEBUG_LOG.with_name(DEBUG_LOG.name + f'.{index + 1}')
            if src.exists():
                src.replace(dst)
        DEBUG_LOG.replace(DEBUG_LOG.with_name(DEBUG_LOG.name + '.1'))
    except Exception:
        pass

def log_event(payload: dict[str, Any]) -> None:
    try:
        payload = dict(payload)
        payload.setdefault('time_ms', now_ms())
        DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n'
        with LOG_LOCK:
            rotate_debug_log()
            with DEBUG_LOG.open('a', encoding='utf-8') as handle:
                handle.write(line)
    except Exception:
        pass
    try:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
    except Exception:
        pass

WHISPER_CPP_EXE = Path(os.environ.get('LLM_GAME_WHISPER_CPP_EXE', '/data/src/external/whisper.cpp/build/bin/whisper-cli'))
LOCAL_MODEL: WhisperModel | None = None
MODEL_LOCK = asyncio.Lock()

def now_ms() -> int:
    return int(time.time() * 1000)

def pcm_rms(pcm: bytes) -> float:
    if len(pcm) < 2:
        return 0.0
    arr = np.frombuffer(pcm[:len(pcm)//2*2], dtype='<i2').astype(np.float32) / 32768.0
    if arr.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(arr * arr)))


def frame_rms(pcm: bytes) -> float:
    return pcm_rms(pcm)


def pcm_activity(pcm: bytes, frame_ms: int = 30, threshold: float = 0.002) -> dict[str, float | int]:
    if len(pcm) < 2:
        return {'rms': 0.0, 'voiced_ratio': 0.0, 'voiced_frames': 0, 'frames': 0}
    arr = np.frombuffer(pcm[:len(pcm)//2*2], dtype='<i2').astype(np.float32) / 32768.0
    if arr.size == 0:
        return {'rms': 0.0, 'voiced_ratio': 0.0, 'voiced_frames': 0, 'frames': 0}
    frame = max(1, int(SAMPLE_RATE * frame_ms / 1000))
    frames = 0
    voiced = 0
    for off in range(0, arr.size, frame):
        part = arr[off:off+frame]
        if part.size < frame // 2:
            continue
        frames += 1
        rr = float(np.sqrt(np.mean(part * part)))
        if rr >= threshold:
            voiced += 1
    rms = float(np.sqrt(np.mean(arr * arr)))
    return {'rms': rms, 'voiced_ratio': (voiced / frames if frames else 0.0), 'voiced_frames': voiced, 'frames': frames}

def pcm_to_wav(pcm: bytes, path: Path) -> None:
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm)

def normalize_stt_language(value: Any) -> str:
    raw = str(value or DEFAULT_STT_LANGUAGE).strip().lower().replace('_', '-')
    if raw in {'auto', ''}:
        return 'auto'
    code = raw.split('-', 1)[0]
    return code if re.fullmatch(r'[a-z]{2}', code) else DEFAULT_STT_LANGUAGE

def load_local_model() -> WhisperModel:
    global LOCAL_MODEL
    if LOCAL_MODEL is None:
        if not LOCAL_FAST_MODEL_PATH.exists():
            raise RuntimeError(f'local faster-whisper model missing: {LOCAL_FAST_MODEL_PATH}')
        started = time.monotonic()
        LOCAL_MODEL = WhisperModel(
            str(LOCAL_FAST_MODEL_PATH),
            device=LOCAL_FAST_DEVICE,
            compute_type=LOCAL_FAST_COMPUTE_TYPE,
        )
        log_event({
            'type':'model_loaded',
            'engine':'nitro-faster-whisper-tiny',
            'model':str(LOCAL_FAST_MODEL_PATH),
            'device':LOCAL_FAST_DEVICE,
            'compute_type':LOCAL_FAST_COMPUTE_TYPE,
            'seconds':round(time.monotonic()-started,3),
        })
    return LOCAL_MODEL

def load_model() -> None:
    if not WHISPER_CPP_EXE.exists():
        raise RuntimeError(f'whisper.cpp executable missing: {WHISPER_CPP_EXE}')
    if not Path(MODEL_PATH).exists():
        raise RuntimeError(f'whisper.cpp model missing: {MODEL_PATH}')
    log_event({'type':'model_loaded','engine':'thor-faster-whisper-large-v3','model':MODEL_PATH,'exe':str(WHISPER_CPP_EXE)})
    return None

def transcribe_pcm_local_fast(wav_path: Path, rms: float, voiced_ratio: float, voiced_frames: int, session: str, language: str) -> dict[str, Any]:
    model = load_local_model()
    started = time.monotonic()
    lang = normalize_stt_language(language)
    segments_iter, info = model.transcribe(
        str(wav_path),
        language=None if lang == 'auto' else lang,
        beam_size=1,
        best_of=1,
        temperature=0,
        vad_filter=False,
        condition_on_previous_text=False,
        word_timestamps=False,
    )
    segments = list(segments_iter)
    elapsed = round(time.monotonic() - started, 3)
    text = ' '.join(str(segment.text or '').strip() for segment in segments).strip()
    avg_logprobs = [float(segment.avg_logprob) for segment in segments if getattr(segment, 'avg_logprob', None) is not None]
    no_speech = [float(segment.no_speech_prob) for segment in segments if getattr(segment, 'no_speech_prob', None) is not None]
    result = {
        'type':'stt','session':session,'engine':'nitro-faster-whisper-tiny','text':text,
        'language':str(getattr(info, 'language', '') or lang),
        'language_probability':getattr(info, 'language_probability', None),
        'rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'voiced_frames':voiced_frames,
        'seconds':elapsed,'avg_logprob':(sum(avg_logprobs)/len(avg_logprobs) if avg_logprobs else None),
        'no_speech_prob':(max(no_speech) if no_speech else None),'time_ms':now_ms(),
    }
    log_event({'type':'transcribed','session':session,**{k:v for k,v in result.items() if k not in {'type','session','time_ms'}}})
    return result

def transcribe_pcm_local_whisper(wav_path: Path, rms: float, voiced_ratio: float, voiced_frames: int, session: str, language: str = 'en') -> dict[str, Any]:
    load_model()
    with tempfile.TemporaryDirectory(prefix='llm-game-stt-local-') as tmp:
        tmpdir = Path(tmp)
        local_wav = tmpdir / 'chunk.wav'
        out_prefix = tmpdir / 'out'
        local_wav.write_bytes(wav_path.read_bytes())
        started = time.monotonic()
        env = os.environ.copy()
        build_root = WHISPER_CPP_EXE.parent.parent
        lib_dirs = [build_root / 'src', build_root / 'ggml' / 'src', build_root / 'ggml' / 'src' / 'ggml-cpu', build_root / 'ggml' / 'src' / 'ggml-cuda', build_root / 'ggml' / 'src' / 'ggml-blas']
        existing = [str(d) for d in lib_dirs if d.exists()]
        env['LD_LIBRARY_PATH'] = ':'.join(existing + ([env['LD_LIBRARY_PATH']] if env.get('LD_LIBRARY_PATH') else []))
        proc = subprocess.run([str(WHISPER_CPP_EXE), '-m', str(MODEL_PATH), '-f', str(local_wav), '-l', 'en', '-nt', '-np', '-otxt', '-of', str(out_prefix)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45, check=False, env=env)
        elapsed = round(time.monotonic() - started, 3)
        txt_path = out_prefix.with_suffix('.txt')
        text = txt_path.read_text(errors='replace').strip() if txt_path.exists() else proc.stdout.strip()
        text = ' '.join(text.split())
        if proc.returncode != 0:
            raise RuntimeError(f'whisper.cpp failed: {proc.stderr[-1000:]}')
    log_event({'type':'transcribed','session':session,'engine':'nitro-whisper-cpp-base-en','text':text,'rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'seconds':elapsed})
    return {'type':'stt','session':session,'engine':'nitro-whisper-cpp-base-en','text':text,'rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'voiced_frames':voiced_frames,'seconds':elapsed,'language':'en','time_ms':now_ms()}

def transcribe_wav_thor(wav_path: Path, rms: float, voiced_ratio: float, voiced_frames: int, session: str, language: str) -> dict[str, Any]:
    started = time.monotonic()
    lang = normalize_stt_language(language)
    with wav_path.open('rb') as handle:
        resp = requests.post(
            THOR_STT_URL,
            files={'audio': ('chunk.wav', handle, 'audio/wav')},
            data={'language':lang,'task':'transcribe'},
            timeout=(THOR_STT_CONNECT_TIMEOUT, THOR_STT_READ_TIMEOUT),
        )
    elapsed = round(time.monotonic() - started, 3)
    resp.raise_for_status()
    obj = resp.json()
    text = ' '.join(str(obj.get('text') or '').split())
    detected = obj.get('language') or obj.get('detected_language') or lang
    lang_prob = obj.get('language_probability')
    engine = 'thor-faster-whisper-large-v3'
    log_event({'type':'transcribed','session':session,'engine':engine,'text':text,'language':detected,'requested_language':lang,'language_probability':lang_prob,'rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'seconds':elapsed,'thor_seconds':obj.get('seconds'),'thor_task':obj.get('task'),'avg_logprob':obj.get('avg_logprob'),'no_speech_prob':obj.get('no_speech_prob'),'compression_ratio':obj.get('compression_ratio'),'segments':obj.get('segments'),'thor_url':THOR_STT_URL})
    return {'type':'stt','session':session,'engine':engine,'text':text,'language':detected,'requested_language':lang,'language_probability':lang_prob,'rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'voiced_frames':voiced_frames,'seconds':elapsed,'thor_seconds':obj.get('seconds'),'thor_task':obj.get('task'),'avg_logprob':obj.get('avg_logprob'),'no_speech_prob':obj.get('no_speech_prob'),'compression_ratio':obj.get('compression_ratio'),'segments':obj.get('segments'),'time_ms':now_ms()}

def transcribe_pcm(pcm: bytes, session: str, language: str | None = None) -> dict[str, Any]:
    activity = pcm_activity(pcm)
    rms = float(activity['rms'])
    voiced_ratio = float(activity['voiced_ratio'])
    voiced_frames = int(activity['voiced_frames'])
    lang = normalize_stt_language(language)
    if rms < RMS_THRESHOLD or voiced_ratio < 0.03 or voiced_frames < 1:
        log_event({'type':'transcribed','session':session,'text':'','reason':'silence','rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'voiced_frames':voiced_frames})
        return {'type':'stt','session':session,'text':'','rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'voiced_frames':voiced_frames,'reason':'silence','time_ms':now_ms()}
    with tempfile.TemporaryDirectory(prefix='llm-game-stt-') as tmp:
        wav_path = Path(tmp) / 'chunk.wav'
        pcm_to_wav(pcm, wav_path)
        errors: list[str] = []
        if STT_BACKEND in {'local','local-first','hybrid'}:
            try:
                result = transcribe_pcm_local_fast(wav_path, rms, voiced_ratio, voiced_frames, session, lang)
                if str(result.get('text') or '').strip():
                    return result
                errors.append('local_fast_empty')
            except Exception as exc:
                errors.append(f'local_fast:{exc.__class__.__name__}:{exc}')
                log_event({'type':'local_stt_error','session':session,'error':f'{exc.__class__.__name__}: {exc}','model':str(LOCAL_FAST_MODEL_PATH)})
        if THOR_STT_URL and STT_BACKEND not in {'local'}:
            try:
                result = transcribe_wav_thor(wav_path, rms, voiced_ratio, voiced_frames, session, lang)
                if str(result.get('text') or '').strip():
                    return result
                errors.append('thor_empty')
            except Exception as exc:
                errors.append(f'thor:{exc.__class__.__name__}:{exc}')
                log_event({'type':'thor_stt_error','session':session,'error':f'{exc.__class__.__name__}: {exc}','url':THOR_STT_URL})
        if ALLOW_LOCAL_STT_FALLBACK:
            try:
                return transcribe_pcm_local_whisper(wav_path, rms, voiced_ratio, voiced_frames, session, lang)
            except Exception as exc:
                errors.append(f'whisper_cpp:{exc.__class__.__name__}:{exc}')
                log_event({'type':'local_whisper_cpp_error','session':session,'error':f'{exc.__class__.__name__}: {exc}'})
        return {'type':'stt','session':session,'text':'','rms':round(rms,5),'voiced_ratio':round(voiced_ratio,3),'voiced_frames':voiced_frames,'reason':'stt_unavailable','suppressed':True,'errors':errors[-3:],'time_ms':now_ms()}

def norm_text(text: str) -> str:
    return ' '.join(''.join(ch.lower() if ch.isalnum() else ' ' for ch in text).split())

def token_set(text: str) -> set[str]:
    return set(norm_text(text).split())

def repeated_word_run(text: str) -> bool:
    words = norm_text(text).split()
    if len(words) < 4:
        return False
    for i in range(len(words)-2):
        if words[i] == words[i+1] == words[i+2]:
            return True
    if len(words) >= 6 and len(set(words)) <= max(2, len(words)//3):
        return True
    return False

def is_duplicate(new_text: str, state: dict[str, Any]) -> bool:
    n = norm_text(new_text)
    if not n or len(n) < 3:
        return True
    # Repeated concrete nouns such as 'cat cat cat' are valid speech topics.
    # Do not drop them here; the LLM/topic validator decides whether they become world objects.
    recent = state.setdefault('recent_norms', [])
    if n in recent:
        return True
    new_tokens = token_set(new_text)
    for old in recent[-6:]:
        old_tokens = set(old.split())
        if not old_tokens or not new_tokens:
            continue
        overlap = len(new_tokens & old_tokens) / max(1, min(len(new_tokens), len(old_tokens)))
        if overlap >= 0.75:
            return True
        if n in old or old in n:
            return True
    recent.append(n)
    del recent[:-8]
    state['last_text'] = new_text
    return False

async def emit_transcription(websocket, session: str, chunk: bytes, state: dict[str, Any]) -> None:
    state['busy'] = True
    state['last_started'] = time.monotonic()
    try:
        language = normalize_stt_language(state.get('language'))
        await websocket.send(json.dumps({'type':'stt_processing','session':session,'language':language,'audio_seconds':round(len(chunk)/BYTES_PER_SECOND,3),'backend':STT_BACKEND,'time_ms':now_ms()}))
        async with MODEL_LOCK:
            result = await asyncio.to_thread(transcribe_pcm, chunk, session, language)
        text = str(result.get('text') or '').strip()
        accepted, accept_reason = should_accept_stt_result(result)
        if not accepted:
            original_reason = str(result.get('reason') or '')
            reason = original_reason or accept_reason
            log_event({'type':'stt_rejected','session':session,'text':text,'reason':reason,'accept_reason':accept_reason,'rms':result.get('rms'),'voiced_ratio':result.get('voiced_ratio'),'seconds':result.get('seconds'),'engine':result.get('engine')})
            result['text'] = ''
            result['new_text'] = ''
            result['full_text'] = state.get('full_text','')
            result['duplicate'] = True
            result['reason'] = reason
            result['suppressed'] = True
            if reason == 'thor_stt_unavailable':
                log_event({'type':'audio_backlog_cleared_after_stt_error','session':session})
                await websocket.send(json.dumps(result))
            return
        duplicate = is_duplicate(text, state)
        result['duplicate'] = bool(duplicate)
        if text:
            state['full_text'] = trim_scene_words((state.get('full_text','') + ' ' + text), 100)
            result['new_text'] = '' if duplicate else text
        else:
            result['new_text'] = ''
        result['full_text'] = state.get('full_text','')
        await websocket.send(json.dumps(result))
        if text:
            topic_text = trim_scene_words(state.get('full_text','') or text, 100)
            log_event({'type':'topic_chunk_cut','session':session,'chars':len(topic_text),'text':topic_text,'source':'immediate'})
            topic_result = await asyncio.to_thread(extract_topic_candidates, topic_text)
            if str(topic_result.get('engine')) == 'llama-error':
                msg = {'type':'topic_error','session':session,'engine':'llama','error':topic_result.get('error','unknown topic extractor error'),'source_text_chars':len(topic_text),'time_ms':now_ms()}
                await websocket.send(json.dumps(msg))
                log_event({'type':'topic_error_sent','session':session,'source':'immediate','error':msg['error'],'source_text_chars':len(topic_text)})
            else:
                candidates = topic_result.get('candidates', []) if isinstance(topic_result, dict) else []
                known = state.setdefault('topic_counts', {})
                for item in candidates:
                    name = item.get('name', '')
                    known[name] = known.get(name, 0) + int(item.get('weight', 1))
                msg = {'type':'topics','session':session,'engine':'llama','source_text_chars':len(topic_text),'source_text':topic_result.get('scene_text', topic_text),'candidates':candidates,'topic_counts':known,'llm_raw':topic_result.get('raw_content',''),'rejected':topic_result.get('rejected',[]),'time_ms':now_ms()}
                await websocket.send(json.dumps(msg))
                if candidates:
                    log_event({'type':'topics_sent','session':session,'engine':'llama','source':'immediate','candidates':candidates})
                else:
                    log_event({'type':'topics_empty_sent','session':session,'engine':'llama','source':'immediate','source_text_chars':len(topic_text)})
    except Exception as exc:
        try:
            await websocket.send(json.dumps({'type':'error','session':session,'error':f'{exc.__class__.__name__}: {exc}','time_ms':now_ms()}))
        except Exception:
            pass
    finally:
        state['busy'] = False


def vad_state(state: dict[str, Any]) -> dict[str, Any]:
    vad = state.get('vad')
    if not isinstance(vad, dict):
        vad = {'pre': bytearray(), 'utt': bytearray(), 'rem': bytearray(), 'active': False, 'speech_bytes': 0, 'silence_bytes': 0}
        state['vad'] = vad
    return vad


def reset_vad(vad: dict[str, Any]) -> None:
    vad['utt'] = bytearray()
    vad['pre'] = bytearray()
    vad['rem'] = bytearray()
    vad['active'] = False
    vad['speech_bytes'] = 0
    vad['silence_bytes'] = 0


async def maybe_transcribe(websocket, session: str, audio: bytearray, state: dict[str, Any], force: bool=False) -> None:
    vad = vad_state(state)
    if audio:
        vad['rem'].extend(audio)
        audio.clear()
    frame_bytes = max(2, int(SAMPLE_RATE * 0.03) * 2)
    pre_max = int(UTTERANCE_PREROLL_SECONDS * BYTES_PER_SECOND)
    min_utt = int(UTTERANCE_MIN_SECONDS * BYTES_PER_SECOND)
    max_utt = int(UTTERANCE_MAX_SECONDS * BYTES_PER_SECOND)
    end_silence = int(UTTERANCE_END_SILENCE_SECONDS * BYTES_PER_SECOND)
    chunks: list[bytes] = []
    while len(vad['rem']) >= frame_bytes:
        frame = bytes(vad['rem'][:frame_bytes])
        del vad['rem'][:frame_bytes]
        rr = frame_rms(frame)
        if not vad['active']:
            vad['pre'].extend(frame)
            if len(vad['pre']) > pre_max:
                del vad['pre'][:-pre_max]
            if rr >= UTTERANCE_START_RMS:
                vad['active'] = True
                vad['utt'].extend(vad['pre'])
                vad['pre'].clear()
                vad['speech_bytes'] = frame_bytes
                vad['silence_bytes'] = 0
                log_event({'type':'utterance_start','session':session,'rms':round(rr,5),'bytes':len(vad['utt'])})
            continue
        vad['utt'].extend(frame)
        if rr >= UTTERANCE_CONTINUE_RMS:
            vad['speech_bytes'] += frame_bytes
            vad['silence_bytes'] = 0
        else:
            vad['silence_bytes'] += frame_bytes
        if (vad['silence_bytes'] >= end_silence and len(vad['utt']) >= min_utt) or len(vad['utt']) >= max_utt:
            chunk = bytes(vad['utt'])
            log_event({'type':'utterance_end','session':session,'bytes':len(chunk),'speech_bytes':vad.get('speech_bytes',0),'silence_bytes':vad.get('silence_bytes',0),'force':False})
            chunks.append(chunk)
            reset_vad(vad)
    if force:
        if vad['active'] and len(vad['utt']) >= min_utt:
            if vad['rem']:
                vad['utt'].extend(vad['rem']); vad['rem'].clear()
            chunk = bytes(vad['utt'])
            log_event({'type':'utterance_end','session':session,'bytes':len(chunk),'speech_bytes':vad.get('speech_bytes',0),'silence_bytes':vad.get('silence_bytes',0),'force':True})
            chunks.append(chunk)
        reset_vad(vad)
    for chunk in chunks:
        while state.get('busy'):
            await asyncio.sleep(0.02)
        await emit_transcription(websocket, session, chunk, state)


TOPIC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["candidates"],
    "properties": {
        "candidates": {
            "type": "array",
            "minItems": 0,
            "maxItems": 24,
            "items": {"type": "string"}
        }
    }
}

STOPWORDS = set('the a an and or but if then else because about actually really maybe okay hello hi how are you what is that this there here click button microphone bluetooth phone browser text window start stop working works does did doing it its i you he she we they them me my your our their to of in on for with from at by as be been being was were will would should could can just like look see say said talk talking good bad thing things stuff whatever ignore ignored ignoring fuck fucking shit asshole retarded useless need needs needed have has had do does did not no yes now later current currently simply probably possible possible so into across around all'.split())

CATEGORY_HINTS = {
    'cat':'animal','cats':'animal','dog':'animal','dogs':'animal','hund':'animal','hunde':'animal','horse':'animal','horses':'animal','pferd':'animal','bird':'animal','birds':'animal','vogel':'animal','cow':'animal','kuh':'animal',
    'tree':'plant','trees':'plant','baum':'plant','flower':'plant','flowers':'plant','blume':'plant','blumen':'plant','flauer':'plant','flauers':'plant','grass':'plant','cactus':'plant','kaktus':'plant',
    'house':'place','houses':'place','haus':'place','haeuser':'place','city':'place','street':'place','streets':'place','ground':'place','castle':'place','door':'object','gate':'object',
    'car':'vehicle','bus':'vehicle','train':'vehicle','ship':'vehicle','plane':'vehicle','bicycle':'vehicle','bike':'vehicle','fahrrad':'vehicle','fahrraeder':'vehicle','mountainbike':'vehicle','rennrad':'vehicle',
    'stone':'object','stones':'object','rock':'object','rocks':'object','boulder':'object','bone':'object','bones':'object','poop':'object','shit':'object','crap':'object','kacke':'object','trash':'object',
    'toilet':'object','toilette':'object','toothbrush':'object','teeth':'object','tooth':'object','bottle':'object','smell cloud':'object','decay':'object','music':'object','song':'object','microphone':'object','phone':'object','computer':'object',
    'cupcake':'food','cupcakes':'food','cake':'food','bread':'food','coffee':'food','kaffee':'food','juice':'food','saft':'food','milkshake':'food','wiener':'food','apple':'food','banana':'food','pizza':'food',
    'cup':'object','tasse':'object','plate':'object','plates':'object','teller':'object','table':'object','tables':'object','tisch':'object','coffee table':'object','couchtisch':'object','picture':'object','word':'object',
    'superhero':'person','superheld':'person','held':'person','people':'person','person':'person','jews':'person','jewish':'person','hobo':'person','hobos':'person','homeless':'person','homeless person':'person','singer':'person','dancing':'person','lying person':'person','doctor':'person','child':'person','baby':'person',
    'monster':'fantasy','shrek':'fantasy','dragon':'fantasy','drache':'fantasy','ghost':'fantasy','robot':'object',
}


DRAWABLE_CANONICAL = {
    'cat':('cat','animal'), 'cats':('cat','animal'), 'katze':('katze','animal'), 'katzen':('katze','animal'),
    'dog':('dog','animal'), 'dogs':('dog','animal'), 'hund':('hund','animal'), 'hunde':('hund','animal'),
    'horse':('horse','animal'), 'horses':('horse','animal'), 'pferd':('pferd','animal'), 'pferde':('pferd','animal'),
    'bird':('bird','animal'), 'vogel':('vogel','animal'), 'cow':('cow','animal'), 'kuh':('kuh','animal'), 'kühe':('kuh','animal'),
    'tree':('tree','plant'), 'trees':('tree','plant'), 'baum':('baum','plant'), 'bäume':('baum','plant'),
    'flower':('flower','plant'), 'flowers':('flower','plant'), 'blume':('blume','plant'), 'blumen':('blume','plant'), 'cactus':('cactus','plant'), 'kaktus':('kaktus','plant'),
    'house':('house','place'), 'houses':('house','place'), 'haus':('haus','place'), 'häuser':('haus','place'),
    'car':('car','vehicle'), 'cars':('car','vehicle'), 'auto':('auto','vehicle'), 'autos':('auto','vehicle'),
    'stone':('stone','object'), 'stones':('stone','object'), 'rock':('rock','object'), 'rocks':('rock','object'), 'stein':('stein','object'), 'steine':('stein','object'), 'fels':('fels','object'),
    'cupcake':('cupcake','food'), 'cupcakes':('cupcake','food'), 'cake':('cake','food'), 'kuchen':('kuchen','food'),
    'coffee':('coffee','food'), 'kaffee':('kaffee','food'), 'cup':('cup','object'), 'tasse':('tasse','object'),
    'plate':('plate','object'), 'plates':('plate','object'), 'teller':('teller','object'),
    'table':('table','object'), 'tables':('table','object'), 'tisch':('tisch','object'), 'coffee table':('coffee table','object'), 'couchtisch':('couchtisch','object'),
    'chili':('chili','food'), 'pepper':('pepper','food'), 'paprika':('paprika','food'),
    'superhero':('superhero',), 'superheld':('superheld',), 'held':('held',),
    'monster':('monster','fantasy'), 'shrek':('shrek','fantasy'), 'dragon':('dragon','fantasy'), 'drache':('drache','fantasy'),
}
TOPIC_IGNORED_WORDS = {
    'hallo','hello','hey','yo','richie','coach','doktor','doctor','wes','uessu','danke','thank','you','bitte','ja','nein','okay','ok','zofo',
    'maedels','madel','maedel','girl','girls','name','thema','rolle','wahl',
    'weg','wegen','vorstadt','trainieren','training','talentiert','vernuenftig','vernunftig',
    'mahlzeit','koks','diaet','scheissperfekt','perfekt','break','уэссу','доктор',
    'word','words','picture','pictures','debug','button','browser','microphone','app','speech','foreign','language','speaking',
}

def fold_text(text: str) -> str:
    raw = ' '.join(str(text or '').lower().strip().split())
    raw = raw.replace('ß','ss').replace('ä','ae').replace('ö','oe').replace('ü','ue')
    raw = ''.join(ch if (ch.isalnum() or ch.isspace() or ch in '-_') else ' ' for ch in raw)
    return ' '.join(raw.split())

def preserve_word_text(text: str) -> str:
    raw = ' '.join(str(text or '').strip().split())
    out=[]
    for ch in raw:
        cat=unicodedata.category(ch)
        if ch.isspace() or ch in '-_': out.append(' ')
        elif cat[0] in ('L','N'): out.append(ch.lower())
        else: out.append(' ')
    return ' '.join(''.join(out).split())

def canonical_drawable_name(name: str) -> tuple[str, str] | None:
    n = preserve_word_text(name)
    f = fold_text(n)
    if not f or f in TOPIC_IGNORED_WORDS or n in TOPIC_IGNORED_WORDS:
        return None
    val = DRAWABLE_CANONICAL.get(f) or DRAWABLE_CANONICAL.get(n)
    if isinstance(val, tuple) and len(val) == 2:
        return val
    for suffix in ('en','e','s'):
        if f.endswith(suffix):
            val = DRAWABLE_CANONICAL.get(f[:-len(suffix)])
            if isinstance(val, tuple) and len(val) == 2:
                return val
    return None


DRAWABLE_CANONICAL.update({
    'milk':('milch','food'), 'milch':('milch','food'),
    'wiener':('wiener','food'), 'hotdog':('wiener','food'), 'sausage':('wiener','food'), 'wurst':('wiener','food'),
    'heart':('heart','object'), 'herz':('herz','object'),
    'energy':('energie','object'), 'energie':('energie','object'), 'lightning':('energie','object'), 'blitz':('energie','object'),
    'nail':('nagel','object'), 'nails':('nagel','object'), 'nagel':('nagel','object'), 'nägel':('nagel','object'),
    'rescue':('rettung','object'), 'rettung':('rettung','object'), 'rettungen':('rettung','object'),
    'planet':('planet','object'), 'planets':('planet','object'),
    'pause':('pause','object'), 'minute':('pause','object'), 'minutes':('pause','object'), 'minuten':('pause','object'),
    'demo':('demo','object'), 'shield':('schild','object'), 'schild':('schild','object'),
    'meow':('katze','animal'), 'miau':('katze','animal'),
})
TOPIC_IGNORED_WORDS.update({'ashley','ryan','tim','noah','homelander','peter','franzose','franzosen','pippi','langstrumpf','total','ward','home teamer','a train','a-train'})

DRAWABLE_CANONICAL.update({
    'city':('city','place'), 'stadt':('city','place'), 'street':('street','place'), 'straße':('street','place'), 'strasse':('street','place'),
    'stage':('stage','place'), 'bühne':('stage','place'), 'buehne':('stage','place'), 'camera':('camera','object'), 'kamera':('camera','object'),
    'watchlist':('watchlist','object'), 'nachricht':('message','object'), 'nachrichten':('message','object'), 'message':('message','object'),
    'child':('child',), 'kind':('child',), 'baby':('baby',), 'trauma':('shadow','object'),
    'nerves':('lightning','object'), 'nerven':('lightning','object'), 'scheisse':('trash','object'), 'scheiße':('trash','object'),
    'blood':('blood','object'), 'blut':('blood','object'),  'water':('water','weather'), 'wasser':('water','weather'), 'wet':('water','weather'), 'nass':('water','weather'),
    'promise':('scroll','object'), 'versprechen':('scroll','object'), 'schwur':('scroll','object'), 'truth':('scroll','object'), 'wahrheit':('scroll','object'),
    'fear':('shadow','object'), 'angst':('shadow','object'), 'support':('shield','object'), 'unterstützung':('shield','object'), 'unterstuetzung':('shield','object'),
    'rescue':('rettung','object'), 'rettung':('rettung','object'), 'training':('training','object'), 'trainieren':('training','object'), 'stunt':('stunt','object'),
})

SEMANTIC_SCENE_RULES = [
    (('katze','cat','meow','miau'), [('katze','animal'),('fisch','food'),('milch','food')]),
    (('hund','dog','bark','bellen'), [('hund','animal'),('bone','object')]),
    (('rettung','rescue','save','saved','gerettet','retten'), [('rettung','object'),('shield','object'),('city','place'),('superheld',)]),
    (('superheld','hero','held','homelander','a-train','super'), [('superheld',),('cape','object'),('lightning','object'),('city','place')]),
    (('training','trainieren','probe','proben','stunt','auftritt','positionen'), [('training','object'),('stage','place'),('camera','object'),('pause','object')]),
    (('nachricht','nachrichten','news','landesweit','demo','watchlist'), [('message','object'),('demo','object'),('camera','object'),('city','place')]),
    (('planet','ward','südamerika','suedamerika','franzose','franzose'), [('planet','object'),('flag','object'),('city','place')]),
    (('kind','baby','milch','titten','kindheit'), [('baby',),('milch','food'),('heart','object')]),
    (('angst','trauma','nerven','scheisse','scheiße','verflucht'), [('shadow','object'),('lightning','object'),('trash','object')]),
    (('versprechen','schwur','wahrheit','sprechen','sagen'), [('scroll','object'),('speech bubble','object')]),
    (('essen','mahlzeit','wiener','koks','diät','diaet','spuck'), [('wiener','food'),('plate','object'),('cup','object')]),
    (('wasser','nass','fresse'), [('water','weather'),('face',)]),
]

INFERRED_CANONICAL = {
    'fisch':('fish','animal'), 'bone':('bone','object'), 'cape':('cape','object'), 'lightning':('energie','object'), 'flag':('flag','object'),
    'baby':('baby',), 'shadow':('shadow','object'), 'trash':('trash','object'), 'scroll':('scroll','object'), 'speech bubble':('speech bubble','object'),
    'face':('face',), 'shield':('shield','object'), 'stage':('stage','place'), 'camera':('camera','object'), 'message':('message','object'),
    'city':('city','place'), 'street':('street','place'), 'water':('water','weather'), 'training':('training','object'), 'stunt':('stunt','object'),
}
DRAWABLE_CANONICAL.update(INFERRED_CANONICAL)

VARIED_SCENE_EXTRA_CANONICAL = {
    'milkshake':('milkshake','food'), 'milchshake':('milkshake','food'), 'shake':('milkshake','food'),
    'video':('video','object'), 'videos':('video','object'),
    'split':('clone',), 'teilen':('clone',), 'geteilt':('clone',), 'clone':('clone',), 'clones':('clone',),
    'death':('skull','object'), 'dead':('skull','object'), 'tot':('skull','object'), 'sterben':('skull','object'), 'leichen':('skull','object'),
    'promise':('scroll','object'), 'versprochen':('scroll','object'), 'versprechen':('scroll','object'),
    'thought':('thought','object'), 'gedanken':('thought','object'), 'sorge':('thought','object'),
    'values':('graph','object'), 'werte':('graph','object'),
    'single rescue':('rettung','object'), 'einzelrettung':('rettung','object'), 'einzelrettungen':('rettung','object'),
    'brian':('portrait',), 'portrait':('portrait',), 'love':('heart','object'), 'geliebt':('heart','object'),
}
DRAWABLE_CANONICAL.update(VARIED_SCENE_EXTRA_CANONICAL)
INFERRED_CANONICAL.update({
    'milkshake':('milkshake','food'), 'video':('video','object'), 'clone':('clone',), 'skull':('skull','object'), 'thought':('thought','object'), 'graph':('graph','object'), 'portrait':('portrait',),
    'street':('street','place'), 'watchlist':('watchlist','object'), 'trash':('trash','object'), 'speech bubble':('speech bubble','object'), 'stage':('stage','place'), 'shadow':('shadow','object'),
})
DRAWABLE_CANONICAL.update(INFERRED_CANONICAL)
SEMANTIC_SCENE_RULES.extend([
    (('milchshake','milkshake','shake','cremig','köstlich','koestlich'), [('milkshake','food'),('cup','object'),('milk','food')]),
    (('video','geliebt','brian'), [('video','object'),('portrait',),('heart','object')]),
    (('teilen','split','clone','geteilt'), [('clone',),('mirror','object'),('shadow','object')]),
    (('tot','sterben','dead','death','leichen'), [('skull','object'),('shadow','object'),('grave','object')]),
    (('einzelrettung','einzelrettungen','rettungen','rettung','versprochen'), [('rettung','object'),('shield','object'),('city','place'),('cape','object')]),
    (('werte','values'), [('graph','object'),('scroll','object')]),
    (('sorge','gedanken','worry'), [('thought','object'),('speech bubble','object')]),
])

RECENCY_SCENE_EXTRA_CANONICAL = {
    'ticket':('ticket','object'), 'tickets':('ticket','object'), 'karte':('ticket','object'), 'karten':('ticket','object'),
    'music':('music','object'), 'musik':('music','object'), 'joel':('music','object'),
    'door':('door','object'), 'doors':('door','object'), 'haustür':('door','object'), 'haustuer':('door','object'), 'tür':('door','object'), 'tuer':('door','object'),
    'doctor':('doctor',), 'arzt':('doctor',), 'ärztin':('doctor',),
    'court':('court','place'), 'gericht':('court','place'), 'vollmacht':('document','object'), 'entscheidung':('document','object'), 'medizinische':('medical cross','object'),
    'document':('document','object'), 'letter':('letter','object'), 'freude':('heart','object'), 'joy':('heart','object'),
    'trash':('trash','object'), 'scheisse':('trash','object'), 'scheiße':('trash','object'),
}
DRAWABLE_CANONICAL.update(RECENCY_SCENE_EXTRA_CANONICAL)
INFERRED_CANONICAL.update({
    'ticket':('ticket','object'), 'music':('music','object'), 'door':('door','object'), 'doctor':('doctor',), 'court':('court','place'), 'document':('document','object'), 'letter':('letter','object'), 'medical cross':('medical cross','object')
})
DRAWABLE_CANONICAL.update(INFERRED_CANONICAL)
SEMANTIC_SCENE_RULES.extend([
    (('ticket','tickets','billy','joel','freude'), [('ticket','object'),('music','object'),('heart','object')]),
    (('haustür','haustuer','tür','tuer','woche','gewartet'), [('door','object'),('clock','object'),('shadow','object')]),
    (('arzt','medizinische','entscheidung','gericht','vollmacht'), [('doctor',),('medical cross','object'),('document','object'),('court','place')]),
    (('scheisse','scheiße','stinkt','hassen'), [('trash','object'),('shadow','object')]),
])



TOOTHBRUSH_POOP_BIKE_HUMAN_TOPICS = {
    'toothbrush':('toothbrush','object'), 'toothbrushes':('toothbrush','object'), 'zahnbuerste':('toothbrush','object'),
    'teeth':('teeth','object'), 'tooth':('teeth','object'), 'zaehne':('teeth','object'),
    'toilet':('toilet','object'), 'toilette':('toilet','object'), 'wc':('toilet','object'),
    'juice':('juice','food'), 'saft':('juice','food'), 'dancing':('dancing','person'), 'dance':('dancing','person'),
    'jews':('people','person'), 'jewish':('people','person'),
    'shit':('poop','object'), 'crap':('poop','object'), 'poop':('poop','object'), 'feces':('poop','object'), 'faeces':('poop','object'), 'dogshit':('poop','object'), 'dog shit':('poop','object'), 'scheisse':('poop','object'), 'shit_ru':('poop','object'), 'kacke':('poop','object'),
    'bike':('bicycle','object'), 'bikes':('bicycle','object'), 'bicycle':('bicycle','object'), 'bicycles':('bicycle','object'), 'fahrrad':('bicycle','object'), 'fahrraeder':('bicycle','object'), 'mountainbike':('mountainbike','object'), 'rennrad':('racing bike','object'),
    'flower':('blume','plant'), 'flowers':('blume','plant'), 'flauer':('blume','plant'), 'flauers':('blume','plant'), 'bone':('bone','object'), 'bones':('bone','object'),
    'hobo':('hobo','person'), 'hobos':('hobo','person'), 'homeless':('homeless person','person'), 'homeless people':('homeless person','person'), 'homeless person':('homeless person','person'), 'homeless boys':('homeless person','person'),
    'lying':('lying person','person'), 'ground':('ground','place'), 'rotting':('decay','object'), 'stinky':('smell cloud','object'), 'alcoholic':('bottle','object'), 'alcohol':('bottle','object'), 'bottle':('bottle','object'),
    'singing':('singer','person'), 'sing':('singer','person'), 'singer':('singer','person'), 'song':('music','object'), 'havana':('music','object'), 'hava':('music','object'), 'gila':('music','object'), 'streets':('street','place'),
}
DRAWABLE_CANONICAL.update(TOOTHBRUSH_POOP_BIKE_HUMAN_TOPICS)
INFERRED_CANONICAL.update(TOOTHBRUSH_POOP_BIKE_HUMAN_TOPICS)
SEMANTIC_SCENE_RULES.extend([
    (('toothbrush','teeth','tooth','zahnbuerste','zaehne'), [('toothbrush','object'),('teeth','object')]),
    (('toilette','toilet','wc'), [('toilet','object')]),
    (('juice','saft'), [('juice','food'),('cup','object')]),
    (('shit','crap','poop','dog shit','dogshit','scheisse','kacke','шит'), [('poop','object'),('trash','object'),('dog','animal'),('bone','object')]),
    (('fahrrad','fahrraeder','mountainbike','rennrad','bike','bicycle'), [('bicycle','object'),('mountainbike','object'),('racing bike','object')]),
    (('flauer','flauers','flower','flowers','blumen','blume'), [('blume','plant')]),
    (('dancing','dance'), [('dancing','person'),('music','object')]),
    (('jews','jewish','people'), [('people','person'),('singer','person'),('dancing','person')]),
    (('hobo','hobos','homeless'), [('hobo','person'),('homeless person','person'),('lying person','person'),('bottle','object')]),
    (('lying','ground'), [('lying person','person'),('ground','place')]),
    (('rotting','stinky'), [('decay','object'),('smell cloud','object'),('poop','object')]),
    (('alcoholic','alcohol','bottle'), [('bottle','object'),('hobo','person')]),
    (('singing','sing','song','havana','hava','gila'), [('singer','person'),('music','object')]),
])

def clean_candidate_name(raw: str) -> str:
    return preserve_word_text(raw)[:60]


def category_for_candidate(name: str) -> str:
    canon = canonical_drawable_name(name)
    if canon:
        return canon[1]
    return 'unknown'



def transcript_tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w-]{2,}", fold_text(text), flags=re.UNICODE))


def candidate_in_transcript(name: str, text: str) -> bool:
    f_name = fold_text(name)
    f_text = ' ' + fold_text(text) + ' '
    words = re.findall(r"[\w-]{2,}", f_name, flags=re.UNICODE)
    if not words:
        return False
    if ' ' + f_name + ' ' in f_text:
        return True
    toks = transcript_tokens(text)
    for w in words:
        singular = w[:-1] if w.endswith('s') else w
        plural = w + 's'
        if w not in toks and singular not in toks and plural not in toks:
            return False
    return True



VISUAL_STOP_SCENE_WORDS = set('thank thanks you peace bitte danke ok okay ja nein hello hi hey'.split())
PROFANITY_ONLY_WORDS = set('hurensohn hurensoehne hurensohne ohrensohn verdammte verdammt fuck fucking shit scheisse scheiße'.split())

def has_scene_signal(text: str) -> bool:
    f = fold_text(text)
    toks = [t for t in f.split() if t]
    if not toks:
        return False
    meaningful = [t for t in toks if t not in VISUAL_STOP_SCENE_WORDS]
    if not meaningful:
        return False
    if all(t in PROFANITY_ONLY_WORDS for t in meaningful):
        return False
    return True


def is_placeholder_stt_text(text: str) -> bool:
    raw = str(text or '').strip()
    f = fold_text(raw)
    if not f:
        return True
    # Whisper placeholder captions, not user speech. Suppress all variants before transcript/status/topics.
    if 'foreign language' in f or 'singing in' in f or 'speaking in' in f:
        return True
    if re.search(r'(undertexter|subtitles?|subtitle|caption|captions?)\s+(av|by|from)', f):
        return True
    if re.search(r'^(undertexter|subtitles?|subtitle|caption|captions?)\b', f):
        return True
    if 'non english speech' in f or 'non-english speech' in raw.lower():
        return True
    if re.fullmatch(r'\[?non[- ]english speech\]?', f):
        return True
    if re.fullmatch(r'\(?\s*(speaking|singing|music|speaks|sings)\s+in\s+foreign\s+language\s*\)?', f):
        return True
    if f in {'thank you for watching','thanks for watching','subtitle','subtitles'}:
        return True
    return False



def should_accept_stt_result(result: dict[str, Any]) -> tuple[bool, str]:
    text = str(result.get('text') or '').strip()
    if not text:
        return False, 'empty'
    return True, 'accepted'


SCENE_LLAMA_URL = os.environ.get('LLM_GAME_SCENE_LLAMA_URL', 'http://10.8.0.7:14829')
SCENE_PLANNER_TIMEOUT_SECONDS = float(os.environ.get('LLM_GAME_SCENE_PLANNER_TIMEOUT_SECONDS', '3.0'))
SCENE_PLAN_SCHEMA = {
    'type':'object', 'additionalProperties':False, 'required':['objects'],
    'properties':{
        'objects':{
            'type':'array','minItems':1,'maxItems':16,
            'items':{
                'type':'object','additionalProperties':False,
                'required':['name','category','x','y','z','scale','count','motion','prompt'],
                'properties':{
                    'name':{'type':'string','minLength':2,'maxLength':40},
                    'category':{'type':'string','enum':['person','animal','object','place','plant','food','vehicle','weather','sound','fantasy']},
                    'x':{'type':'number','minimum':-1.0,'maximum':1.0},
                    'y':{'type':'number','minimum':-1.0,'maximum':1.0},
                    'z':{'type':'number','minimum':0.0,'maximum':1.0},
                    'scale':{'type':'number','minimum':0.45,'maximum':1.8},
                    'count':{'type':'integer','minimum':1,'maximum':4},
                    'motion':{'type':'string','enum':['idle','walk','dance','sing','lie','float','pulse','roll','wag','steam','spin']},
                    'prompt':{'type':'string','minLength':4,'maxLength':180}
                }
            }
        }
    }
}

def trim_scene_words(text: str, max_words: int = 100) -> str:
    words = str(text or '').split()
    return ' '.join(words[-max_words:])

def clean_scene_object_name(name: str) -> str:
    n = preserve_word_text(name)[:40]
    return n or 'object'

def call_scene_planner(scene_text: str) -> dict[str, Any] | None:
    scene_text = trim_scene_words(scene_text, 100)
    if len(scene_text) < 3:
        return None
    prompt = (
        'You are the scene planner for a live 2.5D game. Read the transcript window and create the whole scene. '
        'Only create drawable visual objects, materials, fluids, places, animals, vehicles, plants, weather, or effects that are justified by the transcript. '
        'Use concrete visible entities only: people, animals, objects, places, plants, vehicles, food, weather, sound symbols. '
        'For each object choose x and y relative to the player in range -1..1, z depth 0..1, scale, count, motion, and a short visual prompt for an image generator. '
        'Keep the newest spoken content most important but keep useful context from the 100-word window. Return JSON only.\nTRANSCRIPT WINDOW:\n' + scene_text
    )
    payload = {
        'prompt': prompt,
        'n_predict': 420,
        'temperature': 0.10,
        'top_p': 0.85,
        'seed': int(time.time()*1000) % 1000000,
        'json_schema': SCENE_PLAN_SCHEMA,
        'cache_prompt': False,
    }
    started = time.monotonic()
    try:
        url = SCENE_LLAMA_URL.rstrip()
        endpoint = url if url.endswith('/llm') else (url + '/completion')
        resp = requests.post(endpoint, json=payload, timeout=(1.2, SCENE_PLANNER_TIMEOUT_SECONDS))
        resp.raise_for_status()
        jobj = resp.json()
        raw = str(jobj.get('content') or jobj.get('response') or jobj.get('raw') or jobj.get('text') or '')
        if not raw and isinstance(jobj.get('result'), dict):
            raw = str(jobj['result'].get('content') or jobj['result'].get('response') or '')
        objs = extract_json_objects(raw)
        plan = objs[0] if objs and isinstance(objs[0], dict) else json.loads(raw)
        if not isinstance(plan, dict) or not isinstance(plan.get('objects'), list):
            raise ValueError('scene plan missing objects')
        log_event({'type':'scene_plan_llm_ok','seconds':round(time.monotonic()-started,3),'objects':len(plan.get('objects') or []),'scene_chars':len(scene_text),'raw_preview':raw[:500]})
        return plan
    except Exception as exc:
        log_event({'type':'scene_plan_llm_error','seconds':round(time.monotonic()-started,3),'error':f'{exc.__class__.__name__}: {exc}','scene_chars':len(scene_text),'url':SCENE_LLAMA_URL})
        return None

def plan_to_topic_result(plan: dict[str, Any], scene_text: str) -> dict[str, Any]:
    candidates=[]; rejected=[]; seen=set()
    for idx, obj in enumerate((plan.get('objects') or [])[:12]):
        if not isinstance(obj, dict):
            rejected.append({'index':idx,'reason':'not_object'})
            continue
        raw_name = str(obj.get('name') or '').strip()
        name = clean_scene_object_name(raw_name)
        category = str(obj.get('category') or 'object').lower().strip()[:24]
        if not name:
            rejected.append({'index':idx,'reason':'missing_name'})
            continue
        if name in seen:
            rejected.append({'name':name,'reason':'duplicate'})
            continue
        if category not in {'object','animal','place','effect','food','vehicle','plant','house','weather','fluid','material'}:
            rejected.append({'name':name,'reason':'bad_category','category':category})
            continue
        def num(key, default):
            try: return float(obj.get(key, default))
            except Exception: return default
        try:
            count = int(obj.get('count', 1))
        except Exception:
            count = 1
        count = max(1, min(3, count))
        prompt = str(obj.get('prompt') or name).strip()[:220]
        motion = str(obj.get('motion') or 'idle').strip()[:30]
        seen.add(name)
        candidates.append({
            'name': name, 'category': category, 'weight': 6, 'animation': motion,
            'reason': 'model_json_schema', 'x': max(-1,min(1,num('x',0))), 'y': max(-1,min(1,num('y',0))), 'z': max(0,min(1,num('z',0))),
            'scale': max(.35,min(2.2,num('scale',1))), 'count': count, 'prompt': prompt
        })
    return {'engine':'scene-llm-json-schema','seconds':0,'candidates':candidates,'raw_content':json.dumps({'objects':candidates}, ensure_ascii=False),'rejected':rejected, 'scene_text': trim_scene_words(scene_text,100)}

def add_topic_candidate(*args, **kwargs) -> None:
    # Intentionally disabled. Scene content must come from the model JSON output, not keyword hardcodes.
    return None

def fallback_topic_candidates(scene_text: str) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    tokens = re.findall(r'[\w-]{2,}', preserve_word_text(scene_text), flags=re.UNICODE)
    for token in tokens[-48:]:
        canonical = canonical_drawable_name(token)
        if not canonical or len(canonical) != 2:
            continue
        name, category = canonical
        if name in seen:
            continue
        seen.add(name)
        position = len(candidates)
        candidates.append({
            'name':name,'category':category,'weight':3,'animation':'idle','reason':'deterministic_fallback',
            'x':max(-0.8,min(0.8,((position % 5)-2)*0.32)),'y':max(-0.7,min(0.7,((position // 5)-1)*0.35)),
            'z':min(1.0,0.15 + position*0.07),'scale':1.0,'count':1,'prompt':name,
        })
        if len(candidates) >= 10:
            break
    return {'engine':'deterministic-fallback','seconds':0,'candidates':candidates,'raw_content':json.dumps({'objects':candidates},ensure_ascii=False),'rejected':[],'scene_text':trim_scene_words(scene_text,100)}

def extract_topic_candidates(text: str) -> dict[str, Any]:
    scene_text = trim_scene_words(text, 100)
    if len(scene_text) < 1:
        return {'engine':'scene-llm-json-schema','seconds':0,'candidates':[],'raw_content':'{"objects": []}','rejected':[],'scene_text':scene_text}
    plan = call_scene_planner(scene_text)
    if not plan:
        result = fallback_topic_candidates(scene_text)
        log_event({'type':'scene_plan_fallback','engine':result['engine'],'candidate_count':len(result['candidates']),'candidates':result['candidates'],'scene_text':scene_text})
        return result
    result = plan_to_topic_result(plan, scene_text)
    log_event({'type':'scene_plan_result','engine':result['engine'],'candidate_count':len(result['candidates']),'candidates':result['candidates'],'rejected':result.get('rejected',[]),'scene_text':scene_text})
    return result

async def topic_loop(websocket, session: str, state: dict[str, Any]) -> None:
    while True:
        await asyncio.sleep(TOPIC_EXTRACT_EVERY_SECONDS)
        buffer = ' '.join(state.get('topic_buffer', [])).strip()
        if not buffer:
            continue
        state['topic_buffer'] = []
        log_event({'type':'topic_chunk_cut','session':session,'chars':len(buffer),'text':buffer})
        result = await asyncio.to_thread(extract_topic_candidates, buffer)
        if str(result.get('engine')) == 'llama-error':
            msg = {'type':'topic_error','session':session,'engine':'llama','error':result.get('error','unknown topic extractor error'),'source_text_chars':len(buffer),'time_ms':now_ms()}
            try:
                await websocket.send(json.dumps(msg))
            except Exception:
                return
            log_event({'type':'topic_error_sent','session':session,'error':msg['error'],'source_text_chars':len(buffer)})
            continue
        candidates = result.get('candidates', []) if isinstance(result, dict) else []
        known = state.setdefault('topic_counts', {})
        for item in candidates:
            name = item.get('name', '')
            known[name] = known.get(name, 0) + int(item.get('weight', 1))
        msg = {'type':'topics','session':session,'engine':'llama','source_text_chars':len(buffer),'source_text':result.get('scene_text', buffer),'candidates':candidates,'topic_counts':known,'llm_raw':result.get('raw_content',''),'rejected':result.get('rejected',[]),'time_ms':now_ms()}
        try:
            await websocket.send(json.dumps(msg))
        except Exception:
            return
        if candidates:
            log_event({'type':'topics_sent','session':session,'engine':'llama','candidates':candidates,'source':'llm_loop'})
        else:
            log_event({'type':'topics_empty_sent','session':session,'engine':'llama','source_text_chars':len(buffer),'source':'llm_loop'})




def topic_gif_slug(value: str) -> str:
    slug = re.sub(r'[^a-z0-9_-]+', '-', str(value).lower()).strip('-')[:64]
    return slug or 'object'


def extract_json_objects(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    stack = 0
    start = None
    in_string = False
    esc = False
    for i, ch in enumerate(text):
        if in_string:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            if stack == 0:
                start = i
            stack += 1
        elif ch == '}':
            if stack:
                stack -= 1
                if stack == 0 and start is not None:
                    try:
                        obj = json.loads(text[start:i+1])
                        if isinstance(obj, dict):
                            out.append(obj)
                    except Exception:
                        pass
                    start = None
    return out

def normalize_hex_color(value: str, fallback: str) -> str:
    v = str(value or '').strip()
    if re.fullmatch(r'#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?', v):
        return v
    if re.fullmatch(r'[0-9a-fA-F]{6}([0-9a-fA-F]{2})?', v):
        return '#' + v
    return fallback

PIXEL_GRID = 24
PLAN_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['kind', 'palette', 'features', 'animation'],
    'properties': {
        'kind': {'type': 'string', 'enum': ['animal','plant','flower','tree','house','rock','food','person','hero','monster','object']},
        'palette': {'type': 'array', 'minItems': 3, 'maxItems': 3, 'items': {'type': 'string'}},
        'features': {'type': 'array', 'minItems': 2, 'maxItems': 8, 'items': {'type': 'string'}},
        'animation': {'type': 'string', 'enum': ['tail','legs','sparkle','leaf','blink','bounce','flame','cape','idle']}
    }
}

def lexical_sprite_kind(name: str, category: str) -> str:
    canon = canonical_drawable_name(name)
    n = fold_text(canon[0] if canon else name)
    c = (category or '').lower()
    if any(x in n for x in ['horse','pferd','dog','hund','cat','katze','bird','vogel','cow','kuh','sheep','lion','tiger','fish','chicken','rooster']): return 'animal'
    if any(x in n for x in ['tree','baum','forest']): return 'tree'
    if any(x in n for x in ['flower','blume','rose','tulip','flauer']): return 'flower'
    if any(x in n for x in ['cactus','kaktus','plant','leaf','grass']): return 'plant'
    if any(x in n for x in ['house','haus','home','hut','castle','building']) and not any(x in n for x in ['stage','city','street']): return 'house'
    if any(x in n for x in ['stone','stein','rock','fels','boulder']): return 'rock'
    if any(x in n for x in ['coffee','kaffee','cupcake','cake','kuchen','chili','pepper','paprika','apple','fruit','food','milkshake','milch','wiener','juice','saft']): return 'food'
    if any(x in n for x in ['table','tisch','plate','teller','cup','tasse','stage','city','street','ground','camera','message','shield','flag','video','skull','shadow','speech bubble','clone','thought','graph','portrait','scroll','trash','window','grave','mirror','ticket','music','door','court','document','letter','medical cross','clock','cape','poop','bone','toothbrush','teeth','toilet','bicycle','bike','mountainbike','racing bike','rennrad','decay','smell cloud','bottle']): return 'object'
    if any(x in n for x in ['superhero','superheld','hero','held']): return 'hero'
    if any(x in n for x in ['people','person','jews','jewish','hobo','homeless','singer','dancing','lying person','doctor','child','baby']): return 'person'
    if any(x in n for x in ['shrek','ogre','monster','enemy','dragon','drache']): return 'monster'
    if c in {'animal','plant','food'}: return c
    if c == 'person': return 'person'
    if c == 'place': return 'object'
    return ''

def infer_sprite_kind(name: str, category: str, plan: dict[str, Any] | None = None) -> str:
    # Do NOT let the LLM relabel the object class when the word/category is clear.
    lexical = lexical_sprite_kind(name, category)
    if lexical:
        return lexical
    if plan and str(plan.get('kind','')).lower() in {'animal','plant','flower','tree','house','rock','food','hero','monster','object'}:
        return str(plan.get('kind')).lower()
    return 'object'

def color_from_name(name: str, kind: str) -> list[str]:
    n = fold_text(name)
    name_palettes = {
        'katze':['#b8793a','#3a2415','#f6d28b'], 'hund':['#9b6234','#3a2415','#f2d2a0'], 'dog':['#9b6234','#3a2415','#f2d2a0'], 'pferd':['#8b5a2b','#2b160a','#f5d78e'],
        'milch':['#f7f8ff','#3d6bd8','#ffffff'], 'kaffee':['#7a4a23','#2b160a','#d8a35d'], 'juice':['#ff9f1a','#7a3d00','#fff4b0'], 'wiener':['#d9823b','#8b351d','#ffd36a'], 'milkshake':['#f5e7ff','#8d5fbf','#ffffff'],
        'heart':['#e43d5c','#7a1025','#ffd1dc'], 'herz':['#e43d5c','#7a1025','#ffd1dc'], 'energie':['#ffd22e','#ff8c00','#fff3a6'], 'nagel':['#bfc7d5','#505866','#ffffff'],
        'rettung':['#ff3b30','#0d47a1','#ffffff'], 'planet':['#4979d8','#183a7a','#9be7ff'], 'pause':['#ffd45a','#5a3b00','#ffffff'],
        'poop':['#7a3b1d','#2b1209','#d8a35d'], 'bone':['#eadfcb','#6f604e','#fff8e7'], 'toilet':['#e8f7ff','#175a9e','#ffffff'], 'toothbrush':['#7cf9ff','#0d47a1','#ffffff'], 'teeth':['#fff8e7','#6f604e','#ffffff'],
        'bicycle':['#7cf9ff','#12355a','#ffffff'], 'mountainbike':['#5df08a','#145a25','#ffffff'], 'racing bike':['#ffda5a','#7a3d00','#ffffff'],
        'people':['#5aa9ff','#3a1f14','#ffda5a'], 'hobo':['#8b6f52','#3a2a1a','#d9905a'], 'homeless person':['#8b6f52','#3a2a1a','#d9905a'], 'lying person':['#d9905a','#3a1f14','#6b7cff'], 'singer':['#6bd6ff','#12355a','#fff06a'], 'dancing':['#ff6bd6','#5a103a','#ffffff'], 'bottle':['#2fbf8a','#063c2b','#ffffff'], 'decay':['#7a6b3a','#2b2410','#d8b74a'], 'smell cloud':['#9a7b3d','#4a3210','#e8d28a'],
        'demo':['#e8e8e8','#1c1c1c','#ffcc00'], 'teller':['#e8edf7','#6c7a89','#ffffff'], 'tisch':['#8b5a2b','#3b2415','#d8a35d'],
        'haus':['#c96b3a','#6b2e1d','#f7d26a'], 'house':['#c96b3a','#6b2e1d','#f7d26a'], 'baum':['#2fbf4a','#70431f','#b8ff70'], 'tree':['#2fbf4a','#70431f','#b8ff70'], 'blume':['#ff4fb8','#2fbf4a','#fff06a'], 'flower':['#ff4fb8','#2fbf4a','#fff06a'], 'stein':['#8f98a3','#4f5963','#d8dee8'],
        'speech bubble':['#f7fbff','#2a5c7a','#ffffff'], 'stage':['#6b4a9e','#21133a','#ffd45a'], 'shadow':['#2d2540','#0c0a12','#6d5fa8'],
        'city':['#5e7fbf','#1a2b55','#f7d26a'], 'street':['#444b55','#20242b','#ffd45a'], 'ground':['#5b4b32','#2a2118','#9a7b3d'], 'camera':['#2c3440','#0b0e14','#9be7ff'], 'message':['#f3f1dc','#8a6d3b','#ffffff'],
        'shield':['#2f6bff','#0d255f','#ffffff'], 'water':['#3db8ff','#075f91','#b9f2ff'], 'flag':['#e33b3b','#ffffff','#1d4ed8'], 'cape':['#d22d3d','#5c0b18','#ffccaa'],
        'video':['#30343f','#0b0e14','#7cf9ff'], 'clone':['#d9905a','#3a1f14','#b7d7ff'], 'skull':['#e8e8d8','#5f5f55','#ffffff'], 'portrait':['#d9905a','#3a1f14','#5aa9ff'],
        'thought':['#d9e9ff','#4d6c99','#ffffff'], 'graph':['#7bdff2','#1a4960','#ffda5a'], 'scroll':['#e0b86a','#73502a','#fff3c4'], 'trash':['#6d7a75','#26302d','#b6c3bd'],
        'mirror':['#b7d7ff','#2b4b66','#ffffff'], 'grave':['#6f7470','#2a2e2b','#b6c3bd'], 'window':['#5eb7ff','#12355a','#ffffff'],
        'ticket':['#ffd45a','#6b3d00','#ffffff'], 'music':['#b56cff','#21133a','#fff06a'], 'door':['#8b5a2b','#3b2415','#d8a35d'], 'doctor':['#e8f7ff','#175a9e','#ffffff'],
        'court':['#b98d52','#4b2f19','#f7e4b0'], 'document':['#f4ead0','#6b4b2a','#ffffff'], 'letter':['#f3f1dc','#8a6d3b','#ffffff'], 'medical cross':['#ff3b30','#0d47a1','#ffffff'], 'clock':['#f7f7e8','#2d3748','#ffd45a'],
    }
    if n in name_palettes:
        return ['#00000000'] + name_palettes[n]
    palettes = {
        'animal':['#8b5a2b','#3b2415','#f5d78e'], 'plant':['#2fbf4a','#146b2a','#9cff65'], 'tree':['#2fbf4a','#70431f','#b8ff70'],
        'flower':['#ff4fb8','#2fbf4a','#fff06a'], 'house':['#c96b3a','#6b2e1d','#f7d26a'], 'rock':['#8f98a3','#4f5963','#d8dee8'],
        'food':['#d9823b','#7a2e1a','#ffd36a'], 'hero':['#2f6bff','#111947','#ffeb3b'], 'monster':['#4bbf4f','#18351d','#d8b74a'],
        'person':['#d9905a','#3a1f14','#5aa9ff'], 'object':['#9aa7b3','#34404a','#ffffff'], 'place':['#5e7fbf','#1a2b55','#f7d26a']
    }
    return ['#00000000'] + palettes.get(kind, palettes['object'])


def request_llm_sprite_plan(name: str, category: str) -> dict[str, Any]:
    clean = re.sub(r'[^a-zA-Z0-9 _-]+',' ',name or '').strip()[:50] or 'object'
    cat = re.sub(r'[^a-zA-Z0-9 _-]+',' ',category or '').strip()[:30] or 'object'
    prompt = ('Return JSON only. Describe visual styling for a high quality 24x24 pixel sprite of "'+clean+'" category "'+cat+'". '
              'The server locks object kind from the spoken word; your kind is advisory only. '
              'Return three high-contrast hex colors, 3-8 concrete visual features, and one animation. '
              'Use subject-specific materials, markings, accessories, and accent colors. No text or labels.')
    payload={'prompt':prompt,'n_predict':220,'temperature':0.12,'top_p':0.85,'seed':int(time.time())%100000,'json_schema':PLAN_SCHEMA,'cache_prompt':False}
    started=time.monotonic()
    try:
        resp=requests.post(PIXEL_LLAMA_URL.rstrip()+'/completion', json=payload, timeout=(3,35))
        elapsed=round(time.monotonic()-started,3); resp.raise_for_status()
        raw=str(resp.json().get('content',''))
        objs=extract_json_objects(raw)
        log_event({'type':'topic_gif_llm_plan_raw','name':name,'category':category,'seconds':elapsed,'raw_chars':len(raw),'json_objects':len(objs),'raw_preview':raw[:500],'pixel_llama_url':PIXEL_LLAMA_URL})
        if objs and isinstance(objs[0],dict): return objs[0]
    except Exception as exc:
        log_event({'type':'topic_gif_llm_plan_error','name':name,'category':category,'error':f'{exc.__class__.__name__}: {exc}'})
    return {'kind': infer_sprite_kind(name, category), 'palette': color_from_name(name, infer_sprite_kind(name, category))[1:], 'features': [name, category], 'animation': 'idle'}

def blank_grid() -> list[list[int]]:
    return [[0 for _ in range(PIXEL_GRID)] for _ in range(PIXEL_GRID)]

def setp(g,x,y,c):
    if 0 <= x < PIXEL_GRID and 0 <= y < PIXEL_GRID: g[y][x]=c

def rect(g,x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
      for x in range(x0,x1+1): setp(g,x,y,c)

def line(g,pts,c):
    for x,y in pts: setp(g,x,y,c)

def draw_animal(g, name, frame):
    n=name.lower(); dx=[0,1,0][frame]
    rect(g,8,11,16,14,1); rect(g,6,9,9,12,1); rect(g,5,11,6,12,1)
    line(g,[(7,8),(8,7),(9,8)],2); setp(g,6,10,2); setp(g,7,10,3); setp(g,9,11,3)
    line(g,[(9,15),(9+dx,18),(12,15),(12-dx,18),(15,15),(15,18)],2)
    line(g,[(16,12),(18,11),(20,11+dx)],2); rect(g,10,10,14,10,3)
    if 'horse' in n or 'pferd' in n:
        rect(g,9,10,18,14,1); rect(g,6,8,9,12,1); line(g,[(6,7),(7,6),(8,6),(9,7)],2)
        line(g,[(8,13),(8,18),(12,14),(12,19),(16,14),(16,19),(18,13),(19,18)],2)
        line(g,[(18,11),(20,9),(21,9+dx)],2); rect(g,9,8,10,10,2); setp(g,7,9,3)
    if 'cat' in n or 'katze' in n:
        setp(g,6,8,2); setp(g,9,8,2); line(g,[(16,12),(18,10),(20,9+dx)],2); setp(g,6,10,3)

def draw_tree(g, frame):
    rect(g,11,12,13,20,2); rect(g,8,9,16,15,1); rect(g,9,5,15,11,1); rect(g,6,10,18,13,1)
    setp(g,11,4,3); setp(g,7+frame%2,11,3); setp(g,16,8,3); setp(g,13,6,3); rect(g,10,20,14,21,2)

def draw_flower(g, frame):
    line(g,[(12,11),(12,12),(12,13),(12,14),(12,15),(12,16),(12,17),(12,18),(12,19)],2); line(g,[(10,15),(9,14),(14,14),(15,13)],1)
    cx,cy=12,9; petals=[(cx,cy-4),(cx-3,cy-2),(cx+3,cy-2),(cx-4,cy+1),(cx+4,cy+1),(cx-2,cy+3),(cx+2,cy+3)]
    for x,y in petals: rect(g,x-1+(1 if frame==1 and x>cx else 0),y-1,x+1+(1 if frame==1 and x>cx else 0),y+1,1)
    rect(g,cx-1,cy-1,cx+1,cy+1,3)

def draw_plant(g, name, frame):
    if 'cactus' in name.lower():
        rect(g,11,6,13,20,1); rect(g,7,10,9,15,1); rect(g,15,9,17,14,1); rect(g,8,14,11,15,1); rect(g,13,12,16,13,1)
        for p in [(10,7),(14,8),(10,12),(14,15),(12,18),(7,11),(17,10+frame%2)]: setp(g,p[0],p[1],3)
    else: draw_flower(g, frame)

def draw_house(g, frame):
    rect(g,6,11,17,19,1); line(g,[(5,11),(6,10),(7,9),(8,8),(9,7),(10,6),(11,5),(12,4),(13,5),(14,6),(15,7),(16,8),(17,9),(18,10),(19,11)],2)
    rect(g,10,15,12,19,2); rect(g,14,13,16,15,3); rect(g,7,13,9,15,3); setp(g,13,5,3); setp(g,14+frame%2,6,3); rect(g,5,20,18,21,2)

def draw_rock(g, frame):
    line(g,[(5,17),(6,14),(9,12),(13,11),(17,13),(20,16),(19,19),(15,20),(8,20),(5,17)],2); rect(g,7,16,18,19,1); rect(g,9,14,16,17,1)
    setp(g,10,13,3); setp(g,15+frame%2,14,3); line(g,[(8,18),(11,17),(14,18)],2)

def draw_food(g, name, frame):
    n=fold_text(name)
    if 'coffee' in n or 'kaffee' in n:
        rect(g,8,10,15,17,1); rect(g,16,12,18,15,2); rect(g,9,17,14,18,2); line(g,[(9,8),(9,6+frame%2),(12,8),(12,6),(15,8),(15,6+frame%2)],3)
    elif 'milk' in n or 'milch' in n:
        rect(g,8,7,16,18,1); line(g,[(8,7),(10,4),(14,4),(16,7)],2); rect(g,10,10,14,14,3); line(g,[(10,16),(14,16)],2); setp(g,12,6+frame%2,3)
    elif 'wiener' in n or 'wurst' in n or 'hotdog' in n or 'sausage' in n:
        line(g,[(6,13),(7,12),(8,12),(9,12),(10,12),(11,13),(12,13),(13,13),(14,14),(15,14),(16,14),(17,15)],1); rect(g,8,13,16,15,1); line(g,[(8,14),(10,13),(12,14),(14,13),(16,14)],3); setp(g,17,15,2)
    elif 'cupcake' in n or 'cake' in n or 'kuchen' in n:
        rect(g,8,12,16,18,1); line(g,[(7,12),(9,9),(12,8),(15,9),(17,12)],3); rect(g,9,14,15,18,2); setp(g,12,7+frame%2,3); setp(g,10,11,3); setp(g,15,12,3)
    elif 'chili' in n or 'pepper' in n or 'paprika' in n:
        line(g,[(7,8),(8,9),(9,10),(10,11),(11,12),(12,13),(13,14),(14,15),(15,16)],1); rect(g,9,10,14,15,1); setp(g,7,8,2); setp(g,15,16,2); setp(g,8,7,2); setp(g,11+frame%2,12,3)
    else:
        rect(g,8,10,16,17,1); setp(g,10,9,2); setp(g,13,12,3)


def draw_person(g, kind, frame):
    rect(g,11,5,13,7,3); rect(g,9,8,15,15,1); line(g,[(9,16),(8,19+frame%2),(15,16),(16,19-frame%2)],2); line(g,[(8,10),(6,12),(16,10),(18,12)],2)
    if kind=='hero': line(g,[(16,8),(20,10),(20,16),(16,17)],2); setp(g,12,9,3); setp(g,11,6,2)
    if kind=='monster': setp(g,9,4,2); setp(g,15,4,2); rect(g,9,8,15,16,1); setp(g,11,7,3); setp(g,13,7,3); line(g,[(10,17),(9,20),(15,17),(16,20)],2)

def draw_object(g, name, frame):
    n=fold_text(name)
    if 'table' in n or 'tisch' in n:
        rect(g,5,11,19,13,1); line(g,[(7,14),(6,19),(17,14),(18,19)],2); setp(g,12+frame%2,10,3)
    elif 'plate' in n or 'teller' in n:
        rect(g,7,11,17,15,1); line(g,[(6,13),(7,10),(12,9),(17,10),(18,13),(17,16),(12,17),(7,16)],2); setp(g,12,13,3)
    elif 'stage' in n:
        rect(g,4,14,20,18,1); line(g,[(5,13),(19,13)],2); line(g,[(7,10),(7,13),(12,8),(12,13),(17,10),(17,13)],3); setp(g,12,7+frame%2,3)
    elif 'city' in n or 'street' in n:
        rect(g,5,10,8,19,1); rect(g,10,7,14,19,1); rect(g,16,11,19,19,1); line(g,[(4,20),(20,20)],2); setp(g,11,9,3); setp(g,17+frame%2,13,3)
    elif 'speech bubble' in n:
        rect(g,5,6,18,14,1); line(g,[(5,6),(18,6),(18,14),(11,14),(8,18),(8,14),(5,14),(5,6)],2); line(g,[(8,9),(15,9),(8,11),(13,11)],3)
    elif 'shadow' in n:
        rect(g,8,7,16,18,1); rect(g,10,5,14,8,2); line(g,[(7,19),(17,19)],2); setp(g,11+frame%2,9,3); setp(g,14-frame%2,9,3)
    elif 'camera' in n:
        rect(g,6,9,18,16,1); rect(g,9,7,14,9,2); rect(g,10,10,14,14,3); line(g,[(18,11),(21,9),(21,16),(18,14)],2); setp(g,12,12,2)
    elif 'message' in n or 'letter' in n:
        rect(g,6,7,18,15,1); line(g,[(6,7),(12,12),(18,7),(18,15),(6,15),(6,7)],2); setp(g,13+frame%2,11,3)
    elif 'shield' in n:
        line(g,[(12,4),(18,7),(17,14),(12,20),(7,14),(6,7),(12,4)],2); rect(g,9,8,15,14,1); rect(g,11,7,13,16,3); rect(g,8,10,16,12,3)
    elif 'flag' in n:
        line(g,[(8,5),(8,20)],2); rect(g,9,5,18,11,1); line(g,[(9,8),(18,8)],3); setp(g,17,11+frame%2,2)
    elif 'video' in n:
        rect(g,5,7,19,17,1); line(g,[(5,7),(19,7),(19,17),(5,17),(5,7)],2); line(g,[(10,10),(10,15),(15,12),(10,10)],3)
    elif 'clone' in n:
        rect(g,7,6,10,10,3); rect(g,6,11,11,17,1); rect(g,14,6,17,10,3); rect(g,13,11,18,17,1); setp(g,9,9,2); setp(g,16,9,2)
    elif 'portrait' in n:
        rect(g,7,5,17,19,1); line(g,[(7,5),(17,5),(17,19),(7,19),(7,5)],2); rect(g,10,7,14,11,3); rect(g,9,13,15,17,2)
    elif 'skull' in n:
        rect(g,8,6,16,14,1); rect(g,10,14,14,17,1); setp(g,10,10,2); setp(g,14,10,2); line(g,[(10,16),(14,16),(11,18),(13,18)],2)
    elif 'grave' in n:
        rect(g,8,8,16,19,1); line(g,[(8,8),(9,6),(15,6),(16,8)],2); line(g,[(10,11),(14,11),(12,9),(12,15)],3)
    elif 'mirror' in n:
        rect(g,8,5,16,18,1); line(g,[(8,5),(16,5),(16,18),(8,18),(8,5)],2); line(g,[(10,8),(14,14),(11,15)],3)
    elif 'window' in n:
        rect(g,7,6,17,17,1); line(g,[(12,6),(12,17),(7,11),(17,11),(7,6),(17,6),(17,17),(7,17),(7,6)],2); setp(g,15,8+frame%2,3)
    elif 'thought' in n:
        rect(g,7,7,17,14,1); setp(g,5,15,1); setp(g,4,17,1); line(g,[(8,9),(16,9),(8,11),(14,11)],3)
    elif 'graph' in n:
        line(g,[(6,18),(6,7),(6,18),(19,18)],2); rect(g,8,14,10,17,1); rect(g,12,10,14,17,1); rect(g,16,7,18,17,1); setp(g,17,6+frame%2,3)
    elif 'scroll' in n or 'document' in n:
        rect(g,7,6,17,18,1); line(g,[(7,6),(17,6),(17,18),(7,18),(7,6)],2); line(g,[(9,9),(15,9),(9,12),(15,12),(9,15),(13,15)],3)
    elif 'trash' in n:
        rect(g,8,9,16,19,1); line(g,[(7,8),(17,8),(15,6),(10,6),(7,8)],2); line(g,[(10,11),(10,17),(13,11),(13,17),(15,11),(15,17)],3)
    elif 'ticket' in n:
        rect(g,6,9,18,15,1); line(g,[(6,9),(18,9),(18,15),(6,15),(6,9)],2); line(g,[(9,11),(15,11),(9,13),(13,13)],3)
    elif 'music' in n:
        line(g,[(10,6),(10,16),(10,6),(16,5),(16,14)],1); rect(g,7,15,10,18,2); rect(g,13,13,16,16,2); setp(g,16,6+frame%2,3)
    elif 'door' in n:
        rect(g,8,5,16,20,1); line(g,[(8,5),(16,5),(16,20),(8,20),(8,5)],2); setp(g,14,13,3)
    elif 'doctor' in n or 'medical cross' in n:
        rect(g,9,6,15,19,1); rect(g,11,8,13,16,3); rect(g,8,11,16,13,3); setp(g,12,5,2)
    elif 'court' in n:
        line(g,[(5,18),(19,18),(7,16),(17,16),(8,8),(16,8),(12,5),(8,8)],2); line(g,[(9,9),(9,16),(12,9),(12,16),(15,9),(15,16)],1)
    elif 'clock' in n:
        line(g,[(12,5),(16,7),(19,12),(16,17),(12,19),(8,17),(5,12),(8,7),(12,5)],2); line(g,[(12,12),(12,8),(15,13)],1); setp(g,12,12,3)
    elif 'heart' in n or 'herz' in n:
        rect(g,8,9,11,12,1); rect(g,13,9,16,12,1); rect(g,7,11,17,15,1); rect(g,9,16,15,17,1); setp(g,12,18,1); line(g,[(8,9),(16,9),(7,12),(17,12),(12,18)],2); setp(g,12+frame%2,12,3)
    elif 'energy' in n or 'energie' in n or 'lightning' in n:
        line(g,[(13,4),(10,11),(13,11),(10,20),(17,9),(14,9),(17,4)],1); line(g,[(13,4),(10,11),(10,20)],2); setp(g,14+frame%2,10,3); setp(g,12,13,3)
    elif 'nail' in n or 'nagel' in n:
        line(g,[(7,7),(8,8),(9,9),(10,10),(11,11),(12,12),(13,13),(14,14),(15,15),(16,16)],1); rect(g,5,5,9,7,2); setp(g,12+frame%2,12,3)
    elif 'rescue' in n or 'rettung' in n:
        rect(g,8,6,16,18,1); rect(g,11,8,13,16,3); rect(g,9,11,15,13,3); line(g,[(7,19),(17,19)],2); setp(g,12,5+frame%2,3)
    elif 'planet' in n:
        rect(g,9,8,15,16,1); line(g,[(5,14),(8,12),(12,11),(16,12),(19,14)],2); setp(g,11,10,3); setp(g,14+frame%2,14,3)
    elif 'pause' in n:
        line(g,[(12,5),(15,6),(18,9),(19,12),(18,15),(15,18),(12,19),(9,18),(6,15),(5,12),(6,9),(9,6),(12,5)],2); rect(g,10,9,11,15,1); rect(g,13,9,14,15,1)
    elif 'demo' in n:
        rect(g,7,6,17,13,1); line(g,[(12,14),(12,20)],2); line(g,[(8,9),(16,9),(8,11),(16,11)],3)
    else:
        line(g,[(7,7),(17,7),(17,17),(7,17),(7,7)],2); line(g,[(9,12),(12,9),(15,12),(12,15),(9,12)],1); setp(g,12+frame%2,12,3)


def should_use_plan_palette(pal: Any) -> bool:
    if not isinstance(pal, list) or len(pal) < 3:
        return False
    vals=[str(x).strip().lower() for x in pal[:3]]
    if not all(re.fullmatch(r'#[0-9a-fA-F]{6}', v) for v in vals):
        return False
    if set(vals) in ({'#ff0000','#00ff00','#0000ff'}, {'#ff5733','#33ff57','#3357ff'}):
        return False
    return True

def render_plan_frames(name: str, category: str, plan: dict[str, Any]) -> tuple[list[str], list[list[str]], dict[str, Any]]:
    kind=infer_sprite_kind(name, category, plan)
    colors=color_from_name(name, kind)
    if False and should_use_plan_palette(plan.get('palette')):
        colors=['#00000000']+[normalize_hex_color(str(x), color_from_name(name,kind)[i+1]) for i,x in enumerate(plan.get('palette')[:3])]
    frames=[]
    for fi in range(3):
        g=blank_grid()
        if kind=='animal': draw_animal(g,name,fi)
        elif kind=='tree': draw_tree(g,fi)
        elif kind=='flower': draw_flower(g,fi)
        elif kind=='plant': draw_plant(g,name,fi)
        elif kind=='house': draw_house(g,fi)
        elif kind=='rock': draw_rock(g,fi)
        elif kind=='food': draw_food(g,name,fi)
        elif kind in {'hero','monster'}: draw_person(g,kind,fi)
        else: draw_object(g,name,fi)
        frames.append([''.join(str(v) for v in row) for row in g])
    validation='semantic_plan kind='+kind+' nonzero='+str([sum(ch!='0' for row in f for ch in row) for f in frames])
    return colors, frames, {'format':'semantic_plan_v1','kind':kind,'plan':plan,'validation':validation,'pixel_llama_url':PIXEL_LLAMA_URL}

def request_llm_pixel_art(name: str, category: str) -> tuple[list[str], list[list[str]], dict[str, Any]]:
    kind = infer_sprite_kind(name, category, None)
    plan = {'kind': kind, 'palette': color_from_name(name, kind)[1:], 'features': [name, category], 'animation': 'idle'}
    colors, frames, info = render_plan_frames(name, category, plan)
    info['format'] = 'deterministic_template_v2'
    log_event({'type':'topic_gif_template_rendered','name':name,'category':category,'kind':info.get('kind'),'validation':info.get('validation')})
    return colors, frames, info


def render_pixel_frames(colors: list[str], frames: list[list[str]], scale: int = 4) -> list[Image.Image]:
    rgba=[]
    for c in colors:
        c=normalize_hex_color(c, '#000000')
        rgba.append(tuple(int(c[i:i+2],16) for i in (1,3,5)) + ((int(c[7:9],16),) if len(c)==9 else (255,)))
    out=[]
    for rows in frames:
        grid=len(rows); img=Image.new('RGBA',(grid,grid),(0,0,0,0)); pix=img.load()
        for y,row in enumerate(rows):
            for x,ch in enumerate(row): pix[x,y]=rgba[int(ch)]
        out.append(img.resize((96,96), Image.Resampling.NEAREST))
    return out


def load_openai_api_key_for_images() -> str:
    key = os.environ.get('OPENAI_API_KEY') or os.environ.get('LLM_GAME_OPENAI_API_KEY')
    if key:
        key = key.strip()
        if key and key != 'sk-local' and not key.endswith('-local'):
            return key
    for env_path in OPENAI_IMAGE_ENV_FILES:
        try:
            if not env_path.exists():
                continue
            for line in env_path.read_text(errors='ignore').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                if k.strip() in {'OPENAI_API_KEY','LLM_GAME_OPENAI_API_KEY'}:
                    val = v.strip().strip('"').strip("'")
                    if val and val != 'sk-local' and not val.endswith('-local'):
                        return val
        except Exception:
            continue
    return ''

def scene_gif_slug(name: str, category: str, prompt: str) -> str:
    base = topic_gif_slug(f'real-{category}-{name}')
    h = hashlib.sha256((name+'|'+category+'|'+prompt+'|'+OPENAI_IMAGE_MODEL).encode('utf-8')).hexdigest()[:12]
    return f'{base}-{h}'[:90]

def make_animated_gif_from_png_bytes(raw: bytes, out_path: Path, meta_path: Path, info: dict[str, Any]) -> None:
    src = Image.open(io.BytesIO(raw)).convert('RGBA')
    src.thumbnail((160, 160), Image.Resampling.LANCZOS)
    canvas_size = (176, 176)
    frames = []
    for i in range(8):
        frame = Image.new('RGBA', canvas_size, (0,0,0,0))
        wob = math.sin(i/8*math.tau) * 3
        scale = 1.0 + math.sin(i/8*math.tau) * 0.025
        w = max(1, int(src.width * scale)); h = max(1, int(src.height * scale))
        im = src.resize((w, h), Image.Resampling.LANCZOS)
        frame.alpha_composite(im, ((canvas_size[0]-w)//2, (canvas_size[1]-h)//2 + int(wob)))
        frames.append(frame)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2, transparency=0)
    meta_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n')


def generate_via_thor_image_service(name: str, category: str, prompt: str, motion: str, path: Path, meta_path: Path) -> Path:
    if not THOR_IMAGE_URL:
        raise RuntimeError('Thor image URL not configured')
    strict_prompt = ('isolated high quality physical object sprite: ' + str(prompt or name) + '; single centered object only, transparent background, no text, no label, no scene, no people unless explicitly requested')[:600]
    payload = {'name': name, 'category': category, 'prompt': strict_prompt, 'motion': motion or 'idle'}
    started = time.monotonic()
    resp = requests.post(THOR_IMAGE_URL, json=payload, timeout=(4, 180))
    if resp.status_code >= 400:
        raise RuntimeError(f'thor image status {resp.status_code}: {resp.text[:500]}')
    obj = resp.json()
    if not obj.get('ok'):
        raise RuntimeError('thor image failed: ' + str(obj.get('error') or obj)[:500])
    if obj.get('gif_b64'):
        raw = base64.b64decode(obj['gif_b64'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    elif obj.get('png_b64'):
        raw = base64.b64decode(obj['png_b64'])
        make_animated_gif_from_png_bytes(raw, path, meta_path, {'engine':'thor-sd-turbo','source':'png_b64','name':name,'category':category,'prompt':prompt,'motion':motion})
    else:
        raise RuntimeError('thor image response missing gif_b64/png_b64')
    info = {'engine':'thor-sd-turbo','url':THOR_IMAGE_URL,'name':name,'category':category,'prompt':prompt,'motion':motion,'seconds':round(time.monotonic()-started,3),'thor':{k:v for k,v in obj.items() if k not in ('png_b64','gif_b64')}}
    meta_path.write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n')
    log_event({'type':'thor_image_gif_generated','name':name,'category':category,'path':str(path),'bytes':path.stat().st_size,'seconds':info['seconds'],'thor_seconds':obj.get('gen_seconds')})
    return path

def generate_real_image_gif_file(name: str, category: str, prompt: str, motion: str='idle') -> Path:
    clean_name = re.sub(r'[^\w\s-]+', ' ', str(name or 'object')).strip()[:60] or 'object'
    clean_category = re.sub(r'[^\w\s-]+', ' ', str(category or 'object')).strip()[:30] or 'object'
    clean_prompt = ' '.join(str(prompt or clean_name).split())[:350]
    slug = scene_gif_slug(clean_name, clean_category, clean_prompt)
    path = GIF_DIR / f'{slug}.gif'
    meta_path = path.with_suffix('.json')
    if validate_existing_gif(path):
        return path
    thor_error = None
    if THOR_IMAGE_URL:
        try:
            return generate_via_thor_image_service(clean_name, clean_category, clean_prompt, motion, path, meta_path)
        except Exception as exc:
            thor_error = f'{exc.__class__.__name__}: {exc}'
            log_event({'type':'thor_image_gif_error','name':clean_name,'category':clean_category,'error':thor_error,'url':THOR_IMAGE_URL})
    key = load_openai_api_key_for_images()
    if not key:
        raise RuntimeError(thor_error or 'no OpenAI image API key configured and Thor image service unavailable')
    image_prompt = (
        'Create a clean game sprite image on transparent or plain background, no text, no watermark. '
        f'Subject: {clean_name}. Category: {clean_category}. Scene detail: {clean_prompt}. '
        'Style: colorful illustrated game object, readable at small size, centered full object, high contrast, not pixel art, not emoji, not UI icon. '
        f'Motion hint for later GIF animation: {motion or "idle"}.'
    )
    payload = {'model': OPENAI_IMAGE_MODEL, 'prompt': image_prompt, 'size': OPENAI_IMAGE_SIZE}
    started = time.monotonic()
    resp = requests.post('https://api.openai.com/v1/images/generations', headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json'}, json=payload, timeout=(8, 120))
    if resp.status_code >= 400:
        raise RuntimeError(f'openai image status {resp.status_code}: {resp.text[:500]}')
    obj = resp.json()
    item = (obj.get('data') or [{}])[0]
    if item.get('b64_json'):
        raw = base64.b64decode(item['b64_json'])
    elif item.get('url'):
        img_resp = requests.get(item['url'], timeout=(8, 60)); img_resp.raise_for_status(); raw = img_resp.content
    else:
        raise RuntimeError('openai image response missing b64_json/url')
    info = {'engine':'thor-sd-turbo' if THOR_IMAGE_URL else 'openai-images','model':OPENAI_IMAGE_MODEL,'name':clean_name,'category':clean_category,'prompt':clean_prompt,'seconds':round(time.monotonic()-started,3),'bytes_png':len(raw),'motion':motion}
    make_animated_gif_from_png_bytes(raw, path, meta_path, info)
    log_event({'type':'real_image_gif_generated','name':clean_name,'category':clean_category,'path':str(path),'bytes':path.stat().st_size,'model':OPENAI_IMAGE_MODEL,'seconds':info['seconds']})
    return path

def generate_topic_gif_file(name: str, category: str) -> Path:
    slug = topic_gif_slug(f'llm-{category}-{name}')
    path = GIF_DIR / f'{slug}.gif'
    meta = path.with_suffix('.json')
    if path.exists() and path.stat().st_size > 100 and meta.exists():
        return path
    colors, frames, info = request_llm_pixel_art(name, category)
    images = render_pixel_frames(colors, frames)
    images[0].save(path, save_all=True, append_images=images[1:], duration=180, loop=0, disposal=2, transparency=0)
    meta.write_text(json.dumps({'name':name,'category':category,'colors':colors,'frames':frames,'info':info,'gif':str(path),'time_ms':now_ms()}, indent=2) + '\n')
    log_event({'type':'topic_gif_llm_generated','name':name,'category':category,'path':str(path),'bytes':path.stat().st_size,'frames':len(images),'llm_seconds':info.get('seconds'),'attempt':info.get('attempt'),'validation':info.get('validation')})
    return path

GIF_JOBS: dict[str, asyncio.Task] = {}
GIF_ERRORS: dict[str, str] = {}
GIF_STARTED: dict[str, int] = {}
GIF_LOCK: asyncio.Lock | None = None


def validate_existing_gif(path: Path) -> bool:
    try:
        return path.exists() and path.is_file() and path.stat().st_size > 64 and path.read_bytes()[:6] in (b'GIF87a', b'GIF89a')
    except Exception:
        return False

async def http_gif(request: web.Request) -> web.StreamResponse:
    raw_slug = request.match_info.get('slug', 'object.gif')
    name = str(request.query.get('name') or raw_slug.rsplit('.', 1)[0]).strip()[:80]
    category = str(request.query.get('category') or category_for_candidate(name) or 'object').strip()[:40]
    prompt = str(request.query.get('prompt') or name).strip()[:400]
    motion = str(request.query.get('motion') or 'idle').strip()[:40]
    slug = scene_gif_slug(name, category, prompt)
    path = GIF_DIR / f'{slug}.gif'
    if (not THOR_IMAGE_URL) and (not load_openai_api_key_for_images()):
        return http_json({'type':'topic_gif_error','engine':'image','status':'disabled','name':name,'category':category,'slug':slug,'error':'no image backend configured','retry_after_seconds':60,'time_ms':now_ms()}, status=503)
    if validate_existing_gif(path):
        return web.FileResponse(path, headers={'Cache-Control':'public, max-age=86400', 'X-Generated-By':'openai-image-gif'})
    err_path = GIF_DIR / f'{slug}.error.json'
    if THOR_IMAGE_URL and err_path.exists():
        try:
            err_path.unlink()
        except Exception:
            pass
    if err_path.exists():
        try:
            err = json.loads(err_path.read_text(errors='ignore')).get('error','previous generation failed')
        except Exception:
            err = 'previous generation failed'
        return http_json({'type':'topic_gif_error','engine':'thor-sd-turbo' if THOR_IMAGE_URL else 'openai-images','status':'failed','name':name,'category':category,'slug':slug,'error':err,'retry_after_seconds':60,'time_ms':now_ms()}, status=503)
    task = GIF_JOBS.get(slug)
    if task and task.done():
        try:
            task.result()
        except Exception as exc:
            err = f'{exc.__class__.__name__}: {exc}'
            err_path.write_text(json.dumps({'error':err,'time_ms':now_ms(),'name':name,'category':category,'prompt':prompt}, ensure_ascii=False, indent=2))
            log_event({'type':'real_image_gif_error','name':name,'category':category,'slug':slug,'error':err})
        GIF_JOBS.pop(slug, None)
    if slug not in GIF_JOBS:
        async def run_job() -> None:
            await asyncio.to_thread(generate_real_image_gif_file, name, category, prompt, motion)
        GIF_STARTED[slug] = now_ms()
        GIF_JOBS[slug] = asyncio.create_task(run_job())
        log_event({'type':'real_image_gif_job_started','name':name,'category':category,'slug':slug,'prompt_chars':len(prompt)})
    age = max(0, now_ms() - int(GIF_STARTED.get(slug, now_ms())))
    active = sum(1 for t in GIF_JOBS.values() if not t.done())
    return http_json({'type':'topic_gif_pending','engine':'thor-sd-turbo' if THOR_IMAGE_URL else 'openai-images','status':'queued_or_generating','name':name,'category':category,'slug':slug,'active_jobs':active,'retry_after_seconds':6,'age_ms':age,'time_ms':now_ms()}, status=202)


HTTP_SESSIONS: dict[str, dict[str, Any]] = {}

def new_session_state() -> dict[str, Any]:
    return {'busy':False,'last_started':0.0,'last_text':'','full_text':'','recent_norms':[],'topic_buffer':[],'topic_counts':{},'language':normalize_stt_language(DEFAULT_STT_LANGUAGE)}

class MessageCollector:
    def __init__(self) -> None:
        self.messages: list[Any] = []
    async def send(self, data: str) -> None:
        try:
            self.messages.append(json.loads(data))
        except Exception:
            self.messages.append({'type':'raw','data':str(data)})

def http_json(payload: dict[str, Any], status: int = 200) -> web.Response:
    return web.json_response(payload, status=status, headers={'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0','Pragma':'no-cache','Expires':'0'})

async def http_start(request: web.Request) -> web.Response:
    session = f'http-{now_ms()}'
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    language = normalize_stt_language(payload.get('language') or request.query.get('language'))
    state = new_session_state()
    state['language'] = language
    HTTP_SESSIONS[session] = {'audio': bytearray(), 'state': state, 'created': time.monotonic(), 'last': time.monotonic()}
    log_event({'type':'http_start','session':session,'remote':request.remote,'language':language})
    return http_json({'type':'ready','transport':'http','session':session,'sample_rate':SAMPLE_RATE,'model':'nitro-faster-whisper-tiny','backend':STT_BACKEND,'language':language,'topics_interval_seconds':TOPIC_EXTRACT_EVERY_SECONDS,'time_ms':now_ms()})

async def http_audio(request: web.Request) -> web.Response:
    session = request.match_info.get('session','')
    entry = HTTP_SESSIONS.get(session)
    if not entry:
        return http_json({'type':'error','error':'unknown http session','session':session,'time_ms':now_ms()}, status=404)
    pcm = await request.read()
    audio: bytearray = entry['audio']
    state: dict[str, Any] = entry['state']
    entry['last'] = time.monotonic()
    if pcm:
        audio.extend(pcm)
    max_keep = int(MAX_WINDOW_SECONDS * BYTES_PER_SECOND * 2)
    if len(audio) > max_keep:
        del audio[:-max_keep]
    collector = MessageCollector()
    await maybe_transcribe(collector, session, audio, state)
    log_event({'type':'http_audio','session':session,'bytes_received':len(pcm),'bytes_kept':len(audio),'messages':len(collector.messages)})
    return http_json({'type':'http_audio','session':session,'bytes_received':len(pcm),'bytes_kept':len(audio),'messages':collector.messages,'time_ms':now_ms()})

async def http_event(request: web.Request) -> web.Response:
    session = request.match_info.get('session','')
    try:
        payload = await request.json()
    except Exception:
        payload = {'raw': (await request.text())[:500]}
    log_event({'type':'client_debug','session':session,'payload':payload,'transport':'http'})
    return http_json({'type':'ack','session':session,'time_ms':now_ms()})

async def http_stop(request: web.Request) -> web.Response:
    session = request.match_info.get('session','')
    entry = HTTP_SESSIONS.get(session)
    if not entry:
        return http_json({'type':'stopped','session':session,'messages':[],'time_ms':now_ms()})
    collector = MessageCollector()
    audio: bytearray = entry['audio']
    await maybe_transcribe(collector, session, audio, entry['state'], force=True)
    meta = OUT_DIR / f'{session}.json'
    meta.write_text(json.dumps({'session':session,'closed_ms':now_ms(),'bytes_kept':len(audio),'full_text':entry['state'].get('full_text',''),'transport':'http'}, indent=2) + '\n')
    log_event({'type':'http_stop','session':session,'bytes_kept':len(audio),'full_text':entry['state'].get('full_text','')})
    HTTP_SESSIONS.pop(session, None)
    return http_json({'type':'stopped','session':session,'messages':collector.messages,'time_ms':now_ms()})

async def http_health(request: web.Request) -> web.Response:
    return http_json({
        'ok': True,
        'service': 'llm-game-stt',
        'backend': STT_BACKEND,
        'default_language': normalize_stt_language(DEFAULT_STT_LANGUAGE),
        'local_model': str(LOCAL_FAST_MODEL_PATH),
        'local_model_loaded': LOCAL_MODEL is not None,
        'thor_configured': bool(THOR_STT_URL),
        'local_fallback': ALLOW_LOCAL_STT_FALLBACK,
        'time_ms': now_ms(),
    })

async def start_http_server(host: str, port: int) -> web.AppRunner:
    app = web.Application(client_max_size=8*1024*1024)
    app.router.add_post('/http/start', http_start)
    app.router.add_post('/http/{session}/audio', http_audio)
    app.router.add_post('/http/{session}/event', http_event)
    app.router.add_post('/http/{session}/stop', http_stop)
    app.router.add_get('/http/health', http_health)
    app.router.add_get('/gif/{slug}', http_gif)
    install_game_llm_routes(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port, reuse_address=True)
    await site.start()
    log_event({'type':'http_listening','host':host,'port':port})
    return runner

async def handle_client(websocket) -> None:
    session = f'session-{now_ms()}'
    audio = bytearray()
    state: dict[str, Any] = new_session_state()
    topic_task = asyncio.create_task(topic_loop(websocket, session, state))
    try:
        await websocket.send(json.dumps({'type':'ready','session':session,'sample_rate':SAMPLE_RATE,'model':'nitro-faster-whisper-tiny','backend':STT_BACKEND,'language':state['language'],'topics_interval_seconds':TOPIC_EXTRACT_EVERY_SECONDS,'time_ms':now_ms()}))
        async for message in websocket:
            if isinstance(message, bytes):
                audio.extend(message)
                max_keep = int(MAX_WINDOW_SECONDS * BYTES_PER_SECOND * 2)
                if len(audio) > max_keep:
                    del audio[:-max_keep]
                await maybe_transcribe(websocket, session, audio, state)
            else:
                try:
                    data = json.loads(message)
                except Exception:
                    data = {'type':'text','value':str(message)}
                if data.get('type') == 'hello':
                    state['language'] = normalize_stt_language(data.get('language'))
                    await websocket.send(json.dumps({'type':'ack','session':session,'received':{'type':'hello','sample_rate':data.get('sample_rate'),'format':data.get('format'),'language':state['language']},'language':state['language'],'backend':STT_BACKEND,'time_ms':now_ms()}))
                    log_event({'type':'hello','session':session,'language':state['language'],'sample_rate':data.get('sample_rate'),'format':data.get('format')})
                elif data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type':'pong','session':session,'time_ms':now_ms()}))
                elif data.get('type') == 'client_debug':
                    log_event({'type':'client_debug','session':session,'payload':data})
                elif data.get('type') == 'debug_transcript':
                    text = str(data.get('text') or '').strip()
                    log_event({'type':'debug_transcript','session':session,'text':text})
                    result = await asyncio.to_thread(extract_topic_candidates, text)
                    if str(result.get('engine')) == 'llama-error':
                        msg = {'type':'topic_error','session':session,'engine':'llama','error':result.get('error','unknown topic extractor error'),'source_text_chars':len(text),'time_ms':now_ms()}
                        await websocket.send(json.dumps(msg))
                        log_event({'type':'topic_error_sent','session':session,'source':'debug','error':msg['error']})
                    else:
                        candidates = result.get('candidates', []) if isinstance(result, dict) else []
                        msg = {'type':'topics','session':session,'engine':'llama','source_text_chars':len(text),'source_text':result.get('scene_text', text),'candidates':candidates,'topic_counts':{},'llm_raw':result.get('raw_content',''),'rejected':result.get('rejected',[]),'time_ms':now_ms()}
                        await websocket.send(json.dumps(msg))
                        log_event({'type':'topics_sent' if candidates else 'topics_empty_sent','session':session,'engine':'llama','source':'debug','candidates':candidates})
                elif data.get('type') == 'reset':
                    audio.clear(); state.update({'last_text':'','full_text':'','topic_buffer':[],'topic_counts':{}})
                    await websocket.send(json.dumps({'type':'reset','session':session,'time_ms':now_ms()}))
                else:
                    await websocket.send(json.dumps({'type':'ack','session':session,'received':data,'time_ms':now_ms()}))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        try:
            if len(audio) > 0:
                await maybe_transcribe(websocket, session, audio, state, force=True)
        except Exception as exc:
            log_event({'type':'flush_on_close_error','session':session,'error':f'{exc.__class__.__name__}: {exc}','bytes_kept':len(audio)})
        try:
            topic_task.cancel()
        except Exception:
            pass
        meta = OUT_DIR / f'{session}.json'
        meta.write_text(json.dumps({'session':session,'closed_ms':now_ms(),'bytes_kept':len(audio),'full_text':state.get('full_text','')}, indent=2) + '\n')
        log_event({'type':'closed','session':session,'bytes_kept':len(audio),'full_text':state.get('full_text','')})

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=18891)
    parser.add_argument('--http-port', type=int, default=18892)
    parser.add_argument('--warmup', action='store_true')
    args = parser.parse_args()
    if args.warmup:
        if STT_BACKEND in {'local','local-first','hybrid'}:
            await asyncio.to_thread(load_local_model)
        elif ALLOW_LOCAL_STT_FALLBACK:
            load_model()
    await start_http_server(args.host, args.http_port)
    log_event({'type':'listening','host':args.host,'port':args.port,'engine':STT_BACKEND,'model':str(LOCAL_FAST_MODEL_PATH),'default_language':normalize_stt_language(DEFAULT_STT_LANGUAGE)})
    async with websockets.serve(handle_client, args.host, args.port, max_size=2*1024*1024, ping_interval=None, ping_timeout=None, reuse_address=True):
        await asyncio.Future()
if __name__ == '__main__':
    asyncio.run(main())
