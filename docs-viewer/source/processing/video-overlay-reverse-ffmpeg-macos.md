---
doc_id: video-overlay-reverse-ffmpeg-macos
title: Video Overlay Reverse Ffmpeg Macos
added_date: "2026-07-14 18:11"
last_updated: "2026-07-14 18:11"
parent_id: unsorted
---
[2025-08-14 14:00] User: How to overlay 2 videos to create a composite video. macOS, using free tools
[2025-08-14 14:01] Assistant:
Provided three options for overlaying videos:
1. FFmpeg command-line method (powerful, free)
2. iMovie GUI method (basic overlay)
3. Shotcut GUI method (open-source, more control)

Included example FFmpeg commands for scaling, positioning, blending, and using transparency.

[2025-08-14 14:02] User: Both videos same size and 50% opacity
[2025-08-14 14:03] Assistant:
Gave FFmpeg blend filter command for 50% opacity:
ffmpeg -i video1.mp4 -i video2.mp4 -filter_complex "[0:v][1:v]blend=all_mode=overlay:all_opacity=0.5" -c:a copy output.mp4
Also provided optional command for mixing audio.

[2025-08-14 14:04] User: Yes
[2025-08-14 14:05] Assistant:
Provided interactive-like FFmpeg command allowing opacity to be set via shell variable.

[2025-08-14 14:06] User: Yes
[2025-08-14 14:07] Assistant:
Gave Automator Quick Action script for macOS to blend two selected videos with adjustable opacity.

[2025-08-14 14:08] User: Can ffmpeg reverse a video?
[2025-08-14 14:09] Assistant:
Provided FFmpeg commands to reverse video only, reverse both video and audio, reverse without re-encoding, and reverse a clip section.

[2025-08-14 14:10] User: Yes
[2025-08-14 14:11] Assistant:
Provided FFmpeg command to reverse one of two overlay videos and blend forward and reverse versions with 50% opacity and mixed audio.

[2025-08-14 14:12] User: Yes
[2025-08-14 14:13] Assistant:
Provided full Automator Quick Action script to:
- Reverse second video
- Blend forward + reverse at adjustable opacity
- Resize second video to match first
- Mix forward + reversed audio
- Save result in same folder
Includes FFmpeg installation check and user input for opacity.

-----
### Main Scripts Included
1. **Blend Two Videos at 50% Opacity**:
ffmpeg -i video1.mp4 -i video2.mp4 \
  -filter_complex "[0:v][1:v]blend=all_mode=overlay:all_opacity=0.5" \
  -c:a copy output.mp4

2. **Blend Two Videos with Adjustable Opacity (Shell Variable)**:
OPACITY=0.5 && ffmpeg -i video1.mp4 -i video2.mp4 \
-filter_complex "[0:v][1:v]blend=all_mode=overlay:all_opacity=${OPACITY}" \
-c:a copy output.mp4

3. **Automator Quick Action - Blend Two Videos with Adjustable Opacity**:
<full bash script provided in chat>

4. **Reverse Video (Video Only)**:
ffmpeg -i input.mp4 -vf reverse -af anull output.mp4

5. **Reverse Video + Audio**:
ffmpeg -i input.mp4 -vf reverse -af areverse output.mp4

6. **Forward + Reverse Composite Blend (FFmpeg)**:
ffmpeg -i video1.mp4 -i video2.mp4 \
-filter_complex "[1:v]reverse[rev]; [0:v][rev]blend=all_mode=overlay:all_opacity=0.5[v]; [0:a]volume=0.5[a0]; [1:a]areverse,volume=0.5[a1]; [a0][a1]amix=inputs=2:duration=longest[a]" \
-map "[v]" -map "[a]" output.mp4

7. **Automator Quick Action - Forward + Reverse Blend with Adjustable Opacity**:
<full bash script provided in chat>
