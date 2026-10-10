import { documentTargetKey } from "./docs-viewer-document-target.js";
function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function mapGet(map, key) {
  return map && typeof map.get === "function" ? map.get(key) : null;
}

function objectRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function activeManagedDocument(value) {
  var context = objectRecord(value);
  var target = objectRecord(context && context.documentTarget);
  var record = objectRecord(context && context.documentRecord);
  var collection = cleanString(target && target.collection).toLowerCase();
  var docId = cleanString(target && target.doc_id);
  if (
    !target || !docId
    || cleanString(record && record.doc_id) !== docId
  ) return null;
  return Object.freeze({
    record: Object.freeze(Object.assign({}, record, { doc_id: docId })),
    target: Object.freeze(collection ? { collection: collection, doc_id: docId } : { doc_id: docId })
  });
}

function selectedPayloadMetadata(payload, appContext, docId) {
  var record = objectRecord(payload);
  if (!record) return null;
  if (appContext && appContext.kind === "public") {
    return {
      doc_id: cleanString(record.doc_id) || cleanString(docId),
      title: cleanString(record.title),
      summary: cleanString(record.summary),
      date: cleanString(record.date),
      date_display: cleanString(record.date_display),
      added_date: cleanString(record.added_date),
      last_updated: cleanString(record.last_updated)
    };
  }
  var metadata = {
    doc_id: cleanString(record.doc_id) || cleanString(docId),
    title: cleanString(record.title),
    summary: cleanString(record.summary),
    parent_id: cleanString(record.parent_id),
    date: cleanString(record.date),
    date_display: cleanString(record.date_display),
    added_date: cleanString(record.added_date),
    last_updated: cleanString(record.last_updated),
    ui_status: cleanString(record.ui_status),
    viewer_url: cleanString(record.viewer_url)
  };
  return metadata;
}

export function resolveDocsViewerSelectedDoc(options = {}) {
  const selectedDocId = cleanString(options.selectedDocId);
  if (!selectedDocId) return null;
  return mapGet(options.docsById, selectedDocId) || null;
}

export function docsViewerStatusLabel(value, uiStatusByValue) {
  const statusValue = cleanString(value);
  if (!statusValue) return "";
  const statusRecord = mapGet(uiStatusByValue, statusValue);
  if (!statusRecord) return statusValue;
  return cleanString(statusRecord.label) || statusValue;
}

export function createDocsViewerHostedViewContext(options = {}) {
  const appContext = options.appContext || {};
  const managedDocument = activeManagedDocument(
    options.managedDocumentContext
  );
  const selectedDoc = managedDocument
    ? managedDocument.record
    : options.selectedDoc || resolveDocsViewerSelectedDoc(options);
  const docId = selectedDoc ? cleanString(selectedDoc.doc_id) : "";
  const payload = docId ? mapGet(options.payloadCache, documentTargetKey(managedDocument ? managedDocument.target : options.sourceTarget || { doc_id: docId })) || null : null;
  const selectedMetadata = selectedPayloadMetadata(
    managedDocument ? managedDocument.record : payload,
    appContext,
    docId
  );
  const trail = selectedDoc && !(managedDocument && managedDocument.target.collection) && typeof options.buildTrail === "function"
    ? options.buildTrail(docId).slice(0, -1)
    : [];
  const canonicalUrl = selectedDoc && typeof options.viewerUrl === "function"
    ? options.viewerUrl(docId, "", "", managedDocument ? managedDocument.target : {})
    : "";

  return {
    appContext: appContext,
    canonicalUrl: canonicalUrl,
    collectionProvider: options.collectionProvider || null,
    managedDocumentTarget: managedDocument ? managedDocument.target : null,
    parentTrail: trail,
    payload: payload,
    selectedDoc: selectedDoc,
    selectedMetadata: selectedMetadata,
    sourceTarget: managedDocument ? managedDocument.target : options.sourceTarget || null,
    sourceEditorServices: appContext.serviceAvailability && appContext.serviceAvailability.source && appContext.serviceAvailability.source.available
      ? options.sourceEditorServices || null
      : null,
    statusLabel: docsViewerStatusLabel(selectedMetadata && selectedMetadata.ui_status, options.uiStatusByValue)
  };
}

function noop() {}

export function createDocsViewerMainViewModuleContext(options = {}) {
  const base = createDocsViewerHostedViewContext(options);
  const mainView = options.mainView && typeof options.mainView === "object" ? options.mainView : {};

  const context = Object.assign({}, base, {
    mount: options.mount || null,
    mainView: {
      activeViewId: cleanString(mainView.activeViewId),
      projectControlState: typeof mainView.projectControlState === "function" ? mainView.projectControlState : noop,
      projectToolbar: typeof mainView.projectToolbar === "function" ? mainView.projectToolbar : noop,
      requestView: typeof mainView.requestView === "function" ? mainView.requestView : function () { return false; },
      showWarning: typeof mainView.showWarning === "function" ? mainView.showWarning : noop
    },
    requestedViewId: cleanString(options.requestedViewId),
    requestReason: cleanString(options.requestReason),
    targetContext: options.targetContext && typeof options.targetContext === "object"
      ? options.targetContext
      : null
  });
  return context;
}

export function createDocsViewerDocumentDisplayModeContext(options = {}) {
  const base = createDocsViewerHostedViewContext(options);
  const documentView = options.documentView && typeof options.documentView === "object" ? options.documentView : {};

  const context = Object.assign({}, base, {
    mount: options.mount || null,
    root: options.root || null,
    documentView: {
      activeModeId: cleanString(documentView.activeModeId),
      projectToolbar: typeof documentView.projectToolbar === "function" ? documentView.projectToolbar : noop,
      requestMode: typeof documentView.requestMode === "function" ? documentView.requestMode : function () { return false; },
      showWarning: typeof documentView.showWarning === "function" ? documentView.showWarning : noop
    },
    requestedModeId: cleanString(options.requestedModeId)
  });
  return context;
}
