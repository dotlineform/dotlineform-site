function appendAppViewerControlsMount(documentRef, toolbar) {
  var mount = documentRef.createElement("div");
  mount.className = "docsViewer__viewerAppControls";
  mount.hidden = true;
  mount.setAttribute("data-docs-viewer-control-surface-mount", "app-viewer");
  toolbar.appendChild(mount);
  return mount;
}

export function renderDocsViewerViewerToolbar(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var mount = settings.mount || null;
  if (!mount) return null;

  var toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewer__viewerToolbar";
  toolbar.id = "docsViewerViewerToolbar";
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "Viewer controls");

  appendAppViewerControlsMount(documentRef, toolbar);

  mount.appendChild(toolbar);
  return toolbar;
}
