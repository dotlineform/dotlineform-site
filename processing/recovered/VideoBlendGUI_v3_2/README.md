# VideoBlendGUI v3.2 (SwiftUI + FFmpeg)

This release adds:
- **Non-blocking probes** (ffprobe runs off the main thread)
- **Executable validation** for FFmpeg/FFprobe (friendly error if invalid)
- **Save As…** types improved (MP4 for H.264, MOV for ProRes; allow general `.movie` too)
- **Safer color mapping** (skip unknown tags; add sRGB/IEC mappings)

It keeps all features from v3.1: ProRes, HDR tag passthrough, Preferences pane, slow‑mo with `minterpolate`, amix normalization, cancel, and per‑node filter logging.

## Build
1. Install FFmpeg:
```bash
brew install ffmpeg
```
2. Open in **Xcode** (macOS SwiftUI app). Build & run.

© 2025 — MIT License
