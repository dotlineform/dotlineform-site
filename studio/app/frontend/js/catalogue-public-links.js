import {
  getStudioRoute
} from "./studio-config.js";

export function buildPublicCatalogueUrl(config, path = "/", params = {}) {
  const normalizedPath = normalizePublicPath(path);
  return buildPublicSiteUrl(config, normalizedPath, params);
}

export function buildPublicWorkUrl(config, workId, params = {}) {
  return buildPublicCatalogueUrl(config, "/works/", {
    ...params,
    work: normalizeText(workId)
  });
}

export function buildPublicSeriesUrl(config, seriesId, params = {}) {
  return buildPublicCatalogueUrl(config, "/series/", {
    ...params,
    series: normalizeText(seriesId)
  });
}

export function buildPublicWorkDetailUrl(config, detailUid, params = {}) {
  return buildPublicCatalogueUrl(config, "/work-details/", {
    ...params,
    detail: normalizeText(detailUid)
  });
}

export function buildPublicMomentUrl(config, momentId, params = {}) {
  return buildPublicRecordUrl(config, "moments_page_base", "/moments/", momentId, params);
}

function buildPublicRecordUrl(config, routeKey, fallbackBase, recordId, params = {}) {
  const id = normalizeText(recordId);
  const routeBase = normalizeRouteBase(getStudioRoute(config, routeKey) || fallbackBase);
  return buildPublicCatalogueUrl(config, id ? `${routeBase}${encodeURIComponent(id)}/` : routeBase, params);
}

function buildPublicSiteUrl(config, path = "/", params = {}, options = {}) {
  const siteKey = options && options.site === "production" ? "production" : "public_preview";
  const base = getStudioSiteBase(config, siteKey);
  if (!base) {
    throw new Error(`Missing Studio site base: ${siteKey}`);
  }
  const url = new URL(String(path || "/"), ensureTrailingSlash(base));
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    url.searchParams.set(key, String(value));
  }
  return url.href;
}

function getStudioSiteBase(config, siteKey) {
  const runtime = config && config.app && config.app.runtime;
  const sites = runtime && runtime.sites && typeof runtime.sites === "object" && !Array.isArray(runtime.sites)
    ? runtime.sites
    : {};
  const site = sites && sites[siteKey];
  const value = site && site.base;
  return typeof value === "string" && value.trim() ? value.trim().replace(/\/+$/, "") : "";
}

function normalizeRouteBase(value) {
  const text = normalizePublicPath(value || "/");
  return text.endsWith("/") ? text : `${text}/`;
}

function normalizePublicPath(value) {
  const text = normalizeText(value) || "/";
  try {
    const url = new URL(text);
    return `${url.pathname}${url.search}${url.hash}` || "/";
  } catch (_error) {
    return text.startsWith("/") ? text : `/${text}`;
  }
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function ensureTrailingSlash(value) {
  const text = String(value || "");
  return text.endsWith("/") ? text : `${text}/`;
}
