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
  createWork: "http://127.0.0.1:8788/catalogue/work/create",
  saveWork: "http://127.0.0.1:8788/catalogue/work/save",
  createWorkDetail: "http://127.0.0.1:8788/catalogue/work-detail/create",
  saveWorkDetail: "http://127.0.0.1:8788/catalogue/work-detail/save",
  importPreview: "http://127.0.0.1:8788/catalogue/import-preview",
  importApply: "http://127.0.0.1:8788/catalogue/import-apply",
  createWorkFile: "http://127.0.0.1:8788/catalogue/work-file/create",
  saveWorkFile: "http://127.0.0.1:8788/catalogue/work-file/save",
  deleteWorkFile: "http://127.0.0.1:8788/catalogue/work-file/delete",
  createWorkLink: "http://127.0.0.1:8788/catalogue/work-link/create",
  saveWorkLink: "http://127.0.0.1:8788/catalogue/work-link/save",
  deleteWorkLink: "http://127.0.0.1:8788/catalogue/work-link/delete",
  createSeries: "http://127.0.0.1:8788/catalogue/series/create",
  saveSeries: "http://127.0.0.1:8788/catalogue/series/save",
  buildPreview: "http://127.0.0.1:8788/catalogue/build-preview",
  buildApply: "http://127.0.0.1:8788/catalogue/build-apply",
  health: "http://127.0.0.1:8788/health"
});

export {
  STUDIO_WRITE_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS
};

export async function probeStudioHealth(timeoutMs = 500) {
  return probeHealth(STUDIO_WRITE_ENDPOINTS.health, timeoutMs);
}

export async function probeCatalogueHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_WRITE_ENDPOINTS.health, timeoutMs);
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
