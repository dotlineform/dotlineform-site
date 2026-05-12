const STUDIO_WRITE_ENDPOINTS = Object.freeze({
  saveTags: "http://127.0.0.1:8787/save-tags",
  health: "http://127.0.0.1:8787/health",
  importTagAssignmentsPreview: "http://127.0.0.1:8787/import-tag-assignments-preview",
  importTagAssignments: "http://127.0.0.1:8787/import-tag-assignments",
  importTagRegistry: "http://127.0.0.1:8787/import-tag-registry",
  mutateTag: "http://127.0.0.1:8787/mutate-tag",
  mutateTagPreview: "http://127.0.0.1:8787/mutate-tag-preview",
  demoteTag: "http://127.0.0.1:8787/demote-tag",
  demoteTagPreview: "http://127.0.0.1:8787/demote-tag-preview",
  importTagAliases: "http://127.0.0.1:8787/import-tag-aliases",
  deleteTagAlias: "http://127.0.0.1:8787/delete-tag-alias",
  mutateTagAlias: "http://127.0.0.1:8787/mutate-tag-alias",
  promoteTagAlias: "http://127.0.0.1:8787/promote-tag-alias",
  promoteTagAliasPreview: "http://127.0.0.1:8787/promote-tag-alias-preview"
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
  brokenLinks: "http://127.0.0.1:8789/docs/broken-links",
  exportDocs: "http://127.0.0.1:8789/docs/export",
  generatedIndex: "http://127.0.0.1:8789/docs/generated/index",
  generatedSearch: "http://127.0.0.1:8789/docs/generated/search",
  importSource: "http://127.0.0.1:8789/docs/import-source",
  importSourceFiles: "http://127.0.0.1:8789/docs/import-source-files",
  importHtml: "http://127.0.0.1:8789/docs/import-html",
  importHtmlFiles: "http://127.0.0.1:8789/docs/import-html-files",
  importFiles: "http://127.0.0.1:8789/docs/import/files",
  importPreview: "http://127.0.0.1:8789/docs/import/preview",
  importApply: "http://127.0.0.1:8789/docs/import/apply",
  openSource: "http://127.0.0.1:8789/docs/open-source"
});

const AUDIT_SERVICE_ENDPOINTS = Object.freeze({
  health: "http://127.0.0.1:8790/health",
  audits: "http://127.0.0.1:8790/audits",
  run: "http://127.0.0.1:8790/audits/run"
});

export {
  AUDIT_SERVICE_ENDPOINTS,
  DOCS_MANAGEMENT_ENDPOINTS,
  STUDIO_WRITE_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS
};

export async function probeStudioHealth(timeoutMs = 500) {
  return probeHealth(STUDIO_WRITE_ENDPOINTS.health, timeoutMs);
}

export async function probeCatalogueHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_WRITE_ENDPOINTS.health, timeoutMs);
}

export async function probeDocsManagementHealth(timeoutMs = 500) {
  return probeHealth(DOCS_MANAGEMENT_ENDPOINTS.health, timeoutMs);
}

export async function probeAuditServiceHealth(timeoutMs = 500) {
  return probeHealth(AUDIT_SERVICE_ENDPOINTS.health, timeoutMs);
}

async function probeHealth(url, timeoutMs = 500) {
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
