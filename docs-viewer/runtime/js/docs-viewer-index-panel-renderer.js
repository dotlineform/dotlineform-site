const INDEX_PANEL_MOUNT_SELECTOR = "[data-docs-viewer-index-panel-mount]";
const SIDEBAR_TOGGLE_ICON_CLASS = "docsViewer__sidebarToggleIcon";

export function indexPanelMount(root) {
  if (!root) return null;
  return root.querySelector(INDEX_PANEL_MOUNT_SELECTOR);
}

export function renderDocsViewerIndexPanelShell(options = {}) {
  const documentRef = options.document || document;
  const mount = options.mount || null;
  if (!mount) return findDocsViewerIndexPanelRefs({ document: documentRef, root: options.root });

  const aside = documentRef.createElement("aside");
  aside.className = "docsViewer__sidebar";
  aside.setAttribute("aria-label", "Docs index");

  const inner = documentRef.createElement("div");
  inner.className = "docsViewer__sidebarInner";

  const header = documentRef.createElement("div");
  header.className = "docsViewer__sidebarHeader";

  const sidebarToggle = renderSidebarToggle(documentRef, {
    id: "docsViewerSidebarToggle",
    label: "Collapse docs index",
    icon: "‹"
  });
  const sidebarExpand = renderSidebarToggle(documentRef, {
    id: "docsViewerSidebarExpand",
    label: "Expand docs index",
    icon: "⤢"
  });

  const nav = documentRef.createElement("nav");
  nav.className = "docsViewer__nav";
  nav.id = "docsViewerNav";
  nav.setAttribute("aria-label", "Docs tree");

  header.append(sidebarToggle, sidebarExpand);
  inner.append(header, nav);
  aside.appendChild(inner);
  mount.replaceChildren(aside);

  return findDocsViewerIndexPanelRefs({ document: documentRef, root: mount });
}

export function findDocsViewerIndexPanelRefs(options = {}) {
  const documentRef = options.document || document;
  const root = options.root || documentRef;
  return {
    sidebar: root.querySelector(".docsViewer__sidebar"),
    nav: root.querySelector("#docsViewerNav"),
    sidebarToggle: root.querySelector("#docsViewerSidebarToggle"),
    sidebarExpand: root.querySelector("#docsViewerSidebarExpand")
  };
}

export function applyDocsViewerIndexPanelProjection(options = {}) {
  const root = options.root || null;
  const refs = options.refs || {};
  const projection = options.projection || {};
  if (root) {
    root.dataset.indexPanelState = projection.activeState || "normal";
  }
  applyToggleProjection(refs.sidebarExpand, {
    hidden: projection.expandHidden,
    ariaExpanded: projection.expandAriaExpanded,
    label: projection.expandLabel,
    icon: projection.expandIcon
  });
  applyToggleProjection(refs.sidebarToggle, {
    hidden: projection.stepHidden,
    ariaExpanded: projection.stepAriaExpanded,
    label: projection.stepLabel,
    icon: projection.stepIcon
  });
}

function renderSidebarToggle(documentRef, options) {
  const button = documentRef.createElement("button");
  button.className = "docsViewer__sidebarToggle";
  button.type = "button";
  button.id = options.id;
  button.setAttribute("aria-controls", "docsViewerNav");
  button.setAttribute("aria-expanded", "true");
  button.setAttribute("aria-label", options.label);
  button.title = options.label;

  const icon = documentRef.createElement("span");
  icon.className = SIDEBAR_TOGGLE_ICON_CLASS;
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = options.icon;
  button.appendChild(icon);

  return button;
}

function applyToggleProjection(button, options) {
  if (!button) return;
  button.hidden = Boolean(options.hidden);
  button.setAttribute("aria-expanded", options.ariaExpanded || "true");
  button.setAttribute("aria-label", options.label || "");
  button.title = options.label || "";
  const icon = button.querySelector("." + SIDEBAR_TOGGLE_ICON_CLASS);
  if (icon) {
    icon.textContent = options.icon || "";
  }
}
