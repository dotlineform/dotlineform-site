---
doc_id: panarchy-processing-helper
title: "Panarchy → Processing Helper Sheet (Phases, CSV Schema, SJT Presets, Blend Recipes)"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Panarchy → Processing Helper Sheet

> Prepared: 2025-09-07 16:47:35 BST · For the “Memory × Consciousness × Nature” project · HTML export with citations

### Original Prompt

> [2025-09-07 16:47:35 BST] User request: “Turn the panarchy write‑up into a Processing helper sheet (CSV schema for phase tagging, SJT subset presets, and blend‑mode recipes).” [2025-09-07 16:47:35 BST] Project prefs: Always include verifiable citations and URLs; primary download format is HTML; include shaded prompt blocks with exact datetimes.

This companion operationalizes panarchy (nested adaptive cycles) for still‑image compositing and sequencing in Processing and FFmpeg. It provides a **CSV schema** for tagging frames by phase and scale, **Steinhaus–Johnson–Trotter (SJT)** presets for minimal‑change permutations, **blend‑mode recipes** for phases (r, K, Ω, α), and practical **encode commands**.

## 1) CSV Schema for Phase‑Tagged Batches

| Column | Type | Example | Notes |
| --- | --- | --- | --- |
| frame_index | int | 0001 | Zero‑padded sequential index. |
| cycle_phase | enum | r \| K \| Ω \| α | Adaptive cycle phase. |
| scale | enum | micro \| meso \| macro | Cross‑scale tagging (local patch / landscape / region). |
| cycle_id | string | wetland_spring_01 | Identifier for nested loop or scene. |
| strategy | enum | AVERAGE \| SEQUENTIAL | Composite strategy in Processing. |
| mode | enum | Multiply | Blend mode for SEQUENTIAL strategy. |
| opacity | float | 0.65 | Per‑layer opacity (0–1). |
| weight | float | 1.0 | AVERAGE weighting or SEQUENTIAL emphasis. |
| auto_levels | bool | true | Percentile‑clip auto levels (post‑composite). |
| clip_low | float | 0.01 | Low percentile for auto levels. |
| clip_high | float | 0.99 | High percentile for auto levels. |
| motif | string | seedbank_macro | Shot family or motif label. |
| notes | string | disturbance hard‑cut here | Editorial cues (Ω break, α emergence). |

Tip

: Keep a

manifest.csv

per batch; include file hashes for reproducibility. During Ω, allow mode=Difference or HardLight at higher contrast; in α, lower contrast and use Screen/Lighten.

## 2) SJT (Minimal‑Change) Permutation Presets

The SJT algorithm produces a *Gray‑code‑like* ordering of permutations via adjacent swaps—ideal for frame‑to‑frame continuity. Select a truncation length to match your target duration (e.g., 1 minute). See references for SJT and Gray code permutations.

| n (layers) | n! (total) | 1‑min @24fps | @25fps | @30fps | @60fps | Suggested use |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | 5,040 | 1,440 | 1,500 | 1,800 | 3,600 | Ample headroom; sample stride or use contiguous prefix. |
| 8 | 40,320 | 1,440 | 1,500 | 1,800 | 3,600 | Use contiguous prefix for ultra‑smooth minimal change. |
| 9 | 362,880 | 1,440 | 1,500 | 1,800 | 3,600 | **Recommended** for “succession”: contiguous prefix or k‑stride sampling. |

- **Prefix strategy**: Take the first `F` permutations from SJT (F = fps × duration).
- **Stride strategy**: Step by `k` through the SJT index (e.g., k≈⌊n!/F⌋) to spread coverage while preserving near‑minimal changes.

## 3) Blend‑Mode Recipes by Phase

| Phase | Intent | Modes & Opacity | Notes |
| --- | --- | --- | --- |
| r (Growth) | Accretion, emergence | SoftLight / Overlay @ 0.4–0.6 | Moderate contrast lift; warm tint acceptable. |
| K (Conservation) | Rigidity, locked capital | Overlay / HardLight @ 0.5–0.7 | Higher connectedness → tighter textures, less motion. |
| Ω (Release) | Break, shock, release | Difference / Subtract @ 0.4–1.0 | Optional hard cut; brief desaturation or high‑pass edge. |
| α (Reorganization) | Novel recombination | Screen / Lighten @ 0.3–0.6 | Lower contrast, soft color re‑introduction; micro‑motion overlays. |

Compositing model

: Use straight‑alpha workflow and consistent premultiplication. Porter–Duff compositing and alpha handling are the ground truth for reliable layering.

## 4) Encoding from Stills (FFmpeg)

- **ProRes master (10‑bit 422)** `ffmpeg -r 25 -f image2 -i %04d.png -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le master_prores.mov`
- **H.264 preview** `ffmpeg -r 25 -f image2 -i %04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart preview_h264.mp4`
- **HEVC delivery** `ffmpeg -r 25 -f image2 -i %04d.png -c:v libx265 -crf 20 -pix_fmt yuv420p10le delivery_hevc.mp4`

## 5) QA Checklist

- Registration check (homography if needed) before batching.
- Alpha edges: verify against black & white mattes; avoid double‑premult.
- Color management: consistent working space; confirm tags on export.
- Manifest completeness: frame counts, hashes, strategy/mode fields.

## References (inline links)

- Panarchy & adaptive cycle: Resilience Alliance—[Panarchy](https://www.resalliance.org/panarchy); [Adaptive Cycle](https://www.resalliance.org/adaptive-cycle); Holling (2001) [Ecosystems](https://link.springer.com/article/10.1007/s10021-001-0101-5).
- SJT minimal‑change permutations: [Steinhaus–Johnson–Trotter](https://en.wikipedia.org/wiki/Steinhaus%E2%80%93Johnson%E2%80%93Trotter_algorithm); Knuth (2011) *TAOCP 4A*.
- Compositing theory: Porter, T., & Duff, T. (1984). [Compositing digital images](https://dl.acm.org/doi/10.1145/964965.808606); Smith, A., & Blinn, J. (1996). [Blue screen matting](https://dl.acm.org/doi/10.1145/237170.237263).
- FFmpeg docs: [ffmpeg manual](https://ffmpeg.org/ffmpeg.html), [H.264](https://trac.ffmpeg.org/wiki/Encode/H.264), [H.265/HEVC](https://trac.ffmpeg.org/wiki/Encode/H.265), [VFX/ProRes tips](https://trac.ffmpeg.org/wiki/Encode/VFX).

## APA References

1. Holling, C. S. (2001). Understanding the complexity of economic, ecological, and social systems. *Ecosystems, 4*(5), 390–405. <https://link.springer.com/article/10.1007/s10021-001-0101-5>
2. Knuth, D. E. (2011). *The Art of Computer Programming, Vol. 4A*. Addison‑Wesley.
3. Porter, T., & Duff, T. (1984). Compositing digital images. *ACM SIGGRAPH Computer Graphics, 18*(3), 253–259. <https://dl.acm.org/doi/10.1145/964965.808606>
4. Resilience Alliance. (n.d.). Adaptive Cycle. <https://www.resalliance.org/adaptive-cycle>
5. Resilience Alliance. (n.d.). Panarchy. <https://www.resalliance.org/panarchy>
6. Smith, A. R., & Blinn, J. F. (1996). Blue screen matting. *Proceedings of SIGGRAPH 96*, 259–268. <https://dl.acm.org/doi/10.1145/237170.237263>
7. Wikipedia contributors. (n.d.). Steinhaus–Johnson–Trotter algorithm. In *Wikipedia, The Free Encyclopedia*. <https://en.wikipedia.org/wiki/Steinhaus%E2%80%93Johnson%E2%80%93Trotter_algorithm>
8. FFmpeg Documentation. <https://ffmpeg.org/ffmpeg.html>

Use this as a working spec for your Processing + FFmpeg pipeline. Suitable for Apple Notes/GitHub.
