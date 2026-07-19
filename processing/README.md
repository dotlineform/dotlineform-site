# Processing

This directory is the repo-owned Processing sketchbook. Processing 4.5.5 in
Java mode is the canonical authoring and rendering environment.

## Structure

- `projects/` contains runnable sketches. Each sketch directory has the same
  name as its primary `.pde` file, as required by Processing.
- `recovered/` preserves source snapshots that have not yet been promoted into
  runnable projects.
- `libraries/` contains sketchbook libraries required by the projects.
  ControlP5 2.2.6 is currently pinned here.
- `previews/` contains small representative output retained for recovery,
  comparison, and documentation.

Processing compiler output under `projects/**/out/` is ignored. Large inputs,
repeated renders, and print masters belong outside Git under
`$DOTLINEFORM_PROJECTS_BASE_DIR/<project-id>/`; only selected small previews
should be copied back into this directory.

Docs Viewer source and its managed attachments are separate from this
sketchbook. They live under `docs-viewer/scopes/processing/source/documents/`.

## Projects

- `InkEngine` is the first recovered runnable project.

## Recovered Source

- `layer-permutations/` contains successive versions of the layer permutation
  experiments.
- `simple-composite/` contains the minimal three-image composite experiments.

Do not extract shared code or choose a canonical recovered version until the
relevant sketches have been understood and run.
