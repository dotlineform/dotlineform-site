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
  bulkSave: "http://127.0.0.1:8788/catalogue/bulk-save",
  deletePreview: "http://127.0.0.1:8788/catalogue/delete-preview",
  deleteApply: "http://127.0.0.1:8788/catalogue/delete-apply",
  publicationPreview: "http://127.0.0.1:8788/catalogue/publication-preview",
  publicationApply: "http://127.0.0.1:8788/catalogue/publication-apply",
  createWork: "http://127.0.0.1:8788/catalogue/work/create",
  saveWork: "http://127.0.0.1:8788/catalogue/work/save",
  createWorkDetail: "http://127.0.0.1:8788/catalogue/work-detail/create",
  saveWorkDetail: "http://127.0.0.1:8788/catalogue/work-detail/save",
  importPreview: "http://127.0.0.1:8788/catalogue/import-preview",
  importApply: "http://127.0.0.1:8788/catalogue/import-apply",
  createSeries: "http://127.0.0.1:8788/catalogue/series/create",
  saveSeries: "http://127.0.0.1:8788/catalogue/series/save",
  buildPreview: "http://127.0.0.1:8788/catalogue/build-preview",
  buildApply: "http://127.0.0.1:8788/catalogue/build-apply",
  previewProseImport: "http://127.0.0.1:8788/catalogue/prose/import-preview",
  applyProseImport: "http://127.0.0.1:8788/catalogue/prose/import-apply",
  previewMomentImport: "http://127.0.0.1:8788/catalogue/moment/import-preview",
  applyMomentImport: "http://127.0.0.1:8788/catalogue/moment/import-apply",
  previewMoment: "http://127.0.0.1:8788/catalogue/moment/preview",
  saveMoment: "http://127.0.0.1:8788/catalogue/moment/save",
  projectStateReport: "http://127.0.0.1:8788/catalogue/project-state-report",
  thumbnailQualityPreview: "http://127.0.0.1:8788/catalogue/thumbnail-quality-preview",
  read: "http://127.0.0.1:8788/catalogue/read",
  health: "http://127.0.0.1:8788/health"
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
  health: "http://127.0.0.1:8789/health",
  prepare: "http://127.0.0.1:8789/data-sharing/prepare",
  returnedPackages: "http://127.0.0.1:8789/data-sharing/returned-packages",
  review: "http://127.0.0.1:8789/data-sharing/review",
  apply: "http://127.0.0.1:8789/data-sharing/apply"
});

const AUDIT_SERVICE_ENDPOINTS = Object.freeze({
  health: "http://127.0.0.1:8790/health",
  audits: "http://127.0.0.1:8790/audits",
  run: "http://127.0.0.1:8790/audits/run"
});

export {
  AUDIT_SERVICE_ENDPOINTS,
  DATA_SHARING_ENDPOINTS,
  DOCS_MANAGEMENT_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS
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
