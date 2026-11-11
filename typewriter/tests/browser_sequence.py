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
 for (const mode of ['keys','text','sequence']) {
   $('mode-'+mode).click();
   const target=$('prompt-surface').getBoundingClientRect(), start=$('primary-button').getBoundingClientRect();
   check(mode+' target and Start fit the initial view',target.top>=0 && start.bottom<=innerHeight);
 }
 check('empty round history has an explanation',$('round-chart').hidden && !$('round-empty').hidden);
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
 $('mode-sequence').click();
 $('mode-sequence').focus();
 $('mode-sequence').dispatchEvent(new KeyboardEvent('keydown',{key:' ',code:'Space',bubbles:true,cancelable:true}));
 check('Space on the selected mode starts and focuses typing',document.activeElement===$('type-capture'));
 document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:' ',code:'Space',repeat:true,bubbles:true,cancelable:true}));
 check('challenge starts', $('phase-text').textContent==='ACTIVE');
 await typeSequence(fixed,70);
 check('round 1 complete', $('phase-text').textContent==='ROUND COMPLETE' && $('sequence-round-position').textContent==='2 / 3');
 check('first record visible', !$('achievement-banner').hidden && $('achievement-title').textContent.includes('First round recorded'));
 check('round log one', $('round-log-items').querySelectorAll('.round-log-row').length===1);
 check('baseline chart contains a single centered round', $('round-plot').querySelectorAll('circle').length===1
   && $('round-axis-end').textContent==='Round 1' && $('round-axis-end').parentElement.classList.contains('single-round'));
 const firstTime=parseFloat($('sequence-personal-best').textContent);
 press(fixed[0]); press(fixed[1]);
 check('round break ignores type-ahead and tells the player to press Space',$('progress-count').textContent==='6 / 18'
   && $('stage-hint').textContent.includes('Press Space to start round 2'));
 press(' ');
 await typeSequence(fixed,12);
 check('round 2 complete', $('sequence-round-position').textContent==='3 / 3');
 check('best improves', $('achievement-title').textContent.includes('All-time best round time') && !$('achievement-banner').hidden,
    $('achievement-title').textContent);
 const newBest=parseFloat($('sequence-personal-best').textContent);
 check('new record faster',newBest<firstTime,firstTime+' -> '+newBest);
 check('round log two', $('round-log-items').querySelectorAll('.round-log-row').length===2);
 const capture=$('type-capture');
 capture.value=' ';
 capture.dispatchEvent(new InputEvent('input',{inputType:'insertText',data:' ',bubbles:true}));
 check('virtual keyboard Space starts the next round',$('phase-text').textContent==='ACTIVE');
 await typeSequence(fixed,80);
 check('three rounds complete', $('phase-text').textContent==='COMPLETED' && $('progress-count').textContent==='18 / 18');
 check('slower final round acknowledged accurately', $('round-result').textContent.startsWith('Clean round') && !$('round-result').textContent.includes('All-time best'));
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
 // Repeat controlled times on a fresh sequence length. Use the normal input handlers.
 set('sequence-length',7);
 set('sequence-rounds',10);
 const race=sequence();
 let clock=10000;
 Object.defineProperty(performance,'now',{configurable:true,value:()=>clock});
 for (const pace of [200,100,300,300,300,220]) {
   press(' ');
   for (const c of race) { clock+=pace; press(c); }
   if ($('sequence-round-position').textContent==='6 / 10')
     check('plateau earns a completion milestone',$('round-result').textContent.includes('5 rounds completed'));
 }
 check('rolling win survives faster lifetime record',$('achievement-banner').dataset.tier==='recent'
   && $('round-result').textContent.includes('previous 3 rounds') && $('sequence-personal-best').textContent==='700 ms'
   && $('recent-best').textContent==='1.54 s');
 check('popup never takes typing focus',document.activeElement===$('type-capture')
   && getComputedStyle($('achievement-banner')).pointerEvents==='none');
 set('round-window',10);
 check('larger comparison includes earlier fastest round',$('recent-best').textContent==='700 ms' && $('round-scope').textContent.includes('6 recent rounds'));
 check('chronological graph includes every comparable round',$('round-plot').querySelectorAll('circle').length===6
   && $('round-axis-start').textContent==='Round 1' && $('round-axis-end').textContent==='Round 6'
   && Number($('scale-top').textContent)<Number($('scale-bottom').textContent));
 set('chart-metric','accuracy');
 const dots=[...$('round-plot').querySelectorAll('circle')];
 check('tied accuracy scores share one height',dots.length===6 && dots.every(dot=>dot.getAttribute('cy')===dots[0].getAttribute('cy'))
   && Number($('scale-top').textContent)>Number($('scale-bottom').textContent));
 check('exact readings accompany the chart',$('round-values').querySelectorAll('tbody tr').length===6
   && $('round-values').querySelector('tbody tr:last-child').textContent.includes('100%'));
 $('celebrations').click();
 press(' ');
 for (const c of race) { clock+=30; press(c); }
 check('celebrations can be silenced without losing the result',$('achievement-banner').hidden
   && $('round-result').textContent.includes('All-time best') && $('reward-announcement').textContent.includes('All-time best'));
 const restored=JSON.parse(localStorage.getItem('typewriter.practice.v1')).profile;
 check('comparison settings and actual rounds stored',restored.celebrations===false && restored.roundWindow===10 && Object.values(restored.sequenceRecords).some(r=>r.recentRounds.length===7));
 check('no horizontal overflow',document.documentElement.scrollWidth<=document.documentElement.clientWidth+1,
   document.documentElement.scrollWidth+'/'+document.documentElement.clientWidth);
 const {renderRoundChart}=await import('./src/round_chart.js');
 const migrated=[{score:1200,accuracy:93},{score:1300,accuracy:null},{score:1000,accuracy:98}];
 renderRoundChart({count:12},migrated,true,String);
 check('missing accuracy leaves a gap and retains the round index',$('round-plot').querySelectorAll('circle').length===2
   && $('round-plot').querySelector('path').getAttribute('d').trim().split('M').length===3
   && $('round-axis-start').textContent==='Round 10' && $('round-axis-end').textContent==='Round 12');
 renderRoundChart({count:1},[migrated[1]],true,String);
 check('unknown metric shows its explanation and round table',!$('chart-missing').hidden
   && $('round-plot').parentElement.hidden && $('round-values').querySelectorAll('tbody tr').length===1);
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
