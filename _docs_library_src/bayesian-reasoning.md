---
doc_id: bayesian-reasoning
title: Bayesian Reasoning
added_date: "2026-05-07 16:55"
last_updated: "2026-05-07 16:55"
parent_id: ""
sort_order: 80
published: true
viewable: false
---
# Bayesian Reasoning

## The core idea

**Bayesian reasoning** is the math of learning from evidence. You start with a belief (*prior*), observe new data (*evidence*), weigh how likely that data would be if your belief were true (*likelihood*), and update to a new belief (*posterior*).

## Flow diagram

<svg viewbox="0 0 980 240" width="100%" height="auto" role="img" aria-label="Bayesian flow: prior to posterior">
<defs>
<marker id="arrow" viewbox="0 0 10 10" refx="10" refy="5" markerwidth="8" markerheight="8" orient="auto-start-reverse">
<path d="M 0 0 L 10 5 L 0 10 z"></path>
</marker>
</defs>
<rect x="20" y="40" width="200" height="120" rx="12" fill="#ffffff" stroke="#d8dee9"></rect>
<text x="120" y="70" text-anchor="middle" font-size="16">Prior</text>
<text x="120" y="96" text-anchor="middle" font-size="13">Belief before data</text>
<rect x="240" y="40" width="200" height="120" rx="12" fill="#ffffff" stroke="#d8dee9"></rect>
<text x="340" y="70" text-anchor="middle" font-size="16">Evidence</text>
<text x="340" y="96" text-anchor="middle" font-size="13">New observation</text>
<rect x="460" y="40" width="200" height="120" rx="12" fill="#ffffff" stroke="#d8dee9"></rect>
<text x="560" y="70" text-anchor="middle" font-size="16">Likelihood</text>
<text x="560" y="96" text-anchor="middle" font-size="13">How compatible?</text>
<rect x="680" y="40" width="280" height="120" rx="12" fill="#ffffff" stroke="#d8dee9"></rect>
<text x="820" y="70" text-anchor="middle" font-size="16">Posterior</text>
<text x="820" y="96" text-anchor="middle" font-size="13">Updated belief</text>
<path d="M 220 100 L 240 100" stroke="#9aa4b2" marker-end="url(#arrow)"></path>
<path d="M 440 100 L 460 100" stroke="#9aa4b2" marker-end="url(#arrow)"></path>
<path d="M 660 100 L 680 100" stroke="#9aa4b2" marker-end="url(#arrow)"></path>
<text x="490" y="190" text-anchor="middle" font-size="12">New belief ∝ Prior × Likelihood</text>
</svg>

## Tiny numeric example (medical test)

Suppose a disease affects **1%** of people (prior = 0.01). A test is **99% sensitive** (true positive) and **95% specific** (true negative). You test positive. What’s the chance you actually have it?

- Likelihood of a positive if sick: 0.99
- Likelihood of a positive if healthy: 1 − 0.95 = 0.05
- Using Bayes: `Posterior = (0.99×0.01) / [(0.99×0.01) + (0.05×0.99)] ≈ 0.167`

**Result:** Even with a “good” test, a positive result means ~**17%** chance of disease because the base rate (prior) is low.

## Everyday intuition

### Weather

- Prior: 30% chance of rain.
- Evidence: dark clouds.
- Likelihood high → posterior rises (e.g., to 80%).

### Inbox

- Prior: friend replies quickly.
- Evidence: no reply in 6h. 
- Likelihood of “busy/phone off” grows → update expectations.

### Science

Start with a hypothesis (prior). Run experiment (evidence). Keep/adjust the theory based on how well it predicts results.

## Key terms

| Term | Meaning | Analogy |
| --- | --- | --- |
| Prior | Belief before data | Map you start with |
| Likelihood | How likely the data are under a belief | How well the map explains landmarks |
| Evidence (marginal) | Overall probability of the data | Normaliser so beliefs sum to 1 |
| Posterior | Updated belief after data | Revised map |

## Where this meets the brain

In predictive processing, the brain behaves like a Bayesian learner: priors (expectations) meet sensory likelihoods; posteriors guide perception and action. This is the core of the Free Energy Principle.

## References

Bayes, T. (1958). An essay towards solving a problem in the doctrine of chances. *Biometrika, 45*(3/4), 296–315. (Original work published 1763). [https://www.jstor.org/stable/2984087](https://www.jstor.org/stable/2984087)

Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience, 11*(2), 127–138. [https://doi.org/10.1038/nrn2787](https://doi.org/10.1038/nrn2787)

Gelman, A., Carlin, J., Stern, H., Dunson, D., Vehtari, A., & Rubin, D. (2013). *Bayesian Data Analysis* (3rd ed.). CRC Press.

Jaynes, E. T. (2003). *Probability Theory: The Logic of Science*. Cambridge University Press. [https://bayes.wustl.edu/etj/prob/book.pdf](https://bayes.wustl.edu/etj/prob/book.pdf)

Tenenbaum, J. B., Kemp, C., Griffiths, T. L., & Goodman, N. D. (2011). How to grow a mind: Statistics, structure, and abstraction. *Science, 331*(6022), 1279–1285. [https://doi.org/10.1126/science.1192788](https://doi.org/10.1126/science.1192788)
