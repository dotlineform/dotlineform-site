---
draft: false
doc_id: d-20260802-205910-533be0
title: Catalogue Data Model Map
added_date: "2026-08-02 20:59:10"
last_updated: "2026-11-18"
summary: Current Catalogue canonical relationships, live Studio views and explicitly refreshed Docs and public projections.
ui_status: stable
parent_id: d-20260802-123451-d0e52e
---
# Catalogue Data Model Map

## Purpose

Each Work has one Series and may belong to any number of Galleries. Series–Gallery relevance is authored separately from direct Work membership. This lets a Series surface a relevant Gallery without putting all its Works in that Gallery. A document can refer to a Work without changing either relationship. [Catalogue Source Model](Catalogue_Source_Model.md#relationships-and-identity) · [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md#catalogue-identity-and-document-associations)

## Diagram

```mermaid
flowchart TB
    accTitle: Catalogue source and reader projections
    accDescr: Studio reads canonical Catalogue records and Save queues known changes with staged media. Refresh prepares selected Working files and Regenerate builds Catalogue documents. Publish transfers selected finished outputs through Preview.
    subgraph canonical["Canonical Catalogue authority"]
        works["Works<br/>one series_id per Work"]
        series["Series definitions"]
        galleries["Gallery definitions"]
        memberships["Direct Work–Gallery membership"]
        relevance["Series–Gallery relevance"]
    end
    editor["Studio editor"]
    updates["Updates queue and staged media"]
    refresh["Refresh Catalogue"]
    working["Selected Working records and ready media"]
    reports["Private report inputs"]
    regenerate["Regenerate Catalogue documents"]
    pending["Publication queue"]
    publish["Publish through Preview"]
    public["Repository artifact and configured public media"]
    canonical -->|"live reads"| editor
    editor -->|"Save"| canonical
    editor -->|"known effects"| updates
    updates --> refresh
    canonical -->|"selected source"| refresh
    refresh --> working --> regenerate
    refresh --> reports
    refresh -->|"finished shared output"| pending
    regenerate -->|"completed Work units"| pending
    pending --> publish --> public
```

## Artefact Register

| Artefact or family | Authority or producer | Reader and refresh boundary |
| --- | --- | --- |
| `studio/data/canonical/catalogue/` | Studio canonical transactions | Live editor records and lookups |
| Projects `catalogue/media-staging/` and Docs `working/catalogue-updates-pending.json` | Studio mutation completion | Exact pending changes for Refresh |
| Docs `working/generated/catalogue/` and `working/assets/works/` | Refresh Catalogue | Selected ready Working Catalogue records, indexes, media and private reports |
| Working Catalogue document source and by-ID payloads | Regenerate and exact document Build | Working Catalogue reader and completed publication selections |
| `site/assets/data/catalogue/`, `site/assets/data/docs/catalogue/` and configured R2 media | Publish through Preview | Repository artifacts reach public readers through Pages deployment. Media transfers take effect at Publish. |

Catalogue JSON and generated document payloads are replaceable outputs. The [Catalogue Source Model](Catalogue_Source_Model.md#canonical-families) lists the exact canonical families. The [payload contract](Catalogue_Indexes_And_Payloads.md#generated-read-models) lists the current generated files and their consumers.

## Change And Recovery

Save can complete while Docs readers still show the previous output. Refresh and Regenerate carry exact effects forward so a correction can resume from unfinished queue entries after the cause is fixed. Publish consumes completed selections. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#current-workflow) · [Catalogue Deployment](Catalogue_Deployment.md)
