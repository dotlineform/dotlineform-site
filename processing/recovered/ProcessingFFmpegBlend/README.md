# Processing FFmpeg Blender

A Processing 4.x sketch that acts as a small GUI wrapper around FFmpeg to **blend two videos** with an **opacity slider**, optional **reverse second video**, and **audio normalization**.

## Requirements
- Processing 4.x (Java mode)
- FFmpeg installed and available on PATH (`ffmpeg`, `ffprobe` optional)
  - macOS: `brew install ffmpeg`

## Use
1. Open `ProcessingFFmpegBlend.pde` in Processing.
2. Click **Choose Video 1** and **Choose Video 2**.
3. Drag the **Opacity** slider (0–1).
4. (Optional) Click **Toggle Reverse 2** or **Toggle Normalize**.
5. Click **Render** (or press `R`). Check the log panel for progress.
6. Output file defaults to `blend_YYYYmmdd-HHMMSS.mp4` next to Video 1. Use **Save As…** to override.

## Notes
- This sketch *calls* FFmpeg; it does not play/preview videos in Processing.
- If `ffmpeg` isn't found, set `ffmpegPath` at the top of the sketch to its absolute path.
- The default encode is H.264 (`libx264`, CRF 20, preset medium). You can tweak the command array in `startFFmpeg()` to switch to HEVC, ProRes, etc.
