# VideoBlendGUI v2 (SwiftUI + FFmpeg) — Optimised MVVM

This Xcode project demonstrates:
- MVVM split (`ContentView`, `BlendViewModel`, `FFmpegCommandBuilder`, `ProbeService`)
- **JSON ffprobe** parsing (robust size/audio detection)
- Centralised filter graph builder with clean line-per-node strings
- Optional **slow‑motion** with `setpts` + `minterpolate` (balanced preset)
- Audio mix with **aformat** normalization and optional **normalize** on amix
- Cancelable FFmpeg process & streamed log

## Build
1. Install FFmpeg:
```bash
brew install ffmpeg
```
2. Open this folder in **Xcode** (App, SwiftUI, macOS). Add these files to the target if needed.
3. Run, pick two videos, set options, choose output, press **Run**.

### Notes
- Encoders: `libx264` (CRF+preset) or `h264_videotoolbox` (fast).
- Pixel format: `yuv420p` for compatibility.
- Filter graph is logged before execution for debugging.

© 2025 — MIT License
