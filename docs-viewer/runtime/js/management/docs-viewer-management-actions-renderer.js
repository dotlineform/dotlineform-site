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
    label: "Import"
  },
  {
    id: "docsViewerManageExportWorkspaceButton",
    actionId: ACTION_IDS.EXPORT_WORKSPACE,
    artwork: "docsViewer__icon--square-arrow-right-exit",
    label: "Export"
  },
  {
    id: "docsViewerManageNewCollectionButton",
    actionId: ACTION_IDS.NEW_COLLECTION,
    artwork: "docsViewer__icon--folder",
    label: "New collection",
    hidden: true
  },
  {
    id: "docsViewerManageDeleteCollectionButton",
    actionId: ACTION_IDS.DELETE_COLLECTION,
    artwork: "docsViewer__icon--folder-x",
    label: "Delete collection",
    hidden: true
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
  button.hidden = Boolean(item.hidden);
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

function renderActionButton(context, options) {
  var settings = options || {};
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
  }
  button.className = "docsViewer__toolbarIconButton";
  button.id = settings.id || "";
  button.type = "button";
  button.replaceChildren(createDocsViewerToolbarIcon(context.document, settings.artwork));
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
      menu.appendChild(renderActionMenuItem(context.document, item));
    });
    root.append(button, menu);
  }
  return { root: root, interactive: root.querySelector("#docsViewerManageActionsButton") };
}

export function createDocsViewerManagementAppControlRenderers() {
  return {
    "manage-toolbar-import": function (context) {
      return renderActionButton(context, {
        id: "docsViewerManageToolbarImportButton",
        artwork: "docsViewer__icon--import"
      });
    },
    "manage-actions-menu": renderManagementActionsMenu,
    "manage-toolbar-rebuild": function (context) {
      return renderActionButton(context, {
        id: "docsViewerManageRebuildButton",
        artwork: "docsViewer__icon--refresh-cw"
      });
    },
    "manage-toolbar-publish": function (context) {
      return renderActionButton(context, {
        id: "docsViewerManageToolbarPublishButton",
        artwork: "docsViewer__icon--globe"
      });
    },
    "manage-toolbar-pre-publish": function (context) {
      return renderActionButton(context, {
        id: "docsViewerManagePrePublishButton",
        artwork: "docsViewer__icon--book-up"
      });
    },
    "manage-stage-select": function (context) {
      var root = context.existingRoot || context.document.createElement("div");
      root.className = "docsViewer__stageButtons";
      root.dataset.docsViewerStages = "true";
      root.setAttribute("role", "group");
      return root;
    }
  };
}
