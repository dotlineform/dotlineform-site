# VideoBlendGUI v3.1 (SwiftUI + FFmpeg)

This release fixes compile/runtime issues and adds safer color-tag mapping.

## Fixes & Improvements
- ✅ Shared **AppSettings** instance for both the Preferences pane and the ViewModel (constructor injection).
- ✅ `JSONDecoder().decode(…, from:)` now uses the `.self` metatype correctly.
- ✅ **Save As…** respects encoder: `.mp4` for H.264, `.mov` for ProRes.
- ✅ Logged filter graph prints each node on its own line for readability.
- ✅ Color metadata mapping to FFmpeg-friendly tokens (`bt2020ncl`, `arib-std-b67`, etc.).

## Features (from v3)
- ProRes output (prores_ks) with profile selection and 10‑bit 4:2:2 / 4:4:4.
- HDR/color tag passthrough from Video 1 (`-colorspace`, `-color_trc`, `-color_primaries`, `-color_range`).
- Preferences pane (⌘,) for custom ffmpeg/ffprobe paths.
- Optional slow‑motion using `setpts` + `minterpolate` (balanced preset).
- Audio mix with `aformat`, optional `amix normalize`.
- Cancel button, live log, clean MVVM.

## Build
1. Install FFmpeg:
```bash
brew install ffmpeg
```
2. Open in **Xcode** (macOS SwiftUI app). Build & run.

© 2025 — MIT License
