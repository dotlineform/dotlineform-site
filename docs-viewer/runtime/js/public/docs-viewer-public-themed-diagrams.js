const THEMED_DIAGRAM_SELECTOR = 'img[data-docs-viewer-diagram-kind="themed-mermaid"]';
export const PUBLIC_THEME_APPLIED_EVENT = "dlf:theme-applied";

function normalizeTheme(theme) {
  return theme === "dark" ? "dark" : "light";
}

function variantUrl(diagram, theme) {
  if (!diagram || !diagram.dataset) return "";
  var value = theme === "dark"
    ? diagram.dataset.docsViewerDiagramDarkSrc
    : diagram.dataset.docsViewerDiagramLightSrc;
  var url = String(value || "").trim();
  return url.startsWith("/") ? url : "";
}

function appliedTheme(documentRef) {
  var root = documentRef ? documentRef.documentElement : null;
  return normalizeTheme(root && root.getAttribute ? root.getAttribute("data-theme") : "");
}

export function createDocsViewerPublicThemedDiagramAdapter(options) {
  var settings = options || {};
  var diagramDetailAdapter = settings.diagramDetailAdapter || null;
  var recordsByRoot = new WeakMap();
  var activeRecords = new Set();

  function releaseDocument(releaseContext) {
    var context = releaseContext || {};
    var root = context.content;
    if (!root || typeof root !== "object") return { released: 0 };
    var records = recordsByRoot.get(root) || [];
    recordsByRoot.delete(root);
    records.forEach(function (record) {
      activeRecords.delete(record);
    });
    return { released: records.length };
  }

  function selectRecord(record, theme, refreshDetail) {
    var target = variantUrl(record.diagram, theme);
    if (!target) return false;
    record.diagram.setAttribute("src", target);
    record.diagram.removeAttribute("hidden");
    if (
      refreshDetail
      && diagramDetailAdapter
      && typeof diagramDetailAdapter.refreshPersistentDiagram === "function"
    ) {
      diagramDetailAdapter.refreshPersistentDiagram({
        content: record.root,
        diagram: record.diagram,
        document: record.document,
        window: record.window
      });
    }
    return true;
  }

  function mountDocument(mountContext) {
    var context = mountContext || {};
    var root = context.content;
    if (!root || typeof root.querySelectorAll !== "function") {
      return { found: 0, registered: 0, skipped: 0, theme: "light" };
    }
    releaseDocument({ content: root });
    var documentRef = context.document || root.ownerDocument;
    var theme = appliedTheme(documentRef);
    var diagrams = Array.from(root.querySelectorAll(THEMED_DIAGRAM_SELECTOR));
    var records = [];
    diagrams.forEach(function (diagram) {
      if (!variantUrl(diagram, "light") || !variantUrl(diagram, "dark")) return;
      var record = {
        diagram: diagram,
        document: documentRef,
        root: root,
        window: context.window || (documentRef ? documentRef.defaultView : null)
      };
      if (!selectRecord(record, theme, false)) return;
      records.push(record);
      activeRecords.add(record);
    });
    recordsByRoot.set(root, records);
    return {
      found: diagrams.length,
      registered: records.length,
      skipped: diagrams.length - records.length,
      theme: theme
    };
  }

  function handleThemeChange(theme) {
    var normalizedTheme = normalizeTheme(theme);
    var updated = 0;
    activeRecords.forEach(function (record) {
      if (selectRecord(record, normalizedTheme, true)) updated += 1;
    });
    return { theme: normalizedTheme, updated: updated };
  }

  return {
    handleThemeChange: handleThemeChange,
    mountDocument: mountDocument,
    releaseDocument: releaseDocument
  };
}

export function connectDocsViewerPublicThemeOwner(options) {
  var settings = options || {};
  var adapter = settings.adapter;
  var documentRef = settings.document;
  if (
    !adapter
    || typeof adapter.handleThemeChange !== "function"
    || !documentRef
    || typeof documentRef.addEventListener !== "function"
  ) {
    return { connected: false, release: function () {} };
  }
  function handleAppliedTheme(event) {
    adapter.handleThemeChange(event && event.detail ? event.detail.theme : "");
  }
  documentRef.addEventListener(PUBLIC_THEME_APPLIED_EVENT, handleAppliedTheme);
  return {
    connected: true,
    release: function () {
      documentRef.removeEventListener(PUBLIC_THEME_APPLIED_EVENT, handleAppliedTheme);
    }
  };
}
