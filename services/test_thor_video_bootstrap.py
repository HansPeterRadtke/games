#!/usr/bin/env python3
from pathlib import Path
source=Path(__file__).with_name('bootstrap_thor_video_env.sh').read_text()
for token in ['/data/venv-video','/data/venv','base-venv.pth','kornia','timm','opencv-python-headless','torch.cuda.is_available']:
    assert token in source,token
assert 'sudo' not in source
print('thor video bootstrap contracts passed')
