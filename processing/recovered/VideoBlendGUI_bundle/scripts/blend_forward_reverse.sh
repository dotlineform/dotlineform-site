#!/bin/bash
# Blend two videos forward + reverse with opacity
V1="$1"; V2="$2"; OP="${3:-0.5}"
OUT="blend_fwd_rev_$(date +%Y%m%d-%H%M%S).mp4"
ffmpeg -i "$V1" -i "$V2" -filter_complex "[1:v]reverse[rev]; [0:v][rev]blend=all_mode=overlay:all_opacity=${OP}[v]" -map "[v]" "$OUT"
