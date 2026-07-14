---
doc_id: processing-project-setup
title: Processing Project Setup
added_date: "2026-07-14 16:42"
last_updated: "2026-07-14 16:42"
parent_id: ""
---

# Processing Project Setup

Bring the existing unfinished [Processing](https://processing.org) projects into this repository, recover how they work, and establish a maintainable structure for continuing them.

The primary aim is high-quality still artwork for print. Processing in Java mode remains the canonical implementation and rendering environment.

Interactivity belongs mainly to the authoring application:

- adjust parameters with controls such as sliders
- explore compositions quickly at screen resolution
- save useful configurations as named presets
- deliberately render a selected preset at print resolution

## Application

Installed version of Processing is current version 4.5.5

[CLI](https://github.com/processing/processing4/wiki/Command-Line) symlinked:

```
ln -s /Applications/Processing.app/Contents/MacOS/Processing /usr/local/bin/processing

processing cli --help
```

use it like this:

```
processing cli --sketch=/absolute/path/to/MySketch --run
```

A p5.js version may be considered later.

## additional setup

When work begins, review whether implementation also needs to:

- Investigate use of Processing-specific Javadoc or Java checks. This aligns with similar work for JS and Python ([Source Documentation and Linting](/docs/?scope=studio&doc=site-request-source-documentation-and-linting))
- update `source-tree-ownership.md` if a new top-level `processing/` source area is adopted
- update repository setup or dependency documentation once the required Processing version and libraries are known

## Proposed Repository Shape

Use one repo-owned source area for the Processing work:

```text
processing/
  README.md
  docs/
  projects/
    <project-one>/
      <project-one>.pde
      ...original sketch tabs and files...
      README.md
      presets/
    <project-two>/
      <project-two>.pde
      ...original sketch tabs and files...
      README.md
      presets/
  shared/
  tools/
  previews/
```

This is a proposed destination, not a requirement to reorganize the old projects during import.

The first checked-in version of each project should preserve its original sketch structure. Shared code should move into `shared/` only after both projects are understood and a real shared boundary has been identified.

### Tracked Material

Track:

- Processing and Java source
- small configuration and preset files
- project notes and reference documentation
- dependency and version information
- small representative preview images selected for documentation or publication
- scripts that reproduce an export or prepare a publication copy

### Generated And External Material

Do not routinely track:

- repeated high-resolution renders
- print masters that are too large for ordinary Git history
- caches, temporary frames, or animation sequences
- Processing build output
- locally installed libraries
- licensed fonts or assets that cannot be redistributed

Choose an ignored or external output root before enabling full-resolution export. Print masters are important artwork, so their storage and backup location must be explicit even when they are not committed to Git.

## First Import Boundary

Recovery and refactoring are separate stages.

For each project:

1. Copy the complete original project into its own sketch folder without reorganizing it.
2. Preserve an unmodified baseline in Git before substantial edits.
3. Record the original file dates and any available notes about the Processing version.
4. Inventory `.pde`, `.java`, `data/`, `code/`, font, image, configuration, and output files.
5. Identify contributed libraries, local JAR files, fonts, source images, and other external dependencies.
6. Attempt to run the project with the most likely compatible Processing version.
7. Record compilation errors, missing dependencies, warnings, and runtime assumptions.
8. Capture a known-good screen image or export once the project runs.
9. Only then begin cleanup and architectural changes.

If compatibility work changes the source, keep it as a narrow, explained recovery change rather than mixing it with redesign.

## Environment Record

Each project README should eventually record:

- Processing version and Java mode
- operating-system assumptions where relevant
- renderer in use, such as the default renderer, `P2D`, or `P3D`
- required core and contributed libraries, including versions when discoverable
- required fonts and input assets
- how to open and run the sketch
- how presets are loaded and saved
- how preview and final export are triggered
- output formats, dimensions, and storage location
- known memory or performance limits

Do not assume the current Processing release is compatible with an old sketch. Determine and document compatibility from the recovered project.

## Authoring And Rendering Model

The application should distinguish four responsibilities:

```text
saved preset
    -> render configuration
        -> artwork model or scene
            -> preview or final renderer
```

### Render Configuration

Collect related parameters into one or more typed configuration objects rather than passing long lists of values through many functions.

A configuration may contain:

- composition and layout values
- colour palette and background
- random seed
- source-data or asset selection
- algorithm-specific settings
- output width and height
- renderer and quality settings
- export format and filename information

Not every runtime concern belongs in one giant configuration class. Split configuration by stable responsibility when the original code reveals meaningful groups.

### Artwork Logic

The artwork model should express the composition independently from the slider implementation and, as far as practical, independently from a particular output size.

Prefer coordinates and dimensions derived from a logical canvas, proportions, or an explicit scale. Avoid scattering screen dimensions, control values, and output paths through drawing functions.

Randomness should use an explicit seed when repeatable output matters. Saving a preset should preserve enough information to reproduce the selected composition.

### Preview Mode

Preview mode is an authoring tool:

- uses a responsive, screen-sized, or reduced-resolution surface
- updates quickly as controls change
- may reduce expensive sampling or detail where this does not misrepresent the composition
- displays current preset, seed, dimensions, and dirty state where helpful
- does not define the final print resolution

The controls should update configuration. They should not contain the artwork algorithm.

### Final Export Mode

Final export should deliberately render from a saved or confirmable configuration:

- raster output at exact pixel dimensions required by the intended print size and resolution
- vector PDF or SVG when the artwork and Processing renderer support it correctly
- an off-screen `PGraphics` surface where separating the display window from output dimensions is useful
- tiled or staged rendering if the final raster exceeds practical memory limits
- an explicit filename and destination rather than silently overwriting an earlier master

Processing's `PGraphics` and `createGraphics()` support off-screen drawing surfaces. Processing also provides PDF and SVG export libraries, but renderer compatibility and visual fidelity must be tested against the actual projects before choosing an output path.

`pixelDensity()` is a display-density concern and should not be treated as the definition of print DPI. Print output should be based on explicit physical-size and pixel-dimension decisions.

## Presets And Reproducibility

A useful composition should be recoverable without remembering a collection of slider positions.

Prefer human-readable preset files, such as JSON, containing:

- preset schema version
- project version or revision where useful
- named parameter values
- random seed
- logical and final output dimensions
- renderer and export settings
- references to required input assets

An export should write or retain a small manifest beside the master where practical. The manifest should identify the preset and effective rendering settings without embedding user-specific absolute paths.

Schema migration is not needed initially. Add versioning early, then introduce migration only when a real preset change requires it.

## Code Review And Refactoring

Once an original project runs, review it before attempting broad cleanup.

### Inventory

Create a project map covering:

- Processing lifecycle functions such as `setup()` and `draw()`
- tabs, classes, and their responsibilities
- the path from controls to configuration to drawing
- global and shared mutable state
- long parameter chains and structured values passed between functions
- rendering, export, persistence, and asset-loading code
- duplicated algorithms or utilities
- dependencies on frame order, current graphics state, or implicit Processing globals

### Refactoring Priorities

Prioritize:

1. separating controls from artwork and export logic
2. making configuration and data shapes explicit
3. reducing global mutable state
4. replacing long parameter chains with cohesive objects where justified
5. splitting functions and classes that own several responsibilities
6. isolating renderer-specific behaviour
7. consolidating genuine duplication after both projects are understood
8. making deterministic rendering and export paths explicit

Do not force conventional application architecture onto code whose visual algorithm is clearer as a direct Processing sketch. The aim is understandable ownership and reproducible output, not abstraction for its own sake.

## Javadoc And Function Reference

Processing Java-mode source should use Javadoc rather than JSDoc.

Backfill Javadoc first for:

- public and shared classes
- configuration and preset objects
- important rendering and transformation methods
- complex parameters, units, coordinate systems, and return contracts
- lifecycle, mutation, randomness, and graphics-state assumptions
- export methods and their side effects

Do not document every obvious helper or repeat type signatures in prose. If a method remains difficult to explain because it receives many unrelated parameters or changes several kinds of state, review its design before writing a long comment.

The new Processing Docs Viewer scope should initially contain hand-written project maps, setup notes, preset/export instructions, and architectural explanations. Javadoc-generated reference pages can be considered later, after the source comments are useful and the mix of `.pde` and `.java` files is understood.

## Verification

Verification should protect reproducibility without making every intentional visual change look like a defect.

Useful checks include:

- a sketch opens and compiles with the recorded environment
- a known preset renders without interaction
- output width, height, format, and destination are correct
- a fixed seed produces stable structural output where determinism is intended
- presets round-trip without losing values
- missing assets and invalid presets fail clearly
- preview and final export use the same composition configuration

Selected reference renders may be retained for visual comparison. Avoid universal pixel-perfect snapshot testing unless a particular algorithm genuinely requires exact output.

Final visual quality, print suitability, colour handling, and the feel of the authoring controls require manual review.

## Publication

Small selected still images may later be copied into the existing site-owned media pipeline for catalogue, work-detail, or project documentation use.

Publication should be an explicit step from a chosen render. The public site should not read directly from project working folders or high-resolution master storage.

Any later p5.js work should be treated as a separate adaptation with its own purpose. It may provide an interactive interpretation, a lightweight demonstration, or a browser-native edition, but it does not need to reproduce the Processing authoring interface or replace the print renderer.

## Initial Work Sequence

1. Create the `processing/` source area and import the first project unchanged.
2. Preserve the baseline and inventory its environment and dependencies.
3. Recover a runnable version and capture known output.
4. Write the first project map and add it to the Processing Docs Viewer scope.
5. Review the code, parameter flow, configuration, rendering, and export boundaries.
6. Establish Javadoc conventions on representative classes and functions.
7. Separate preview controls from reusable artwork configuration and rendering where needed.
8. Add saved presets and deterministic seeds where the artwork benefits from them.
9. Establish a deliberate high-resolution or vector export path.
10. Repeat the recovery process for the second project before extracting shared code.
11. Compare both projects and move only proven shared responsibilities into `processing/shared/`.
12. Decide much later whether any finished work has a useful browser or p5.js adaptation.

## Decisions To Make During Recovery

- final repo path and project names
- compatible Processing version
- required libraries, fonts, and assets
- storage and backup location for print masters
- raster, PDF, SVG, or mixed export strategy for each project
- physical print sizes, target pixel dimensions, and colour workflow
- preset file shape and naming
- appropriate balance between `.pde` tabs and ordinary `.java` classes
- Processing-aware formatting, linting, and testing options
- Processing Docs Viewer scope id and source location

## Intended Outcome

- both original projects are safely preserved and runnable
- the code can be understood after a long absence
- sliders and controls edit explicit, saveable artwork configurations
- preview and final print export share one composition model
- chosen works can be reproduced from presets and seeds
- high-resolution and vector output are deliberate, documented operations
- the repo contains maintainable source and small reference material without accumulating every print master
- Javadoc and the Processing Docs Viewer scope provide a useful function and architecture reference
- a future browser version remains possible without becoming a present constraint
