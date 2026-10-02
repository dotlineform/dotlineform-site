---
draft: false
doc_id: d-20260716-204013-3be4e1
title: Button Placement
added_date: "2026-07-16 20:40:13"
last_updated: "2026-10-02 12:15:13"
parent_id: d-20260424-000000-50b63f
---
# Button Placement

## Outcome

Docs Viewer puts a control where the user understands its action to be happening. The object of the action chooses the surface; frequency, importance, and desired discoverability choose whether the control is direct or deliberately secondary.

This feature owns that user-facing mental model. The control registry, action targets, controller boundaries, and server authority remain technical concerns owned elsewhere.

## Placement Model

| User is acting on… | Primary placement |
| --- | --- |
| The displayed document and its parent/child structure | Index panel toolbar |
| The right-clicked row, with deliberately secondary discovery | Index panel context menu |
| New, VS Code, Draft/Ready or Star for the displayed document/collection | Context group in Manage Actions |
| Rendered document presentation, editing, or display mode | Document toolbar |
| The workspace or application as a whole | Workspace group in Manage Actions |

The index toolbar is visible only while the index panel is open. Collapsing the panel hides the complete `index-view` control surface, including every current and future index action. The restore control remains visible because it is panel chrome outside that toolbar.

The index context menu acts on the row that was right-clicked, even when another document remains active and displayed. Opening it does not change the active document or the target of Index Actions. This explicit invoked-document target is why the menu can contain unique, rarely used row commands rather than merely duplicating shortcuts for the selected node.

A toolbar control is not justified only by frequency: it may deserve direct placement because it expresses a central operation on that surface.

Whether an action writes data does not choose its placement. Placement follows the user's object of attention; capability projection and the server still decide whether the operation is available and authorized.

## Terminology

| Term | Meaning |
| --- | --- |
| action | one operation with one behavioural owner |
| control | a visible button, toggle, or menu item that invokes an action |
| placement | the surface on which a control appears |
| target | the document set, invoked document, active document, or scope the action operates on |
| active document | the document currently displayed by the route |
| invoked document | the tree row from which a context-menu command was opened; it need not be the active document |
| checked documents | the explicit checkbox set used by Collection Actions |
| promotion | making an existing action directly visible on another appropriate surface without duplicating its behaviour |

In user-facing discussion, **index toolbar** means the toolbar belonging to the active index tree; its technical surface id is `index-view`. **Document toolbar** means the toolbar belonging to the active rendered-document view; its technical surface id is `main-view`. **Manage toolbar** means the app-level management surface. **Actions** is a menu within that toolbar, not another name for the entire surface.

## Examples

### Index Document Actions

The **🛠️ Index Actions** menu operates on the currently displayed ordinary document and all its descendants. **Export…**, **Prepare package…**, and **Delete…** share that target, including children hidden within collapsed branches. Opening the menu does not create selection state, and the Index has no checkboxes or All/Clear/Done controls.

Collection Actions retain their own checked-document workflow. The app-level **Actions** menu contains a context group for New, Open in VS Code, Draft/Ready and Star, then a workspace group for Import, Export, Rebuild docs and Search, Publish and Settings. Unavailable items remain visible and disabled. [Toolbar Model](Toolbar_Model.md#manage-toolbar) owns exact targets and Catalogue exceptions.

[Create And Import Endpoints](Create_And_Import_Endpoints.md) owns the server contract.

### Open in VS Code

**Open in VS Code** is available in the main Actions menu for the exact displayed ordinary document, collection-list host or validated collection subdocument. In Source mode it uses the editor's captured target. The Index context-menu item remains available because it operates directly on an invoked row without first opening that document.

Both placements invoke the same source-opening service. The Index context menu supplies its invoked ordinary document; the main Actions context owner supplies an exact ordinary or collection target. Neither placement changes the other's target.

## Current Boundary

The placement language, displayed-subtree Index Actions and context-aware main Actions menu are shipped. New, VS Code, Draft/Ready and Star have no duplicate document or collection-toolbar controls. Collection checkbox selection remains owned by its mounted report.

## Technical Homes

[Toolbar Model](Toolbar_Model.md) and [Panel Hosts and Control Surfaces](Panel_Hosts_And_Control_Surfaces.md) own surface registration, placement projection, and invocation context. [Runtime Module Ownership](Runtime_Module_Ownership.md) owns the action-definition and focused-controller seam used by source opening.
