---
doc_id: coincidence-salience
title: "Loose Ends — Memory — Coincidence Salience Worksheet (Event Frequency × Filter Specificity)"
added_date: "2026-05-16 09:45"
last_updated: "2026-05-16 09:45"
parent_id: ""
sort_order: 140
published: true
hidden: true
---
# Loose Ends — Memory — Coincidence Salience Worksheet (Event Frequency × Filter Specificity)

> Created: 2025-10-07 15:18 UTC+01:00 — Location: Europe/London

## Original Prompt

[2025-10-07 15:18 Europe/London] Create a short companion worksheet (HTML) with two sliders — event frequency and filter specificity — and a formula readout for a 'coincidence salience index'. Include minimal instructions, inline citation table with URLs, and APA references. Format for Apple Notes/GitHub; include the original prompt.

## How to Use

This worksheet gives a quick, heuristic estimate of how likely a coincidence will feel *salient*. It combines an exposure term (**Event Frequency**) with a filter term (**Filter Specificity**). It is *not* a probability of truth — it’s a guide to expected *experience of synchronicity*.

## Controls

Event Frequency (per day)

30,000

Filter Specificity (0–1)

0.20

## Salience Formula

We define a simple **Coincidence Salience Index** (CSI):

`CSI = 1 − exp(−λ)`, where `λ = (freq × spec × horizon_days) / 1e6`

- `freq` = number of distinct events you attend to per day (exposure).
- `spec` = how narrow your current mental filter is (0 broad → 1 very specific).
- `horizon_days` = time window to consider (default 30 days).
- The 10<sup>6</sup> scale normalises to Littlewood’s “one‑in‑a‑million” yardstick.

Horizon (days)

30

CSI (0–1): 0.45

Interpretation: closer to 1 → you should expect multiple *salient* coincidences in this window (given your filters); closer to 0 → few.

### Notes & Safeguards

- CSI tracks *felt salience*, not external causation.
- High specificity can inflate salience; periodically broaden scope and log “null windows.”
- Use this alongside the *Synchronicity Field‑Notes Template* to record outcomes.

## Inline Citation Table (with URLs)

| Topic | Source | URL |
| --- | --- | --- |
| Littlewood’s Law (background) | Wikipedia overview; Dyson’s NYRB essay | [en.wikipedia.org/wiki/Littlewood%27s_law](https://en.wikipedia.org/wiki/Littlewood%27s_law); [nybooks.com/articles/16991](https://www.nybooks.com/articles/16991) |
| Predictive processing / FEP | Friston (2010), Nature Reviews Neuroscience | [nature.com/articles/nrn2787](https://www.nature.com/articles/nrn2787) |
| Mutual information (primer) | University of Chicago teaching notes | [math.uchicago.edu/.../Delgado.pdf](https://www.math.uchicago.edu/~may/VIGRE/VIGRE2008/REUPapers/Delgado.pdf) |
| Confirmation/bias overview | Stanford Encyclopedia of Philosophy | [plato.stanford.edu/entries/confirmation/](https://plato.stanford.edu/entries/confirmation/) |

## APA References

1. Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience, 11*(2), 127–138. <https://www.nature.com/articles/nrn2787>
2. Dyson, F. (2004). Littlewood’s law of miracles. *The New York Review of Books*. <https://www.nybooks.com/articles/16991>
3. Littlewood, J. E. (1953). *A Mathematician’s Miscellany*. Methuen.
4. Shannon, C. E. (1948). A mathematical theory of communication. (Primer: University of Chicago notes.)
5. Stanford Encyclopedia of Philosophy. (n.d.). Confirmation. <https://plato.stanford.edu/entries/confirmation/>
6. Wikipedia contributors. (n.d.). Littlewood’s law. <https://en.wikipedia.org/wiki/Littlewood%27s_law>

Prepared for the *Living Memory* project. Designed for Apple Notes and GitHub archival.
