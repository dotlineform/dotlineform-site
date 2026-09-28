import { CATALOGUE_READ_ENDPOINTS } from "./studio-transport.js";

const CATALOGUE_SERVER_READ_KEYS = new Set([
  "catalogue_works",
  "catalogue_series",
  "catalogue_galleries",
  "catalogue_gallery_record",
  "catalogue_lookup_work_search",
  "catalogue_lookup_series_search",
  "catalogue_lookup_series_base",
  "catalogue_work_record"
]);

export async function fetchJson(url, options = {}) {
  const cache = String(options.cache || "default");
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  return response.json();
}

export async function loadStudioServerReadJson(key, recordId = "", options = {}) {
  if (!CATALOGUE_SERVER_READ_KEYS.has(key)) {
    throw new Error(`Unsupported catalogue server read key: ${key}`);
  }
  return fetchJson(buildCatalogueReadUrl(key, recordId), options);
}

function buildCatalogueReadUrl(key, recordId = "") {
  const url = new URL(CATALOGUE_READ_ENDPOINTS.read, window.location.origin);
  url.searchParams.set("key", key);
  if (recordId) {
    url.searchParams.set("record_id", String(recordId));
  }
  return url.toString();
}
