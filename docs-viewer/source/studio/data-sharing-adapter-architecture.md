---
doc_id: data-sharing-adapter-architecture
title: Data Sharing Adapter Architecture
added_date: "2026-06-21 00:00"
last_updated: 2026-07-15
parent_id: data-sharing
viewable: true
---
# Data Sharing Adapter Architecture

## Method

Adapters keep shared orchestration independent of document/tag source shapes. The generic layer knows domain, operation, selection, paths, and normalized results; a family knows how one kind of canonical record becomes a package, review row, and apply plan.

```text
registry resolution
  -> DataSharingAdapterHandlers
  -> adapter operation module
  -> family selected by profile/package identity
  -> domain helper
```

## Layout

```text
data-sharing/adapters/<domain>/
  adapter.py       # handler wiring only
  context.py       # shared paths, dependencies, validation, I/O helpers
  prepare.py       # profile/family prepare orchestration
  returned.py      # staged-file parsing, family detection, review/apply dispatch
  families/
    <family>.py    # source + package + review + apply semantics
```

This is a methodology, not a required file count. Split only where responsibility exists; do not preserve compatibility exports after moving an owner.

## Profile Versus Family

- **Profile**: a configured operator choice using behaviour a family already supports.
- **Family**: code for a materially distinct source shape, package shape, selector, returned-package identity, review model, validation, or apply action.

A label/default/limit/format option may be config-only. A new record selection meaning or package/review shape is code even when config can describe it.

## Generic Selection Contract

Prepare selection rows expose at least:

```json
{ "id": "record-id", "name": "Display name" }
```

Domain fields may accompany them, but generic browser code selects `id`. Selectors such as `docs_scope` need registry declaration, request validation, and family implementation.

## Boundary Rules

- `adapter.py` wires handlers; it does not accumulate family logic.
- `data-sharing/` remains headless; Analytics owns browser/HTTP code.
- domain helpers remain canonical authorities for validation/writes.
- adapter resolution is config-driven; package-family detection is code-driven and must fail closed.
- apply actions are narrow and explicitly confirmed; no generic “write returned data” hook.
- moved internals get updated imports/tests, not indefinite aliases.

## Weak Spots

- Documents currently have one broad family while tags have several; the right family granularity is proven by differing behaviour, not symmetry.
- `returned.py` can become a second family registry if package detection and orchestration keep growing.
- Thin `workflows/*.py` modules mostly name ownership around dispatch; avoid adding more layers without behaviour.
- Shared response shapes can hide domain-specific assurance unless review rows/issues and apply counts remain explicit.

## Extension Checklist

For a new family: source loader, selectable-record meaning, prepare package, identity/detection, review rows/issues, apply/non-apply decision, registry profile/capability, safe browser projection, and focused domain/API tests.
