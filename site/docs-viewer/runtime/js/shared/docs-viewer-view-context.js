function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function mapGet(map, key) {
  return map && typeof map.get === "function" ? map.get(key) : null;
}

function objectRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function selectedPayloadMetadata(payload, access, docId) {
  var record = objectRecord(payload);
  if (!record) return null;
  if (access && access.publicReadOnly) {
    return {
      title: cleanString(record.title),
      summary: cleanString(record.summary),
      last_updated: cleanString(record.last_updated)
    };
  }
  return {
    doc_id: cleanString(record.doc_id) || cleanString(docId),
    title: cleanString(record.title),
    summary: cleanString(record.summary),
    parent_id: cleanString(record.parent_id),
    added_date: cleanString(record.added_date),
    last_updated: cleanString(record.last_updated),
    ui_status: cleanString(record.ui_status),
    viewable: record.viewable === false ? false : true,
    viewer_url: cleanString(record.viewer_url)
  };
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
  const access = {
    allowManagement: Boolean(routeAccess.allowManagement),
    publicReadOnly: Boolean(routeAccess.publicReadOnly),
    routeType: cleanString(routeAccess.routeType)
  };
  const payload = docId ? mapGet(options.payloadCache, docId) || null : null;
  const selectedMetadata = selectedPayloadMetadata(payload, access, docId);
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
    access: access,
    canonicalUrl: canonicalUrl,
    parentTrail: trail,
    payload: payload,
    selectedDoc: selectedDoc,
    selectedMetadata: selectedMetadata,
    statusLabel: docsViewerStatusLabel(selectedMetadata && selectedMetadata.ui_status, options.uiStatusByValue),
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

export function createDocsViewerDocumentDisplayModeContext(options = {}) {
  const base = createDocsViewerHostedViewContext(options);
  const routeAccess = options.routeAccess || {};
  const documentView = options.documentView && typeof options.documentView === "object" ? options.documentView : {};

  const context = Object.assign({}, base, {
    mount: options.mount || null,
    documentView: {
      activeModeId: cleanString(documentView.activeModeId),
      projectToolbar: typeof documentView.projectToolbar === "function" ? documentView.projectToolbar : noop,
      requestMode: typeof documentView.requestMode === "function" ? documentView.requestMode : function () { return false; },
      showWarning: typeof documentView.showWarning === "function" ? documentView.showWarning : noop
    },
    requestedModeId: cleanString(options.requestedModeId)
  });
  if (routeAccess.allowManagement) {
    context.sourceEditorServices = options.sourceEditorServices || null;
  }
  return context;
}
