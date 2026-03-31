---
doc_id: config-next-steps
title: Config Next Steps
last_updated: 2026-03-31
parent_id: config
sort_order: 60
---

# Config Next Steps

This document collates the main follow-up areas for the current config layer.

## Search config boundary

The current split between `studio_config.json`, `studio-config.js`, and `assets/data/search/policy.json` is workable, but still evolving.

Detailed follow-up references:

- **[Search Config Architecture](/docs/?scope=studio&doc=search-config-architecture)**
- **[Search Config Implementation Note](/docs/?scope=studio&doc=search-config-implementation-note)**
- **[Search Next Steps](/docs/?scope=studio&doc=search-next-steps)**

## Media/path config overlap

The current site still splits media-related config between:

- `_config.yml` for public site/media origins
- `_data/pipeline.json` for local pipeline subpaths and variant policy

That boundary is serviceable today, but it should be reviewed before another media-path refactor.

Relevant current-state docs:

- **[Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)**
- **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**

## Route-level duplication

Some route-owned values are still configured directly in page front matter rather than coming from a shared config or helper layer. The current Studio `studio_page_doc` links are one example.

This is acceptable in the current build, but it should be re-evaluated if more route-level shared links or shell metadata are added.

Relevant current-state docs:

- **[Studio Runtime](/docs/?scope=studio&doc=studio-runtime)**
- **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**

## Remaining config surfaces

If additional checked-in files become active shared config, document them here rather than leaving them only in setup notes or script docs.

The clearest candidates would be toolchain/version config files if they start affecting normal repo workflows beyond local bootstrap.
