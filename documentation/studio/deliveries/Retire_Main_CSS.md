---
draft: false
doc_id: d-20261017-190405-d18e93
title: Retire Main CSS
added_date: "2026-10-17 19:04:05"
last_updated: "2026-10-17"
---
# Retire Main CSS

Parent: [Planned Features](../Planned_Features.md). Durable owner: [CSS Ownership](../CSS_Ownership.md).

Status: implemented and reviewed on 2026-10-17; awaiting manual normal-use acceptance. The user approved retiring active `main.css`, moving remaining reader styles into shared viewer CSS, minimal dedicated 404 styling and leaving the archive untouched. The exact palette-test cleanup and one-selector run were approved separately. No document generation, Publish, commit or deployment was performed.

## Scope And Ownership

Shared viewer CSS owns page defaults, typography/spacing tokens and standard document prose across Public, Manage and Review. Missing list, code, horizontal-rule and generic-caption styles move there; existing heading, link, table, figure and specialised presentation stay with their current rules. Generic host-token fallbacks, the generic `content` class and public legacy wrapper hooks are retired. The active public root and its maintained route template load only the established shared viewer styles.

The public 404 page uses dedicated `site/assets/css/error.css` and the existing shared palette/theme-toggle script. Active `site/assets/css/main.css` and its route/configuration references are removed. Archive CSS, pages and assets remain untouched. This is frontend presentation and tracked public-artifact maintenance; the server, source data, document generation and publication queues have no new work.

## Completion Gates

- [x] Readiness: inspect active stylesheet consumers, supported renderer markup, existing viewer overrides, public/local shells, 404 and the projection/validation owners.
- [x] Implement shared reader ownership and minimal 404 styling; retire active main CSS and obsolete hooks.
- [x] Apply the separately approved two-line test cleanup and document its exact existing coverage under [Testing](../Testing.md#shared-docs-viewer-palette-ownership).
- [x] Run focused lint, the approved one-selector test, projection/check, site validation and whitespace checks; inspect the exact public delta and archive boundary.
- [x] Review the final change, including redundancy and defensive behaviour, and record evidence limits.

## Evidence And Review

The selected static checks address JavaScript wiring, changed-test syntax, public route/configuration references, tracked projection and deploy-root consistency. The one approved test checks shared-palette source ownership; unchanged scope-era setup may block execution. Expected cost is seconds to a few minutes, with ignored caches and isolated test directories only. No browser automation, new tests, live application operations, document/Search generation, Publish, commit or deployment are included. Manual review covers ordinary prose, lists, code, tables, Moments, public/local layout and the 404 page in both themes.

Changed-path JavaScript lint passed for the shared main-view renderer, and Python lint passed for the edited test module. Public projection updated exactly the main-view renderer, reader CSS and report CSS; the explicit projection was inspected. Projection consistency, site validation and whitespace checks passed. The active root, route template and 404 stylesheet references were inspected; the deploy configuration now requires `error.css`. The archive has no Git diff.

The approved exact palette test stopped at setup with one error: `external_data_sharing_workspace` in `docs-viewer/tests/conftest.py:91` imports removed `docs_scope_config`. No selected-test assertions ran. That fixture and broader scope-era test migration remain unchanged and outside this approval. The test diff is exactly the obsolete file read and its assertion; no replacement coverage or retirement-existence assertion was introduced.

### Code Review: Redundancy And Defensive Behaviour

The final review traced public/local shell loading, the removed generic content hook, component token consumption and the standard prose cascade. It removed the host stylesheet dependency, generic host-token fallbacks, unused wrapper tokens and the unused 404 navigation-script include. Supported reader defaults moved into the existing scoped stylesheet; already-owned tables, links, blockquotes and modern figures were reused. Low-specificity list rules retain report/gallery ownership, and later specialised Moments, figure-caption and expanded-table rules retain precedence. The 404 page consumes the shared palette rather than copying raw colours and retains its existing theme-toggle script. Its visited home link keeps the header foreground.

The frontend owns the complete presentation change; no server request, source scan, generation, validation pass, compatibility alias, recovery path or new runtime loader was added. The exact test edit follows the separately approved scope and its maintained [coverage record](../Testing.md#shared-docs-viewer-palette-ownership). No blocking production findings remain. Computed styles, visual fit and theme interaction remain unexercised; the setup-blocked test is an evidence limit, not a passing check. Retain this delivery link until manual acceptance is recorded.

## Main Content Alignment Follow-Up

On 2026-10-17 the user supplied screenshots of a document heading and the `dotlineform` Selected Documents thumbnails sitting too high relative to Index search. The shared main pane now has top padding equal to the Index's inner spacing plus its border: 15px with current tokens. That one pane-level inset moves document headings and thumbnail reports together. Opening collection lists omit their extra report margin, using the actual `docsViewer__documentMount` boundary so their search controls receive the shared inset once.

The exact reader/report stylesheet projection was inspected; projection consistency, site validation and whitespace checks passed. Bounded source review confirmed the shared pane owns the inset, the collection rule matches the current mounted document wrapper and report-specific interior spacing remains independent. No new handlers, validation, compatibility selectors, service work, tests or browser automation were added. The user's screenshots establish the prior visual issue; manual review after reload must confirm the revised alignment. No document generation, Publish or deployment ran.
