#!/usr/bin/env python3
from __future__ import annotations
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "deploy/web_shell.html"
PRESET = (ROOT / "export_presets.cfg").read_text()
MAIN = (ROOT / "scripts/main.gd").read_text()
html = SHELL.read_text()

class Structure(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.parents: dict[str, list[str]] = {}
        self.ids: set[str] = set()
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        element_id = data.get("id")
        if element_id:
            self.ids.add(element_id)
            self.parents[element_id] = list(self.stack)
        if tag not in {"meta","link","input","img","br","hr"}:
            self.stack.append(element_id or tag)
    def handle_endtag(self, tag: str) -> None:
        if self.stack:
            self.stack.pop()

parsed = Structure()
parsed.feed(html)
required_placeholders = {"$GODOT_URL", "$GODOT_CONFIG", "$GODOT_PROJECT_NAME", "$GODOT_HEAD_INCLUDE"}
assert required_placeholders <= set(re.findall(r"\$GODOT_[A-Z_]+", html))
required_ids = {
    "app", "hud-panel", "stage", "canvas", "controls-panel", "control-deck", "control-status", "touch-controls",
    "stick", "stick-base", "stick-thumb", "action-pad", "reset-button", "loading",
}
assert required_ids <= parsed.ids
assert "stage" not in parsed.parents["touch-controls"]
assert "canvas" not in parsed.parents["touch-controls"]
assert "canvas" not in parsed.parents["hud-panel"]
assert "canvas" not in parsed.parents["controls-panel"]
assert "controls-panel" in parsed.parents["touch-controls"] or "control-deck" in parsed.parents["touch-controls"]
assert 'grid-template-areas:"hud stage controls"' in html
assert 'grid-template-areas:"hud" "stage" "controls"' in html
assert '@media (orientation:portrait)' in html
assert 'env(safe-area-inset-top' in html and 'env(safe-area-inset-bottom' in html
assert '#stick-base { width:118px; height:118px' in html
assert '#stick-thumb { position:absolute; left:50%; top:50%; width:48px; height:48px' in html
assert "setPointerCapture(event.pointerId)" in html
assert "pointermove" in html and "pointerup" in html and "pointercancel" in html and "lostpointercapture" in html
assert "sendMove(dx / stick.max, dy / stick.max)" in html
assert "sendMove(0, 0)" in html
assert "navigator.maxTouchPoints" in html and "matchMedia('(pointer:coarse)')" in html
assert html.count('class="action-button') == 4
for action in ["attack", "jump", "parry", "potion", "reset"]:
    assert f'data-action="{action}"' in html
assert "llmGameGodotMove" in html and "llmGameGodotAction" in html
assert "forge-form" not in html and "forge-input" not in html and "forge-button" not in html
assert "touch-layer" not in html
assert "window.llmGameShell" in html and "updateState(raw)" in html
assert "new ResizeObserver(requestCanvasResize).observe(stage)" in html
assert "canvasResizePolicy:0" in html
assert "viewport-fit=cover" in html
assert 'html/custom_html_shell="res://deploy/web_shell.html"' in PRESET
assert 'html/canvas_resize_policy=0' in PRESET
assert 'html/head_include=""' in PRESET
assert "your-mom-stableanimator-scene-v5" in html
assert "transform:scale(.84)" not in html
assert "interface_canvas.visible = false" in MAIN
assert "window.llmGameGodotMove = _web_move_callback" in MAIN
assert "window.llmGameGodotAction = _web_action_callback" in MAIN
assert "window.llmGameGodotForge = _web_forge_callback" in MAIN
assert 'shell.updateState(JSON.stringify(payload))' in MAIN
print("web_shell_contract ok controls=dedicated-panel canvas=game-only forge=absent objects=opening-route")

assert "Loading Your Mom — generated entirely by models" in html
assert "finishStartup('godotReady')" in html
assert "startupComplete" in html
assert "startupError = 'timeout'" in html
assert "Loading Grounded Medieval RPG" not in html
assert 'Object.entries(inventory)' in html
assert 'Array.isArray(inventory)' in html
assert 'inventoryItems.join' in html
assert 'startEngineSequentially' in html
assert 'engine.start()' in html
assert 'preload-game-package' in html
assert 'initialize-webassembly' in html
assert 'start-generated-scene' in html
assert '180000' in html
assert 'engine.startGame({' not in html
assert "new URL('/llm_game/', location.origin)" in html
assert "const executableUrl = new URL('index', assetBase).href" in html
assert "const packUrl = new URL('index.pck', assetBase).href" in html
assert 'engine.preloadFile(packUrl, packVirtualPath)' in html
assert 'engine.init(executableUrl)' in html
assert 'executable: executableUrl' in html
assert 'engine.preloadFile(pack, pack)' not in html
assert 'engine.init(config.executable)' not in html
assert 'app.dataset.inventory' in html
assert 'app.dataset.gameStats' in html
assert 'app.dataset.objectStates' in html
