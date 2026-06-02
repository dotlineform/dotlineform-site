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

function buildPublicSiteUrl(config, path = "/", params = {}, options = {}) {
  const siteKey = options && options.site === "production" ? "production" : "public_preview";
  const base = getAnalyticsSiteBase(config, siteKey);
  if (!base) {
    throw new Error(`Missing Analytics site base: ${siteKey}`);
  }
  const url = new URL(String(path || "/"), ensureTrailingSlash(base));
  for (const [key, value] of Object.entries(params || {})) {
    if (!key || value == null || value === "") continue;
    url.searchParams.set(key, String(value));
  }
  return url.href;
}

function getAnalyticsSiteBase(config, siteKey) {
  const runtime = config && config.app && config.app.runtime;
  const sites = runtime && runtime.sites && typeof runtime.sites === "object" && !Array.isArray(runtime.sites)
    ? runtime.sites
    : {};
  const site = sites && sites[siteKey];
  const value = site && site.base;
  return typeof value === "string" && value.trim() ? value.trim().replace(/\/+$/, "") : "";
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
