---
doc_id: ui
title: "UI"
added_date: 2026-05-05
last_updated: "2026-05-05"
parent_id: design
sort_order: 9
---
# UI

This is the target framework doc for the site's shared UI system.

It exists to unify guidance that is currently split between:

- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- stable rules currently buried in [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## Direction

UI guidance should be organized around the design problem and affected surfaces, not around an artificial split between Studio and the public site.

Use one framework vocabulary for:

- public pages
- docs viewer pages
- Library pages
- Studio pages
- local-service-backed command pages

Some primitives and patterns will only appear on Studio routes today.
That does not make them Studio-only design rules.
It means the current affected surface is Studio.

## Documentation Model

Use this hierarchy:

- [Design](/docs/?scope=studio&doc=design) remains the high-level section index.
- This `UI` doc becomes the site-wide UI framework and migration target.
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) remains the index for named primitives, composition patterns, and live reference pages.
- Primitive docs live under `ui-catalogue` as one doc per primitive.
- Composition-pattern docs live under `ui-catalogue` as one doc per pattern.
- Historical change notes belong in [Site Change Log](/docs/?scope=studio&doc=site-change-log).

## Migration Targets

Move stable framework material here when it describes:

- interaction defaults
- DOM hook rules
- route state and progressive enhancement principles
- shared modal, status, list, panel, control, and feedback rules at framework level
- guidance that applies across more than one page family

Move primitive-specific details into matching primitive docs, for example:

- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)

Move lifecycle and multi-part UI behavior into composition-pattern docs, for example:

- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)

## Current Status

This doc is a migration target, not yet the full consolidated framework.

Until the migration is complete:

- use [UI Framework](/docs/?scope=studio&doc=ui-framework) for existing site-wide interaction defaults
- use [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework) for existing Studio primitive and modal guidance
- promote durable guidance from [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) into this doc or the matching primitive/pattern doc before retiring that guidance from the decision log
