import {
  DATA_SHARING_ENDPOINTS
} from "./analytics-transport.js";
import {
  usesPrepareDocumentSelection
} from "./data-sharing-prepare-workflow.js";

export async function loadDataSharingPrepareDocsState(options = {}) {
  const {
    dataDomain,
    docsScope,
    prepareCapability,
    workflowActive,
    exportConfigCount,
    loadJson = defaultLoadJson,
    onError
  } = options;

  let selectableRecordsPayload = { records: [] };
  let docsIndexError = false;

  if (
    usesPrepareDocumentSelection(prepareCapability)
    && workflowActive
    && Number(exportConfigCount || 0) > 0
    && docsScope
  ) {
    try {
      selectableRecordsPayload = await loadJson(selectableRecordsUrl(dataDomain, docsScope));
    } catch (error) {
      docsIndexError = true;
      if (typeof onError === "function") onError(error, { dataDomain, docsScope, path: selectableRecordsUrl(dataDomain, docsScope) });
    }
  }

  return {
    docsIndexError,
    ...buildVisibleDocs(selectableRecordsPayload)
  };
}

export function buildVisibleDocs(indexPayload) {
  const sourceDocs = Array.isArray(indexPayload?.records) ? indexPayload.records : [];
  const docs = sourceDocs.filter((doc) => {
    const docId = prepareRecordId(doc);
    const name = normalizeText(doc && doc.name);
    return Boolean(docId && name);
  });

  const visibleIds = new Set(docs.map((doc) => prepareRecordId(doc)));
  const childrenByParent = new Map();
  docs.forEach((doc) => {
    const parentId = normalizeText(doc.parent_id);
    const effectiveParent = visibleIds.has(parentId) ? parentId : "";
    if (!childrenByParent.has(effectiveParent)) childrenByParent.set(effectiveParent, []);
    childrenByParent.get(effectiveParent).push(doc);
  });

  const orderedDocs = [];
  const depthById = new Map();
  const visit = (parentId, depth) => {
    const children = childrenByParent.get(parentId) || [];
    children.forEach((doc) => {
      const docId = prepareRecordId(doc);
      orderedDocs.push(doc);
      depthById.set(docId, depth);
      visit(docId, depth + 1);
    });
  };
  visit("", 0);

  const orderedIds = new Set(orderedDocs.map((doc) => prepareRecordId(doc)));
  docs.forEach((doc) => {
    const docId = prepareRecordId(doc);
    if (!orderedIds.has(docId)) {
      orderedDocs.push(doc);
      depthById.set(docId, 0);
    }
  });

  return { docs: orderedDocs, childrenByParent, depthById };
}

function selectableRecordsUrl(dataDomain, docsScope) {
  const url = new URL(DATA_SHARING_ENDPOINTS.selectableRecords, window.location.origin);
  url.searchParams.set("data_domain", dataDomain);
  if (docsScope) url.searchParams.set("docs_scope", docsScope);
  return url.href;
}

async function defaultLoadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function prepareRecordId(record) {
  return normalizeText(record && record.id);
}
