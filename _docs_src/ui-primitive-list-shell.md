---
doc_id: ui-primitive-list-shell
title: "UI Primitive: List Shell"
last_updated: 2026-04-19
parent_id: ui-catalogue
sort_order: 40
---
# UI Primitive: List Shell

## Purpose

The list shell is the shared outer structure for list-style interfaces.

It should define the container, row rhythm, and header treatment without dictating every row's internal content.

## Contract

A list shell should define:

- optional header row treatment
- list container spacing
- row separation or grouping rhythm
- empty-state placement
- how rows align visually as a set

It should not define:

- page-specific row columns
- domain-specific chip layouts
- action logic inside a row

## Anatomy

The default list shell should define:

- outer list wrapper
- optional head region
- rows container
- row boundary treatment
- empty state placement

## Variants And States

Expected variants:

- simple content list
- data list
- grouped list

Expected states:

- default populated list
- empty state
- filtered state when used with shared filtering controls
- selected row state only if the product surface genuinely needs it

## Usage Rules

- keep the shell shared even when row internals differ
- document new list types as named variants rather than inventing untracked one-offs
- move repeated row-shell behavior into the primitive, but leave domain content in feature-specific markup

## Current Implementation Notes

The current Studio shared list shell pattern is described in `tagStudioList__*`.

This primitive should become the canonical outer-list contract across repeated list pages.

## Visual References

Asset folder:

- `assets/docs/ui-catalogue/list-shell/`

Add screenshots here for:

- default list shell
- grouped list example
- empty state
- list with filter row above it
