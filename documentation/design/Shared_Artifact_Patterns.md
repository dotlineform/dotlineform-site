---
draft: false
doc_id: d-20260419-000000-d5b655
title: Shared Artifact Patterns
added_date: 2026-04-19 00:00:00
last_updated: "2026-11-18"
parent_id: d-20260524-214228-7247ef
---
# Shared Artifact Patterns

## Why Artifacts Are Split

A stable shell can boot a reader while lightweight navigation/discovery and exact by-ID content load independently. This avoids shipping one large runtime dump and lets each consumer acquire the contract it needs. Search has separate normalized postings because discovery fields and ranking differ from tree order or document rendering. [Current reader contracts](../reference/Generated_Data_Contracts.md)

These are complementary products rather than a serial pipeline from shell to Index to content to Search. Canonical runtime/configuration produces the installed reader; authored content and completed metadata produce its data. A direct document read can resolve by ID independently of Index membership.

## Preserve Domain Meaning

A logical Work/document identity, an authored relationship and a generated lookup are different things. Keep schema and authority with their domain owner: a Docs tree is not a Catalogue schema, and a convenient public payload cannot become an authoring record merely because it contains the same ID.

Maps suit exact identity lookup; arrays suit authored or ranked order. Header fields and cached metadata are useful where a consumer needs them. They do not establish a universal envelope, freshness audit or requirement to reconcile the whole repository. Build-time rendered HTML lets readers share prepared presentation without acquiring a Markdown authoring pipeline.

## Separate Preparation From Consumption

Working operations finish document/media/relationship effects and queue eligible public bytes. Publish transfers those selections; the static site consumes them. Runtime projection independently selects canonical code and browser configuration. This keeps source authority, public-safe content and local capability distinct. [Projection contract](../reference/Projection_Contract.md) · [Publication design](Working_Generation_And_Publication.md)

Package preparation has its own configured source/rendered-content inputs, rather than treating a reader index as the editable document set. The former standalone Data Sharing references are superseded by that [current owner](../reference/Document_Packages.md).

## Maintenance Tradeoff

One concept can span several products, so a partial operation may complete before another consumer updates. Carry known effects to the next owner and diagnose that boundary. A global graph, duplicate field inventory or blanket rebuild adds maintenance cost unless it answers a concrete question. Keep the current source/producer/consumer link in the focused reference; [Testing](../development/Verification.md) owns verification policy.

The older generic assurance checklist and its limits are [recorded with the consolidation evidence](../deliveries/Runtime_Configuration_And_Recovery_Review.md#architecture-and-entry-point-consolidation).
