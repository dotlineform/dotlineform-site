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
  read: "/studio/api/catalogue/read",
  health: "/studio/api/catalogue/health"
});

const PROJECT_STATE_ENDPOINTS = Object.freeze({
  catalogueHealth: "/studio/api/catalogue/health",
  report: "/studio/api/catalogue/project-state-report",
  openReport: "/studio/api/catalogue/project-state-open-report"
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
  BULK_ADD_WORK_ENDPOINTS,
  CATALOGUE_READ_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS,
  PROJECT_STATE_ENDPOINTS,
};

export function configureStudioTransport(config) {
  void config;
}

export async function probeCatalogueHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_WRITE_ENDPOINTS.health, timeoutMs);
}

export async function probeProjectStateCatalogueHealth(timeoutMs = 500) {
  return probeHealth(PROJECT_STATE_ENDPOINTS.catalogueHealth, timeoutMs);
}

export async function probeProjectStateCatalogueOpenHealth(timeoutMs = 500) {
  return probeHealth(PROJECT_STATE_ENDPOINTS.catalogueHealth, timeoutMs);
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

export async function deleteJson(url, options = {}) {
  if (!url) {
    throw new Error("Missing service endpoint");
  }

  const response = await fetch(url, {
    method: "DELETE",
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
