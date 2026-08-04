function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function mapGet(map, key) {
  return map && typeof map.get === "function" ? map.get(key) : null;
}

function objectRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function normalizeMetadataInfo(value) {
  var record = objectRecord(value);
  if (!record) return null;
  var fields = (Array.isArray(record.fields) ? record.fields : []).map(function (rawField) {
    var field = objectRecord(rawField);
    var id = cleanString(field && field.id);
    var label = cleanString(field && field.label);
    var valueText = cleanString(field && field.value);
    if (!/^[a-z][a-z0-9_]*$/.test(id) || !label || !valueText) return null;
    return Object.freeze({
      detail: cleanString(field.detail),
      id: id,
      label: label,
      state: cleanString(field.state),
      value: valueText
    });
  }).filter(Boolean);
  var actions = objectRecord(record.actions);
  return Object.freeze({
    actions: Object.freeze({
      assignSubject: Boolean(actions && actions.assignSubject === true)
    }),
    fields: Object.freeze(fields)
  });
}

function activeManagedDocument(value, appContext) {
  if (!appContext || appContext.kind !== "manage") return null;
  var context = objectRecord(value);
  var target = objectRecord(context && context.subdocTarget);
  var record = objectRecord(context && context.subdocRecord);
  var targetKeys = Object.keys(target || {}).sort();
  var scope = cleanString(target && target.scope).toLowerCase();
  var subScope = cleanString(target && target.sub_scope).toLowerCase();
  var docId = cleanString(target && target.doc_id);
  if (
    cleanString(context && context.state).toLowerCase() !== "detail"
    || targetKeys.length !== 3
    || targetKeys[0] !== "doc_id"
    || targetKeys[1] !== "scope"
    || targetKeys[2] !== "sub_scope"
    || !scope
    || !subScope
    || !docId
    || cleanString(record && record.doc_id) !== docId
  ) return null;
  return Object.freeze({
    info: normalizeMetadataInfo(context.subdocInfo),
    record: Object.freeze(Object.assign({}, record, { doc_id: docId })),
    target: Object.freeze({ scope: scope, sub_scope: subScope, doc_id: docId })
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
  return {
    doc_id: cleanString(record.doc_id) || cleanString(docId),
    title: cleanString(record.title),
    summary: cleanString(record.summary),
    parent_id: cleanString(record.parent_id),
    date: cleanString(record.date),
    date_display: cleanString(record.date_display),
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
  const appContext = options.appContext || {};
  const managedDocument = activeManagedDocument(
    options.managedDocumentContext,
    appContext
  );
  const selectedDoc = managedDocument
    ? managedDocument.record
    : options.selectedDoc || resolveDocsViewerSelectedDoc(options);
  const docId = selectedDoc ? cleanString(selectedDoc.doc_id) : "";
  const payload = docId ? mapGet(options.payloadCache, docId) || null : null;
  const selectedMetadata = selectedPayloadMetadata(
    managedDocument ? managedDocument.record : payload,
    appContext,
    docId
  );
  const trail = selectedDoc && !managedDocument && typeof options.buildTrail === "function"
    ? options.buildTrail(docId).slice(0, -1)
    : [];
  const targetDocId = selectedDoc && !managedDocument && typeof options.viewerTargetDocId === "function"
    ? options.viewerTargetDocId(docId)
    : docId;
  const canonicalUrl = selectedDoc && !managedDocument && typeof options.viewerUrl === "function"
    ? options.viewerUrl(targetDocId)
    : "";

  return {
    appContext: appContext,
    canonicalUrl: canonicalUrl,
    collectionProvider: options.collectionProvider || null,
    managedDocumentTarget: managedDocument ? managedDocument.target : null,
    metadataInfo: managedDocument ? managedDocument.info : null,
    parentTrail: trail,
    payload: payload,
    selectedDoc: selectedDoc,
    selectedMetadata: selectedMetadata,
    sourceTarget: managedDocument ? managedDocument.target : options.sourceTarget || null,
    sourceEditorServices: appContext.serviceAvailability && appContext.serviceAvailability.source && appContext.serviceAvailability.source.available
      ? options.sourceEditorServices || null
      : null,
    statusLabel: docsViewerStatusLabel(selectedMetadata && selectedMetadata.ui_status, options.uiStatusByValue),
    viewerScope: cleanString(options.viewerScope)
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
