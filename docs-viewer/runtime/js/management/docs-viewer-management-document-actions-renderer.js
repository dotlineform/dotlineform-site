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
  if (settings.action) button.dataset.docsViewerAction = settings.action;
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

  var editButton = renderDocumentActionButton(documentRef, {
    id: "docsViewerManageEditButton",
    action: "edit",
    emoji: "✏️",
    label: "Edit"
  });

  var sourceButton = renderDocumentActionButton(documentRef, {
    id: "docsViewerManageSourceButton",
    action: "markdown-source",
    emoji: "☰",
    label: "Markdown source"
  });

  var bookmark = bookmarkToggle(root);
  if (bookmark && bookmark.parentElement === mount) {
    mount.insertBefore(editButton, bookmark);
    mount.insertBefore(sourceButton, bookmark);
  } else {
    mount.prepend(editButton, sourceButton);
  }

  return {
    editButton: editButton,
    sourceButton: sourceButton
  };
}
