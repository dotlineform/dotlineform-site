---
draft: false
doc_id: d-20261014-182522-940f57
title: Source File Report Optimisation
added_date: "2026-10-14 18:25:22"
last_updated: "2026-10-14 18:25:22"
parent_id: d-20260428-000000-f5ff18
---
# Source File Report Optimisation

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Reports](../Reports.md). The user approved the reviewed Uncataloged Files and Missing Source Files scope on 2026-10-14, including removal of repeated browser response audits and the invalid `projects/…` rejection; tests must remain unchanged.

## Agreed Result

Keep Python's live filesystem diagnosis and the browser's presentation/activation responsibilities. Each operation explicitly reads one saved Catalogue input and one pipeline configuration, prepares its source map/default once and uses a narrow shared reader for required roots, directory prefixes and terminal metadata. Missing Source Files inspects only declared paths and retains one row per missing Work. Uncataloged Files lists only represented source directories and retains the image-extension policy and physical file-identity matching. Empty complete-registration selections need no Projects setup.

Carry completed facts only during the run, preserve current missing/non-file/symlink/error outcomes and final row ordering, and retain confinement without repeated full-path walks or post-inspection checks. The general Work-media resolver, media processing, source-opening and other report consumers remain unchanged. The browsers consume service-owned fields directly, retaining safe text and destination handling. Durable safeguards, their owners/costs and the exceptional candidate-symlink metadata read are recorded in Reports.

## Completion Gates

- [x] Readiness: traced both services, shared path/configuration/input helpers, browser adapters, related resolver callers and test gaps; user approved this bounded slice.
- [x] Implement one shared run-local inspection owner and explicit report functions; remove constructor/import-time report setup, duplicate declaration checks and repeated filesystem work.
- [x] Remove browser response audits/coercion and the invalid default-source prefix rejection; preserve response fields/versions, columns, destinations and operation errors.
- [x] Focused Python/JavaScript lint, Python compilation and whitespace checks passed. One read-only current-data call to each production report completed, returning 0 missing-source rows and 223 uncataloged-image rows. Results establish current saved-input/root/metadata/listing paths only; no timing comparison, browser/HTTP interaction or synthetic edge-case assurance is claimed.
- [x] Complete the distinct code review and mandatory Redundancy And Defensive Behavior Review. Traced empty/duplicate/shared-path/missing-parent/non-file/symlink/error flows and reviewed configuration/input, lexical confinement, terminal metadata reuse, physical identity and browser destination owners. Removed unnecessary identity construction in Missing Source Files and retained the exceptional followed metadata read solely to preserve Uncataloged Files' candidate-symlink outcomes. Confirmed no general-resolver change, compatibility alias, canonical fallback, freshness recheck, repair, public projection or test delta. Focused checks affected by review changes passed.
- [x] Update Reports, Catalogue Report Inputs and the implementation guardrail; parent this delivery here.
- [x] Review-affected Python/JavaScript lint and Python compilation passed; the updated Missing Source Files type predicate returned 0 rows on its focused current-data rerun. Whitespace and scoped path/security review passed; the retained Studio URL credential rejection is intentional, and no machine-specific path or credential value was introduced.
- [ ] User manual acceptance after restarting Docs Viewer services and force-reloading: both Run/Refresh reports, missing-source paths including `projects/…`, image coverage/order, exact Finder and Studio destinations, and adoption of saved registrations only after Catalogue Refresh.

Tests, fixtures, harnesses and profiles remain unchanged and unrun under [Test Contract Discipline](../Test_Contract_Discipline.md). Existing canonical-path/all-file fixtures and retired producer/normalizer contracts remain unreviewed; separate test migration is not a completion gate for this implementation. Current Missing Source Files data contains no missing rows, so its missing/non-file/symlink cases and the browser prefix fix have static review rather than runtime case evidence. Alias/hard-link and failure variants, HTTP/browser transport, Finder/Studio interaction and tactile presentation remain unverified.

No source, media, report snapshot, Catalogue input, queue, Docs/Search output or publication output was written. No browser automation, service restart, Build, Publish, deployment, commit or push ran. The changed browser modules are local-only and outside the public projection inventory. Each later report run reads and inspects afresh; Finder/source actions keep their own activation checks.
