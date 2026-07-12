#!/usr/bin/env python3
import argparse
import asyncio
import json
import websockets

async def check(url: str, timeout: float, language: str) -> None:
    async with websockets.connect(url, open_timeout=timeout, close_timeout=3, ping_timeout=timeout, max_size=2**20) as ws:
        ready = json.loads(await asyncio.wait_for(ws.recv(), timeout))
        assert ready.get('type') == 'ready', ready
        await ws.send(json.dumps({'type':'hello','sample_rate':16000,'format':'pcm16le','language':language,'test':'smoke'}))
        ack = json.loads(await asyncio.wait_for(ws.recv(), timeout))
        assert ack.get('type') == 'ack', ack
        assert ack.get('language') == language, ack
        print(json.dumps({'ok':True,'url':url,'model':ready.get('model'),'backend':ready.get('backend'),'language':ack.get('language'),'session':ready.get('session')}, sort_keys=True))

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='ws://127.0.0.1:15301/')
    parser.add_argument('--timeout',type=float,default=10.0)
    parser.add_argument('--language',default='en')
    args=parser.parse_args()
    asyncio.run(check(args.url,args.timeout,args.language))

if __name__ == '__main__':
    main()
