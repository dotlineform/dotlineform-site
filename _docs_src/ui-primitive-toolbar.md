---
doc_id: ui-primitive-toolbar
title: "UI Primitive: Toolbar"
last_updated: 2026-04-19
parent_id: ui-catalogue
sort_order: 50
---
# UI Primitive: Toolbar

## Purpose

The toolbar is the shared action band for short control clusters such as import controls, mode switches, filter controls, and local page actions.

It should make grouped controls feel intentional without becoming a generic catch-all container.

## Contract

A toolbar should define:

- spacing and alignment for a short row of controls
- wrapping behavior on smaller screens
- relationships between labels, fields, buttons, and result text
- a consistent visual role as an action strip or control band

## Anatomy

The default toolbar should define:

- outer container
- one or more control groups
- label/control alignment
- inline result or mode text area where relevant
- responsive wrap behavior

## Variants And States

Expected variants:

- action toolbar
- filter toolbar
- import toolbar

Expected states:

- neutral/default
- result or status present
- dense or wrapped mobile layout

## Usage Rules

- use the toolbar for clustered actions that belong together
- do not use it as a substitute for general page layout
- if a toolbar repeatedly gains the same internal pattern, document that as a composition built from shared primitives

## Current Implementation Notes

The current Studio toolbar family is documented as `tagStudioToolbar__*`.

This primitive should make the intended shape and role of those controls visible independently of any one route.

## Visual References

Asset folder:

- `assets/docs/ui-catalogue/toolbar/`

Add screenshots here for:

- import/action toolbar
- toolbar with result text
- wrapped mobile toolbar state
