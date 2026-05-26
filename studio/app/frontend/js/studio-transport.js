const STUDIO_WRITE_RUNTIME_KEYS = Object.freeze({
  deleteTagAlias: "delete_tag_alias",
  demoteTag: "demote_tag",
  demoteTagPreview: "demote_tag_preview",
  health: "health",
  importTagAssignments: "import_tag_assignments",
  importTagAssignmentsPreview: "import_tag_assignments_preview",
  importTagAliases: "import_tag_aliases",
  importTagRegistry: "import_tag_registry",
  mutateTagAlias: "mutate_tag_alias",
  mutateTagAliasPreview: "mutate_tag_alias_preview",
  mutateTag: "mutate_tag",
  mutateTagPreview: "mutate_tag_preview",
  promoteTagAlias: "promote_tag_alias",
  promoteTagAliasPreview: "promote_tag_alias_preview",
  saveTags: "save_tags"
});

const CATALOGUE_WRITE_ENDPOINTS = Object.freeze({
  bulkSave: "/studio/api/catalogue/bulk-save",
  deletePreview: "/studio/api/catalogue/delete-preview",
  deleteApply: "/studio/api/catalogue/delete-apply",
  publicationPreview: "/studio/api/catalogue/publication-preview",
  publicationApply: "/studio/api/catalogue/publication-apply",
  createWork: "/studio/api/catalogue/work/create",
  saveWork: "/studio/api/catalogue/work/save",
  createWorkDetail: "/studio/api/catalogue/work-detail/create",
  saveWorkDetail: "/studio/api/catalogue/work-detail/save",
  importPreview: "/studio/api/catalogue/import-preview",
  importApply: "/studio/api/catalogue/import-apply",
  createSeries: "/studio/api/catalogue/series/create",
  saveSeries: "/studio/api/catalogue/series/save",
  buildPreview: "/studio/api/catalogue/build-preview",
  buildApply: "/studio/api/catalogue/build-apply",
  previewProseImport: "/studio/api/catalogue/prose/import-preview",
  applyProseImport: "/studio/api/catalogue/prose/import-apply",
  previewMomentImport: "/studio/api/catalogue/moment/import-preview",
  applyMomentImport: "/studio/api/catalogue/moment/import-apply",
  previewMoment: "/studio/api/catalogue/moment/preview",
  saveMoment: "/studio/api/catalogue/moment/save",
  projectStateReport: "/studio/api/catalogue/project-state-report",
  projectStateOpenReport: "/studio/api/catalogue/project-state-open-report",
  thumbnailQualityPreview: "/studio/api/catalogue/thumbnail-quality-preview",
  read: "/studio/api/catalogue/read",
  health: "/studio/api/catalogue/health"
});

const DEFAULT_DOCS_VIEWER_BASE_URL = "http://127.0.0.1:8776";

const DOCS_MANAGEMENT_ENDPOINTS = {
  health: `${DEFAULT_DOCS_VIEWER_BASE_URL}/health`,
  generatedIndex: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/generated/index`,
  generatedSearch: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/generated/search`,
  importSource: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/import-source`,
  importSourceFiles: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/import-source-files`,
  importHtml: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/import-html`,
  importHtmlFiles: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/import-html-files`,
  openSource: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/open-source`
};

const DATA_SHARING_ENDPOINTS = {
  health: `${DEFAULT_DOCS_VIEWER_BASE_URL}/health`,
  generatedIndex: `${DEFAULT_DOCS_VIEWER_BASE_URL}/docs/generated/index`,
  prepare: `${DEFAULT_DOCS_VIEWER_BASE_URL}/data-sharing/prepare`,
  returnedPackages: `${DEFAULT_DOCS_VIEWER_BASE_URL}/data-sharing/returned-packages`,
  review: `${DEFAULT_DOCS_VIEWER_BASE_URL}/data-sharing/review`,
  apply: `${DEFAULT_DOCS_VIEWER_BASE_URL}/data-sharing/apply`
};

const AUDIT_API_ENDPOINTS = Object.freeze({
  health: "/studio/api/audits/health",
  audits: "/studio/api/audits/audits",
  run: "/studio/api/audits/audits/run"
});

const PROJECT_STATE_ENDPOINTS = {
  catalogueHealth: "/studio/api/catalogue/health",
  report: "/studio/api/catalogue/project-state-report",
  openReport: "/studio/api/catalogue/project-state-open-report"
};

const THUMBNAIL_QUALITY_ENDPOINTS = Object.freeze({
  catalogueHealth: "/studio/api/catalogue/health",
  refresh: "/studio/api/catalogue/thumbnail-quality-preview"
});

const CATALOGUE_READ_ENDPOINTS = Object.freeze({
  catalogueHealth: "/studio/api/catalogue/health",
  read: "/studio/api/catalogue/read"
});

const BULK_ADD_WORK_ENDPOINTS = Object.freeze({
  catalogueHealth: "/studio/api/catalogue/health",
  importPreview: "/studio/api/catalogue/import-preview",
  importApply: "/studio/api/catalogue/import-apply"
});

export {
  AUDIT_API_ENDPOINTS,
  BULK_ADD_WORK_ENDPOINTS,
  CATALOGUE_READ_ENDPOINTS,
  DATA_SHARING_ENDPOINTS,
  DOCS_MANAGEMENT_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS,
  PROJECT_STATE_ENDPOINTS,
  THUMBNAIL_QUALITY_ENDPOINTS
};

export function configureStudioTransport(config) {
  const docs = config && config.app && config.app.runtime && config.app.runtime.services
    ? config.app.runtime.services.docs
    : null;
  if (!docs || typeof docs !== "object") return;

  const configured = normalizeDocsEndpoints(docs);
  Object.assign(DOCS_MANAGEMENT_ENDPOINTS, {
    health: configured.health || DOCS_MANAGEMENT_ENDPOINTS.health,
    generatedIndex: configured.generated_index || DOCS_MANAGEMENT_ENDPOINTS.generatedIndex,
    generatedSearch: configured.generated_search || DOCS_MANAGEMENT_ENDPOINTS.generatedSearch,
    importSource: configured.import_source || DOCS_MANAGEMENT_ENDPOINTS.importSource,
    importSourceFiles: configured.import_source_files || DOCS_MANAGEMENT_ENDPOINTS.importSourceFiles,
    importHtml: configured.import_html || DOCS_MANAGEMENT_ENDPOINTS.importHtml,
    importHtmlFiles: configured.import_html_files || DOCS_MANAGEMENT_ENDPOINTS.importHtmlFiles,
    openSource: configured.open_source || DOCS_MANAGEMENT_ENDPOINTS.openSource
  });
  Object.assign(DATA_SHARING_ENDPOINTS, {
    health: configured.health || DATA_SHARING_ENDPOINTS.health,
    generatedIndex: configured.generated_index || DATA_SHARING_ENDPOINTS.generatedIndex,
    prepare: configured.data_sharing_prepare || DATA_SHARING_ENDPOINTS.prepare,
    returnedPackages: configured.data_sharing_returned_packages || DATA_SHARING_ENDPOINTS.returnedPackages,
    review: configured.data_sharing_review || DATA_SHARING_ENDPOINTS.review,
    apply: configured.data_sharing_apply || DATA_SHARING_ENDPOINTS.apply
  });
  Object.assign(PROJECT_STATE_ENDPOINTS, {
    openReport: CATALOGUE_WRITE_ENDPOINTS.projectStateOpenReport
  });
}

function normalizeDocsEndpoints(docs) {
  const normalized = {};
  for (const [key, value] of Object.entries(docs || {})) {
    if (typeof value === "string" && value.trim()) {
      normalized[key] = value.trim();
    }
  }
  return normalized;
}

export function getStudioWriteEndpoint(key, config = null) {
  const runtimeKey = STUDIO_WRITE_RUNTIME_KEYS[key] || "";
  const runtime = config && config.app && config.app.runtime;
  const analytics = runtime && runtime.services && runtime.services.analytics;
  const configured = runtimeKey && analytics && analytics[runtimeKey];
  if (typeof configured === "string" && configured.trim()) return configured;
  return "";
}

export async function probeStudioHealth(timeoutMs = 500, options = {}) {
  return probeHealth(getStudioWriteEndpoint("health", options.config), timeoutMs);
}

export async function probeCatalogueHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_WRITE_ENDPOINTS.health, timeoutMs);
}

export async function probeDocsManagementHealth(timeoutMs = 500) {
  return probeHealth(DOCS_MANAGEMENT_ENDPOINTS.health, timeoutMs);
}

export async function probeDataSharingHealth(timeoutMs = 500) {
  return probeHealth(DATA_SHARING_ENDPOINTS.health, timeoutMs);
}

export async function probeAuditApiHealth(timeoutMs = 500) {
  return probeHealth(AUDIT_API_ENDPOINTS.health, timeoutMs);
}

export async function probeProjectStateCatalogueHealth(timeoutMs = 500) {
  return probeHealth(PROJECT_STATE_ENDPOINTS.catalogueHealth, timeoutMs);
}

export async function probeProjectStateCatalogueOpenHealth(timeoutMs = 500) {
  return probeHealth(PROJECT_STATE_ENDPOINTS.catalogueHealth, timeoutMs);
}

export async function probeThumbnailQualityCatalogueHealth(timeoutMs = 500) {
  return probeHealth(THUMBNAIL_QUALITY_ENDPOINTS.catalogueHealth, timeoutMs);
}

export async function probeCatalogueReadHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_READ_ENDPOINTS.catalogueHealth, timeoutMs);
}

export async function probeBulkAddWorkCatalogueHealth(timeoutMs = 500) {
  return probeHealth(BULK_ADD_WORK_ENDPOINTS.catalogueHealth, timeoutMs);
}

async function probeHealth(url, timeoutMs = 500) {
  if (!url) return false;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) return false;
    const payload = await response.json();
    return Boolean(payload && payload.ok);
  } catch (error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function postJson(url, payload, options = {}) {
  if (!url) {
    throw new Error("Missing service endpoint");
  }

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: options.signal
  });

  let responsePayload = null;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`);
  }

  if (!response.ok || !responsePayload || !responsePayload.ok) {
    const message = responsePayload && responsePayload.error ? responsePayload.error : `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.payload = responsePayload;
    throw error;
  }

  return responsePayload;
}

export async function getJson(url, options = {}) {
  if (!url) {
    throw new Error("Missing service endpoint");
  }

  const response = await fetch(url, {
    cache: "no-store",
    signal: options.signal
  });

  let responsePayload = null;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`);
  }

  if (!response.ok || !responsePayload || !responsePayload.ok) {
    const message = responsePayload && responsePayload.error ? responsePayload.error : `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.payload = responsePayload;
    throw error;
  }

  return responsePayload;
}
