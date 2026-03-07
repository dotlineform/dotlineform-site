const STUDIO_WRITE_ENDPOINTS = Object.freeze({
  saveTags: "http://127.0.0.1:8787/save-tags",
  health: "http://127.0.0.1:8787/health",
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

export {
  STUDIO_WRITE_ENDPOINTS
};

export async function probeStudioHealth(timeoutMs = 500) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(STUDIO_WRITE_ENDPOINTS.health, {
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
    throw new Error(message);
  }

  return responsePayload;
}
