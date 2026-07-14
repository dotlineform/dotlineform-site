---
doc_id: engrams-companion-processing
title: engrams_companion_processing
added_date: "2026-07-14 17:38"
last_updated: "2026-07-14 17:38"
parent_id: unsorted
---
# engrams_companion_processing


[Prompt @ 2025-09-10 18:53:49 UTC+01:00] User: "Create a companion HTML that maps each era of the Engram lineage to concrete Processing sketch ideas and workflows." System/Project prefs: "HTML explanations are always needed, include citations and URLs, embed the original prompt as a shaded block with timestamp, do NOT show raw HTML in chat."
**Engram Lineage → Processing Sketches**
Concrete creative‑coding routes that translate historical/philosophical ideas of the *engram* into Processing sketches. Each era is mapped to **Concept → Example → Application** and to your **Select – Change – Reconstruct** framework.
**1) Semon — Biological Engram & Ecphory (1904–1909)**
Imprint
Accumulation
 
| Concept<br/>Experience leaves a physical imprint that can be reactivated (ecphory). Translate “imprint” as cumulative pixel‑space deposition.<br/>Select: input images/brushes → Change: additive blend & micro‑deformation → Reconstruct: recall via stored state (seed + mask). | Sketch Idea<br/>	•	Texture Engraver: accumulate alpha‑weighted strokes on a heightmap; repeated recall sharpens grooves.<br/>	•	Memory Wear: draw paths; each revisit deepens a “trail” via kernel‑based erosion/dilation.                                                        | •	Workflow<br/>	1	Load sequence of source images (UHD OK).<br/>	2	For each frame, update a persistent traceBuffer with low‑gain add/multiply.<br/>	3	Persist traceBuffer + random seed → enables “ecphory” re‑render.                                                             |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Additive/Multiply deposition                                                                                                                                                                                                                                                      | Erosion/Dilation grooves                                                                                                                                                                                                                                                          | State`ful recall (seed + mask)                                                                                                                                                                                                                                                    |

 
**2) Jung — Archetypes & Collective Unconscious (1910s–1950s)**
Form families
Param spaces
 
| Concept<br/>Archetypes as inherited form tendencies. Operationalize as low‑dimensional latent shape spaces that seed compositions.<br/>Select: choose archetype family → Change: morph within latent space → Reconstruct: instantiate images with noise variations. | Sketch Idea<br/>	•	Archetype Atlas: parametric glyphs (circle, cross, spiral, tree) blended with photos.<br/>	•	Dream Morph: interpolate glyph lattices against textures via perlin displacement.                                                                   | •	Workflow<br/>	1	Define archetypeParams.json (glyph type, symmetry, recursion depth).<br/>	2	Generate vector glyphs → rasterize to layers.<br/>	3	Blend with source imagery using your AVERAGE/SEQUENTIAL strategies.                                              |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Latent shape axes                                                                                                                                                                                                                                                   | Perlin displacement                                                                                                                                                                                                                                                 | Composite with rules CSV                                                                                                                                                                                                                                            |

 
**3) Halbwachs — Collective Memory (1920s–1940s)**
Rituals
Places
 
| Concept<br/>Memory is social and spatial. Use place anchors (EXIF GPS, filenames, dates) and ritual schedules as structuring devices.<br/>Select: group by location/time → Change: apply shared transforms per group → Reconstruct: montage sequences per community. | Sketch Idea<br/>	•	Ritual Montage: monthly composites; each month uses a stable palette & mode stack.<br/>	•	City Trace: cluster images by GPS; draw Voronoi regions; render group‑signature textures.                                                               | •	Workflow<br/>	1	Parse EXIF/date; cluster (k‑means by lat/long/time).<br/>	2	Assign group rules (blend modes, opacities, palettes).<br/>	3	Export per‑group sheets + a grand “collective” composite.                                                                |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| EXIF & GPS clustering                                                                                                                                                                                                                                                | Group rule manifests                                                                                                                                                                                                                                                 | Voronoi overlays                                                                                                                                                                                                                                                     |

 
**4) Derrida / Phenomenology — The Trace**
Palimpsest
Deferred reveal
 
| Concept<br/>Meaning as difference and delay. Represent via palimpsest layering, partial erasure, and iterative almost‑present reveals.<br/>Select: motifs & negatives → Change: alternate write/erase cycles → Reconstruct: reveal by thresholds and time‑offset masks. | Sketch Idea<br/>	•	Erase/Write Engine: draw & erase with mismatched masks; keep “ghosts”.<br/>	•	Palimpsest Printer: overlay text/image layers with jittered registration; save intermediate “traces”.                                                                  | •	Workflow<br/>	1	Make paired positive/negative masks.<br/>	2	Iterate: write → blur → subtract → threshold → accumulate ghosts.<br/>	3	Final reveal by adaptive threshold ramp.                                                                                         |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Write/erase cycles                                                                                                                                                                                                                                                      | Ghost accumulation                                                                                                                                                                                                                                                      | Adaptive thresholds                                                                                                                                                                                                                                                     |

 
**5) Neuroscience — Engram Cells**
Ensembles
Tag/Reactivate
 
| Concept<br/>Memories correspond to ensembles whose reactivation is sufficient for recall. Simulate tagging & recall with layer masks and state toggles.<br/>Select: detect salient features → Change: tag feature‑specific masks → Reconstruct: re‑apply masks to “recall”. | Sketch Idea<br/>	•	Tagger: detect SIFT‑like features or high‑contrast blobs; store binary masks.<br/>	•	Recall Mixer: toggle subsets of masks to reconstruct different “memories”.                                                                                          | •	Workflow<br/>	1	Pass 1 (Learning): feature detection → create masks per cluster.<br/>	2	Pass 2 (Recall): turn mask subsets on/off; composite to output.<br/>	3	Optionally degrade or strengthen masks to model reconsolidation.                                           |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Feature clustering                                                                                                                                                                                                                                                          | Mask toggles                                                                                                                                                                                                                                                                | Reconsolidation noise                                                                                                                                                                                                                                                       |

 
**Mapping to Your Video/Batch Pipeline**
| Asset & Rules Manifests<br/>Folders<br/>/source, /masks, /rules, /out<br/>CSV<br/>layer_rules.csv (layer,mode,opacity,weight,group)<br/>JSON<br/>archetypeParams.json, group_rules.json | Batch Steps (Static Generator)<br/>	1	Scan assets → load rules.<br/>	2	Choose strategy (SJT/stride/subset) for ordering.<br/>	3	Render composites deterministically from seed.          | Export<br/>	•	PNG/TIFF (16‑bit if needed)<br/>	•	Manifest CSV (filename, strategy, params)<br/>	•	Optional: palette JSON per group                                                      |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| Folders                                           | /source, /masks, /rules, /out                     |
|---------------------------------------------------|---------------------------------------------------|
| CSV                                               | layer_rules.csv (layer,mode,opacity,weight,group) |
| JSON                                              | archetypeParams.json, group_rules.json            |

 
##  
**References & Links**
| Topic                                                                                                                                                 | Source / URL                                                                                                                                          |
|-------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Semon — Die Mneme (Engram & Ecphory)                                                                                                                  | English translation (Archive.org)                                                                                                                     |
| Engram overview                                                                                                                                       | Josselyn, S. A., & Tonegawa, S. (2020). Memory engrams: Recalling the past and imagining the future. Science. science.org/doi/10.1126/science.aaw4325 |
| Jung — archetypes                                                                                                                                     | Jung, C. G. (1968). The Archetypes and the Collective Unconscious. (trans.). Princeton UP.                                                            |
| Halbwachs — collective memory                                                                                                                         | Halbwachs, M. (1992/1925). On Collective Memory. U. Chicago Press.                                                                                    |
| Derrida — trace/différance                                                                                                                            | Derrida, J. (1976). Of Grammatology. JHU Press. · IEP entry                                                                                           |
| Optogenetic engrams                                                                                                                                   | Liu et al. (2012). Nature. pubmed/22441246; Roy et al. (2016). Nature. pmc/articles/PMC4847731                                                        |

**APA-Style Citations**
* Derrida, J. (1976). *Of grammatology*. Johns Hopkins University Press.
* Halbwachs, M. (1992). *On collective memory*. University of Chicago Press. (Original work published 1925)
* Josselyn, S. A., & Tonegawa, S. (2020). Memory engrams: Recalling the past and imagining the future. *Science*, 367(6473), eaaw4325. <u>[https://doi.org/10.1126/science.aaw4325](https://doi.org/10.1126/science.aaw4325)</u>Jung, C. G. (1968). *The archetypes and the collective unconscious*. Princeton University Press.
* Liu, X., Ramirez, S., Pang, P. T., et al. (2012). Optogenetic stimulation of a hippocampal engram activates fear memory recall. *Nature*, 484, 381–385. <u>[https://pubmed.ncbi.nlm.nih.gov/22441246/](https://pubmed.ncbi.nlm.nih.gov/22441246/)</u>Roy, D. S., Arons, A., Mitchell, T. I., et al. (2016). Memory retrieval by activating engram cells in mouse models of early Alzheimer’s disease. *Nature*, 531, 508–512. <u>[https://pmc.ncbi.nlm.nih.gov/articles/PMC4847731/](https://pmc.ncbi.nlm.nih.gov/articles/PMC4847731/)</u>Semon, R. (1921). *The mneme* (L. Simon, Trans.). Allen & Unwin. (Original work published 1904)
© 2025. Companion to the Engram Timeline. Prepared for the Memory × Processing project. This page is self‑contained for offline use.
**6) Processing Class Skeleton — Substrate · Emergence · Experience**
FrameworkReusable
**Overview**
This skeleton organizes your sketches into three cooperating modules that echo the engram lineage: **Substrate** (material layer), **Emergence** (transform dynamics), and **Experience** (rendered output).
**Select**: inputs & seeds → **Change**: transforms & rules → **Reconstruct**: outputs & recalls.
**Class: Substrate**
* State: *traceBuffer*, *maskStack*, *palettes*, *rngSeed*, *exifIndex*Methods: *loadAssets()*, *deposit()*, *erodeDilate()*, *persist()*, *restore()*Engram link: Semon — imprint & ecphory (stateful recall)
**Class: Emergence**
* State: *latentParams*, *groupRules*, *featureClusters*Methods: *morphLatent()*, *perlinDisplace()*, *applyGroupRules()*, *tagFeatures()*, *reconsolidate()*Engram link: Jung/Halbwachs/Derrida — archetypal morphs, social grouping, palimpsest traces
**Class: Experience**
* State: *compositeStack*, *exportQueue*, *manifest*Methods: *compose()*, *toggleMasks()*, *thresholdReveal()*, *exportPNG()*, *writeManifest()*Engram link: Neuroscience — selective reactivation (mask toggles) and reconstruction
**Parameter Cheat‑Sheet**
Deposition
gain, kernelSize, mode[MULTIPLY|ADD|SCREEN]
Latent
glyphType, symmetry, recursionDepth, noiseScale
Groups
paletteId, modeStack[], opacity[], weight[]
Recall
maskSubset[], threshold, ghostDecay
Stateful buffersLatent morphingGroup rulesRecall toggles
**Implementation tip**: keep all randomness seeded; store seeds and rule hashes in the manifest for exact reproducibility.
**Batch note**: tie *Experience.exportPNG()* to your static, non-animated draw cycle (batch generator) to render UHD composites deterministically.
[Appended @ 2025-09-10 18:56:32 UTC+01:00]
