---
doc_id: tag-groups
title: Tag Groups
last_updated: 2026-03-28
parent_id: tagging
sort_order: 70
---

# Tag Groups

Route:

- `/studio/tag-groups/`

Purpose:

- review configured Studio tag groups and their short/long descriptions

## Page / Template Structure

Primary template:

- `studio/tag-groups/index.md`

Page controller:

- `assets/studio/js/tag-groups.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`

Top-level structure:

- `.tagGroupsPage`
  - page scope for Studio CSS variables
- `#tag-groups[data-role="tag-groups"]`
  - page root
- `[data-role="content"]`
  - template-owned render target inside the shared Studio panel shell

## Named UI Sections

### Group sections

User-facing name:

- group sections

DOM / CSS:

- `.tagGroups__sections`
- `.tagStudio__groupInfoSection.tagGroups__section`
- `.tagStudio__groupInfoHead`
- `.tagStudio__groupInfoText`
- `.tagGroups__short`

JS owner:

- `renderGroups(content, groups, config)`

Meaning:

- the ordered set of configured group descriptions

### Group chip

User-facing name:

- group chip

DOM / CSS:

- `.tagStudio__keyPill`
- `.tagStudio__chip--subject`
- `.tagStudio__chip--domain`
- `.tagStudio__chip--form`
- `.tagStudio__chip--theme`

Meaning:

- the shared Studio chip treatment used for each group heading

## UI Layout and Styling

Primary CSS:

- `assets/studio/css/studio.css`

Shared primitives used:

- `tagStudio__panel`
- `tagStudio__keyPill`
- `tagStudio__empty`
- `tagStudio__groupInfo*`

Page-specific classes retained:

- `tagGroups__*` for page layout and short-description spacing

## DOM Rendering and Event Wiring

Page boot:

- `initTagGroupsPage()`

Main render function:

- `renderGroups(content, groups, config)`

Event wiring:

- none

## UI Contract

This page follows the Studio-specific shared UI boundary documented in `docs/studio/ui-framework.md`:

- classes define presentation
- `data-role` defines JS selectors

`assets/studio/js/studio-ui.js` holds the role selectors plus generated style class tokens used by `tag-groups.js`.

## Data Access

Primary data access:

- group descriptions from `tag_groups.json`
- group ordering from `studio_config.json`

Loaded through:

- `assets/studio/js/studio-data.js`
- `assets/studio/js/studio-config.js`

## Change Guidance

If a request refers to:

- “group section”
  - start with `.tagStudio__groupInfoSection.tagGroups__section`
- “group chip”
  - start with `.tagStudio__keyPill`
- “long description”
  - start with `.tagStudio__groupInfoText`
