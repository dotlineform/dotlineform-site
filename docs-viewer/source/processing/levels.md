---
doc_id: levels
title: Levels
added_date: "2026-07-14 13:06"
last_updated: "2026-07-14 13:06"
parent_id: composites-engine
---
# Levels


Gotcha — here’s an updated **Automator Quick Action that adds an adjustable “auto‑contrast/auto‑levels” step to your forward+reverse blend. You can pick the enhancement each time (Normalize, Histogram Equalize, EQ preset, or None).**

## **Paste this into Automator → Quick Action → Run Shell Script (Shell: /bin/bash, Pass input: as arguments). It still:**
	•	reverses the **second** selected video
	•	scales/pads it to the first video’s size
	•	blends at your chosen opacity
	•	**then** applies the enhancement you choose
	•	mixes audio (handles no/one/both audio tracks gracefully)

#!/bin/bash

*# ---------- Defaults ----------*
DEFAULT_OPACITY="0.5"        *# 0.0–1.0*
CRF="20"                     *# H.264 quality (lower = better)*
PRESET="medium"              *# x264 speed/quality*
AUDIO_MIX_DURATION="shortest" *# shortest|longest|first*

*# ---------- Checks ----------*
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  osascript -e 'display alert "FFmpeg not found" message "Install via: brew install ffmpeg"'
  exit 1
fi

if [ "$#" -ne 2 ]; then
  osascript -e 'display alert "Please select exactly TWO video files in Finder, then run the Quick Action again."'
  exit 1
fi

VIDEO1="$1"   *# forward*
VIDEO2="$2"   *# reversed*

*# ---------- Ask for opacity ----------*
OPACITY=$(osascript -e 'text returned of (display dialog "Enter blend opacity (0.0–1.0):" default answer "'"$DEFAULT_OPACITY"'")' 2>/dev/null)
if ! [[ "$OPACITY" =~ ^0(\.[0-9]+)?$|^1(\.0+)?$ ]]; then
  osascript -e 'display alert "Invalid opacity" message "Enter a number between 0.0 and 1.0."'
  exit 1
fi

*# ---------- Ask for enhancement ----------*
CHOICE=$(osascript -e 'choose from list {"Normalize (auto-levels)","Histogram Equalize","EQ Preset (contrast/brightness)","None"} with title "FFmpeg Enhancement" with prompt "Choose a levels/contrast enhancement to apply AFTER blending:" default items {"Normalize (auto-levels)"}' 2>/dev/null)
*# Handle cancel*
if [ "$CHOICE" = "false" ] || [ -z "$CHOICE" ]; then
  exit 0
fi

*# Map choice to filter*
ENHANCE_FILTER=""
case "$CHOICE" in
  *"Normalize"*)
    *# Stretch luma to near full range (leave tiny headroom to avoid clipping).*
    ENHANCE_FILTER='[blended]normalize=blackpt=0.02:whitept=0.98[v]'
    ;;
  *"Histogram Equalize"*)
    *# Global histogram equalization (milder look with these params).*
    ENHANCE_FILTER='[blended]histeq=strength=0.8:intensity=0.3[v]'
    ;;
  *"EQ Preset"*)
    *# Gentle contrast/brightness/saturation tweak.*
    ENHANCE_FILTER='[blended]eq=contrast=1.2:brightness=0.02:saturation=1.05[v]'
    ;;
  *"None"*)
    ENHANCE_FILTER='[blended]copy[v]'
    ;;
esac

*# ---------- Probe size from VIDEO1 ----------*
read -r W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
  -of csv=p=0:s=" " "$VIDEO1")
if [ -z "$W" ] || [ -z "$H" ]; then
  osascript -e 'display alert "Could not read dimensions" message "VIDEO1 has no detectable video stream."'
  exit 1
fi

*# ---------- Check audio presence ----------*
has_a1=false
has_a2=false
ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of csv=p=0 "$VIDEO1" >/dev/null 2>&1 && has_a1=true
ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of csv=p=0 "$VIDEO2" >/dev/null 2>&1 && has_a2=true

OUTDIR="$(dirname "$VIDEO1")"
STAMP="$(date +"%Y%m%d-%H%M%S")"
OUTFILE="${OUTDIR}/blend_fwd_rev_${STAMP}.mp4"

*# ---------- Build filter graph ----------*
*# Video path:*
*# 1) reverse 2nd, scale/pad to match first*
*# 2) blend forward+reverse -> [blended]*
*# 3) enhancement -> [v]*
VIDEO_CHAIN="
[1:v]reverse,scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2[revv];
[0:v][revv]blend=all_mode=overlay:all_opacity=${OPACITY}[blended];
${ENHANCE_FILTER}
"

*# Audio path (robust to missing streams)*
AUDIO_CHAIN=""
AUDIO_MAP=""
if $has_a1 && $has_a2; then
  AUDIO_CHAIN="
  [0:a]volume=${OPACITY}[a0];
  [1:a]areverse,volume=${OPACITY}[a1];
  [a0][a1]amix=inputs=2:duration=${AUDIO_MIX_DURATION}[a]"
  AUDIO_MAP='-map "[a]"'
elif $has_a1 && ! $has_a2; then
  AUDIO_CHAIN="[0:a]volume=${OPACITY}[a]"
  AUDIO_MAP='-map "[a]"'
elif ! $has_a1 && $has_a2; then
  AUDIO_CHAIN="[1:a]areverse,volume=${OPACITY}[a]"
  AUDIO_MAP='-map "[a]"'
else
  AUDIO_MAP='-an'  *# no audio present*
fi

FILTER_COMPLEX="${VIDEO_CHAIN} ${AUDIO_CHAIN}"

*# ---------- Run FFmpeg ----------*
ffmpeg -hide_banner -y \
  -i "$VIDEO1" -i "$VIDEO2" \
  -filter_complex "$FILTER_COMPLEX" \
  -map "[v]" ${AUDIO_MAP} \
  -c:v libx264 -crf "$CRF" -preset "$PRESET" -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  "$OUTFILE"

STATUS=$?
if [ $STATUS -eq 0 ]; then
  osascript -e 'display notification "Created: '"$(basename "$OUTFILE")"'" with title "FFmpeg Blend + Enhance"'
else
  osascript -e 'display alert "FFmpeg failed" message "Check your inputs and try again."'
  exit $STATUS
fi

**What the enhancement options do**
	•	**Normalize (auto‑levels)**: expands luma to (≈) full range — closest to “auto-levels”.
	•	**Histogram Equalize**: boosts global contrast by redistributing brightness values.
	•	**EQ Preset**: a tasteful bump to contrast/brightness/saturation.
	•	**None**: leaves the blend untouched.

Want a **separate Quick Action that only auto-levels any single video** (no blending), or to **lock a default enhancement** (no prompt) for speed? I can drop trimmed variants too.
