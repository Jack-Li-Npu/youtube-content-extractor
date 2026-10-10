#!/bin/bash
set -euo pipefail
APP_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  echo "Local MLX speech recognition requires an Apple Silicon Mac. Existing captions do not need it." >&2
  exit 1
fi
for tool in uv ffmpeg ffprobe; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing $tool. Install uv and FFmpeg (brew install ffmpeg), then retry." >&2
    exit 1
  fi
done
cd "$APP_ROOT"
echo "Setting up optional local speech recognition. The pinned Whisper model uses about 1.6 GB; Python dependencies need additional space."
uv sync --project backend --frozen
uv sync --project stt --frozen --python 3.12
backend/.venv/bin/python stt/download_model.py
echo "Speech setup complete. Restart the extractor if you changed .env."
