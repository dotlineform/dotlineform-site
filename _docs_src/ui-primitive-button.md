---
doc_id: ui-primitive-button
title: "UI Primitive: Button"
last_updated: 2026-04-19
parent_id: ui-catalogue
sort_order: 20
---
# UI Primitive: Button

## Purpose

The button is the shared action control for page actions, local mutations, confirmations, and secondary commands.

It should feel consistent enough that action emphasis comes from variant choice, not from redesigning button geometry for each page.

## Contract

A shared button should define:

- stable geometry
- predictable padding and height
- focus treatment
- disabled treatment
- clear primary versus secondary emphasis

It should remain usable in:

- toolbars
- inline form rows
- panels
- modal action rows

## Anatomy

The default button should define:

- outer control shape
- text treatment
- border/surface treatment
- hover and focus behavior
- disabled appearance
- optional icon slot if adopted later

## Variants And States

Expected variants:

- primary
- secondary
- subtle or tertiary
- destructive

Expected states:

- default
- hover
- focus-visible
- active
- disabled
- busy if a repeated async pattern is formalized later

## Usage Rules

- keep shared geometry stable across contexts
- use variant changes before inventing new button styles
- destructive actions should remain explicit
- buttons should not communicate structural layout differences; that belongs to the surrounding composition

## Current Implementation Notes

The current Studio shared button family is part of the `tagStudio__*` primitive layer.

This doc should become the canonical design reference for any shared button shape, regardless of page namespace.

## Visual References

Asset folder:

- `assets/docs/ui-catalogue/button/`

Add screenshots here for:

- primary and secondary buttons
- destructive treatment
- disabled and focus-visible states
