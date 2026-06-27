import {
  DATA_SHARING_ENDPOINTS
} from "./analytics-transport.js";
import {
  usesPrepareDocumentSelection,
  usesPrepareRecordSelection
} from "./data-sharing-prepare-workflow.js";

export async function loadDataSharingPrepareDocsState(options = {}) {
  const {
    dataDomain,
    docsScope,
    config,
    prepareCapability,
    workflowActive,
    exportConfigCount,
    loadJson = defaultLoadJson,
    onError
  } = options;

  let selectableRecordsPayload = { records: [] };
  let docsIndexError = false;

  if (
    usesPrepareRecordSelection(prepareCapability, config)
    && workflowActive
    && Number(exportConfigCount || 0) > 0
    && (!usesPrepareDocumentSelection(prepareCapability) || docsScope)
  ) {
    try {
      selectableRecordsPayload = await loadJson(selectableRecordsUrl(dataDomain, docsScope, config && config.id));
    } catch (error) {
      docsIndexError = true;
      if (typeof onError === "function") onError(error, { dataDomain, docsScope, path: selectableRecordsUrl(dataDomain, docsScope, config && config.id) });
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
  return { docs };
}

function selectableRecordsUrl(dataDomain, docsScope, configId) {
  const url = new URL(DATA_SHARING_ENDPOINTS.selectableRecords, window.location.origin);
  url.searchParams.set("data_domain", dataDomain);
  if (docsScope) url.searchParams.set("docs_scope", docsScope);
  if (configId) url.searchParams.set("config_id", configId);
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
