function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function mapGet(map, key) {
  return map && typeof map.get === "function" ? map.get(key) : null;
}

export function resolveDocsViewerSelectedDoc(options = {}) {
  const selectedDocId = cleanString(options.selectedDocId);
  if (!selectedDocId) return null;
  return mapGet(options.docsById, selectedDocId) || mapGet(options.allDocsById, selectedDocId) || null;
}

export function docsViewerStatusLabel(value, uiStatusByValue) {
  const statusValue = cleanString(value);
  if (!statusValue) return "";
  const statusRecord = mapGet(uiStatusByValue, statusValue);
  if (!statusRecord) return statusValue;
  const emoji = cleanString(statusRecord.emoji);
  const label = cleanString(statusRecord.label) || statusValue;
  return emoji ? `${emoji} ${label}` : label;
}

export function createDocsViewerHostedViewContext(options = {}) {
  const selectedDoc = options.selectedDoc || resolveDocsViewerSelectedDoc(options);
  const docId = selectedDoc ? cleanString(selectedDoc.doc_id) : "";
  const routeAccess = options.routeAccess || {};
  const trail = selectedDoc && typeof options.buildTrail === "function"
    ? options.buildTrail(docId).slice(0, -1)
    : [];
  const targetDocId = selectedDoc && typeof options.viewerTargetDocId === "function"
    ? options.viewerTargetDocId(docId)
    : docId;
  const canonicalUrl = selectedDoc && typeof options.viewerUrl === "function"
    ? options.viewerUrl(targetDocId)
    : "";

  return {
    access: {
      allowManagement: Boolean(routeAccess.allowManagement),
      publicReadOnly: Boolean(routeAccess.publicReadOnly),
      routeType: cleanString(routeAccess.routeType)
    },
    canonicalUrl: canonicalUrl,
    parentTrail: trail,
    payload: docId ? mapGet(options.payloadCache, docId) || null : null,
    selectedDoc: selectedDoc,
    statusLabel: docsViewerStatusLabel(selectedDoc && selectedDoc.ui_status, options.uiStatusByValue),
    viewerScope: cleanString(options.viewerScope)
  };
}

function noop() {}

export function createDocsViewerMainViewModuleContext(options = {}) {
  const base = createDocsViewerHostedViewContext(options);
  const routeAccess = options.routeAccess || {};
  const mainView = options.mainView && typeof options.mainView === "object" ? options.mainView : {};

  const context = Object.assign({}, base, {
    mount: options.mount || null,
    mainView: {
      activeViewId: cleanString(mainView.activeViewId),
      projectToolbar: typeof mainView.projectToolbar === "function" ? mainView.projectToolbar : noop,
      requestView: typeof mainView.requestView === "function" ? mainView.requestView : function () { return false; },
      showWarning: typeof mainView.showWarning === "function" ? mainView.showWarning : noop
    },
    requestedViewId: cleanString(options.requestedViewId)
  });
  if (routeAccess.allowManagement) {
    context.sourceEditorServices = options.sourceEditorServices || null;
  }
  return context;
}
