export const DOCUMENT_PACKAGE_ENDPOINTS = Object.freeze({
  config: "/docs/packages/config",
  documents: "/docs/packages/documents",
  returned: "/docs/packages/returned",
  prepare: "/docs/packages/prepare",
  context: "/docs/packages/context",
  reviewReturned: "/docs/packages/returned/review"
});

function endpointUrl(path, query = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries(query).forEach(([key, value]) => {
    const text = String(value == null ? "" : value).trim();
    if (text) url.searchParams.set(key, text);
  });
  return url.href;
}

async function responsePayload(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (_error) {
    return { ok: false, error: text };
  }
}

export async function requestDocumentPackageJson(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    credentials: "same-origin",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.headers || {})
    }
  });
  const payload = await responsePayload(response);
  if (!response.ok || payload.ok === false) {
    const error = new Error(
      String(payload.error || payload.summary_text || `Request failed with HTTP ${response.status}`).trim()
    );
    error.payload = payload;
    error.status = response.status;
    throw error;
  }
  return payload;
}

export function getDocumentPackageConfig() {
  return requestDocumentPackageJson(DOCUMENT_PACKAGE_ENDPOINTS.config);
}

export function getPackageDocuments(scope) {
  return requestDocumentPackageJson(endpointUrl(DOCUMENT_PACKAGE_ENDPOINTS.documents, { scope }));
}

export function getReturnedDocumentPackages(scope) {
  return requestDocumentPackageJson(endpointUrl(DOCUMENT_PACKAGE_ENDPOINTS.returned, { scope }));
}

export function postDocumentPackageJson(path, payload) {
  return requestDocumentPackageJson(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
}

export function prepareDocumentPackage(payload) {
  return postDocumentPackageJson(DOCUMENT_PACKAGE_ENDPOINTS.prepare, payload);
}

export function saveDocumentPackageContext(payload) {
  return postDocumentPackageJson(DOCUMENT_PACKAGE_ENDPOINTS.context, payload);
}

export function reviewReturnedDocumentPackage(payload) {
  return postDocumentPackageJson(DOCUMENT_PACKAGE_ENDPOINTS.reviewReturned, payload);
}
