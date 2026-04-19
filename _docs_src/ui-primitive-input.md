---
doc_id: ui-primitive-input
title: "UI Primitive: Input"
last_updated: 2026-04-19
parent_id: ui-catalogue
sort_order: 30
---
# UI Primitive: Input

## Purpose

The input is the shared text-entry control for search, inline editing, form fields, and small utility workflows.

It should provide a predictable editing surface without carrying page-specific styling assumptions.

## Contract

A shared input should define:

- field geometry
- border and surface treatment
- text size and padding
- focus treatment
- placeholder treatment
- disabled and read-only behavior where relevant

## Anatomy

The default input should define:

- field container
- text area
- placeholder treatment
- focus ring
- optional label relationship in the surrounding composition
- optional help or status relationship outside the field itself

## Variants And States

Expected variants:

- standard text input
- compact input
- search input
- multiline field if it can share the same visual family

Expected states:

- empty
- populated
- focus-visible
- disabled
- read-only
- error only when paired with an external status or validation message pattern

## Usage Rules

- preserve one shared field family unless a different input type has a clear reason to diverge
- do not solve validation by inventing page-local field chrome
- keep labels, hints, and statuses in compositions around the input rather than overloading the primitive itself

## Current Implementation Notes

The current Studio baseline is the `tagStudio__input` family and related search/filter controls.

This doc should help unify search inputs and editor inputs where the visual contract is actually shared.

## Visual References

Asset folder:

- `assets/docs/ui-catalogue/input/`

Add screenshots here for:

- default field
- search field
- focus-visible state
- disabled or read-only state
