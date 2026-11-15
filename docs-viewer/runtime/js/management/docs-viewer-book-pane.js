import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { loadManagedCollectionReportContribution } from "./docs-viewer-management-document-reports.js";

/** Keep the Book controls outside the document mount and its Source editor. */
export function createDocsViewerBookPane(options) {
  const { root, main, window, workspaceConfigState, collectionProvider, managementDocumentActions } = options;
  if (!options.managementService?.baseUrl || !collectionProvider.readBookManifest) return;
  const document = main.ownerDocument;
  const desktop = window.matchMedia("(width > 55rem)");
  const panes = new Map();
  let book = null;
  let target = null;
  let shown = null;

  function createPane(config) {
    const pane = document.createElement("aside");
    pane.className = "docsViewerBookPane";
    pane.setAttribute("aria-label", config.title + " documents");
    const expand = document.createElement("button");
    expand.type = "button";
    expand.className = "docsViewer__toolbarIconButton docsViewerBookPane__expand";
    const reportRoot = document.createElement("section");
    reportRoot.className = "docsViewerReport";
    const body = document.createElement("div");
    body.className = "docsViewerBookPane__body";
    body.append(reportRoot);
    pane.append(body);
    main.before(pane);

    const entry = { pane, expanded: false, selectDocument: null };
    function renderExpand() {
      const label = entry.expanded ? "Restore Book pane width" : "Expand Book pane";
      expand.title = label;
      expand.setAttribute("aria-label", label);
      expand.setAttribute("aria-expanded", String(entry.expanded));
      expand.replaceChildren(createDocsViewerToolbarIcon(document, entry.expanded
        ? "docsViewer__icon--chevron-left" : "docsViewer__icon--chevron-right"));
    }
    expand.addEventListener("click", () => {
      const top = body.getBoundingClientRect().top;
      const anchor = Array.from(body.querySelectorAll("[data-report-subdoc-id]"))
        .find(row => row.getBoundingClientRect().bottom > top);
      const offset = anchor?.getBoundingClientRect().top;
      entry.expanded = !entry.expanded;
      root.dataset.bookPaneExpanded = String(entry.expanded);
      renderExpand();
      if (anchor) body.scrollTop += anchor.getBoundingClientRect().top - offset;
    });
    renderExpand();

    const host = { doc_id: config.reportHostDocId, title: config.title };
    const settings = { ...options, content: pane, managementContext: true };
    const contribution = loadManagedCollectionReportContribution(settings, { doc_id: host.doc_id }, config, {
      bookExpandControl: expand,
      onBookSelectionReady(selectDocument) {
        entry.selectDocument = selectDocument;
        selectDocument(target?.collection === config.collection ? target.doc_id : "");
      }
    });
    import("../shared/docs-collection-report.js").then(({ mountDocsCollectionReport }) => mountDocsCollectionReport({
      reportRoot,
      reportMeta: { collection: config.collection },
      doc: host,
      collectionConfig: config,
      collectionProvider,
      collectionReportContributionPromise: contribution,
      managementContext: true,
      openDocument: managementDocumentActions.openDocument,
      viewerUrlForDocument: options.viewerUrlForDocument
    })).catch(error => options.setStatus(error.message, true));
    return entry;
  }

  function render() {
    const isVisible = book && desktop.matches;
    let next = isVisible ? panes.get(book.collection) : null;
    if (isVisible && !next) {
      next = createPane(book);
      panes.set(book.collection, next);
    }
    if (shown && shown !== next) shown.pane.hidden = true;
    if (next) {
      next.pane.hidden = false;
      next.selectDocument?.(target.collection ? target.doc_id : "");
    }
    shown = next;
    root.dataset.bookPane = next ? "split" : "";
    root.dataset.bookPaneExpanded = String(Boolean(next?.expanded));
  }
  desktop.addEventListener("change", render);

  return function project(documentTarget) {
    target = documentTarget;
    const config = workspaceConfigState.activeConfig;
    const collection = target && options.isActive() && (target.collection
      ? config.collectionsById.get(target.collection)
      : config.collections.find(item => item.reportHostDocId === target.doc_id));
    book = collection?.collectionType === "curated-book" ? collection : null;
    render();
  };
}
