---
doc_id: defining-information-for-cross-boundary-comparisons-concepts
title: "Defining \"Information\" for Cross‑Boundary Comparisons — Concepts"
last_updated: 2026-04-24
parent_id: ""
sort_order: 220
---
# Defining "Information" for Cross‑Boundary Comparisons — Concepts

> Generated: 2025-09-26 19:23:07 BST

> Prompt — Establish a consistent, cross‑domain definition of “information” to compare event boundaries in memory and event horizons in black holes; include sources and APA references.

> **TL;DR** — Use an *operational* notion: information for an observer = any physically realizable signal state that changes the observer’s predictive distribution over a target variable. Quantify with *mutual information*. Then a boundary “passes information” iff there is non‑zero, accessible mutual information across it. Memory boundaries drop—but rarely zero—MI between past and next moments; classical horizons make outside‑accessible MI from the inside effectively zero. [S1][P1][PHI1][M1][M2][M3][BH1][BH2][BH3]

## 1) Why the definition matters

- “Information” has distinct meanings: *syntactic* (Shannon bits), *physical* (thermodynamic cost), and *semantic* (meaning/truth). [S1][P1][PHI1][PHI2]
- A cross‑domain comparison needs a neutral, observer‑tethered metric. Mutual information (MI) fits this bill. [S1][PHI1]

## 2) Working definition (operational)

> **Information (for observer O about system S)** = any state of a channel that, when received by O, changes O’s probability distribution over S’s states. A boundary transmits information if *I(S_⁠inside; S_⁠outside \| access)* > 0.

This is syntactic/physical, not semantic: it measures *predictive constraint*, regardless of meaning. [S1][P1][PHI1]

## 3) Applying the definition

| Case | What changes at the boundary | Information passage (MI) | Key sources |
| --- | --- | --- | --- |
| **Event boundary (memory)** | Prediction error spikes; event model resets; hippocampal response peaks; across‑boundary order/associations weaken. | MI between pre‑ and post‑boundary features *drops* but stays > 0; observers can still recover links, just less reliably. | [M1][M2][M3] |
| **Event horizon (black holes)** | Causal structure forbids outward signals from inside the horizon (classically); black‑hole entropy scales with horizon area. | Outside‑accessible MI from inside → *≈ 0* (classically). Quantum theories suggest unitarity with information encoded in radiation, but not classically transmitted across the horizon. | [BH1][BH2][BH3] |

## 4) Edge notes

- **Semantic vs syntactic**: The brain cares about meaning, but our metric stays at the syntactic/physical level to compare domains. [PHI1][PHI2]
- **Information is physical**: Any encoding/erasure has thermodynamic costs (Landauer). [P1]
- **Black‑hole information**: Modern views preserve unitarity (information not destroyed), with entropy ∝ area (Bekenstein–Hawking). Our operational MI outside the horizon remains near zero for inside states, consistent with the “point of no return” description. [BH2][BH3][BH1]

## 5) Formula panel (operational & compact)

- **Shannon entropy**: H(X) = -∑<sub>x</sub> p(x) log p(x). *Units*: bits (base-2). [S1]
- **Mutual information**: I(X;Y) = ∑<sub>x,y</sub> p(x,y) log p(x,y)/(p(x)p(y)) = H(X) - H(X\|Y). *Interpretation*: reduction in uncertainty about X given Y. [S1]
- **Conditional MI**: I(X;Y\|Z) = H(X\|Z) - H(X\|Y,Z). *Use*: “accessible MI,” conditioning on what an observer can actually receive. [S1]
- **Operational definition (this note)**: A boundary “passes information” iff I(S<sub>inside</sub>; O<sub>outside</sub> \| access) > 0.

### Estimating MI around a *memory event boundary*

1. Extract features in a sliding window before (W<sub>pre</sub>) and after (W<sub>post</sub>) the putative boundary (e.g., embeddings, motion/scene vectors).
2. Estimate I(W<sub>pre</sub>; W<sub>post</sub>) via a nonparametric estimator (e.g., kNN MI) or discretized bins. Expect a *drop* vs. within‑event windows. [M1][M2][M3]
3. Relate boundary strength to prediction error: PE<sub>t</sub> = −log p(s<sub>t</sub> \| model<sub>t−1</sub>); boundaries where PE spikes. [M1][M2]

### “Accessible MI” at a *black‑hole event horizon*

- For an outside observer, classical channels from inside → outside are absent; treat I(S<sub>inside</sub>; O<sub>outside</sub> \| access) ≈ 0. [BH1]
- Quantum context: unitarity + Hawking radiation imply *global* information conservation, but not classical transmission across the horizon. [BH2][BH3]
- Entropy bound context: S<sub>BH</sub> = (k<sub>B</sub> c³ A)/(4 G ħ). (Bekenstein–Hawking area law) [BH2]

This panel stays at the syntactic/physical level; it does not take a stance on semantic information. See SEP overviews for semantics. [PHI1][PHI2]

## Citation index (clickable)

| ID | Reference (URL) |
| --- | --- |
| [S1] | [Shannon (1948) — A Mathematical Theory of Communication (PDF)](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf) |
| [P1] | [Landauer (1961) — Irreversibility and Heat Generation (IBM JRD, PDF)](https://sites.pitt.edu/~jdnorton/lectures/Rotman_Summer_School_2013/thermo_computing_docs/Landauer_1961.pdf) |
| [PHI1] | [SEP — Information (overview)](https://plato.stanford.edu/entries/information/) |
| [PHI2] | [SEP — Semantic Conceptions of Information](https://plato.stanford.edu/entries/information-semantic/) |
| [M1] | [Zacks et al. (2007) — Event Segmentation (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3314399/) |
| [M2] | [Kurby & Zacks (2008) — Segmentation in Perception & Memory (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2263140/) |
| [M3] | [Ben‑Yakov & Henson (2018) — Hippocampal boundary response (J. Neurosci.)](https://www.jneurosci.org/content/38/47/10057) |
| [BH1] | [NASA GSFC — Event horizon as point of no return](https://imagine.gsfc.nasa.gov/science/objects/black_holes1.html) |
| [BH2] | [Bekenstein (1973) — Black Holes and Entropy (PRD)](https://link.aps.org/doi/10.1103/PhysRevD.7.2333) |
| [BH3] | [ArXiv — Black Holes, Entropy, and Information (review)](https://arxiv.org/pdf/0708.3680) |

## APA references

1. Shannon, C. E. (1948). A mathematical theory of communication. The Bell System Technical Journal, 27(3), 379–423; 27(4), 623–656.
2. Landauer, R. (1961). Irreversibility and heat generation in the computing process. IBM Journal of Research and Development, 5(3), 183–191.
3. Adriaans, P. (2020). Information. In E. N. Zalta (Ed.), Stanford Encyclopedia of Philosophy (Summer 2020 ed.).
4. Sequoiah‑Grayson, S. (2017). Semantic Conceptions of Information. In E. N. Zalta (Ed.), Stanford Encyclopedia of Philosophy (Spring 2017 ed.).
5. Zacks, J. M., Speer, N. K., Swallow, K. M., Braver, T. S., & Reynolds, J. R. (2007). Event segmentation. Current Directions in Psychological Science, 16(2), 80–84.
6. Kurby, C. A., & Zacks, J. M. (2008). Segmentation in the perception and memory of events. Trends in Cognitive Sciences, 12(2), 72–79.
7. Ben‑Yakov, A., & Henson, R. N. (2018). The hippocampal film editor: Sensitivity and specificity to event boundaries in continuous experience. Journal of Neuroscience, 38(47), 10057–10068.
8. NASA Goddard. Black Holes — Imagine the Universe! (accessed 2025).
9. Bekenstein, J. D. (1973). Black holes and entropy. Physical Review D, 7(8), 2333–2346.
10. Bekenstein, J. D. (2007). Black holes, entropy, and information. arXiv:0708.3680 [gr-qc].
