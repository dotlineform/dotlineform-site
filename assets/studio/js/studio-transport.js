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
  thumbnailQualityPreview: "/studio/api/catalogue/thumbnail-quality-preview",
  read: "/studio/api/catalogue/read",
  health: "/studio/api/catalogue/health"
});

const DOCS_MANAGEMENT_ENDPOINTS = Object.freeze({
  health: "http://127.0.0.1:8789/health",
  generatedIndex: "http://127.0.0.1:8789/docs/generated/index",
  generatedSearch: "http://127.0.0.1:8789/docs/generated/search",
  importSource: "http://127.0.0.1:8789/docs/import-source",
  importSourceFiles: "http://127.0.0.1:8789/docs/import-source-files",
  importHtml: "http://127.0.0.1:8789/docs/import-html",
  importHtmlFiles: "http://127.0.0.1:8789/docs/import-html-files",
  openSource: "http://127.0.0.1:8789/docs/open-source"
});

const DATA_SHARING_ENDPOINTS = Object.freeze({
  health: "/studio/api/docs/health",
  generatedIndex: "/studio/api/docs/docs/generated/index",
  prepare: "/studio/api/docs/data-sharing/prepare",
  returnedPackages: "/studio/api/docs/data-sharing/returned-packages",
  review: "/studio/api/docs/data-sharing/review",
  apply: "/studio/api/docs/data-sharing/apply"
});

const AUDIT_SERVICE_ENDPOINTS = Object.freeze({
  health: "/studio/api/audits/health",
  audits: "/studio/api/audits/audits",
  run: "/studio/api/audits/audits/run"
});

const PROJECT_STATE_ENDPOINTS = Object.freeze({
  catalogueHealth: "/studio/api/catalogue/health",
  docsHealth: "/studio/api/docs/health",
  report: "/studio/api/catalogue/project-state-report",
  openSource: "/studio/api/docs/docs/open-source"
});

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
  AUDIT_SERVICE_ENDPOINTS,
  BULK_ADD_WORK_ENDPOINTS,
  CATALOGUE_READ_ENDPOINTS,
  DATA_SHARING_ENDPOINTS,
  DOCS_MANAGEMENT_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS,
  PROJECT_STATE_ENDPOINTS,
  THUMBNAIL_QUALITY_ENDPOINTS
};

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

export async function probeAuditServiceHealth(timeoutMs = 500) {
  return probeHealth(AUDIT_SERVICE_ENDPOINTS.health, timeoutMs);
}

export async function probeProjectStateCatalogueHealth(timeoutMs = 500) {
  return probeHealth(PROJECT_STATE_ENDPOINTS.catalogueHealth, timeoutMs);
}

export async function probeProjectStateDocsHealth(timeoutMs = 500) {
  return probeHealth(PROJECT_STATE_ENDPOINTS.docsHealth, timeoutMs);
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
