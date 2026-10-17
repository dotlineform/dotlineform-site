---
draft: false
doc_id: d-20261017-184905-346b1a
title: Docs Viewer Heading Typography
added_date: "2026-10-17 18:49:05"
last_updated: "2026-10-17"
---
# Docs Viewer Heading Typography

Parent: [Planned Features](../Planned_Features.md). Durable owner: [CSS Ownership](../CSS_Ownership.md).

Subsequent [Retire Main CSS](Retire_Main_CSS.md) extends shared ownership to body, layout and remaining prose styles; its current boundary supersedes the host inheritance retained by this heading-only change.

Status: implemented and reviewed on 2026-10-17; awaiting manual normal-use acceptance after reloading Docs Viewer. The user approved consolidating document heading tokens and rules into shared viewer CSS after a public-site CSS edit had no effect in Manage. No commit, Publish or deployment was performed.

## Scope And Ownership

Manage and Review do not load the public site's `main.css`. The shared `docs-viewer.css` therefore owns the intended document H1–H4 scale directly: 28, 20, 18 and 16px at the default 16px root. It supplies heading sizes, weight, line heights and margins across public and local readers. The heading tokens no longer inherit generic public-site values; unused intermediate viewer size tokens are removed. Moments retains compact title spacing without a different title size, and specialised Catalogue record headings retain their existing presentation.

This is browser-owned presentation with no server, persistence or generation work. The user's temporary `main.css` edit remains untouched. Other site typography and non-heading token ownership are outside this change. Shared CSS reaches the tracked public artifact through the existing explicit projection; no stylesheet, loader, alias or runtime dependency is added.

## Completion Gates

- [x] Readiness: confirm local shell stylesheets, host heading inheritance, shared heading consumers and specialised overrides.
- [x] Consolidate heading tokens and H1–H4 rules in shared viewer CSS; update the durable ownership guidance.
- [x] Update and inspect the public projection; check projection consistency, site validation and whitespace.
- [x] Complete bounded code review, including redundancy and defensive behaviour.

## Evidence And Review

Selected evidence is focused CSS/token/cascade review, exact public projection inspection, projection consistency, site validation and whitespace checks. These take seconds locally, with no service startup, live writes or network transfer. No tests, browser actions, document generation, Search rebuild, Publish or deployment are included. Visual acceptance remains manual after reloading Docs Viewer.

The public projection changed only the shared stylesheet and was inspected. Projection consistency, site validation and whitespace checks passed. Reference inspection found no remaining consumers of the removed intermediate heading-size tokens. Public and local shell inspection confirmed the shared stylesheet load boundary; cascade review covered ordinary H1–H4, Moments, Related Links and the specialised Catalogue heading rules. This is static evidence, not a browser measurement of computed typography.

### Code Review: Redundancy And Defensive Behaviour

The shared heading tokens now contain their own values. Generic public-site heading fallbacks and three unused intermediate size tokens were removed, together with two redundant consumer fallbacks and Moments' duplicate H1 line height. Explicit H2–H4 rules remove reliance on browser defaults, and the shared scoped heading rules outrank the public host's generic element rules. Existing specialised Catalogue and Related Links selectors retain their precedence; Moments keeps its compact margin while using shared title typography.

No validation, preflight, source read, reload handler, compatibility alias or recovery machinery was added. Existing body/layout token inheritance remains outside this heading-specific consolidation. The frontend owns the full change and the server has no new work. No blocking findings remain. Visual fit in Public, Manage and Review remains manual; retain this delivery link until that acceptance is recorded.

H2 section-divider follow-up — 2026-10-17: the user chose to retain the font scale and distinguish document H2 sections with a line immediately below the heading. The existing H2 rule now uses a 1px bottom border with `--docs-viewer-border-strong`, matching normal horizontal rules, and the smallest shared spacing token between text and divider. Both lines use the stronger grey following the user's visibility adjustment. The exact shared stylesheet projection, projection consistency, site validation and whitespace checks passed. Bounded review confirmed that the cue stays within the existing content-heading rule and reuses established tokens, with no renderer changes, new validation or runtime work. No tests, browser actions, generation, Publish or deployment ran; visual review remains manual after reload.
