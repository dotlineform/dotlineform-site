import { CATALOGUE_READ_ENDPOINTS } from "./studio-transport.js";

let studioConfigModulePromise = null;

const CATALOGUE_SERVER_READ_KEYS = new Set([
  "activity_log",
  "catalogue_works",
  "catalogue_work_details",
  "catalogue_series",
  "catalogue_moments",
  "catalogue_lookup_work_search",
  "catalogue_lookup_series_search",
  "catalogue_lookup_work_detail_search",
  "catalogue_lookup_work_base",
  "catalogue_lookup_work_detail_base",
  "catalogue_lookup_series_base"
]);

export async function fetchJson(url, options = {}) {
  const cache = String(options.cache || "default");
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  return response.json();
}

export async function loadStudioLookupJson(config, key, options) {
  if (shouldUseCatalogueServerRead(key, options)) {
    return fetchJson(buildCatalogueReadUrl(key), options);
  }
  const { getStudioDataPath } = await loadStudioConfigModule();
  return fetchJson(getStudioDataPath(config, key), options);
}

export async function loadStudioServerReadJson(key, options) {
  if (!CATALOGUE_SERVER_READ_KEYS.has(key)) {
    throw new Error(`Unsupported catalogue server read key: ${key}`);
  }
  return fetchJson(buildCatalogueReadUrl(key), options);
}

export async function loadStudioLookupRecordJson(config, baseKey, recordId, options) {
  if (shouldUseCatalogueServerRead(baseKey, options)) {
    return fetchJson(buildCatalogueReadUrl(baseKey, recordId), options);
  }
  const { getStudioDataPath } = await loadStudioConfigModule();
  const basePath = getStudioDataPath(config, baseKey);
  return fetchJson(buildLookupRecordPath(basePath, recordId), options);
}

function shouldUseCatalogueServerRead(key, options = {}) {
  return Boolean(options && options.catalogueServerAvailable && CATALOGUE_SERVER_READ_KEYS.has(key));
}

function buildCatalogueReadUrl(key, recordId = "") {
  const url = new URL(CATALOGUE_READ_ENDPOINTS.read, window.location.origin);
  url.searchParams.set("key", key);
  if (recordId) {
    url.searchParams.set("record_id", String(recordId));
  }
  return url.toString();
}

function buildLookupRecordPath(basePath, recordId) {
  const rawBase = String(basePath || "");
  const [beforeHash, hash = ""] = rawBase.split("#", 2);
  const [beforeQuery, query = ""] = beforeHash.split("?", 2);
  const normalizedBase = beforeQuery.endsWith("/") ? beforeQuery : `${beforeQuery}/`;
  const encodedId = encodeURIComponent(String(recordId || ""));
  return `${normalizedBase}${encodedId}.json${query ? `?${query}` : ""}${hash ? `#${hash}` : ""}`;
}

async function loadStudioConfigModule() {
  if (!studioConfigModulePromise) {
    const url = new URL("./studio-config.js", import.meta.url);
    const assetVersion = readAssetVersion(import.meta.url);
    if (assetVersion) {
      url.searchParams.set("v", assetVersion);
    }
    studioConfigModulePromise = import(url.href);
  }
  return studioConfigModulePromise;
}

function readAssetVersion(importUrl = "") {
  try {
    const importVersion = new URL(importUrl).searchParams.get("v");
    if (importVersion) return importVersion;
  } catch (_error) {
    // Ignore malformed import URLs and continue to DOM-based lookup.
  }

  if (typeof document !== "undefined") {
    const meta = document.querySelector('meta[name="dlf-asset-version"]');
    const value = meta ? String(meta.getAttribute("content") || "").trim() : "";
    if (value) return value;
  }

  return "";
}
