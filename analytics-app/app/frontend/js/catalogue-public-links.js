import {
  getStudioRoute
} from "./studio-config.js";
import {
  buildPublicSiteUrl
} from "./studio-navigation.js";

export function buildPublicCatalogueUrl(config, path = "/", params = {}) {
  const normalizedPath = normalizePublicPath(path);
  return buildPublicSiteUrl(config, normalizedPath, params);
}

export function buildPublicWorkUrl(config, workId, params = {}) {
  return buildPublicRecordUrl(config, "works_page_base", "/works/", workId, params);
}

export function buildPublicSeriesUrl(config, seriesId, params = {}) {
  return buildPublicRecordUrl(config, "series_page_base", "/series/", seriesId, params);
}

export function buildPublicWorkDetailUrl(config, detailUid, params = {}) {
  return buildPublicRecordUrl(config, "work_details_page_base", "/work_details/", detailUid, params);
}

export function buildPublicMomentUrl(config, momentId, params = {}) {
  return buildPublicRecordUrl(config, "moments_page_base", "/moments/", momentId, params);
}

function buildPublicRecordUrl(config, routeKey, fallbackBase, recordId, params = {}) {
  const id = normalizeText(recordId);
  const routeBase = normalizeRouteBase(getStudioRoute(config, routeKey) || fallbackBase);
  return buildPublicCatalogueUrl(config, id ? `${routeBase}${encodeURIComponent(id)}/` : routeBase, params);
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
