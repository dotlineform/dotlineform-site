---
doc_id: data-models-catalogue-indexes
title: Catalogue Indexes And Payloads
added_date: 2026-05-19
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Indexes And Payloads

## Public Read Models

| Artifact | Purpose | Main consumers |
| --- | --- | --- |
| `site/assets/data/series_index.json` | published Series identity, ordering, primary Work, and ordered membership | Series index, Work navigation, Studio Works |
| `site/assets/data/works_index.json` | lightweight Work identity, title, year, and Series membership | public/Studio Work lists and Series grids |
| `site/assets/data/recent_index.json` | publication snapshots for recent additions | `/recent/` |
| `site/assets/series/index/<series_id>.json` | selected Series metadata and optional rendered prose | Series selection runtime |
| `site/assets/works/index/<work_id>.json` | selected Work metadata, optional rendered prose, downloads, links, and grouped details | Work and Work-detail runtimes |
| `site/assets/data/search/catalogue/index.json` | flat search records for current catalogue kinds | `/catalogue/search/` |

These are generated payloads. Their schema builders under `studio/services/catalogue/catalogue_generation_*.py` and the consuming route modules are the exact authority.

## Why There Are Aggregate And Per-Record Files

Lists need many small records; selected routes need one rich record.

- A Series grid can combine `series_index.json` and `works_index.json` without loading every Work payload.
- A selected Work loads one Work payload containing its local detail sections.
- A selected detail derives its parent Work from `detail_uid` and reuses that Work payload rather than requiring a global detail index.
- Search uses its own flattened representation instead of forcing list or selected-record payloads to carry search-only text.

## Studio Read Models

Studio also uses `studio/data/generated/catalogue-lookup/` for Work and Series search plus Series-focused list data. Rich focused Work/detail payloads are built by the catalogue service at read time.

This distinction is intentional:

- generated list data is cheap to serve and cache;
- service projections can combine current canonical data and generated context without creating another per-record file family;
- the browser still has one logical configuration map in `studio-config.json`.

## Publication And Versioning

Public indexes include published runtime data and stable content versions needed by their consumers. Per-Work payloads carry confirmed media versions where primary remote media can be independently replaced. Aggregate indexes generally point to repo-owned thumbnails and do not need those primary-media version fields.

Recent entries are publication snapshots rather than a normalized view of current titles. That is why recent history remains a separate artifact.

## Moments Boundary

Moments now use the public Docs Viewer `moments` scope and its generated docs/search payloads. They are not a current Local Studio catalogue source or editor family, and the current catalogue search index contains Series and Works.

Do not restore retired Moment catalogue payloads merely because older generator helpers or documents still mention them. Follow the active Moments scope and code authority.

## Change Rule

- list/card or cross-record context: change the appropriate aggregate serializer;
- selected Series content: change the Series record serializer;
- selected Work or detail content: change the Work record/section serializer;
- search-visible content: change the catalogue search builder;
- Studio-only editing/search context: change the lookup or focused service projection.

Then update the field registry so build and lookup planning selects the affected artifact family.
