"""Real Chromium sequence-challenge UI regression, no WebDriver dependency.

Run: python3 tests/browser_sequence.py
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
PROBE = ROOT / '.typewriter-sequence-probe-temporary.html'
SCRIPT = r'''<script type="module">
const $=id=>document.getElementById(id);
const results=[];
const check=(name,ok,detail='')=>results.push({name,ok,detail});
const press=key=>document.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true}));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const set=(id,value)=>{ $(id).value=String(value); $(id).dispatchEvent(new Event('change',{bubbles:true}));};
const sequence=()=> $('target-text').textContent;
async function typeSequence(text,delay) {
 for (const char of text) { await sleep(delay);press(char); }
}
try {
 await sleep(300);
 $('mode-sequence').click();
 check('sequence mode shown', $('mode-sequence').getAttribute('aria-selected')==='true' && !$('sequence-options').hidden);
 check('original modes hidden', $('text-controls').hidden && $('key-goal-block').hidden && $('keys-controls').hidden && !$('level-controls').hidden);
 check('default length', Number($('sequence-length').value)===2 && Number($('sequence-length').min)===2);
 check('default rounds', Number($('sequence-rounds').value)===10);
 const defaultSequence=sequence();
 check('initial complete shuffled set',defaultSequence.length===2 && [...defaultSequence].sort().join('')==='fj');
 $('level-up').click();
 check('level increases unlocked count', $('level-hint').textContent==='3 keys' && $('sequence-length').value==='3');
 set('sequence-length',6);
 check('length selectable', $('sequence-length').value==='6' && $('sequence-length').min==='3');
 const six=sequence();
 check('each complete shuffle contains all keys',six.length===6 && [...six.slice(0,3)].sort().join('')==='dfj' && [...six.slice(3)].sort().join('')==='dfj',six);
 set('sequence-rounds',3);
 check('short rounds selectable', $('sequence-rounds').value==='3');
 const beforeShuffle=sequence();
 $('shuffle-sequence').click();
 const fixed=sequence();
 check('explicit shuffle changes order',fixed!==beforeShuffle, fixed);
 $('primary-button').click();
 check('challenge starts', $('phase-text').textContent==='ACTIVE');
 await typeSequence(fixed,70);
 check('round 1 complete', $('phase-text').textContent==='ACTIVE' && $('sequence-round-position').textContent==='2 / 3');
 check('first record visible', !$('achievement-banner').hidden && $('achievement-title').textContent.includes('FIRST PERSONAL RECORD'));
 check('round log one', $('round-log-items').querySelectorAll('.round-log-row').length===1);
 const firstTime=parseFloat($('sequence-personal-best').textContent);
 await typeSequence(fixed,12);
 check('round 2 complete', $('sequence-round-position').textContent==='3 / 3');
 check('best improves', $('achievement-title').textContent.includes('NEW PERSONAL BEST') && !$('achievement-banner').hidden,
    $('achievement-title').textContent);
 const newBest=parseFloat($('sequence-personal-best').textContent);
 check('new record faster',newBest<firstTime,firstTime+' -> '+newBest);
 check('round log two', $('round-log-items').querySelectorAll('.round-log-row').length===2);
 await typeSequence(fixed,80);
 check('three rounds complete', $('phase-text').textContent==='COMPLETED' && $('progress-count').textContent==='18 / 18');
 check('non-record does not claim improvement', $('achievement-banner').hidden);
 check('record still correct',parseFloat($('sequence-personal-best').textContent)===newBest);
 check('round log three', $('round-log-items').querySelectorAll('.round-log-row').length===3);
 check('session history', $('history-list').textContent.includes('Sequence'));
 check('storage includes sequence records', JSON.parse(localStorage.getItem('typewriter.practice.v1')).profile.sequenceRecords && Object.keys(JSON.parse(localStorage.getItem('typewriter.practice.v1')).profile.sequenceRecords).length===1);
 $('new-session').click();
 check('new session preserves sequence',sequence()===fixed && $('progress-count').textContent==='0 / 18');
 check('previous best survives new session',parseFloat($('sequence-personal-best').textContent)===newBest);
 $('shuffle-sequence').click();
 check('new shuffle does not lose prior record',sequence()!==fixed && Object.keys(JSON.parse(localStorage.getItem('typewriter.practice.v1')).profile.sequenceRecords).length===1);
 const afterShuffle=sequence();
 $('mode-keys').click();
 check('old key trainer still works', $('mode-keys').getAttribute('aria-selected')==='true' && $('sequence-options').hidden && $('sequence-score').hidden);
 $('mode-text').click();
 check('old text trainer still works', $('mode-text').getAttribute('aria-selected')==='true' && !$('text-controls').hidden);
 $('mode-sequence').click();
 check('temporarily changing modes preserves sequence',sequence()===afterShuffle && $('mode-sequence').getAttribute('aria-selected')==='true');
 check('no horizontal overflow',document.documentElement.scrollWidth<=document.documentElement.clientWidth+1,
   document.documentElement.scrollWidth+'/'+document.documentElement.clientWidth);
} catch(e) {results.push({name:'exception',ok:false,detail:e.message});}
const out=document.createElement('pre');out.id='typewriter-sequence-probe';out.textContent=JSON.stringify(results);document.body.append(out);
</script>'''

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def run():
    os.chdir(ROOT)
    if PROBE.exists():
        raise RuntimeError('Temporary test file is already present.')
    page = (ROOT / 'index.html').read_text()
    PROBE.write_text(page.replace('</body>', SCRIPT + '\n</body>'))
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(('127.0.0.1', 0), QuietHandler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f'http://127.0.0.1:{server.server_address[1]}/{PROBE.name}'
            cmd = [os.environ.get('CHROMIUM_BIN', 'chromium'), '--headless', '--no-sandbox',
                   '--disable-gpu', '--disable-dev-shm-usage', '--window-size=390,844',
                   '--virtual-time-budget=9000', '--dump-dom', url]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            match = re.search(r'<pre id="typewriter-sequence-probe">(.*?)</pre>', proc.stdout, re.S)
            if not match:
                print(proc.stderr[-1600:])
                raise RuntimeError('Chromium did not return the sequence probe.')
            results = json.loads(html.unescape(match.group(1)))
            for result in results:
                print(('PASS' if result['ok'] else 'FAIL') + ': ' + result['name'] + ' ' + str(result.get('detail', '')))
            assert results and all(r['ok'] for r in results), 'Sequence browser regression failed.'
            print(f'All {len(results)} sequence browser checks passed.')
            server.shutdown()
    finally:
        PROBE.unlink(missing_ok=True)

if __name__ == '__main__':
    run()
