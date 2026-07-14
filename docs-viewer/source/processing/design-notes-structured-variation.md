---
doc_id: design-notes-structured-variation
title: design_notes_structured_variation
added_date: "2026-07-14 17:38"
last_updated: "2026-07-14 17:38"
parent_id: unsorted
---
# design_notes_structured_variation


**Design Notes — Structured Variation in Repetitive Pipelines (Processing × FFmpeg)**
Prepared for the Memory project · Europe/London · 2025-09-07 17:36:12 BST
**Prompt & Context**
Original prompt @ 2025-09-07 17:36:12 BST: Append a short design‑notes panel that maps the essays’ ideas to Processing/FFmpeg workflows — where to harness constructive repetition vs. inject variation.
**Principle**
**Treat “repeat” as “iterate with controlled variation.”** Stabilise invariants (color space, resolution, frame order); vary what benefits generalisation and interest (blend modes, timings, cue order).
**Where to Harness Constructive Repetition**
 
| Deterministic Seeds<br/>	•	Set and log randomSeed() in Processing per run.<br/>	•	Record RNG seeds with outputs (CSV manifest).<br/>	•	Use SJT/Gray‑code‑like permutations for minimal‑change frame sequences.                    | Stable Transforms<br/>	•	Fix resize/scaling kernels and color management (e.g., sRGB tags).<br/>	•	Normalise input frame rates and pixel formats before compositing.<br/>	•	Enforce naming schemas; hash inputs; version outputs. | Spaced Practice in Batches<br/>	•	Break long runs into spaced batches; re‑initialise environment between batches.<br/>	•	Surface summary metrics after each batch (histograms; RMS error).                                        |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

 <span style="font-size: 16.0;">
     **Where to Inject Variation (Deliberately)**

 </span> 
| Blend Strategy<br/>	•	Alternate MULTIPLY/SCREEN/OVERLAY schedules.<br/>	•	Cycle opacity ramps; add small jitter (±1–2%) to avoid banding.                  | Ordering & Subsets<br/>	•	Stride or decimate permutations (e.g., render 1 in n).<br/>	•	Interleave source orders to maintain novelty without abrupt jumps. | Optical‑Flow Interpolations<br/>	•	Vary flow regularisation and pyramid scales per segment.<br/>	•	Blend optical flow with mesh‑warp in difficult regions. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|

 <span style="font-size: 16.0;">
     **Quality & Drift Control**

 </span>| Risk                                                                                    | Control                                                                                 | Notes                                                                                   |
|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| RNG non‑repeatability                                                                   | Log seeds; set per‑segment seeds                                                        | Per‑run CSV manifest listing seed, order, modes.                                        |
| Color/levels drift                                                                      | Auto‑levels with fixed percentiles; or reference‑frame matching                         | Record chosen clip percent; keep a reference LUT.                                       |
| Truthiness bias                                                                         | Audit repeated headlines/captions                                                       | Counteract illusory truth via fact checks; rotate phrasing while keeping verified core. |
| Overfitting to a look                                                                   | Inject micro‑variation                                                                  | Scheduled opacity jitter; periodic mode change.                                         |

 <span style="font-size: 16.0;">
     **Minimal Manifest (append to your existing CSV)**

 </span>timestamp, seed, strategy, subset_rule, modes, opacities, auto_levels, clip_percent, input_files_hash, output_file
2025-09-07 17:36:12, 123456, SEQUENTIAL, stride:5, MULTIPLY|SCREEN|OVERLAY, 0.5|0.5|0.5, true, 0.5, abcdef..., out_0001.png
**Citations**
* Spacing & LTP: Smolen, P., Zhang, Y., & Byrne, J. H. (2016). <u>[https://pmc.ncbi.nlm.nih.gov/articles/PMC5126970/](https://pmc.ncbi.nlm.nih.gov/articles/PMC5126970/)</u>Illusory truth: Fazio, L. K., et al. (2020). <u>[https://online.ucpress.edu/collabra/article/6/1/38/114468](https://online.ucpress.edu/collabra/article/6/1/38/114468)</u>Chaos/logistic map: May, R. M. (1976). <u>[https://sites.ifi.unicamp.br/aguiar/files/2014/10/May-Nature-1976.pdf](https://sites.ifi.unicamp.br/aguiar/files/2014/10/May-Nature-1976.pdf)</u>Phenology/mismatch: Visser & Both (2005); Visser & Gienapp (2019). <u>[https://pmc.ncbi.nlm.nih.gov/articles/PMC1559974/](https://pmc.ncbi.nlm.nih.gov/articles/PMC1559974/)</u> ; <u>[https://pmc.ncbi.nlm.nih.gov/articles/PMC6544530/](https://pmc.ncbi.nlm.nih.gov/articles/PMC6544530/)</u>
