---
doc_id: docs-viewer-css-cascade-design
title: CSS Ownership
added_date: 2026-05-11
last_updated: 2026-07-15
parent_id: docs-viewer
viewable: true
---
# Docs Viewer CSS Ownership

Docs Viewer is portable but intentionally inherits the prose language of its host site. The cascade has four owners.

## Owners

- **host CSS** owns site chrome, layout, baseline typography, theme tokens, and generic `.content` prose/media rules.
- **portable Docs Viewer CSS** at `site/docs-viewer/static/css/docs-viewer.css` owns the reader shell, navigation, panels, search, bookmarks, status, and shared viewer controls.
- **scope CSS** owns presentation meaningful to one content scope. `docs-viewer-moments.css` activates through `data-viewer-scope="moments"`, so the same rules work on public and manage routes.
- **manage feature CSS** under `docs-viewer/static/css/` owns the manage shell, source editor, import, and other local-only surfaces.

Rendered document HTML uses both `docsViewer__content` and `content`. This is deliberate: the viewer owns its container while the host owns ordinary document typography.

## Load Boundary

Public routes load host CSS, the portable viewer stylesheet, and an explicit scope stylesheet when needed. They do not load management CSS.

The local manage shell loads the portable viewer stylesheet, shared report styles, applicable scope styles, and focused management feature styles. Management controls must not depend on Studio CSS even when Studio is the local host.

The local Docs Viewer service maps the public portable CSS URL to the same tracked file, so public and manage routes do not maintain separate reader styles.

## Extension Method

- host-wide prose or theme rule: host stylesheet
- reader behaviour used across scopes/surfaces: portable Docs Viewer stylesheet
- content presentation tied to a scope: scope stylesheet keyed by active scope
- local workflow control: owning manage feature stylesheet

Do not place a rule in the portable layer merely because a public route needs it. Ask whether it describes the reader or that route's content.

Components should consume Docs Viewer custom properties with host-token fallbacks. Exact variables and selectors live in CSS; do not mirror their inventory here.

## Weak Spots

- host prose inheritance is intentional, so portable installs must provide reasonable token and content fallbacks
- scope styles are loaded explicitly rather than through a general plugin loader
- raw HTML documents can introduce local presentation that bypasses the normal Markdown shape
- stylesheet order is part of the contract but is expressed in route shells rather than a central manifest

Verify representative public and manage routes after moving ownership between layers. Use visual/manual checks for cascade and layout; use public-boundary checks to confirm management assets do not leak into public shells.
