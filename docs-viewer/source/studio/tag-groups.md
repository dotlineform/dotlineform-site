---
doc_id: tag-groups
title: Tag Groups
added_date: 2026-03-31
last_updated: 2026-05-30
parent_id: analytics
---
# Tag Groups

Route:

- `/analytics/tag-groups/`

Purpose:

- review configured Analytics tag groups and their short/long descriptions

## Route Ready State

The page root `#tag-groups` exposes the shared Studio route-ready contract:

- `data-studio-ready` is `false` while config and group descriptions load, then `true` after the list or error state is rendered
- `data-studio-busy` remains `false`; this route has no route-level commands
- `data-studio-mode` is `list` when groups are shown and `empty` for empty or failed loads
- `data-studio-record-loaded` is `true` when group descriptions are loaded

## Page / Template Structure

Primary shell:

- `analytics-app/app/server/analytics_app/analytics_app_views.py`

Page controller:

- `analytics-app/app/frontend/js/tag-groups.js`

Supporting modules:

- `analytics-app/app/frontend/js/studio-ui.js`

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

- `analytics-app/app/assets/css/analytics.css`

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

This page follows the Studio-specific shared UI boundary documented in [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework):

- classes define presentation
- `data-role` defines JS selectors

`analytics-app/app/frontend/js/studio-ui.js` holds the role selectors plus generated style class tokens used by `tag-groups.js`.

## Data Access

Primary data access:

- group descriptions from `/analytics/api/tag-groups` in the Local Analytics app
- group ordering from `analytics-app/app/frontend/config/analytics-config.json`

Loaded through:

- `analytics-app/app/frontend/js/studio-data.js`
- `analytics-app/app/frontend/js/studio-config.js`

## Change Guidance

If a request refers to:

- “group section”
  - start with `.tagStudio__groupInfoSection.tagGroups__section`
- “group chip”
  - start with `.tagStudio__keyPill`
- “long description”
  - start with `.tagStudio__groupInfoText`
