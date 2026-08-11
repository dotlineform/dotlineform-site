import {
  committedDocumentLocation,
  createDocumentLocationProvider,
  resolveDocumentLocationRecords
} from "/shared/frontend/js/document-location-provider.js";


export const TAG_REGISTRY_DOCUMENT_SCOPE_IDS = Object.freeze([
  "analysis"
]);

export function tagRegistryDocumentHref(config, url) {
  const documentUrl = String(url == null ? "" : url).trim();
  const previewBase = String(
    config
      && config.app
      && config.app.runtime
      && config.app.runtime.sites
      && config.app.runtime.sites.public_preview
      && config.app.runtime.sites.public_preview.base
      || ""
  ).trim();
  if (!previewBase || !documentUrl) return documentUrl;
  try {
    return new URL(documentUrl, `${previewBase.replace(/\/+$/, "")}/`).href;
  } catch (_error) {
    return documentUrl;
  }
}

function cleanUrls(values) {
  return (Array.isArray(values) ? values : [])
    .map((value) => String(value == null ? "" : value).trim())
    .filter(Boolean);
}

export function tagRegistryDocumentUrls(tags) {
  const urls = [];
  const seen = new Set();
  (Array.isArray(tags) ? tags : []).forEach((tag) => {
    cleanUrls(tag && tag.docUrl).forEach((url) => {
      if (seen.has(url)) return;
      seen.add(url);
      urls.push(url);
    });
  });
  return urls;
}

export function unavailableTagRegistryDocument(url) {
  return resolveDocumentLocationRecords([], [url])[0];
}

export function documentLocationMap(records) {
  return new Map(
    (Array.isArray(records) ? records : [])
      .filter((record) => record && record.url)
      .map((record) => [record.url, record])
  );
}

export function attachTagRegistryDocuments(tags, locationsByUrl) {
  const byUrl = locationsByUrl instanceof Map ? locationsByUrl : new Map();
  return (Array.isArray(tags) ? tags : []).map((tag) => {
    const docUrl = cleanUrls(tag && tag.docUrl);
    return {
      ...tag,
      docUrl,
      documents: docUrl.map((url) => (
        byUrl.get(url) || unavailableTagRegistryDocument(url)
      ))
    };
  });
}

export async function loadTagRegistryDocumentLocations(tags, options = {}) {
  const urls = tagRegistryDocumentUrls(tags);
  if (!urls.length) {
    return {
      records: [],
      locationsByUrl: new Map(),
      error: ""
    };
  }
  const provider = options.provider || createDocumentLocationProvider();
  try {
    const records = await provider.resolve({
      scopeIds: TAG_REGISTRY_DOCUMENT_SCOPE_IDS,
      urls
    });
    return {
      records,
      locationsByUrl: documentLocationMap(records),
      error: ""
    };
  } catch (error) {
    const records = resolveDocumentLocationRecords([], urls);
    return {
      records,
      locationsByUrl: documentLocationMap(records),
      error: String(error && error.message ? error.message : "Document locations could not be loaded.")
    };
  }
}

export function setTagRegistryDocumentLocation(state, record) {
  if (!state || !record || !record.url) return;
  if (!(state.documentLocationsByUrl instanceof Map)) {
    state.documentLocationsByUrl = new Map();
  }
  state.documentLocationsByUrl.set(record.url, record);
}

export function appendTagRegistryDocumentUrl(urls, record) {
  const committed = committedDocumentLocation(record);
  if (committed.scope_id !== "analysis") {
    throw new Error("Tag Registry accepts Analysis document locations only");
  }
  const current = cleanUrls(urls);
  return current.includes(committed.url)
    ? current
    : [...current, committed.url];
}

export function removeTagRegistryDocumentUrl(urls, selectedUrl) {
  const target = String(selectedUrl == null ? "" : selectedUrl).trim();
  return cleanUrls(urls).filter((url) => url !== target);
}
