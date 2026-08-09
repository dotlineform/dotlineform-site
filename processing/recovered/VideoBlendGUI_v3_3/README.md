# VideoBlendGUI v3.3 (SwiftUI + FFmpeg)

**New in v3.3**
- **HEVC encoders**: `libx265` (CRF+Preset) and `hevc_videotoolbox` (fast, hardware).
- **Interpolation quality** picker for `minterpolate` (Fast / Balanced / High).
- **Preserve original audio format** toggle:
  - If both inputs share the same sample rate & layout, we keep it.
  - Otherwise we fall back to 48k stereo for stable mixing.

**Still included**
- Non-blocking ffprobe, executable validation, ProRes output, HDR color-tag passthrough with safe mapping, Preferences pane, cancel button, readable filter graph logging, audio normalization.

## Build
1. Install FFmpeg:
```bash
brew install ffmpeg
```
2. Open in **Xcode** (macOS SwiftUI app). Build & run.

© 2025 — MIT License
