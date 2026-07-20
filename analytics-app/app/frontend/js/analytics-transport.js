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
