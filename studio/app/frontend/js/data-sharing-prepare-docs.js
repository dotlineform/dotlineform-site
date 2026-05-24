import {
  getDocsScopeDataPath
} from "./studio-config.js";
import {
  DATA_SHARING_ENDPOINTS
} from "./studio-transport.js";
import {
  usesPrepareDocumentSelection
} from "./data-sharing-prepare-workflow.js";

export async function loadDataSharingPrepareDocsState(options = {}) {
  const {
    config,
    scope,
    serviceAvailable,
    prepareCapability,
    workflowActive,
    exportConfigCount,
    loadJson = defaultLoadJson,
    onError
  } = options;

  let docsIndexPayload = { docs: [] };
  let docsIndexError = false;

  if (
    usesPrepareDocumentSelection(prepareCapability)
    && workflowActive
    && Number(exportConfigCount || 0) > 0
  ) {
    const docsIndexPath = getDocsScopeDataPath(config, scope, "index")
      || `/assets/data/docs/scopes/${encodeURIComponent(scope)}/index.json`;
    const docsIndexReadPath = serviceAvailable ? docsGeneratedIndexUrl(scope) : docsIndexPath;
    try {
      docsIndexPayload = await loadJson(docsIndexReadPath);
    } catch (error) {
      docsIndexError = true;
      if (typeof onError === "function") onError(error, { scope, path: docsIndexReadPath });
    }
  }

  return {
    docsIndexError,
    ...buildVisibleDocs(docsIndexPayload)
  };
}

export function buildVisibleDocs(indexPayload) {
  const sourceDocs = Array.isArray(indexPayload?.docs) ? indexPayload.docs : [];
  const docs = sourceDocs.filter((doc) => {
    const docId = normalizeText(doc?.doc_id);
    if (!docId) return false;
    return doc.published !== false;
  });

  const visibleIds = new Set(docs.map((doc) => normalizeText(doc.doc_id)));
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
      const docId = normalizeText(doc.doc_id);
      orderedDocs.push(doc);
      depthById.set(docId, depth);
      visit(docId, depth + 1);
    });
  };
  visit("", 0);

  const orderedIds = new Set(orderedDocs.map((doc) => normalizeText(doc.doc_id)));
  docs.forEach((doc) => {
    const docId = normalizeText(doc.doc_id);
    if (!orderedIds.has(docId)) {
      orderedDocs.push(doc);
      depthById.set(docId, 0);
    }
  });

  return { docs: orderedDocs, childrenByParent, depthById };
}

function docsGeneratedIndexUrl(scope) {
  const url = new URL(DATA_SHARING_ENDPOINTS.generatedIndex, window.location.origin);
  url.searchParams.set("scope", scope);
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
