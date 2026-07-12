#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stt_ws_server_backend',ROOT/'server/stt_ws_server.py')
stt=importlib.util.module_from_spec(spec); spec.loader.exec_module(stt)

speech=b'\x20\x4e' * stt.SAMPLE_RATE
originals={name:getattr(stt,name) for name in ('pcm_activity','transcribe_pcm_local_fast','transcribe_wav_thor','transcribe_pcm_local_whisper')}
try:
    stt.pcm_activity=lambda pcm:{'rms':0.1,'voiced_ratio':0.9,'voiced_frames':10,'frames':10}
    calls=[]
    stt.STT_BACKEND='local-first'
    stt.transcribe_pcm_local_fast=lambda wav,rms,ratio,frames,session,language: calls.append(('local',language)) or {'type':'stt','session':session,'text':'local text','engine':'local','time_ms':stt.now_ms()}
    stt.transcribe_wav_thor=lambda *args,**kwargs: calls.append(('thor',None)) or {'type':'stt','text':'thor text'}
    result=stt.transcribe_pcm(speech,'session','de-DE')
    assert result['text']=='local text',result
    assert calls==[('local','de')],calls

    calls.clear()
    stt.transcribe_pcm_local_fast=lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError('local unavailable'))
    stt.transcribe_wav_thor=lambda wav,rms,ratio,frames,session,language: calls.append(('thor',language)) or {'type':'stt','session':session,'text':'thor text','engine':'thor','time_ms':stt.now_ms()}
    result=stt.transcribe_pcm(speech,'session','en-US')
    assert result['text']=='thor text',result
    assert calls==[('thor','en')],calls
finally:
    for name,value in originals.items(): setattr(stt,name,value)
print('backend_selection ok')
