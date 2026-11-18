---
draft: false
doc_id: d-20261118-191221-7a5d03
title: Studio And Catalogue Ownership
added_date: "2026-11-18 19:12:21"
last_updated: "2026-11-18"
summary: Rationale for canonical relationship ownership, browser authoring and explicit Save/Refresh handoffs.
parent_id: d-20261118-151521-a0f9c3
---
# Studio and Catalogue ownership

## Keep relationships explicit

Work identity, Series assignment, direct Gallery membership and Series–Gallery relevance answer different editorial questions. Keeping separate sources lets a Gallery span Series and lets a Series suggest a relevant Gallery while preserving its curated members. Converting Details into ordinary Works removed the special parent/section lifecycle. Descriptive Medium text now carries materials, process and support in one authored value. [Current model](../reference/Catalogue_Source_Model.md) · [Original model discussion](../deliveries/Catalogue_Data_Model.md)

## Let the browser finish authoring choices

The mounted editor already holds the draft and saved choice maps. It owns field completion, bulk membership choices, empty-Series deletion availability and unsaved-state decisions. Python owns exact identity and request boundaries, persistence, confined files and required media work. Passing the completed before/after state and known relationships into Save completion gives queue selection an explicit source. [Implementation trace](../reference/Catalogue_Services.md) · [Editor](../reference/Catalogue_Work_Editor.md)

## Make saved state usable before reader adoption

Live canonical projections let the editor reflect a completed Save immediately. Selected prepared media has a staging flag that keeps the saved preview usable until Refresh hands it to Working. The explicit updates queue records which effects need that handoff. Refresh can load the selected dependencies and preserve unselected generated rows. Docs Viewer then adopts the ready Work facts into documents before Publish transfers finished units. [Lifecycle](../reference/Catalogue_Save_And_Refresh.md)

## Keep composition and evidence with their owners

Studio's shell composes a validated template and route script. Domain controllers and services perform the operation. Private reports read saved projections through Docs Viewer's local authority and keep curator context with those inputs. Current references describe these owners, and the delivery record retains the cutovers and manual evidence still relevant to diagnosis. [Studio composition](../reference/Studio.md) · [Review evidence](../deliveries/Studio_And_Catalogue_Ownership_Review.md)
