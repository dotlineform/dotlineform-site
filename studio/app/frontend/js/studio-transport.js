const CATALOGUE_WRITE_ENDPOINTS = Object.freeze({
  bulkSave: "/studio/api/catalogue/bulk-save",
  deletePreview: "/studio/api/catalogue/delete-preview",
  deleteApply: "/studio/api/catalogue/delete-apply",
  createWorkDetailSection: "/studio/api/catalogue/work-detail-section/create",
  saveWorkDetailSection: "/studio/api/catalogue/work-detail-section/save",
  createWork: "/studio/api/catalogue/work/create",
  saveWork: "/studio/api/catalogue/work/save",
  createSeries: "/studio/api/catalogue/series/create",
  saveSeries: "/studio/api/catalogue/series/save",
  projectMedia: "/studio/api/catalogue/project-media",
  read: "/studio/api/catalogue/read",
  health: "/studio/api/catalogue/health"
});

const CATALOGUE_READ_ENDPOINTS = Object.freeze({
  catalogueHealth: "/studio/api/catalogue/health",
  read: "/studio/api/catalogue/read"
});

export {
  CATALOGUE_READ_ENDPOINTS,
  CATALOGUE_WRITE_ENDPOINTS,
};

export function configureStudioTransport(config) {
  void config;
}

export async function probeCatalogueHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_WRITE_ENDPOINTS.health, timeoutMs);
}

export async function probeCatalogueReadHealth(timeoutMs = 500) {
  return probeHealth(CATALOGUE_READ_ENDPOINTS.catalogueHealth, timeoutMs);
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

  let responsePayload;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`, { cause: error });
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

  let responsePayload;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`, { cause: error });
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

  let responsePayload;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`, { cause: error });
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
