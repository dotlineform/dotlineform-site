const INFO_PANEL_MOUNT_SELECTOR = "[data-docs-viewer-info-panel-mount]";

export function infoPanelMount(root) {
  if (!root) return null;
  return root.querySelector(INFO_PANEL_MOUNT_SELECTOR);
}

export function renderDocsViewerInfoPanelShell(options = {}) {
  const documentRef = options.document || document;
  const mount = options.mount || null;
  if (!mount) return findDocsViewerInfoPanelRefs({ document: documentRef, root: options.root });

  const panel = documentRef.createElement("aside");
  panel.className = "docsViewer__infoPanel";
  panel.id = "docsViewerInfoPanel";
  panel.hidden = true;
  panel.setAttribute("aria-labelledby", "docsViewerInfoPanelTitle");
  panel.setAttribute("data-docs-viewer-panel", "info");

  const header = documentRef.createElement("div");
  header.className = "docsViewer__infoPanelHeader";

  const copy = documentRef.createElement("div");
  copy.className = "docsViewer__infoPanelHeaderCopy";

  const title = documentRef.createElement("h2");
  title.className = "docsViewer__infoPanelTitle";
  title.id = "docsViewerInfoPanelTitle";
  title.textContent = "Info";

  const label = documentRef.createElement("p");
  label.className = "docsViewer__infoPanelLabel muted small";
  label.id = "docsViewerInfoPanelLabel";
  label.textContent = "Document metadata";

  copy.append(title, label);

  const closeButton = documentRef.createElement("button");
  closeButton.className = "docsViewer__infoPanelClose";
  closeButton.id = "docsViewerInfoPanelClose";
  closeButton.type = "button";
  closeButton.setAttribute("aria-label", "Hide info panel");
  closeButton.title = "Hide info panel";
  closeButton.textContent = "×";

  header.append(copy, closeButton);

  const status = documentRef.createElement("p");
  status.className = "docsViewer__panelStatus muted small";
  status.id = "docsViewerInfoPanelStatus";
  status.hidden = true;

  const body = documentRef.createElement("div");
  body.className = "docsViewer__infoPanelBody";
  body.id = "docsViewerInfoPanelBody";
  body.setAttribute("data-docs-viewer-hosted-view-mount", "metadata-info");

  panel.append(header, status, body);
  mount.replaceChildren(panel);

  return findDocsViewerInfoPanelRefs({ document: documentRef, root: mount });
}

export function findDocsViewerInfoPanelRefs(options = {}) {
  const documentRef = options.document || document;
  const root = options.root || documentRef;
  return {
    panel: root.querySelector("#docsViewerInfoPanel"),
    title: root.querySelector("#docsViewerInfoPanelTitle"),
    label: root.querySelector("#docsViewerInfoPanelLabel"),
    closeButton: root.querySelector("#docsViewerInfoPanelClose"),
    status: root.querySelector("#docsViewerInfoPanelStatus"),
    body: root.querySelector("#docsViewerInfoPanelBody")
  };
}

export function applyDocsViewerInfoPanelProjection(options = {}) {
  const root = options.root || null;
  const refs = options.refs || {};
  const projection = options.projection || {};
  const visible = Boolean(projection.visible);
  const state = visible ? "open" : "closed";

  if (root && root.dataset) {
    root.dataset.infoPanelState = state;
    root.dataset.viewerLayout = projection.layout || (visible ? "index-document-info" : "index-document");
  }

  if (refs.panel) {
    refs.panel.hidden = !visible;
    refs.panel.dataset.infoPanelState = state;
    refs.panel.dataset.activeViewId = projection.activeViewId || "";
  }
  if (refs.title && Object.prototype.hasOwnProperty.call(projection, "title")) {
    refs.title.textContent = projection.title || "Info";
  }
  if (refs.label && Object.prototype.hasOwnProperty.call(projection, "label")) {
    refs.label.textContent = projection.label || "";
    refs.label.hidden = !projection.label;
  }
  if (refs.status) {
    if (Object.prototype.hasOwnProperty.call(projection, "statusText")) {
      refs.status.textContent = projection.statusText || "";
    }
    if (Object.prototype.hasOwnProperty.call(projection, "statusHidden")) {
      refs.status.hidden = Boolean(projection.statusHidden);
    }
    if (Object.prototype.hasOwnProperty.call(projection, "statusError")) {
      refs.status.classList.toggle("is-error", Boolean(projection.statusError));
    }
  }
}
