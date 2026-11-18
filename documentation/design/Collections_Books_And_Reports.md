---
draft: false
doc_id: d-20261118-204400-19c8f3
title: Collections Books And Reports
added_date: "2026-11-18 20:44:00"
last_updated: "2026-11-18"
summary: Rationale for independent collection hosts, curated Book placement and separate report compositions.
parent_id: d-20261118-151521-a0f9c3
---
# Collections, Books and reports

## Keep placement independent of content ownership

An ordinary Index host lets an editor place the entry to a collection alongside other documents. Moving that entry can change its ancestor eligibility while the collection's IDs, storage and reader routes stay fixed. Keeping the report declaration independent of the registered collection also lets a document present a view without granting it authority over the viewed data. [Host reparenting delivery](../deliveries/Sub_Scope_Report_Reparenting.md) · [Current host behaviour](../reference/Collections_And_Books.md#reachability-is-not-ownership)

## Use one Book order for different audiences

Library keeps the independent source material. Book working copies can preserve provenance and adopt the media needed for their own lifecycle. The Tree owns editorial placement and keeps private Sections available for research and drafting. Draft answers whether a page is ready. Placement and edition answer where a ready page belongs. Keeping these choices independent lets the author stage ready material and derive both the TOC and exact web membership from one saved order. The export sequence can reuse the same placements while including export-only matter. [Current editions](../reference/Collections_And_Books.md#book-editions) · [Book delivery evidence](../deliveries/Collections_Books_And_Reports_Review.md)

## Compose a report around its data and adopter

Shared report modules can prepare and render supplied data without taking on local authority. A Manage contribution can add actions and private inputs without changing the public import graph. Public safety describes the implementation and its transitive dependencies. Public composition describes which entrypoints import its code or load its stylesheet. Public adoption requires an actual report using it with an explicit data projection and loader. Keeping those decisions separate avoids loading unused controls or making private metadata public simply because the view is read-only. [Current composition](../reference/Reports.md#composition-and-capabilities) · [Earlier contribution design](../deliveries/Sub_Scope_Customisation_Architecture.md)
