# InkEngine

InkEngine is a recovered Processing sketch for comparing several ways of
drawing an ink-like curve: vector-field displacement, particle tracing,
diffuse particles, textured particles, and a weighted composite.

## Environment

- Processing 4.5.5
- Java mode
- ControlP5 2.2.6 from `processing/libraries/controlP5/`
- default Processing renderer
- macOS fonts `Arial` and `Arial-BoldMT`

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

## Source And Data

- `InkEngine.pde` owns the application lifecycle, controls, curve definitions,
  ink renderers, composite, preset loading, and preset saving.
- `droplets.pde` contains the experimental droplet renderer.
- `data/sliderSettings.json` contains named, user-authored slider
  configurations. It is project source and should remain tracked.
- `data/brush.png` is a sketch asset.

The preset buttons load entries from `sliderSettings.json`. Saving a named
configuration updates that file through the sketch.

## Recovered Baseline

The recovered sketch compiles and runs under Processing 4.5.5. It opens
full-screen and presents four ink-type comparisons plus a composite. The
ControlP5 controls are functional but are known to be brittle.

Current behavior intentionally remains unchanged:

- `randomSeed(millis())` makes a refreshed curve non-deterministic.
- the `save` control writes `exportedDrawing.jpg` into the sketch directory.
- preview and final-resolution rendering are not yet separated.

Historical images from the recovered project are under
`processing/previews/ink-engine/`. Recovery and structural refactoring should
remain separate until the drawing and preset flows are mapped.
