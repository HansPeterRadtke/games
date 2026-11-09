"""Real Chromium checks for shared level, progressive text, and Delete/Backspace.
Run: python3 tests/browser_level_text.py. Browser artifacts remain temporary.
"""
import html
import http.server
import json
import os
from pathlib import Path
import re
import socketserver
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / '.typewriter-level-text-probe-temp.html'
SCRIPT = r'''<script type="module">
const $=id=>document.getElementById(id);
const results=[];
const check=(name,ok,detail='')=>results.push({name,ok,detail});
const press=key=>document.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true}));
const event=(el,type)=>el.dispatchEvent(new Event(type,{bubbles:true}));
const snapshot=()=>JSON.parse(localStorage.getItem('typewriter.practice.v1'));
try {
 await new Promise(r=>setTimeout(r,300));
 check('global level visible in keys',!$('level-controls').hidden && $('level-hint').textContent==='2 keys');
 $('primary-button').click();
 const initial=$('target-key').textContent.toLowerCase();
 press('x');
 check('key mistake turns red', $('prompt-surface').classList.contains('wrong') && $('stat-errors').textContent==='1');
 press('Delete');
 check('key Delete clears red', !$('prompt-surface').classList.contains('wrong') && $('stat-errors').textContent==='1');
 press('x');
 check('second mistake shows red', $('prompt-surface').classList.contains('wrong'));
 press('Backspace');
 check('key Backspace clears red', !$('prompt-surface').classList.contains('wrong') && $('stat-errors').textContent==='2');
 press(initial);
 check('original key mode still advances', $('progress-count').textContent==='1 / 50');
 window.confirm=()=>true;
 $('mode-sequence').click();
 check('global level visible in sequence',!$('level-controls').hidden && $('sequence-options').hidden===false);
 $('primary-button').click();
 const sequence=$('target-text').textContent;
 press(sequence[0]);
 check('sequence cursor advances', $('target-text').querySelectorAll('.typed').length===1);
 press('x');
 check('sequence wrong highlights red',$('prompt-surface').classList.contains('wrong'));
 press('Delete');
 check('sequence Delete moves back and clears red',!$('prompt-surface').classList.contains('wrong') && $('target-text').querySelectorAll('.typed').length===0);
 $('mode-text').click();
 check('global level visible in text', !$('level-controls').hidden && $('level-hint').textContent==='2 keys');
 check('text defaults to level-generated content', $('passage-select').value==='level-mixed');
 const short=$('target-text').textContent;
 check('level one only unlocked keys',short.length>=50 && [...short].every(c=>'fj '.includes(c)),short.slice(0,20));
 check('honest small-level label', $('text-stage-label').textContent.includes('KEY GROUPS'));
 $('primary-button').click();
 press(short[0]);
 check('text cursor advances', $('target-text').querySelectorAll('.typed').length===1);
 press('x');
 check('text typo red', $('prompt-surface').classList.contains('wrong') && $('target-text').querySelector('.wrong-current')!==null);
 press('Backspace');
 check('text Backspace clears red',!$('prompt-surface').classList.contains('wrong') && $('target-text').querySelectorAll('.typed').length===0 && $('target-text').querySelector('.wrong-current')===null);
 check('text cursor visibly moved backward', [...$('target-text').querySelectorAll('span')].findIndex(x=>x.classList.contains('current'))===0);
 press(short[0]); press(short[1]);
 check('cursor moves forward again', $('target-text').querySelectorAll('.typed').length===2);
 const capture=$('type-capture');
 const handled=capture.dispatchEvent(new InputEvent('beforeinput',{inputType:'deleteContentBackward',bubbles:true,cancelable:true}));
 check('mobile delete event handled',handled===false && $('target-text').querySelectorAll('.typed').length===1);
 check('mistake count remains honest',Number($('stat-errors').textContent)>=1);
 $('new-session').click();
 for(let i=0;i<5;i++) $('level-up').click();
 check('text level six unlocked', $('level-label').textContent==='06' && $('level-hint').textContent==='7 keys');
 const practice=$('target-text').textContent;
 check('real phrases at level six', $('text-stage-label').textContent.includes('SHORT PHRASES') && practice.includes(' '),practice.slice(0,50));
 check('level six letters only', [...practice].every(c=>'fjdksla '.includes(c)));
 check('level summary lists unlocked keys', $('unlocked-key-list').querySelectorAll('.key-sample').length===7);
 $('passage-select').value='custom';event($('passage-select'),'change');
 $('custom-text').value='hello';event($('custom-text'),'input');
 check('invalid custom passage rejected', $('primary-button').disabled && $('custom-text-validation').classList.contains('invalid'));
 $('custom-text').value='lass das';event($('custom-text'),'input');
 check('allowed custom passage accepted', !$('primary-button').disabled && !$('custom-text-validation').classList.contains('invalid'));
 $('passage-select').value='de-everyday';event($('passage-select'),'change');
 check('full alphabet preset gated at low level', $('primary-button').disabled);
 $('passage-select').value='level-en';event($('passage-select'),'change');
 check('English-only exercises valid', [...$('target-text').textContent].every(c=>'fjdksla '.includes(c)));
 check('no horizontal overflow',document.documentElement.scrollWidth<=document.documentElement.clientWidth+1,
   document.documentElement.scrollWidth+'/'+document.documentElement.clientWidth);
 const old=await import('./src/core.js');
 const data=await import('./src/storage.js');
 const restored=data.parseExport(JSON.stringify(snapshot()));
 check('saved text persists at current level', restored.session.mode==='text' && restored.session.level===6 && restored.session.passageId==='level-en');
} catch(e) {results.push({name:'exception',ok:false,detail:e.message});}
const out=document.createElement('pre');out.id='level-text-probe';out.textContent=JSON.stringify(results);document.body.append(out);
</script>'''

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def run():
    os.chdir(ROOT)
    if PROBE.exists():
        raise RuntimeError('Temporary probe file already exists.')
    page=(ROOT/'index.html').read_text()
    PROBE.write_text(page.replace('</body>',SCRIPT+'\n</body>'))
    try:
        socketserver.TCPServer.allow_reuse_address=True
        with socketserver.TCPServer(('127.0.0.1',0),QuietHandler) as server:
            t=threading.Thread(target=server.serve_forever,daemon=True)
            t.start()
            url=f'http://127.0.0.1:{server.server_address[1]}/{PROBE.name}'
            command=[os.environ.get('CHROMIUM_BIN','chromium'),'--headless','--no-sandbox',
               '--disable-gpu','--disable-dev-shm-usage','--window-size=390,844',
               '--virtual-time-budget=4000','--dump-dom',url]
            result=subprocess.run(command,capture_output=True,text=True,timeout=35)
            match=re.search(r'<pre id="level-text-probe">(.*?)</pre>',result.stdout,re.S)
            if not match:
                print(result.stderr[-1800:])
                raise RuntimeError('Chromium did not return probe results.')
            checks=json.loads(html.unescape(match.group(1)))
            for check in checks:
                print(('PASS' if check['ok'] else 'FAIL') + ': ' + check['name'] + ' ' + str(check.get('detail','')))
            assert checks and all(check['ok'] for check in checks),'Level-aware text browser regression'
            print(f'All {len(checks)} level-text Chromium checks passed.')
            server.shutdown()
    finally:
        PROBE.unlink(missing_ok=True)

if __name__=='__main__':
    run()
