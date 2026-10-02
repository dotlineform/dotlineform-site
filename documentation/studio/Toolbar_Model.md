---
draft: false
doc_id: d-20260531-152622-ed2451
title: Toolbar Model
added_date: 2026-05-31 15:26:22
last_updated: "2026-10-02 13:52:21"
summary: Placement and ownership rules for app, active-view, docs_subscope, management, and context-panel controls.
parent_id: d-20260424-000000-50b63f

---
# Docs Viewer Toolbar Model

This document answers one question: where should a Docs Viewer control live?

The placement owner does not decide whether a control is available or what operation it performs. The view registry projects eligibility; stable surface hosts render contributed controls; controllers and action definitions own behaviour.

## Top Bar

```text
top bar
  +-- viewer toolbar
  +-- active main-view toolbar
  +-- manage toolbar
```

The top bar is a fluid layout container. It provides ordered mounts and may wrap whole toolbar groups when desktop window space is constrained. It owns no commands and does not establish mobile support for local routes; the public composition owns its responsive acceptance separately.

## Viewer Toolbar

Use the viewer toolbar for collection-reading and top-level index-view selection controls that are not tied to the selected document or a write workflow.

Current examples are search, recently added, and the index-view toggle. Panel-local collapse and expand controls remain in index-panel chrome. A control can appear only on manage routes and still belong here when its purpose is changing the reading surface rather than performing management.

Surface: `app-viewer`, mounted by `docs-viewer-viewer-toolbar-renderer.js` and rendered by the shared control-surface host.

## Main-View Toolbar

Use the main-view toolbar for controls belonging to the active central view, its content, or its current display mode.

For `rendered-document`, this includes its breadcrumb, info control and manage-only **Edit document** dropdown. Its items are Source editor, Open in VS Code, Draft/Ready, Star, Copy link, Delete, Assign Subject and Open in Finder, in that order. Source editor opens the complete Markdown buffer for the exact ordinary document, collection-list host or validated collection detail. Copy link uses that same displayed identity. Delete retains ordinary subtree confirmation or the collection's singular validated-detail workflow; Catalogue detail deletion stays disabled. Assign Subject and Open in Finder retain the configured subject-aware collection rules, with Finder requiring a valid Folder subject. Unsupported items remain visible and disabled. Collection detail contributions supply their existing live state and handlers inside this menu instead of duplicate toolbar buttons. A detail has no parent Source action.

New stays in the Manage Actions menu. Source mode registers only Return to doc, Save Markdown source and Directives, in that order on one row at the document's left edge. Directives opens to the right and contains Add image, Add Catalogue image, Add file, Add Media View link, Insert doc link and Open in VS Code. A separator groups Table detail, Insert related links and Insert icon in the same flat list. Source and management owners project loaded/busy availability; unavailable entries remain disabled. The menu captures the mounted adapter and selection, while VS Code uses that adapter's immutable target. There are no duplicate standalone insertion buttons. [Source Editor Scripts](Source_Editor_Scripts.md) owns the workflows.

For `content-detail`, the same surface supplies the public-safe **Back to document** control and presentation label; later Manage-only table tools may contribute beside them without creating another toolbar.

The shared renderer creates one stable `main-view` mount. Shared and manage entrypoints contribute eligible controls to the same host in definition order.

In Manage, Edit document retains the pen artwork and aligns to the right edge of the centered document and collection report using the shared document-width token. Its dropdown opens to the left; Source editor uses `square-code.svg`. Its existing view/mode eligibility hides it in expanded content views and Source mode. Disclosure closes when the target or availability changes. Delete and Subject modals restore focus to the Edit trigger. Actions retains its app-toolbar position.

Owners: `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js`, shared control renderers, and manage-owned `docs-viewer-management-control-renderers.js`.

## Manage Toolbar

The Manage toolbar exposes one **Actions** menu. Its first group contains context-aware New. Its second group contains Import, Export, Rebuild docs and Search, Publish and Settings. Open in VS Code, Draft/Ready and Star appear only in Edit for the displayed document. These actions have no duplicate main-view or collection-toolbar buttons. Unavailable menu items remain visible and disabled; their tooltips explain the reason. The Actions entrypoint retains route, service and busy gating.

Context-aware targets across Actions and Edit:

| Action | Menu | Ordinary document | Collection list | Validated collection detail |
| --- | --- | --- | --- | --- |
| New | Actions | Creates a sibling after the displayed document, or a root document when none is selected | Creates a member of the displayed collection | Creates a member of the displayed collection |
| Open in VS Code | Edit | Opens the exact displayed document source | Opens the ordinary collection report host source | Opens the exact collection subdocument source |
| Draft/Ready | Edit | Marks the displayed document ready or draft | Marks the ordinary report host ready or draft | Marks the exact subdocument ready or draft |
| Star | Edit | Toggles the displayed document's Selected Documents membership | Toggles the ordinary report host's membership | Toggles the exact subdocument's membership |

New is disabled in Catalogue lists and details because regeneration owns creation. Draft/Ready is disabled for Catalogue subdocuments because their Publish eligibility is fixed; the ordinary Catalogue report host retains its own readiness. Documents excluded by `unpublishable.json` retain disabled readiness controls. Draft/Ready changes eligibility for a later Publish and does not publish immediately. Star uses outline/filled artwork, an explicit menu checkbox state and the next-action labels Star/Remove star.

Loading or invalid collection details disable target-dependent actions without falling back to the report host. Edit, including VS Code, Draft/Ready and Star, is hidden in Source and expanded views; Source has its own VS Code item in Directives, and New keeps its existing app-level availability. The mounted collection report owns the immediate projection of a committed draft save and refresh/open after creation. Independently invoked Index context-menu commands retain their explicit row targets.

The workspace Actions dropdown aligns to the button's right edge and opens to the left, keeping it inside the desktop window when the button sits near the right side of the top row.

Its mount exists only when route access allows management UI. Individual operations remain capability-gated and server-authorized.

Surface: `app-management`. Manage definitions, renderer contributions, focused controllers, and action definitions remain outside the public/review import graph.

## Sub-Scope Report Controls

Collection-specific list controls stay in the report. The shared report owns title search and Back. Its standard Manage contribution owns the title/recency sort toggle, collection Actions and selection commands, Prepare Package, Copy Link, and validated-detail Delete. Copy Link and Delete are contributed to Edit; configured Subject and Finder actions join them there. New uses Actions; Draft/Ready uses Edit. Both consume the report's published context, and Import consumes its explicitly published collection.

The collection list's package-selection Actions menu stays in the report's filter toolbar alongside sort and selection commands. It does not mount beside Home in the top row. Its checkbox-based subdocument package preparation remains separate from the Index right-click menu's ordinary-document package preparation.

A configured collection may select one registered customisation. Its controls
render only in the composition positions supplied for that collection; they
do not insert DOM into the default toolbar or become app controls. Any added
action must register its placement, explicit collection/selection/validated
detail target, capability, empty-state, and refresh effect before dispatch.

A collection detail creates its action host once when opening the detail shell. Manage portals that host into Edit while the document is rendered and retains it in the hidden collection-action mount during Source or expanded views. The report's internal `detail-toolbar` contribution position still owns exact targets and lifecycle. A generated document-content refresh updates the body, metadata and Info without recreating the actions. Source mode retains the mounted report beneath its editor so entering or leaving Source does not invalidate the report's target or controls.

## Context Panel Chrome

The info/context panel owns only panel chrome such as status and close. The outside document or mode context chooses the hosted info view; do not add an internal toolbar merely to switch context.

A hosted view may render controls inside its own body when they operate on that view's content. Those are view UI, not top-bar controls.

## Placement Test

1. Does it change collection reading or select the active index view? Put it in the viewer toolbar.
2. Does it resize, collapse, or otherwise operate on one panel? Put it in that panel's chrome.
3. Does it act on tree structure, hierarchy, or a subtree? Put it in the index-view toolbar; use the index context menu for deliberately secondary invoked-row commands.
4. Does it operate on the active main view or document mode? Put it in the main-view toolbar. Document actions, including VS Code, Draft/Ready and Star, use Edit; New remains in Manage Actions.
5. Does it act on the workspace or application as a whole? Put it in Manage Actions.
6. Does it operate only inside one mounted sub-scope collection? Put it in the
   default or registered report contribution position.
7. Does it operate only inside one hosted view? Let that view render it inside its mount.

Do not choose placement based on which module currently has convenient DOM access.

## Weak Spots

- Definition order is presentation order; do not reintroduce post-render DOM insertion.
- Commands appearing in more than one placement must resolve the same action definition and invocation context before dispatch.
- At supported desktop widths, wrap toolbar groups before interleaving unrelated controls; public responsive rules own any narrower fallback.
- Visibility, pressed state, dirty state, and busy state come from focused control-state projections; the toolbar model is not a global UI-state owner.

[Button Placement](Button_Placement.md) owns the user-facing mental model and terminology. [Panel Hosts and Control Surfaces](Panel_Hosts_And_Control_Surfaces.md) owns the registry, hosts, state, dispatch, action-context, and lifecycle model behind these placements.
