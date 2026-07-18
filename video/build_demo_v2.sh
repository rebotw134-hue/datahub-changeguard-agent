#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/submission"
BUILD="$OUT/v2-build"
SLIDES="$OUT/slides"
AUDIO="$BUILD/audio"
SEGMENTS="$BUILD/segments"
FFMPEG="$($ROOT/.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
FINAL="$OUT/datahub-changeguard-demo-v2.mp4"

mkdir -p "$AUDIO" "$SEGMENTS"

motion_filter() {
  case "$1" in
    02)
      printf "%s" "zoompan=z='1.045':x='(iw-iw/zoom)*on/600':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
      ;;
    04)
      printf "%s" "zoompan=z='1.045':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*on/600':d=1:s=1920x1080:fps=30"
      ;;
    06)
      printf "%s" "zoompan=z='1.045':x='(iw-iw/zoom)*(1-on/600)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
      ;;
    *)
      printf "%s" "zoompan=z='zoom+0.00009':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
      ;;
  esac
}

for index in 01 02 03 04 05 06 07; do
  test -f "$SLIDES/$index.png"
  /usr/bin/say -v Samantha -r 178 -f "$ROOT/video/narration/$index.txt" \
    -o "$AUDIO/$index.aiff"

  "$FFMPEG" -y -hide_banner -loglevel warning \
    -loop 1 -framerate 30 -i "$SLIDES/$index.png" \
    -i "$AUDIO/$index.aiff" \
    -vf "$(motion_filter "$index")" \
    -af "apad=pad_dur=0.45" \
    -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
    "$SEGMENTS/$index.mp4"
done

CONCAT="$BUILD/concat.txt"
: > "$CONCAT"
for index in 01 02 03 04 05 06 07; do
  printf "file '%s'\n" "$SEGMENTS/$index.mp4" >> "$CONCAT"
done

RAW="$BUILD/datahub-changeguard-demo-v2-raw.mp4"
"$FFMPEG" -y -hide_banner -loglevel warning -fflags +genpts \
  -f concat -safe 0 -i "$CONCAT" \
  -c:v copy -c:a aac -b:a 192k -af "aresample=async=1:first_pts=0" \
  -movflags +faststart "$RAW"

"$FFMPEG" -y -hide_banner -loglevel warning -i "$RAW" \
  -vf "subtitles=$ROOT/video/captions_v2.srt:fontsdir=/System/Library/Fonts:force_style='FontName=PingFang SC,FontSize=12,PrimaryColour=&H00FFFFFF,BackColour=&H60000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=8,Alignment=2'" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=7" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$FINAL"

printf 'Created %s\n' "$FINAL"
