export const DOCUMENT_PACKAGE_ENDPOINTS = Object.freeze({
  prepareOptions: "/docs/packages/prepare-options",
  prepare: "/docs/packages/prepare",
  reviewReturned: "/docs/packages/returned/review"
});

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

export function readDocumentPackagePrepareOptions(docIds, collection) {
  return postDocumentPackageJson(DOCUMENT_PACKAGE_ENDPOINTS.prepareOptions, { doc_ids: docIds, collection });
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

export function reviewReturnedDocumentPackage(payload) {
  return postDocumentPackageJson(DOCUMENT_PACKAGE_ENDPOINTS.reviewReturned, payload);
}
