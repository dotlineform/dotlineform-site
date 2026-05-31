---
doc_id: risks
title: risks
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
---

# risks

I recommend turning the inventories into a small reporting system rather than longer single documents.

**Recommended Structure**

Keep the current scoring definitions, but split the analysis into four document types:

1. **Risk Policy**
   - Keep `studio-javascript-payload-inventory.md` mostly as policy.
   - Define categories, scoring rules, bands, and rescore rules.
   - Avoid putting current findings here.

2. **Current Risk Dashboard**
   - One short priority document for humans.
   - Purpose: answer “what should we improve next?”
   - Include:
     - top 5 priorities
     - why each matters
     - recommended next action
     - expected evidence of improvement
     - owner area
     - whether it is file-level, family-level, or cross-cutting

3. **Raw Inventories**
   - Keep long tables here only.
   - Separate by unit:
     - JavaScript file inventory
     - JavaScript family rollup
     - Python/Ruby script-family inventory
     - largest-file watch list as an appendix or separate report
   - These are evidence, not the main reading path.

4. **Risk Category Reports**
   - One report per risk type:
     - Maintenance risk
     - Structural/ownership risk
     - Performance risk
     - Architectural drift risk
   - Each report should rank only that risk, across relevant files/families.
   - This avoids one table asking the reader to compare maintenance, performance, and architecture at the same time.

**Main Change**

Separate “what is risky?” from “what should we do?”

For each priority, use a compact action card like:

```md
## Catalogue Save/Build Path

Priority: 1
Risk type: performance + maintenance
Unit: script family
Evidence: broad save path touches source writes, generated artifacts, lookup refreshes, search, media, and activity rows.
Recommended action: add save/build diagnostics before further structural splitting.
Expected improvement: identify repeated broad rebuilds and slow media/search/generated steps.
Concrete next slice: catalogue diagnostics for elapsed time, counts, fallback reasons.
Verification: local save response/log includes per-step counts and timings.
```

**Specific Recommendations**

- Do not make the big inventory tables the main artifact. They should support decisions, not be the decision surface.
- Add a short “Current Priorities” dashboard that is no more than 1-2 screens.
- Split file-level and family-level analysis. They answer different questions:
  - file-level: “where should future edits slow down?”
  - family-level: “where should improvement work be scheduled?”
- Keep largest-file analysis separate from risk priority. Large files are useful watch items, but size is not the same as risk.
- Convert “Recommended improvements” bullets into explicit actions with owner, evidence, verification, and expected score/class movement.
- For JavaScript, add family rollups so `Catalogue editors`, `Docs Viewer`, `Analytics tag routes`, and `Public runtime` can be prioritized without scanning 190 rows.
- For Python/Ruby, keep the family matrix but move the detailed prose into separate family notes or category reports.
- Add a “Do not prioritize now” section. This is useful where something is large but currently acceptable, or where diagnostics should come before refactoring.

**Best Next Step**

Create a new concise dashboard first, probably something like:

`docs-viewer/source/studio/studio-risk-priority-dashboard.md`

Then gradually move detailed category-specific analysis out of the long inventories as they are refreshed. The immediate priority list should probably start with catalogue diagnostics, because the current Python/Ruby analysis already says visibility should come before another broad split.