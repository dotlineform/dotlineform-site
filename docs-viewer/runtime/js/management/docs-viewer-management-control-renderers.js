function renderDocumentActionButton(context, options) {
  var settings = options || {};
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__documentActionButton";
    button.id = settings.id || "";
    button.type = "button";
  }
  button.textContent = typeof settings.emoji === "function"
    ? settings.emoji(context.control.state || {})
    : settings.emoji || "";
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

  var selectAllButton = selectionCommandButton(context.document, "select-all", "Select all");
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
    emoji: "⬇️",
    label: "Export…"
  },
  {
    id: "docsViewerIndexPreparePackageButton",
    actionId: "prepare-document-package",
    emoji: "📦",
    label: "Prepare package…"
  },
  {
    id: "docsViewerIndexCopyButton",
    actionId: "copy",
    emoji: "⧉",
    label: "Copy to scope…"
  },
  {
    id: "docsViewerIndexMoveButton",
    actionId: "move",
    emoji: "↗",
    label: "Move to scope…"
  },
  {
    id: "docsViewerIndexDeleteButton",
    actionId: "delete",
    emoji: "🗑️",
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
  var emoji = documentRef.createElement("span");
  emoji.className = "docsViewer__actionMenuEmoji";
  emoji.setAttribute("aria-hidden", "true");
  emoji.textContent = definition.emoji;
  var label = documentRef.createElement("span");
  label.className = "docsViewer__actionMenuLabel";
  label.textContent = definition.label;
  button.replaceChildren(emoji, label);
  return button;
}

function renderIndexActionsControl(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerIndexActionsButton")) {
    root = context.document.createElement("div");
    root.className = "docsViewer__indexActionsHost";
    var button = context.document.createElement("button");
    button.className = "docsViewer__indexActionsButton";
    button.type = "button";
    button.id = "docsViewerIndexActionsButton";
    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", "docsViewerIndexActionsMenu");
    button.setAttribute("aria-label", "Index actions");
    button.title = "Index actions";
    button.textContent = "🛠️";
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
    "manage-edit": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageEditButton",
        emoji: "✏️"
      });
    },
    "manage-open-vscode": function (context) {
      var button = renderDocumentActionButton(context, {
        id: "docsViewerManageOpenVsCodeButton",
        emoji: ""
      });
      var icon = context.document.createElement("img");
      icon.src = new URL("./icons/vscode.svg", import.meta.url).href;
      icon.alt = "";
      icon.width = 20;
      icon.height = 20;
      icon.setAttribute("aria-hidden", "true");
      button.replaceChildren(icon);
      return button;
    },
    "markdown-source-entry": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceButton",
        emoji: "☰"
      });
    },
    "subdoc-source-entry": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSubdocSourceButton",
        emoji: "§"
      });
    },
    "return-to-doc": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageReturnToDocButton",
        emoji: "↩"
      });
    },
    "markdown-source-save": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceSaveButton",
        emoji: "💾"
      });
    },
    "source-add-image": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceAddImageButton",
        emoji: "🧜‍♀️"
      });
    },
    "source-add-file": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceAddFileButton",
        emoji: "📎"
      });
    }
  };
}
