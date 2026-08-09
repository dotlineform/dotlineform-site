# VideoBlendGUI (SwiftUI + FFmpeg) — Fixed Build

This bundle contains **debugged SwiftUI code** ready to build in Xcode.

### Fixes included
- ✅ Corrected `onChange` usage (single `newValue` parameter).
- ✅ Replaced invalid filter `"copy"` with `"null"` in filter graphs.
- ✅ Removed duplicate `-an` by deferring audio mapping logic.
- ✅ Made pass-through video step explicit (`null`) when slow-mo disabled.
- ✅ Joined filter graph with semicolons (robust parsing).
- ✅ Added `@MainActor` to `ContentView` and explicit `self` inside closures.
- ✅ Added `import UniformTypeIdentifiers` for `NSOpenPanel.allowedContentTypes`.
- ✅ Avoided unnecessary `"areverse"` when not reversing.

## Build
1. Install FFmpeg:
```bash
brew install ffmpeg
```
2. Open **Xcode** → New Project → **App (SwiftUI)** → Name it `VideoBlendGUI` (macOS).
3. Replace the two source files in the new project with the ones under `Sources/` here.
4. Build & Run. Select two videos, set options, choose output file, hit **Run**.

© 2025 — MIT License
