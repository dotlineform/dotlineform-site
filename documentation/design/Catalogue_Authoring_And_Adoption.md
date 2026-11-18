---
draft: false
doc_id: d-20261118-190400-9d52d3
title: Catalogue Authoring And Adoption
added_date: "2026-11-18 19:04:00"
last_updated: "2026-11-18"
summary: Why Catalogue authoring, Working readiness, adoption and publication have separate owners.
parent_id: d-20261118-151521-a0f9c3
---
# Catalogue authoring and adoption

## One authoring owner and a separate adoption boundary

Studio can show completed authoring and staged media immediately. Keeping originals with Projects and the ready rendition set in Working gives Refresh a transfer boundary without asking the Docs reader to process originals. The Catalogue document adopts the Work's exact ID and ready presentation facts after Refresh. This keeps source, by-ID data and media selections aligned while letting Collection, Entry and Media View share one document identity. [Canonical model](../reference/Catalogue_Source_Model.md) · [Per-Work source](../deliveries/Catalogue_Per_Work_Detail_Source.md) · [Initial Regenerate delivery](../deliveries/Catalogue_Work_Regeneration.md)

## Exact items from mutation through publication

The authoring operation already knows the changed IDs and selected media, including deletion identities available before the Work disappears. Carrying these selections forward avoids rediscovering changes through another whole-Catalogue read. Completed Work readiness allows Regenerate to consume ready items, and completed adoption creates the distinct publication selection. A saved-content version can suppress an unchanged by-ID write without deciding whether a handoff is complete. Each completed unit remains useful when a later unit fails. [Targeted Regenerate decision](../deliveries/Catalogue_Changed_Regeneration_Delivery.md) · [Current lifecycle](../reference/Catalogue_Save_And_Refresh.md)

## Shared definitions travel with their actual consumers

Gallery membership expresses which Works a Gallery contains. A Series–Gallery pair expresses relevance for Works outside that membership. A rename can therefore affect two sets of Work captions, as well as the Gallery's own record and compact title rows. A description or marker stays a report field. Shared files have their own completion path so a presentation-only edit can publish after Refresh. For a release that changes both the shared title and adopted Work labels, finish Regenerate before Publish. The operator controls release timing across these independently completed selections. [Gallery rationale](Media_View_And_Document_Relationships.md) · [Generated outputs](../reference/Catalogue_Indexes_And_Payloads.md)
