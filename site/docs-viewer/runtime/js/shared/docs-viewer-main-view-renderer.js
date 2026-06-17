const MAIN_VIEW_MOUNT_SELECTOR = "[data-docs-viewer-main-view-mount]";

export function mainViewMount(root) {
  if (!root) return null;
  return root.querySelector(MAIN_VIEW_MOUNT_SELECTOR);
}

export function renderDocsViewerMainView(options = {}) {
  const documentRef = options.document || document;
  const mount = options.mount || null;
  if (!mount) return findDocsViewerMainViewRefs({ document: documentRef, root: options.root });

  const main = documentRef.createElement("article");
  main.className = "docsViewer__main";
  main.setAttribute("aria-live", "polite");
  main.setAttribute("data-docs-viewer-panel", "main");

  const toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewer__mainViewToolbar";
  toolbar.id = "docsViewerMainViewToolbar";
  toolbar.hidden = true;
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "Document controls");

  const path = renderParagraph(documentRef, "docsViewerPath", "docsViewer__path small");
  path.hidden = true;

  const actions = documentRef.createElement("div");
  actions.className = "docsViewer__mainViewToolbarActions";

  const infoToggle = documentRef.createElement("button");
  infoToggle.className = "docsViewer__infoToggle";
  infoToggle.id = "docsViewerInfoToggle";
  infoToggle.type = "button";
  infoToggle.hidden = true;
  infoToggle.setAttribute("aria-label", "Show document info");
  infoToggle.setAttribute("aria-expanded", "false");
  infoToggle.title = "Show document info";
  infoToggle.textContent = "i";

  const bookmarkToggle = documentRef.createElement("button");
  bookmarkToggle.className = "docsViewer__bookmarkToggle";
  bookmarkToggle.id = "docsViewerBookmarkToggle";
  bookmarkToggle.type = "button";
  bookmarkToggle.hidden = true;
  bookmarkToggle.setAttribute("aria-label", "Add bookmark");
  bookmarkToggle.setAttribute("aria-pressed", "false");
  bookmarkToggle.title = "Add bookmark";
  bookmarkToggle.textContent = "☆";

  actions.append(bookmarkToggle, infoToggle);
  toolbar.append(path, actions);

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

  main.append(toolbar, content, resultsStatus, results, more);
  mount.replaceChildren(main);

  return findDocsViewerMainViewRefs({ document: documentRef, root: mount });
}

export function findDocsViewerMainViewRefs(options = {}) {
  const documentRef = options.document || document;
  const root = options.root || documentRef;
  return {
    main: root.querySelector(".docsViewer__main"),
    toolbar: root.querySelector("#docsViewerMainViewToolbar"),
    pathEl: root.querySelector("#docsViewerPath"),
    infoToggle: root.querySelector("#docsViewerInfoToggle"),
    bookmarkToggle: root.querySelector("#docsViewerBookmarkToggle"),
    content: root.querySelector("#docsViewerContent"),
    resultsStatus: root.querySelector("#docsViewerResultsStatus"),
    results: root.querySelector("#docsViewerResults"),
    more: root.querySelector("#docsViewerMore")
  };
}

export function applyDocsViewerMainViewProjection(options = {}) {
  const refs = options.refs || {};
  const projection = options.projection || {};

  applyHidden(refs.toolbar, projection, "toolbarHidden");
  applyHidden(refs.content, projection, "contentHidden");
  applyHidden(refs.resultsStatus, projection, "resultsStatusHidden");
  applyHidden(refs.results, projection, "resultsHidden");
  applyHidden(refs.more, projection, "moreHidden");

  if (refs.infoToggle) {
    if (Object.prototype.hasOwnProperty.call(projection, "infoToggleHidden")) {
      refs.infoToggle.hidden = Boolean(projection.infoToggleHidden);
    }
    if (Object.prototype.hasOwnProperty.call(projection, "infoTogglePressed")) {
      refs.infoToggle.classList.toggle("is-active", Boolean(projection.infoTogglePressed));
      refs.infoToggle.setAttribute("aria-expanded", projection.infoTogglePressed ? "true" : "false");
    }
    if (Object.prototype.hasOwnProperty.call(projection, "infoToggleLabel")) {
      refs.infoToggle.setAttribute("aria-label", projection.infoToggleLabel || "Show document info");
      refs.infoToggle.title = projection.infoToggleLabel || "Show document info";
    }
  }
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
