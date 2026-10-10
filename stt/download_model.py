"""Install pinned Whisper data files; never execute remote model code."""

import argparse
import hashlib
import os
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

REPO = "mlx-community/whisper-large-v3-turbo"
REVISION = "a4aaeec0636e6fef84abdcbe3544cb2bf7e9f6fb"
FILES = {
    "config.json": (
        268,
        "b34fc29e4e11e0a25e812775dd67f4dd16fc2c8eb43d28ae25ff7d660ecb6379",
    ),
    "weights.safetensors": (
        1613977612,
        "951ed3fc1203e6a62467abb2144a96ce7eafca8fa77e3704fdb8635ff3e7f8a6",
    ),
}


def matches(path, size, sha):
    if not path.is_file() or path.stat().st_size != size:
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == sha


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path(
            os.environ.get(
                "STT_MODEL_DIR",
                str(
                    Path.home()
                    / ".cache/efficient-content-extractor/models/whisper-turbo"
                ),
            )
        ),
    )
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("YT_PROXY") or os.environ.get("HTTPS_PROXY")
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"https": proxy} if proxy else {})
    )
    for name, (size, sha) in FILES.items():
        target = args.destination / name
        if matches(target, size, sha):
            print(f"Verified existing {name}", flush=True)
            continue
        partial = target.with_suffix(".partial")
        print(f"Downloading {name} ({size / 1e9:.2f} GB)…", flush=True)
        with (
            opener.open(
                f"https://huggingface.co/{REPO}/resolve/{REVISION}/{name}", timeout=60
            ) as response,
            partial.open("wb") as stream,
        ):
            while chunk := response.read(8 * 1024 * 1024):
                stream.write(chunk)
        if not matches(partial, size, sha):
            partial.unlink(missing_ok=True)
            raise RuntimeError(
                f"Incomplete file or SHA-256 mismatch for {name}; run setup again."
            )
        partial.replace(target)
        print(f"Verified {name}", flush=True)


if __name__ == "__main__":
    main()
