"""Exercise actual Typewriter DOM in headless Chromium, without WebDriver."""
import contextlib
import html
import http.server
import json
import os
from pathlib import Path
import re
import socketserver
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / '.typewriter-probe-temporary.html'

SCRIPT = r'''<script type="module">
const $=id=>document.getElementById(id);
const results=[];
const check=(name,ok,detail='')=>results.push({name,ok,detail});
const press=key=>document.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true}));
try {
 await new Promise(r=>setTimeout(r,300));
 check('ready', $('phase-text').textContent==='READY');
 check('passages', $('passage-select').options.length===8);
 $('primary-button').click();
 check('start', $('phase-text').textContent==='ACTIVE');
 const k=$('target-key').textContent.toLowerCase();
 press('x');
 check('wrong key', $('stat-errors').textContent==='1');
 press(k);
 check('correct key', $('progress-count').textContent==='1 / 50');
 press(' ');
 check('pause', $('phase-text').textContent==='PAUSED');
 press(' ');
 check('resume', $('phase-text').textContent==='ACTIVE');
 press('Escape');
 check('escape', $('phase-text').textContent==='PAUSED');
 window.confirm=()=>true;
 $('mode-text').click();
 check('mode switch', $('mode-text').getAttribute('aria-selected')==='true');
 $('passage-select').value='custom'; $('passage-select').dispatchEvent(new Event('change',{bubbles:true}));
 $('custom-text').value='f j'; $('custom-text').dispatchEvent(new Event('input',{bubbles:true}));
 check('custom passage', $('custom-text').value==='f j');
 $('primary-button').click();
 for(const c of 'f j') press(c);
 check('complete', $('phase-text').textContent==='COMPLETED');
 check('progress', $('progress-count').textContent==='3 / 3');
 check('accuracy', $('stat-accuracy').textContent==='100%');
 check('persisted', Boolean(localStorage.getItem('typewriter.practice.v1')));
 check('responsive',document.documentElement.scrollWidth<=document.documentElement.clientWidth+1);
} catch(e) {results.push({name:'exception',ok:false,detail:e.message});}
const out=document.createElement('pre');out.id='typewriter-probe';out.textContent=JSON.stringify(results);document.body.append(out);
</script>'''

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def run():
    os.chdir(ROOT)
    if PROBE.exists():
        raise RuntimeError('Temporary test page already exists; will not overwrite it.')
    html_text = (ROOT / 'index.html').read_text()
    if '</body>' not in html_text:
        raise RuntimeError('Cannot find page body.')
    PROBE.write_text(html_text.replace('</body>', SCRIPT + '\n</body>'))
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(('127.0.0.1', 0), QuietHandler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f'http://127.0.0.1:{server.server_address[1]}/{PROBE.name}'
            cmd = [os.environ.get('CHROMIUM_BIN', 'chromium'), '--headless', '--no-sandbox',
                   '--disable-gpu', '--disable-dev-shm-usage', '--window-size=390,844',
                   '--virtual-time-budget=3500', '--dump-dom', url]
            # Running Chrome as snap can be noisy on stderr, which is captured rather than printed.
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            match = re.search(r'<pre id="typewriter-probe">(.*?)</pre>', proc.stdout, re.S)
            if not match:
                print(proc.stderr[-1500:])
                raise RuntimeError('Chromium did not return the result element.')
            results = json.loads(html.unescape(match.group(1)))
            for result in results:
                print(('PASS' if result['ok'] else 'FAIL') + ': ' + result['name'] + ' ' + str(result.get('detail', '')))
            assert all(x['ok'] for x in results), 'Browser interaction failures'
            print(f'All {len(results)} Chromium interaction checks passed.')
            server.shutdown()
    finally:
        PROBE.unlink(missing_ok=True)

if __name__ == '__main__':
    run()
