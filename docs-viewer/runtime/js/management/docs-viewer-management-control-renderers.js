import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

function renderDocumentActionButton(context, options) {
  var settings = options || {};
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.id = settings.id || "";
    button.type = "button";
  }
  var artwork = typeof settings.artwork === "function"
    ? settings.artwork(context.control.state || {})
    : settings.artwork;
  button.className = "docsViewer__toolbarIconButton";
  button.replaceChildren();
  if (artwork) button.appendChild(createDocsViewerToolbarIcon(context.document, artwork));
  return button;
}

function selectionCommandButton(documentRef, command, label) {
  var button = documentRef.createElement("button");
  button.type = "button";
  button.className = "docsViewer__indexSelectionButton";
  button.dataset.docsViewerSelectionCommand = command;
  button.textContent = label;
  return button;
}

function renderIndexSelectionControl(context) {
  var state = context.control.state || {};
  var disabled = Boolean(state.disabled);
  var total = Number.isFinite(Number(state.total)) ? Number(state.total) : 0;
  var hasSelection = Boolean(state.hasSelection);
  var allSelected = Boolean(state.allSelected);
  var root = context.existingRoot;
  if (!root || root.tagName !== "DIV") {
    root = context.document.createElement("div");
    root.className = "docsViewer__indexSelectionControl";
    root.setAttribute("role", "group");
    root.setAttribute("aria-label", "Index selection");
  }

  var selectAllButton = selectionCommandButton(context.document, "select-all", "All");
  selectAllButton.disabled = disabled || total === 0 || allSelected;
  var clearButton = selectionCommandButton(context.document, "clear", "Clear");
  clearButton.disabled = disabled || !hasSelection;
  var doneButton = selectionCommandButton(context.document, "done", "Done");
  doneButton.disabled = disabled;
  root.replaceChildren(selectAllButton, clearButton, doneButton);
  return { root: root, interactive: doneButton };
}

var INDEX_ACTION_ITEMS = [
  {
    id: "docsViewerIndexExportButton",
    actionId: "export-docs",
    artwork: "docsViewer__icon--square-arrow-right-exit",
    label: "Export…"
  },
  {
    id: "docsViewerIndexPreparePackageButton",
    actionId: "prepare-document-package",
    artwork: "docsViewer__icon--package",
    label: "Prepare package…"
  },
  {
    id: "docsViewerIndexDeleteButton",
    actionId: "delete",
    artwork: "docsViewer__icon--trash",
    label: "Delete…"
  }
];

function indexActionItem(documentRef, definition) {
  var button = documentRef.createElement("button");
  button.className = "docsViewer__actionMenuItem";
  button.type = "button";
  button.id = definition.id;
  button.setAttribute("role", "menuitem");
  button.dataset.docsViewerAction = definition.actionId;
  var icon = createDocsViewerToolbarIcon(documentRef, definition.artwork);
  var label = documentRef.createElement("span");
  label.className = "docsViewer__actionMenuLabel";
  label.textContent = definition.label;
  button.replaceChildren(icon, label);
  return button;
}

function renderIndexActionsControl(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerIndexActionsButton")) {
    root = context.document.createElement("div");
    root.className = "docsViewer__indexActionsHost";
    var button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.type = "button";
    button.id = "docsViewerIndexActionsButton";
    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", "docsViewerIndexActionsMenu");
    button.setAttribute("aria-label", "Index actions");
    button.title = "Index actions";
    button.appendChild(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--wrench"));
    var menu = context.document.createElement("div");
    menu.className = "docsViewer__actionsMenu docsViewer__indexActionsMenu";
    menu.id = "docsViewerIndexActionsMenu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    INDEX_ACTION_ITEMS.forEach(function (definition) {
      menu.appendChild(indexActionItem(context.document, definition));
    });
    root.replaceChildren(button, menu);
  }

  var state = context.control.state || {};
  var itemStates = state.items || {};
  INDEX_ACTION_ITEMS.forEach(function (definition) {
    var item = root.querySelector("#" + definition.id);
    var itemState = itemStates[definition.actionId] || {};
    var reason = String(itemState.disabledReason || "").trim();
    var accessibleLabel = reason ? definition.label + " " + reason : definition.label;
    item.disabled = Boolean(itemState.disabled);
    item.hidden = Boolean(itemState.hidden);
    item.title = accessibleLabel;
    item.setAttribute("aria-label", accessibleLabel);
    if (reason) item.dataset.docsViewerDisabledReason = reason;
    else delete item.dataset.docsViewerDisabledReason;
  });
  return { root: root, interactive: root.querySelector("#docsViewerIndexActionsButton") };
}

export function createDocsViewerManagementControlRenderers() {
  return {
    "manage-index-selection": renderIndexSelectionControl,
    "manage-index-actions": renderIndexActionsControl,
    "manage-index-position": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerIndexPositionButton",
        artwork: "docsViewer__icon--arrow-up-down"
      });
    },
    "manage-edit": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageEditButton",
        artwork: "docsViewer__icon--pen"
      });
    },
    "manage-draft": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageDraftButton",
        artwork: function (state) { return state.pressed === true ? "docsViewer__icon--circle-dashed-check" : "docsViewer__icon--circle-check"; }
      });
    },
    "manage-selected": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSelectedButton",
        artwork: function (state) { return state.pressed === true ? "docsViewer__icon--star-filled" : "docsViewer__icon--star"; }
      });
    },
    "manage-open-vscode": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageOpenVsCodeButton",
        artwork: "docsViewer__icon--file-code-corner"
      });
    },
    "return-to-doc": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageReturnToDocButton",
        artwork: "docsViewer__icon--corner-down-left"
      });
    },
    "markdown-source-save": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceSaveButton",
        artwork: "docsViewer__icon--download"
      });
    },
    "source-add-image": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceAddImageButton",
        artwork: "docsViewer__icon--image"
      });
    },
    "source-add-file": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceAddFileButton",
        artwork: "docsViewer__icon--paperclip"
      });
    }
  };
}
