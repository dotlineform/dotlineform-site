---
draft: false
doc_id: d-20260930-202533-921c4b
title: Icon Tokens Delivery
added_date: "2026-09-30 20:25:33"
last_updated: "2026-11-18"
summary: Deliver manual SVG icon tokens and Source insertion; static verification and code review precede user visual acceptance.
ui_status: in-progress
parent_id: d-20260910-223116-9a1011
---
# Icon Tokens Delivery

## Current State

Implemented manual extensionless `[[icon:name]]`, inline Source insertion with stem selection and portable SVG-mask rendering. [Icon Tokens](../reference/Icon_Tokens.md) owns current syntax, literal handling, failures and exports. The old watcher claim is retired: Source Save awaits its exact build and fresh display.

The 30 September record reports explicit Python/JavaScript lint, Python compilation, whitespace, public-projection consistency and the builder's read-only help/import diagnostic. Code review tightened path confinement and diagnostics and checked literal preservation, operation-scoped caching and export portability. It did not build authored content, exercise export, run tests/browser checks or establish user visual acceptance. [Compiled evidence](../deliveries/Shared_Controls_And_Visual_Assets_Review.md#icon-migration-evidence)

## Completion Gate

- [x] Deliver renderer, ordinary/collection integration and local Directives insertion.
- [x] Transfer durable behaviour to Reference and complete the recorded static review.
- [ ] Record user manual acceptance of insertion/selection and rendered icon appearance.

Keep this delivery in Working until that remaining gate is settled. Collection/Related Links reuse has since been implemented through its own owner; native App work and an icon picker remain separately scoped.
