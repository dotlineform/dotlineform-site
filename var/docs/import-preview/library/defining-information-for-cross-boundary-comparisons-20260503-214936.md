---
doc_id: "defining-information-for-cross-boundary-comparisons"
title: "Defining \"Information\" for Cross‑Boundary Comparisons"
parent_id: "library"
import_type: "full_document_content"
preview_generated_at: "2026-05-03T21:49:36Z"
---

# Defining "Information" for Cross‑Boundary Comparisons

## Import Metadata

- doc_id: `defining-information-for-cross-boundary-comparisons`
- parent_id: `library`
- current library match: yes
- generated payload: yes

## Imported Headings

- Defining “Information” for Cross‑Boundary Comparisons — Concepts
- 1) Why the definition matters
- 2) Working definition (operational)
- 3) Applying the definition
- 4) Edge notes
- 5) Formula panel (operational & compact)
- Estimating MI around a memory event boundary
- “Accessible MI” at a black‑hole event horizon
- Citations

## Imported Source Text

Defining “Information” for Cross‑Boundary Comparisons — Concepts

Use an operational notion: information for an observer = any physically realizable signal state that changes the observer’s predictive distribution over a target variable. Quantify with mutual information. Then a boundary “passes information” if there is non‑zero, accessible mutual information across it. Memory boundaries drop—but rarely zero—MI between past and next moments; classical horizons make outside‑accessible MI from the inside effectively zero.

1) Why the definition matters

- “Information” has distinct meanings: syntactic (Shannon bits), physical (thermodynamic cost), and semantic (meaning/truth).
- A cross‑domain comparison needs a neutral, observer‑tethered metric. Mutual information (MI) fits this bill.

2) Working definition (operational)

> Information (for observer O about system S) = any state of a channel that, when received by O, changes O’s probability distribution over S’s states. A boundary transmits information if I(S_⁠inside; S_⁠outside | access) > 0.

This is syntactic/physical, not semantic: it measures predictive constraint, regardless of meaning.

3) Applying the definition

Case What changes at the boundary Information passage (MI) Event boundary (memory) Prediction error spikes; event model resets; hippocampal response peaks; across‑boundary order/associations weaken. MI between pre‑ and post‑boundary features drops but stays > 0; observers can still recover links, just less reliably. Event horizon (black holes) Causal structure forbids outward signals from inside the horizon (classically); black‑hole entropy scales with horizon area. Outside‑accessible MI from inside → ≈ 0 (classically). Quantum theories suggest unitarity with information encoded in radiation, but not classically transmitted across the horizon.

4) Edge notes

- Semantic vs syntactic: The brain cares about meaning, but our metric stays at the syntactic/physical level to compare domains.
- Information is physical: Any encoding/erasure has thermodynamic costs (Landauer).
- Black‑hole information: Modern views preserve unitarity (information not destroyed), with entropy ∝ area (Bekenstein–Hawking). Our operational MI outside the horizon remains near zero for inside states, consistent with the “point of no return” description.

5) Formula panel (operational & compact)

- Shannon entropy: H(X) = -∑ x p(x) log p(x). Units: bits (base-2).
- Mutual information: I(X;Y) = ∑ x,y p(x,y) log p(x,y)/(p(x)p(y)) = H(X) - H(X|Y). Interpretation: reduction in uncertainty about X given Y.
- Conditional MI: I(X;Y|Z) = H(X|Z) - H(X|Y,Z). Use: “accessible MI,” conditioning on what an observer can actually receive.
- Operational definition (this note): A boundary “passes information” iff I(S inside; O outside | access) > 0.

Estimating MI around a memory event boundary

1. Extract features in a sliding window before (W pre ) and after (W post ) the putative boundary (e.g., embeddings, motion/scene vectors).
2. Estimate I(W pre; W post ) via a nonparametric estimator (e.g., kNN MI) or discretized bins. Expect a drop vs. within‑event windows.
3. Relate boundary strength to prediction error: PE t = −log p(s t | model t−1 ); boundaries where PE spikes.

“Accessible MI” at a black‑hole event horizon

- For an outside observer, classical channels from inside → outside are absent; treat I(S inside; O outside | access) ≈ 0.
- Quantum context: unitarity + Hawking radiation imply global information conservation, but not classical transmission across the horizon.
- Entropy bound context: S BH = (k B c³ A)/(4 G ħ). (Bekenstein–Hawking area law)

This description stays at the syntactic/physical level; it does not take a stance on semantic information. See SEP overviews for semantics.

Citations

Shannon (1948) — A Mathematical Theory of Communication (PDF)
Landauer (1961) — Irreversibility and Heat Generation (IBM JRD, PDF)
SEP — Information (overview)
SEP — Semantic Conceptions of Information
Zacks et al. (2007) — Event Segmentation (PMC)
Kurby & Zacks (2008) — Segmentation in Perception & Memory (PMC)
Ben‑Yakov & Henson (2018) — Hippocampal boundary response (J. Neurosci.)
NASA GSFC — Event horizon as point of no return
Bekenstein (1973) — Black Holes and Entropy (PRD)
ArXiv — Black Holes, Entropy, and Information (review)
