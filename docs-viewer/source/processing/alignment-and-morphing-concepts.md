---
doc_id: alignment-and-morphing-concepts
title: "Conceptual Notes — Alignment & Morphing (Homography • Triangle Mesh • Optical Flow)"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Alignment & Morphing Concepts for Image Interpolation

> Original prompt — 2025-09-01 13:15:55 (Europe/London) Explain: Homography alignment (auto-register per pair) before blending, Triangle-mesh morph (feature points → Delaunay → affine per triangle), Optical-flow morph (flow-based warp + blend)

Concise reference for planning implementations. Geared toward Processing/FFmpeg pipelines, but the ideas are general.

## 1) Homography Alignment (Auto-register per pair)

**Idea:** Estimate a 3×3 projective transform that maps one planar view onto another. Align image B to A before blending to reduce ghosting.

### Workflow

1. Detect features in A and B (e.g., ORB/SIFT); compute descriptors.
2. Match descriptors and filter (ratio test + cross-check).
3. Estimate homography H via RANSAC.
4. Warp B using H → B′ aligned to A.
5. Blend A and B′ (gamma-correct crossfade recommended).

Best for:

Planar scenes (posters, walls), or approximate camera rotations/zooms without parallax.

Limit:

Misaligns 3D structures / large parallax.

### Quality Notes

- Use robust matching and outlier rejection; too few inliers ⇒ skip alignment.
- Consider a multi-resolution pass or pre-smoothing to stabilise matches.
- Keep a fallback path (plain crossfade) if homography confidence is low.

## 2) Triangle‑Mesh Morph (Feature Points → Delaunay → Affine per Triangle)

**Idea:** Define corresponding control points; compute an intermediate shape per t; warp both images into that shape triangle-by-triangle; blend.

### Workflow

1. Collect corresponding points (manual GUI or automatic landmarks).
2. For time t, compute intermediate points P<sub>t</sub> = (1−t)·P<sub>A</sub> + t·P<sub>B</sub>.
3. Run Delaunay triangulation on P<sub>t</sub>.
4. For each triangle: compute affine maps A→P<sub>t</sub> and B→P<sub>t</sub>; warp and rasterise.
5. Blend warped outputs (prefer premultiplied, gamma‑correct).

Best for:

Faces, bodies, logos, well‑structured shapes.

Limit:

Needs good correspondences; triangles can invert if points are inconsistent.

### Practical Notes

- Ensure consistent point ordering and coverage (corners/outlines + key features).
- Regularise mesh (avoid skinny triangles) for stable warps.
- Feather triangle borders or composite in a pyramid for seamless edges.

## 3) Optical‑Flow Morph (Flow‑based Warp + Blend)

**Idea:** Estimate dense motion field from A→B; for time t, warp A forward by t·flow and B backward by (1−t)·flow, then blend.

### Workflow

1. Compute dense flow (e.g., Farnebäck/TV‑L1/RAFT) from A to B.
2. For each pixel p in the output, sample A at p − t·F(p) and B at p + (1−t)·F(p).
3. Blend warped samples (premultiplied, gamma‑correct).
4. Handle occlusions (confidence maps, forward‑backward consistency, inpainting).

Best for:

Arbitrary scenes, smooth “melting” transitions.

Limit:

Computationally heavy; bad flow ⇒ tearing/ghosting.

### Stability Notes

- Use confidence/consistency to mask unreliable regions.
- Fill holes via edge‑aware interpolation or pyramid‑level splatting.
- Clamp flow near strong edges; regularise at coarse scales.

## Comparison

| Method | Inputs | Complexity | Best For | Common Artefacts |
| --- | --- | --- | --- | --- |
| Homography | Keypoints + matches | Low | Planar scenes, small camera motion | Parallax misalignment, residual ghosting |
| Triangle‑mesh | Feature points + triangulation | Medium | Faces, logos, structured shapes | Triangle seams, mesh fold‑over |
| Optical flow | Dense motion field | High | General scenes, liquid morphs | Warp tearing, hallucinated flow |

## Implementation Pointers

- **Homography:** OpenCV: ORB/SIFT → BF/FLANN matcher → `findHomography(..., RANSAC)` → `warpPerspective`. Integrate as a pre‑step in your batch pipeline.
- **Triangle‑mesh:** Landmarks (e.g., face detectors) or manual point files → Delaunay (e.g., *Triangle* or library impl) → barycentric sampling in shader or CPU affine per triangle.
- **Optical flow:** OpenCV Farnebäck/TV‑L1 for classical; deep methods like RAFT for higher quality. Warp with bilinear sampling (shader or CPU). Combine with confidence masks.

## Blending & Color

- Prefer **gamma‑correct** blending (convert to linear light for mix, then back to sRGB).
- Use **premultiplied alpha** to avoid dark fringes on transparency.
- For seamlessness, consider **multi‑band (Laplacian pyramid)** compositing of warped results.

Prepared: 2025-09-01 13:15:55 (Europe/London). Designed for Apple Notes/GitHub use.
