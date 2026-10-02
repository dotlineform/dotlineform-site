import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";

var ACTION_IDS = DOCS_VIEWER_ACTION_IDS;

var MANAGEMENT_ACTION_MENU_ITEMS = [
  {
    id: "docsViewerManageNewButton",
    actionId: ACTION_IDS.NEW,
    artwork: "docsViewer__icon--file",
    label: "New"
  },
  {
    id: "docsViewerManageImportButton",
    actionId: ACTION_IDS.IMPORT,
    artwork: "docsViewer__icon--import",
    label: "Import",
    separatorBefore: true
  },
  {
    id: "docsViewerManageExportWorkspaceButton",
    actionId: ACTION_IDS.EXPORT_WORKSPACE,
    artwork: "docsViewer__icon--square-arrow-right-exit",
    label: "Export"
  },
  {
    id: "docsViewerManageRebuildButton",
    actionId: ACTION_IDS.REBUILD_DOCS,
    artwork: "docsViewer__icon--refresh-cw",
    label: "Rebuild docs and Search"
  },
  {
    id: "docsViewerManagePublishButton",
    actionId: ACTION_IDS.PUBLISH,
    artwork: "docsViewer__icon--globe",
    label: "Publish"
  },
  {
    id: "docsViewerManageSettingsButton",
    actionId: ACTION_IDS.SETTINGS,
    artwork: "docsViewer__icon--settings",
    label: "Settings"
  }
];

function renderActionMenuItem(documentRef, item) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__actionMenuItem";
  button.id = item.id;
  button.type = "button";
  button.disabled = true;
  button.dataset.docsViewerAction = item.actionId;
  button.setAttribute("role", "menuitem");
  button.setAttribute("aria-label", item.label);
  button.title = item.label;
  var label = documentRef.createElement("span");
  label.className = "docsViewer__actionMenuLabel";
  label.textContent = item.label;
  button.append(createDocsViewerToolbarIcon(documentRef, item.artwork), label);
  return button;
}

function renderManagementActionsMenu(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerManageActionsButton")) {
    root = context.document.createElement("div");
    root.className = "docsViewer__actionsMenuHost";
    var button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.id = "docsViewerManageActionsButton";
    button.type = "button";
    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", "docsViewerManageActionsMenu");
    button.appendChild(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--wrench"));
    var menu = context.document.createElement("div");
    menu.className = "docsViewer__actionsMenu";
    menu.id = "docsViewerManageActionsMenu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    MANAGEMENT_ACTION_MENU_ITEMS.forEach(function (item) {
      if (item.separatorBefore) {
        var separator = context.document.createElement("div");
        separator.className = "docsViewer__actionMenuSeparator";
        separator.setAttribute("role", "separator");
        menu.appendChild(separator);
      }
      menu.appendChild(renderActionMenuItem(context.document, item));
    });
    root.append(button, menu);
  }
  return { root: root, interactive: root.querySelector("#docsViewerManageActionsButton") };
}

/** Project a visible menu action; disabled reasons belong to its tooltip. */
export function projectDocsViewerManagementActionMenuItem(menu, actionId, state) {
  if (!menu) return;
  var button = menu.querySelector('[data-docs-viewer-action="' + actionId + '"]');
  if (!button) return;
  button.disabled = Boolean(state.disabled);
  button.title = state.reason || state.label;
  button.setAttribute("aria-label", state.label);
  button.querySelector(".docsViewer__actionMenuLabel").textContent = state.label;
  if (typeof state.checked === "boolean") button.setAttribute("aria-checked", String(state.checked));
  if (state.artwork) {
    button.querySelector(".docsViewer__toolbarIcon").replaceWith(
      createDocsViewerToolbarIcon(button.ownerDocument, state.artwork)
    );
  }
}

export function createDocsViewerManagementAppControlRenderers() {
  return {
    "manage-actions-menu": renderManagementActionsMenu
  };
}
