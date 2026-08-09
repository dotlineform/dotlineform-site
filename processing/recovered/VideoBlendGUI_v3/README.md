# VideoBlendGUI v3 (SwiftUI + FFmpeg) — ProRes, HDR tags, Preferences

This version adds:
- **ProRes output** (prores_ks) with profiles (Proxy/LT/Standard/HQ/4444/4444XQ) and 10‑bit 4:2:2 or 4:4:4.
- **HDR / color tag passthrough** from the first input (colorspace, TRC, primaries, range) to the output.
- **Preferences pane** for custom **FFmpeg** and **FFprobe** binary paths.

It retains v2 features: MVVM structure, JSON ffprobe probing, minterpolate slow‑mo, audio mix with aformat, cancel button.

## Build
1. Install FFmpeg:
```bash
brew install ffmpeg
```
2. Open the Xcode project folder and add these files to a macOS SwiftUI target if needed.
3. In the app, open **Settings** (⌘,) to set custom binary paths if Homebrew paths aren't used.

## Notes
- ProRes uses `prores_ks`:
  - Profile `HQ`/`4444`/`4444 XQ` recommended for mastering.
  - Pixel format: 10‑bit (`yuv422p10le` or `yuv444p10le` when 4:4:4 is toggled).
- Color tags are read from **Video 1** and passed to the encoder via `-colorspace`, `-color_trc`, `-color_primaries`, `-color_range`.
- MP4 for H.264, MOV for ProRes.

© 2025 — MIT License
