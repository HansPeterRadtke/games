#!/usr/bin/env python3
import asyncio
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stt_ws_server', ROOT / 'server' / 'stt_ws_server.py')
stt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stt)

class FakeSocket:
    def __init__(self):
        self.messages = []
    async def send(self, data):
        self.messages.append(json.loads(data))

async def run_case():
    original_transcribe = stt.transcribe_pcm
    original_extract = stt.extract_topic_candidates
    try:
        stt.transcribe_pcm = lambda pcm, session, language=None: {
            'type': 'stt',
            'session': session,
            'engine': 'test',
            'text': 'Thank you.',
            'rms': 0.00335,
            'voiced_ratio': 0.348,
            'voiced_frames': 12,
            'seconds': 0.01,
            'time_ms': stt.now_ms(),
        }
        stt.extract_topic_candidates = lambda text: {
            'engine': 'scene-llm-json-schema',
            'seconds': 0,
            'candidates': [],
            'raw_content': '{"objects": []}',
            'rejected': [],
            'scene_text': text,
        }
        ws = FakeSocket()
        state = stt.new_session_state()
        audio = bytearray((int(12000)).to_bytes(2, 'little', signed=True) * int(stt.SAMPLE_RATE * 1.0) + b'\x00\x00' * int(stt.SAMPLE_RATE * 1.0))
        await stt.maybe_transcribe(ws, 'test-session', audio, state, force=True)
        assert ws.messages, 'no websocket messages sent'
        processing = next((m for m in ws.messages if m.get('type') == 'stt_processing'), None)
        assert processing is not None, ws.messages
        stt_msg = next((m for m in ws.messages if m.get('type') == 'stt'), None)
        assert stt_msg is not None, ws.messages
        assert stt_msg.get('text') == 'Thank you.', stt_msg
        assert stt_msg.get('new_text') == 'Thank you.', stt_msg
        topic_msg = next((m for m in ws.messages if m.get('type') == 'topics'), None)
        assert topic_msg is not None, ws.messages
        assert topic_msg.get('source_text') == 'Thank you.', topic_msg
        assert state.get('full_text') == 'Thank you.', state
        assert len(audio) == 0, 'audio buffer was not cleared after transcription'
        assert stt.should_accept_stt_result({'text': 'Undertexter av Nicolai Winther'}) == (True, 'accepted')
    finally:
        stt.transcribe_pcm = original_transcribe
        stt.extract_topic_candidates = original_extract

if __name__ == '__main__':
    asyncio.run(run_case())
    print('raw_stt_flow regression ok')
