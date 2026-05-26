#!/usr/bin/env bash
# Generate hicolor PNG icons from a master source image.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-$ROOT/data/icons/screen-off-timer-master.png}"
ICONS="$ROOT/data/icons/hicolor"

if [[ ! -f "$SRC" ]]; then
    echo "Source icon not found: $SRC" >&2
    exit 1
fi

for size in 16 32 48 64 128 256; do
    dir="$ICONS/${size}x${size}/apps"
    mkdir -p "$dir"
    if command -v magick >/dev/null 2>&1; then
        magick "$SRC" -resize "${size}x${size}" -filter Lanczos "$dir/screen-off-timer.png"
    elif command -v convert >/dev/null 2>&1; then
        convert "$SRC" -resize "${size}x${size}" -filter Lanczos "$dir/screen-off-timer.png"
    else
        python3 - "$SRC" "$dir/screen-off-timer.png" "$size" <<'PY'
import sys
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    sys.exit("Install python3-pil or imagemagick")
src, dest, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
img = Image.open(src).convert("RGBA")
img.resize((size, size), Image.Resampling.LANCZOS).save(dest)
PY
    fi
    echo "Wrote $dir/screen-off-timer.png"
done
