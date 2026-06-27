const ANALYTICS_WRITE_RUNTIME_KEYS = Object.freeze({
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

const DATA_SHARING_ENDPOINTS = {
  health: "/analytics/api/data-sharing/health",
  config: "/analytics/api/data-sharing/config",
  selectableRecords: "/analytics/api/data-sharing/selectable-records",
  prepare: "/analytics/api/data-sharing/prepare",
  context: "/analytics/api/data-sharing/context",
  returnedPackages: "/analytics/api/data-sharing/returned-packages",
  returnedRecords: "/analytics/api/data-sharing/returned-records",
  review: "/analytics/api/data-sharing/review",
  apply: "/analytics/api/data-sharing/apply"
};

export {
  DATA_SHARING_ENDPOINTS
};

export function configureAnalyticsTransport(config) {
  const services = config && config.app && config.app.runtime && config.app.runtime.services
    ? config.app.runtime.services
    : {};
  const dataSharing = services && typeof services.data_sharing === "object" ? services.data_sharing : null;
  if (dataSharing) {
    const configuredDataSharing = normalizeServiceEndpoints(dataSharing);
    Object.assign(DATA_SHARING_ENDPOINTS, {
      health: configuredDataSharing.health || DATA_SHARING_ENDPOINTS.health,
      config: configuredDataSharing.config || DATA_SHARING_ENDPOINTS.config,
      selectableRecords: configuredDataSharing.selectable_records || DATA_SHARING_ENDPOINTS.selectableRecords,
      prepare: configuredDataSharing.prepare || DATA_SHARING_ENDPOINTS.prepare,
      context: configuredDataSharing.context || DATA_SHARING_ENDPOINTS.context,
      returnedPackages: configuredDataSharing.returned_packages || DATA_SHARING_ENDPOINTS.returnedPackages,
      returnedRecords: configuredDataSharing.returned_records || DATA_SHARING_ENDPOINTS.returnedRecords,
      review: configuredDataSharing.review || DATA_SHARING_ENDPOINTS.review,
      apply: configuredDataSharing.apply || DATA_SHARING_ENDPOINTS.apply
    });
  }
}

function normalizeServiceEndpoints(service) {
  const normalized = {};
  for (const [key, value] of Object.entries(service || {})) {
    if (typeof value === "string" && value.trim()) {
      normalized[key] = value.trim();
    }
  }
  return normalized;
}

export function getAnalyticsWriteEndpoint(key, config = null) {
  const runtimeKey = ANALYTICS_WRITE_RUNTIME_KEYS[key] || "";
  const runtime = config && config.app && config.app.runtime;
  const analytics = runtime && runtime.services && runtime.services.analytics;
  const configured = runtimeKey && analytics && analytics[runtimeKey];
  if (typeof configured === "string" && configured.trim()) return configured;
  return "";
}

export async function probeAnalyticsHealth(timeoutMs = 500, options = {}) {
  return probeHealth(getAnalyticsWriteEndpoint("health", options.config), timeoutMs);
}

export async function probeDataSharingHealth(timeoutMs = 500) {
  return probeHealth(DATA_SHARING_ENDPOINTS.health, timeoutMs);
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
