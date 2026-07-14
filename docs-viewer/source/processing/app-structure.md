---
doc_id: app-structure
title: App structure
added_date: "2026-07-14 17:27"
last_updated: "2026-07-14 17:27"
parent_id: unsorted
---
# App structure


```
processing-app/
├─ app/                      # the main "launcher" sketch (one PApplet)
│  ├─ AppMain.pde            # entry point (setup/draw), state machine/router
│  ├─ AppContext.pde         # shared services (config, paths, caches)
│  ├─ AppMenu.pde            # keyboard/GUI menu to switch tools
│  └─ events/                # simple event bus (optional)
│
├─ core/                     # reusable utilities (no app-specific logic)
│  ├─ io/                    # loading, saving, folder pickers, CSV helpers
│  ├─ gfx/                   # image math, blend modes, auto-levels
│  ├─ ui/                    # lightweight UI controls (buttons, sliders)
│  ├─ math/                  # noise, easing, color utils, geometry
│  └─ video/                 # wrappers (FFmpeg command builder, Movie helpers)
│
├─ tools/                    # each feature/screen = one Tool module
│  ├─ permutations/          # e.g., layered composites from permutations
│  │  ├─ PermutationsTool.pde
│  │  └─ PermutationsEngine.pde
│  ├─ composites/            # simple N-layer composite, UHD-safe pipeline
│  │  └─ CompositesTool.pde
│  ├─ interpolator/          # Batch image interp (flow/tri-mesh notes)
│  │  └─ InterpolatorTool.pde
│  └─ ffmpeg_overlay/        # Processing GUI that builds FFmpeg commands
│     └─ FFmpegOverlayTool.pde
│
├─ data/                     # default Processing data folder
│  ├─ config.yaml            # global settings (paths, defaults)
│  ├─ ui_theme.json          # colors, margins, sizes
│  ├─ shaders/               # .glsl if used
│  └─ demo/                  # small sample assets
│
├─ libs/                     # external jars or contributed libs (if any)
│
├─ export/                   # app writes outputs here by default
│  ├─ images/
│  ├─ video/
│  └─ logs/
│
└─ build-notes/              # notes + scripts for Export Application
   └─ gradle-bridge.md       # optional: IntelliJ/Gradle pathway

```
