#!/usr/bin/env bash
set -euo pipefail
VENV=${LLM_GAME_VIDEO_VENV:-/data/venv-video}
BASE_VENV=${LLM_GAME_BASE_VENV:-/data/venv}
python3 -m venv --system-site-packages "$VENV"
python_version=$($VENV/bin/python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')
site_dir="$VENV/lib/$python_version/site-packages"
mkdir -p "$site_dir"
printf '%s\n' "$BASE_VENV/lib/$python_version/site-packages" > "$site_dir/base-venv.pth"
"$VENV/bin/pip" install --disable-pip-version-check --no-cache-dir \
  'kornia>=0.8,<0.9' \
  'timm>=1.0,<2.0' \
  'opencv-python-headless>=4.12,<4.13'
"$VENV/bin/python3" - <<'PY'
import cv2,diffusers,kornia,timm,torch,transformers
print({
    'torch':torch.__version__,
    'diffusers':diffusers.__version__,
    'transformers':transformers.__version__,
    'kornia':kornia.__version__,
    'timm':timm.__version__,
    'cv2':cv2.__version__,
    'cuda':torch.cuda.is_available(),
})
PY
