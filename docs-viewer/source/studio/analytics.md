---
doc_id: analytics
title: Analytics
added_date: "2026-05-06 18:19"
last_updated: 2026-07-15
parent_id: ""
---
# Analytics

## Start Here

- [Analytics Overview](/docs/?scope=studio&doc=analytics-overview) — boundaries, execution path, configuration, extension points, and weak spots.
- [Analytics Config JSON](/docs/?scope=studio&doc=config-analytics-config-json) — route registry, catalogue inputs, tag-group order, and RAG policy.
- [Tag Source Data](/docs/?scope=studio&doc=analytics-tag-source-data) — the four canonical tag sources and their relationships.
- [Tag Services](/docs/?scope=studio&doc=analytics-tag-services) — read/write service architecture and safety boundary.

## Tag Workflows

- [Tag Groups](/docs/?scope=studio&doc=tag-groups) — read the group taxonomy.
- [Tag Registry](/docs/?scope=studio&doc=tag-registry) — maintain canonical tags.
- [Tag Aliases](/docs/?scope=studio&doc=tag-aliases) — maintain shorthand and promote/demote vocabulary.
- [Series Tags](/docs/?scope=studio&doc=series-tags) — review coverage and manage offline assignment sessions.
- [Tag Editor](/docs/?scope=studio&doc=tag-editor) — edit one series and its per-work overrides.

## Data Sharing

Analytics hosts the browser and HTTP boundary for [Data Sharing](/docs/?scope=studio&doc=data-sharing). Data Sharing itself owns adapter registration, packages, workspace paths, review, and apply semantics.

## Paused Exploration

[Tag Dimensions](/docs/?scope=studio&doc=analytics-tag-dimensions) separates the unimplemented dimension/scoring concept, proposed architecture, and a possible first delivery. None is a current runtime contract.

## Run

```bash
bin/local-analytics
```

Default route: `http://127.0.0.1:8766/analytics/`.
