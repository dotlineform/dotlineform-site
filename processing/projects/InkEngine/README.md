# InkEngine

InkEngine is a recovered Processing sketch for comparing several ways of
drawing an ink-like curve: vector-field displacement, particle tracing,
diffuse particles, textured particles, and a weighted composite.

## Environment

- Processing 4.5.5
- Java mode
- ControlP5 2.2.6 from `processing/libraries/controlP5/`
- default Processing renderer
- macOS fonts `Arial`, `Arial-BoldMT`, and `Apple Symbols`

The repo's `processing/` directory must be selected as the Processing
sketchbook so the IDE and command-line runner can discover ControlP5.

## Run

From the repository root:

```sh
processing cli --sketch="$(pwd)/processing/projects/InkEngine" --build
processing cli --sketch="$(pwd)/processing/projects/InkEngine" --run
```

The VS Code task in `.vscode/tasks.json` is retained from the recovered
project. It expects `processing.path` to resolve to the Processing launcher and
writes ignored compiler output to `out/`.

## Output Workspace

InkEngine does not read `.env.local` and does not assume that a GUI launch
inherits `DOTLINEFORM_PROJECTS_BASE_DIR`. Copy the tracked example to the one
ignored local configuration file:

```sh
cp processing/projects/InkEngine/output-config.example.json \
  processing/projects/InkEngine/data/output-config.local.json
```

Set `projects_base_dir` to the existing absolute readable and writable external
projects base. Keep `project_id` as the exact value `ink-engine`. Those are the
only accepted keys. At startup the sketch derives only
`<projects_base_dir>/processing/ink-engine`, creating the missing `processing/`
and exact project directory when needed. Blank, relative, traversing, hidden,
nested, unknown, symlinked, unavailable, or unwritable targets fail visibly in
the sketch and console; there is no repository fallback.

Press `F8` to deliberately render the PWP-1.1 configuration-evidence frame and
call `exportDrawing()`. The frame is a black `䷑` (U+4DD1, WORK ON THE DECAYED)
glyph on a plain background. InkEngine confirms an installed glyph-supporting
font through `PFont.list()` and loads it with `createFont()`, preferring
`Apple Symbols` and logging the exact selected font. The JPEG is written to the
configured directory with a UTC timestamp and collision token, for example
`ink-engine-20260831T221530.123Z-a1b2c3d4.jpg`.

## Source And Data

- `InkEngine.pde` owns the application lifecycle, controls, curve definitions,
  ink renderers, composite, preset loading and saving, configuration-evidence
  rendering, and the deliberate export trigger.
- `OutputWorkspace.java` owns exact configuration validation, confined output
  directory creation, revalidation, and collision-resistant export paths.
- `output-config.example.json` documents the portable two-key local contract;
  `data/output-config.local.json` is machine-local and ignored.
- `droplets.pde` contains the experimental droplet renderer.
- `data/sliderSettings.json` contains named, user-authored slider
  configurations. It is project source and should remain tracked.
- `data/brush.png` is a sketch asset.

The preset buttons load entries from `sliderSettings.json`. Saving a named
configuration updates that tracked source file through `saveInkParameters()`;
it does not export artwork or change the external output workspace.

## Recovered Baseline

The recovered sketch compiles and runs under Processing 4.5.5. It opens
full-screen and presents four ink-type comparisons plus a composite. The
ControlP5 controls are functional but are known to be brittle.

Current authoring behavior intentionally remains narrow:

- `randomSeed(millis())` makes a refreshed curve non-deterministic.
- the `save` control continues to update tracked preset source.
- `F8` is the one artwork-export trigger and calls the existing
  `exportDrawing()` function after drawing the evidence frame.
- preview and final-resolution rendering are not yet separated.

Historical preview copies were removed from the repository after the user
confirmed that the wanted files had been copied to external
`processing/ink-engine`. The retirement made no inventory, hash,
byte-comparison, backup, or recovery guarantee.
