#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/submission"
SLIDES="$OUT/slides"
AUDIO="$OUT/audio"
SEGMENTS="$OUT/segments"
FFMPEG="$($ROOT/.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"

mkdir -p "$AUDIO" "$SEGMENTS"

for index in 01 02 03 04 05 06 07; do
  test -f "$SLIDES/$index.png"
  /usr/bin/say -v Samantha -r 178 -f "$ROOT/video/narration/$index.txt" -o "$AUDIO/$index.aiff"
  "$FFMPEG" -y \
    -loop 1 -framerate 24 -i "$SLIDES/$index.png" \
    -i "$AUDIO/$index.aiff" \
    -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
    -af "apad=pad_dur=0.45" \
    -c:v libx264 -preset veryfast -tune stillimage -crf 22 -pix_fmt yuv420p -r 24 \
    -c:a aac -b:a 160k -shortest -movflags +faststart \
    "$SEGMENTS/$index.mp4"
done

CONCAT="$OUT/concat.txt"
: > "$CONCAT"
for index in 01 02 03 04 05 06 07; do
  printf "file '%s'\n" "$SEGMENTS/$index.mp4" >> "$CONCAT"
done

"$FFMPEG" -y -fflags +genpts -f concat -safe 0 -i "$CONCAT" \
  -c:v copy -c:a aac -b:a 128k -af "aresample=async=1:first_pts=0" \
  -movflags +faststart "$OUT/datahub-changeguard-demo.mp4"

printf 'Created %s\n' "$OUT/datahub-changeguard-demo.mp4"
