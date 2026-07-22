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
  var active = Boolean(state.active);
  var disabled = Boolean(state.disabled);
  var count = Number.isFinite(Number(state.count)) ? Number(state.count) : 0;
  var total = Number.isFinite(Number(state.total)) ? Number(state.total) : 0;
  var root = context.existingRoot;
  if (!root || root.tagName !== "DIV") {
    root = context.document.createElement("div");
    root.className = "docsViewer__indexSelectionControl";
    root.setAttribute("role", "group");
    root.setAttribute("aria-label", "Index selection");
  }

  if (!active) {
    var selectButton = selectionCommandButton(context.document, "enter", "Select");
    selectButton.disabled = disabled;
    root.replaceChildren(selectButton);
    return { root: root, interactive: selectButton };
  }

  var countLabel = context.document.createElement("output");
  countLabel.className = "docsViewer__indexSelectionCount";
  countLabel.setAttribute("aria-live", "polite");
  countLabel.textContent = count + " selected";
  var selectAllButton = selectionCommandButton(context.document, "select-all", "Select all");
  selectAllButton.disabled = disabled || total === 0 || count === total;
  var clearButton = selectionCommandButton(context.document, "clear", "Clear");
  clearButton.disabled = disabled || count === 0;
  var doneButton = selectionCommandButton(context.document, "done", "Done");
  doneButton.disabled = disabled;
  root.replaceChildren(countLabel, selectAllButton, clearButton, doneButton);
  return { root: root, interactive: doneButton };
}

export function createDocsViewerManagementControlRenderers() {
  return {
    "manage-index-selection": renderIndexSelectionControl,
    "manage-copy-subtree": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageCopySubtreeButton",
        emoji: "⧉"
      });
    },
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
    "markdown-source-toggle": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceButton",
        emoji: function (state) { return state.pressed ? "📄" : "☰"; }
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
