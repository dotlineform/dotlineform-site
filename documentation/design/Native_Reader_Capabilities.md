---
draft: false
doc_id: d-20261118-231100-379d5e
title: Native Reader Capabilities
added_date: "2026-11-18 23:11:00"
last_updated: "2026-11-18"
summary: Why the proposed native Docs Viewer grows by complete capabilities with a selected web behaviour baseline.
parent_id: d-20261013-210028-8b3c2f
---
# Native Reader Capabilities

## Align One Capability At A Time

The web apps continue to evolve. Requiring complete parity would keep a native reader unfinished; freezing both apps would obstruct useful work. The [proposed roadmap](../app/Docs_Viewer_App_Roadmap.md) instead selects a supported behaviour/resource baseline for one complete capability. Acceptance records its limits and resource revision. Later web additions become candidates for a later release; defects in supported behaviour remain bounded corrections.

A useful reader can stand alone before local generation, publication or source editing exists. Each later operation must complete its actual effects, so a source write alone cannot stand in for Save. This keeps release boundaries meaningful without requiring a general management framework first.

## Reuse Interaction, Own Native Access

The established reader and JavaScript interaction owners preserve the document model and presentation. Swift owns the shell, authorized access, native resource serving and execution required by supported operations. Bundle selected canonical resources through an owned build step; avoid a manually maintained second runtime or loading mutable repository files at launch.

The existing About message/reply host establishes a narrow native bridge, not Docs workspace support. Apple's [message/reply bridge](https://developer.apple.com/documentation/webkit/wkscriptmessagehandlerwithreply) and [resource handler](https://developer.apple.com/documentation/webkit/wkurlschemehandler) are candidate mechanisms for the first real reader path. A general filesystem abstraction or prerequisite web refactor needs a demonstrated consumer.

Direct authorized access to generated Working content and an imported app workspace remain different product choices. Configuration, media access and [iPad directory permissions](https://developer.apple.com/documentation/uikit/providing-access-to-directories) must follow that choice explicitly. Core capabilities should not conceal a local server or Python dependency; remote content and later publication have their own boundaries. Current implementation and release decisions remain in the roadmap and [App instructions](../../app/AGENTS.md).
