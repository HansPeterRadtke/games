"""Exercise the public UI on desktop and mobile. An optional argument selects a deployed URL."""
from contextlib import ExitStack
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import sys
import tempfile
import threading

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def exercise(url, width, height):
    snap = Path.home() / 'snap/chromium/common'
    with tempfile.TemporaryDirectory(dir=snap if snap.is_dir() else None) as profile:
        options = webdriver.ChromeOptions()
        for arg in ['--headless=new', '--no-sandbox', '--disable-gpu', '--user-data-dir=' + profile]:
            options.add_argument(arg)
        driver = shutil.which('chromium.chromedriver') or shutil.which('chromedriver')
        with webdriver.Chrome(service=Service(driver), options=options) as browser:
            browser.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',
                dict(width=width, height=height, deviceScaleFactor=1, mobile=width<500))
            browser.get(url)
            def el(name): return browser.find_element(By.ID,name)
            def text(name): return el(name).get_attribute('textContent')
            def click(name): el(name).click()
            def select(name,value): Select(el(name)).select_by_value(value)
            def enter(name,value):
                field=el(name)
                field.click()
                field.send_keys(Keys.CONTROL,'a')
                field.send_keys(Keys.BACKSPACE)
                if value: field.send_keys(value)
                field.send_keys(Keys.TAB)
            def press(*keys): ActionChains(browser).send_keys(*keys).perform()
            def data(): return browser.execute_script("return JSON.parse(localStorage.getItem('typewriter.practice.v1'))")
            wait=WebDriverWait(browser,15)
            wait.until(lambda _:len(el('round-window').find_elements(By.TAG_NAME,'option'))==5)
            click('mode-word')
            assert not el('primary-button').is_enabled()
            click('first-word-level')
            assert el('primary-button').is_enabled() and el('word-repeats').get_attribute('value')=='10'
            click('mode-text')
            assert len(text('target-text').split())==3 and 'All 7 letters covered in words' in text('text-coverage-note')
            enter('text-limit','4')
            assert len(text('target-text'))<=4 and 'All letters fit in words from' in text('text-coverage-note')
            enter('text-limit','1')
            assert not el('primary-button').is_enabled() and not text('target-text')
            enter('text-limit','55')
            assert 48 <= len(text('target-text')) <= 55
            enter('text-limit','')
            assert len(text('target-text').split())==3
            if not el('practice-settings').get_attribute('open'):
                browser.find_element(By.CSS_SELECTOR,'#practice-settings > summary').click()
            for _ in range(4): click('level-up')
            assert 'No eligible word for Ä' in text('text-coverage-note') and len(text('target-text').split())==4
            click('mode-word')
            select('word-language','de')
            current=data()['session']['practiceWord']
            enter('word-repeats','3')
            assert data()['session']['practiceWord']==current
            select('word-strategy','selected')
            enter('word-choice','glas')
            assert data()['session']['practiceWord']=='glas'
            click('primary-button')
            press('g','!','l')
            assert len(browser.find_elements(By.CSS_SELECTOR,'#target-text .typed'))==1
            press(Keys.DELETE,'l','a','s')
            assert data()['profile']['wordStats']['glas']['errors']==1 and 'Space for the next' in text('stage-hint')
            press(Keys.SPACE,'g')
            assert '2 OF 3' in text('text-stage-label')
            click('primary-button')
            browser.refresh()
            wait.until(lambda _:text('phase-text')=='PAUSED')
            assert data()['session']['practiceWord']=='glas'
            click('primary-button')
            press('l','a','s',Keys.SPACE,'g','l','a','s')
            assert text('phase-text')=='COMPLETED' and data()['profile']['wordStats']['glas']['count']==3
            select('word-strategy','mistakes')
            assert 'glas' in text('word-draw-note') and '%' in text('word-draw-note')
            select('word-strategy','slowest')
            assert 'glas' in text('word-draw-note')
            select('word-strategy','random')
            samples=set()
            for _ in range(6):
                click('draw-word')
                samples.add(data()['session']['practiceWord'])
            assert len(samples)>1 and browser.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
            print(width,'word coverage and cap, four word sources, corrections, repetition timing, reload and layout passed',flush=True)


if __name__ == '__main__':
    with ExitStack() as stack:
        if len(sys.argv)>1:
            url=sys.argv[1]
        else:
            handler=partial(Quiet,directory=Path(__file__).resolve().parents[1])
            server=stack.enter_context(ThreadingHTTPServer(('127.0.0.1',0),handler))
            threading.Thread(target=server.serve_forever,daemon=True).start()
            stack.callback(server.shutdown)
            url='http://127.0.0.1:%d/' % server.server_address[1]
        for viewport in [(1280,900),(390,844)]: exercise(url,*viewport)
