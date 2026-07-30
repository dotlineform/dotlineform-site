import {
  normalizeManagedDocumentCollectionTarget,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

function cleanText(value) {
  return String(value == null ? "" : value).trim();
}

function exactQueryKeys(url, expected) {
  const actual = Array.from(url.searchParams.keys()).sort();
  const required = expected.slice().sort();
  return (
    actual.length === required.length
    && actual.every((key, index) => key === required[index])
  );
}

export function docsImportResultDestination(payload, options = {}) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Docs Import result is unavailable.");
  }
  const collection = options.collection === true;
  const target = collection
    ? normalizeManagedDocumentCollectionTarget(payload.target)
    : normalizeManagedDocumentTarget(payload.target);
  const rawUrl = cleanText(payload.viewer_url);
  if (!rawUrl) {
    throw new Error("Docs Import result destination URL is unavailable.");
  }

  const base = new URL("http://docs-import.local/");
  const url = new URL(rawUrl, base);
  if (url.origin !== base.origin || url.pathname !== "/docs/" || url.hash) {
    throw new Error("Docs Import result destination URL is invalid.");
  }
  if (url.searchParams.get("scope") !== target.scope) {
    throw new Error("Docs Import result destination scope does not match its target.");
  }

  let expectedKeys = ["scope"];
  if (target.sub_scope) {
    const reportDocId = cleanText(url.searchParams.get("doc"));
    if (!reportDocId) {
      throw new Error("Docs Import child destination requires its report document.");
    }
    expectedKeys.push("doc");
    if (!collection) {
      if (url.searchParams.get("subdoc") !== target.doc_id) {
        throw new Error("Docs Import child destination does not match its document.");
      }
      expectedKeys.push("subdoc");
    }
  } else if (!collection) {
    if (url.searchParams.get("doc") !== target.doc_id) {
      throw new Error("Docs Import destination does not match its document.");
    }
    expectedKeys.push("doc");
  }
  if (!exactQueryKeys(url, expectedKeys)) {
    throw new Error("Docs Import result destination contains unexpected route state.");
  }

  return Object.freeze({
    target,
    href: `${url.pathname}${url.search}`,
    label: collection ? "Open imported collection" : "Open imported document"
  });
}
