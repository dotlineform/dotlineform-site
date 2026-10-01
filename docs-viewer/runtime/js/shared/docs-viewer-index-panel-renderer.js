const INDEX_PANEL_MOUNT_SELECTOR = "[data-docs-viewer-index-panel-mount]";

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

  const listControls = documentRef.createElement("div");
  listControls.className = "docsViewer__indexListControls";
  listControls.setAttribute("data-docs-viewer-control-surface-mount", "index-lists");
  listControls.hidden = true;

  const viewControls = documentRef.createElement("div");
  viewControls.className = "docsViewer__indexViewControls";
  viewControls.hidden = true;
  viewControls.setAttribute("data-docs-viewer-control-surface-mount", "index-view");

  const nav = documentRef.createElement("nav");
  nav.className = "docsViewer__nav";
  nav.id = "docsViewerNav";
  nav.setAttribute("aria-label", "Docs tree");

  const placeholder = documentRef.createElement("div");
  placeholder.className = "docsViewer__indexPlaceholder";
  placeholder.id = "docsViewerIndexPlaceholder";
  placeholder.hidden = true;

  const resultsView = documentRef.createElement("section");
  resultsView.className = "docsViewer__indexResults";
  resultsView.hidden = true;
  resultsView.setAttribute("aria-label", "Document results");
  const resultsStatus = documentRef.createElement("p");
  resultsStatus.className = "docsViewer__panelStatus muted small";
  resultsStatus.id = "docsViewerResultsStatus";
  resultsStatus.setAttribute("role", "status");
  resultsStatus.hidden = true;
  const results = documentRef.createElement("ol");
  results.className = "docsViewer__results";
  results.id = "docsViewerResults";
  const more = documentRef.createElement("div");
  more.className = "docsViewer__more";
  more.id = "docsViewerMore";
  more.hidden = true;
  resultsView.append(resultsStatus, results, more);

  header.append(listControls, viewControls);
  inner.append(header, nav, resultsView, placeholder);
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
    listControls: root.querySelector('[data-docs-viewer-control-surface-mount="index-lists"]'),
    resultsView: root.querySelector(".docsViewer__indexResults"),
    resultsStatus: root.querySelector("#docsViewerResultsStatus"),
    results: root.querySelector("#docsViewerResults"),
    more: root.querySelector("#docsViewerMore"),
    indexPlaceholder: root.querySelector("#docsViewerIndexPlaceholder"),
    viewControls: root.querySelector('[data-docs-viewer-control-surface-mount="index-view"]')
  };
}

export function applyDocsViewerIndexPanelProjection(options = {}) {
  const root = options.root || null;
  const refs = options.refs || {};
  const projection = options.projection || {};
  if (root) {
    root.dataset.indexPanelView = projection.activeViewId || "";
  }
  if (refs.nav) refs.nav.hidden = Boolean(projection.treeHidden);
  if (refs.resultsView) {
    refs.resultsView.hidden = projection.activeViewRenderer !== "index-results";
    refs.resultsView.setAttribute("aria-label", projection.activeViewLabel || "Document results");
  }
  if (refs.indexPlaceholder) {
    refs.indexPlaceholder.hidden = Boolean(projection.placeholderHidden);
    refs.indexPlaceholder.textContent = projection.placeholderText || "";
  }
}
