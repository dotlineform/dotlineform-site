function mainViewToolbarActionsMount(root) {
  if (!root) return null;
  return root.querySelector(".docsViewer__mainViewToolbarActions");
}

function bookmarkToggle(root) {
  if (!root) return null;
  return root.querySelector("#docsViewerBookmarkToggle");
}

function renderDocumentActionButton(documentRef, options) {
  var settings = options || {};
  var button = documentRef.createElement("button");
  button.className = "docsViewer__documentActionButton";
  button.id = settings.id || "";
  button.type = "button";
  button.hidden = true;
  if (settings.actionId) button.dataset.docsViewerAction = settings.actionId;
  button.setAttribute("aria-label", settings.label || "");
  button.title = settings.label || "";
  button.textContent = settings.emoji || "";
  return button;
}

export function renderDocsViewerManagementDocumentActions(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var root = settings.root || documentRef;
  var mount = settings.mount || mainViewToolbarActionsMount(root);
  if (!mount) return null;

  var controls = settings.viewRegistry
    ? settings.viewRegistry.listControls({ ownerViewId: "rendered-document" }).filter(function (control) {
        return control.available;
      })
    : [];
  var buttonsByRenderer = new Map();
  controls.forEach(function (control) {
    var optionsByRenderer = {
      "manage-edit": { id: "docsViewerManageEditButton", emoji: "✏️" },
      "markdown-source-toggle": { id: "docsViewerManageSourceButton", emoji: "☰" },
      "markdown-source-save": { id: "docsViewerManageSourceSaveButton", emoji: "💾" }
    };
    var buttonOptions = optionsByRenderer[control.renderer];
    if (!buttonOptions) return;
    buttonsByRenderer.set(control.renderer, renderDocumentActionButton(documentRef, Object.assign({}, buttonOptions, {
      actionId: control.actionId,
      label: control.label
    })));
  });
  var editButton = buttonsByRenderer.get("manage-edit") || null;
  var sourceButton = buttonsByRenderer.get("markdown-source-toggle") || null;
  var sourceSaveButton = buttonsByRenderer.get("markdown-source-save") || null;

  var buttons = [editButton, sourceSaveButton, sourceButton].filter(Boolean);

  var bookmark = bookmarkToggle(root);
  if (bookmark && bookmark.parentElement === mount) {
    buttons.forEach(function (button) {
      mount.insertBefore(button, bookmark);
    });
  } else {
    mount.prepend.apply(mount, buttons);
  }

  return {
    editButton: editButton,
    sourceSaveButton: sourceSaveButton,
    sourceButton: sourceButton
  };
}
