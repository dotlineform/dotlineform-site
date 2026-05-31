const DOCUMENT_SHELL_MOUNT_SELECTOR = "[data-docs-viewer-document-shell-mount]";

export function documentShellMount(root) {
  if (!root) return null;
  return root.querySelector(DOCUMENT_SHELL_MOUNT_SELECTOR);
}

export function renderDocsViewerDocumentShell(options = {}) {
  const documentRef = options.document || document;
  const mount = options.mount || null;
  if (!mount) return findDocsViewerDocumentShellRefs({ document: documentRef, root: options.root });

  const main = documentRef.createElement("article");
  main.className = "docsViewer__main";
  main.setAttribute("aria-live", "polite");

  const meta = documentRef.createElement("div");
  meta.className = "docsViewer__meta";
  meta.id = "docsViewerMeta";
  meta.hidden = true;

  const metaRow = documentRef.createElement("div");
  metaRow.className = "docsViewer__metaRow";

  const metaCopy = documentRef.createElement("div");
  metaCopy.className = "docsViewer__metaCopy";
  metaCopy.append(
    renderParagraph(documentRef, "docsViewerPath", "docsViewer__path small"),
    renderParagraph(documentRef, "docsViewerUpdated", "docsViewer__updated muted small"),
    renderParagraph(documentRef, "docsViewerSummary", "docsViewer__summary muted small")
  );

  const metaActions = documentRef.createElement("div");
  metaActions.className = "docsViewer__metaActions";

  const statusPills = documentRef.createElement("div");
  statusPills.className = "docsViewer__statusPills";
  statusPills.id = "docsViewerStatusPills";
  statusPills.hidden = true;

  const bookmarkToggle = documentRef.createElement("button");
  bookmarkToggle.className = "docsViewer__bookmarkToggle";
  bookmarkToggle.id = "docsViewerBookmarkToggle";
  bookmarkToggle.type = "button";
  bookmarkToggle.hidden = true;
  bookmarkToggle.setAttribute("aria-label", "Add bookmark");
  bookmarkToggle.setAttribute("aria-pressed", "false");
  bookmarkToggle.title = "Add bookmark";
  bookmarkToggle.textContent = "☆";

  metaActions.append(statusPills, bookmarkToggle);
  metaRow.append(metaCopy, metaActions);
  meta.appendChild(metaRow);

  const content = documentRef.createElement("div");
  content.className = "docsViewer__content content";
  content.id = "docsViewerContent";

  const resultsStatus = documentRef.createElement("p");
  resultsStatus.className = "docsViewer__panelStatus muted small";
  resultsStatus.id = "docsViewerResultsStatus";
  resultsStatus.hidden = true;

  const results = documentRef.createElement("ol");
  results.className = "docsViewer__results";
  results.id = "docsViewerResults";
  results.hidden = true;

  const more = documentRef.createElement("div");
  more.className = "docsViewer__more";
  more.id = "docsViewerMore";
  more.hidden = true;

  main.append(meta, content, resultsStatus, results, more);
  mount.replaceChildren(main);

  return findDocsViewerDocumentShellRefs({ document: documentRef, root: mount });
}

export function findDocsViewerDocumentShellRefs(options = {}) {
  const documentRef = options.document || document;
  const root = options.root || documentRef;
  return {
    main: root.querySelector(".docsViewer__main"),
    meta: root.querySelector("#docsViewerMeta"),
    pathEl: root.querySelector("#docsViewerPath"),
    updatedEl: root.querySelector("#docsViewerUpdated"),
    summaryEl: root.querySelector("#docsViewerSummary"),
    statusPills: root.querySelector("#docsViewerStatusPills"),
    bookmarkToggle: root.querySelector("#docsViewerBookmarkToggle"),
    content: root.querySelector("#docsViewerContent"),
    resultsStatus: root.querySelector("#docsViewerResultsStatus"),
    results: root.querySelector("#docsViewerResults"),
    more: root.querySelector("#docsViewerMore")
  };
}

export function applyDocsViewerDocumentShellProjection(options = {}) {
  const refs = options.refs || {};
  const projection = options.projection || {};

  applyHidden(refs.meta, projection, "metaHidden");
  applyHidden(refs.content, projection, "contentHidden");
  applyHidden(refs.resultsStatus, projection, "resultsStatusHidden");
  applyHidden(refs.results, projection, "resultsHidden");
  applyHidden(refs.more, projection, "moreHidden");
  if (refs.resultsStatus) {
    if (Object.prototype.hasOwnProperty.call(projection, "resultsStatusText")) {
      refs.resultsStatus.textContent = String(projection.resultsStatusText || "");
    }
    if (Object.prototype.hasOwnProperty.call(projection, "resultsStatusError")) {
      refs.resultsStatus.classList.toggle("is-error", Boolean(projection.resultsStatusError));
    }
  }

  if (refs.more && projection.clearMore) {
    refs.more.innerHTML = "";
  }
}

function renderParagraph(documentRef, id, className) {
  const paragraph = documentRef.createElement("p");
  paragraph.className = className;
  paragraph.id = id;
  return paragraph;
}

function applyHidden(element, projection, key) {
  if (!element || !Object.prototype.hasOwnProperty.call(projection, key)) return;
  element.hidden = Boolean(projection[key]);
}
