#!/usr/bin/env python3
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
apache = (ROOT / 'deploy/apache.conf.in').read_text()
preset = (ROOT / 'export_presets.cfg').read_text()
shell = (ROOT / 'deploy/web_shell.html').read_text()
build = (ROOT / 'deploy/build-web.sh').read_text()
install = (ROOT / 'deploy/install-nitro.sh').read_text()
verify = (ROOT / 'deploy/nitro-verify.sh').read_text()
generated_build = (ROOT / 'deploy/build-generated-world.sh').read_text()
project = (ROOT / 'project.godot').read_text()
assert 'Alias /llm_game/ "/data/src/github/games/godot_llm_generated_game_lab/web/"' in apache
assert 'Header always set Cross-Origin-Opener-Policy "same-origin"' in apache
assert 'Header always set Cross-Origin-Embedder-Policy "require-corp"' in apache
assert 'Header always set Cross-Origin-Resource-Policy "same-origin"' in apache
assert 'variant/thread_support=false' in preset
assert 'html/custom_html_shell="res://deploy/web_shell.html"' in preset
assert 'html/canvas_resize_policy=0' in preset
assert 'your-mom-generated-world-v1' in shell
assert 'Loading Your Mom — generated entirely by models' in shell
assert "finishStartup('godotReady')" in shell
assert "startupError = 'timeout'" in shell
assert 'Loading Grounded Medieval RPG' not in shell
assert 'id="controls-panel"' in shell and 'id="touch-controls"' in shell
assert 'forge-form' not in shell and 'touch-layer' not in shell
assert 'viewport-fit=cover' in shell and 'touch-action:none' in shell and 'overscroll-behavior:none' in shell
assert 'grid-template-areas:"hud stage controls"' in shell
assert 'grid-template-areas:"hud" "stage" "controls"' in shell
assert 'run/main_scene="res://scenes/generated_world.tscn"' in project
assert 'config/name="Your Mom"' in project
match = re.search(r'GODOT_WEB_BIN=\$\{GODOT_WEB_BIN:-([^}]+)\}', build)
assert match
web_exporter = Path(match.group(1))
assert web_exporter.name == 'Godot_v4.6.1-stable_linux.x86_64'
assert web_exporter.is_file() and web_exporter.stat().st_mode & 0o111
assert '"$GODOT_WEB_BIN" --headless' in build
assert 'your-mom-generated-world-v1' in build
assert 'your-mom-generated-world-v1' in install
assert 'build-generated-world.sh' in str(ROOT / 'deploy/build-generated-world.sh')
assert 'compile_world_assets' in generated_build
assert 'fallback_used' in generated_build
assert 'generated_assets/manifest.json' in generated_build
assert 'https://nitro.jonnyontherun.org/llm_game' in verify
assert 'Cross-Origin-Opener-Policy' not in verify or 'cross-origin-opener-policy' in verify.lower()
assert 'verify_generated_world_browser.py' in verify
assert 'firefox --no-remote' in verify and '"$PUBLIC/"' in verify
assert 'scene=Dining_Room assets=10' in verify
for script in ['deploy/build-web.sh','deploy/install-nitro.sh','deploy/nitro-verify.sh','deploy/build-generated-world.sh']:
    assert (ROOT / script).is_file()
print(f'deployment_contract ok exporter={web_exporter} generated_world=true public_browser=true')
