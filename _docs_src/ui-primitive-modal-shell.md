---
doc_id: ui-primitive-modal-shell
title: "UI Primitive: Modal Shell"
last_updated: 2026-04-19
parent_id: ui-catalogue
sort_order: 60
---
# UI Primitive: Modal Shell

## Purpose

The modal shell is the shared overlay container for focused tasks and confirmations.

It should standardize the outer experience of a modal before feature-specific content is added.

## Contract

A modal shell should define:

- overlay treatment
- dialog surface
- dialog width and padding behavior
- title/body/actions structure
- dismissal affordances and focus behavior expectations

The shell is separate from:

- modal-specific form fields
- feature-specific validation logic
- mutation behavior

## Anatomy

The default modal shell should define:

- overlay
- dialog container
- title area
- body area
- actions area
- close affordance if used by the modal type

## Variants And States

Expected variants:

- confirm modal
- detail confirm modal
- form modal

Expected states:

- opening/open
- busy or submitting when needed
- error or warning content inside the body area
- narrow/mobile layout

## Usage Rules

- keep shell behavior and content behavior separate
- standardize shell structure before adding modal-specific fields
- only introduce new modal types when the interaction contract is materially different

## Current Implementation Notes

The current Studio modal family is documented as `tagStudioModal__*` and in the Studio modal type guidance.

This primitive doc complements that guidance by giving the shell itself a stable visual and structural reference.

## Visual References

Asset folder:

- `assets/docs/ui-catalogue/modal-shell/`

Add screenshots here for:

- confirm modal
- form modal
- mobile modal layout
- overlay/dialog relationship
