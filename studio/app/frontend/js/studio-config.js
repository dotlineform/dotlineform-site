const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
let studioConfigPromise = null;
const scopedTextPromises = new Map();

export async function loadStudioConfig() {
  if (!studioConfigPromise) {
    studioConfigPromise = fetch(resolveStudioConfigUrl(), { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      });
  }
  return studioConfigPromise;
}

function resolveStudioConfigUrl() {
  const configuredUrl = readConfiguredStudioConfigUrl();
  if (configuredUrl) {
    return buildAssetUrl(resolveSitePath(configuredUrl));
  }
  throw new Error('Studio runtime config meta tag is required: meta[name="dlf-studio-config-url"]');
}

function readConfiguredStudioConfigUrl() {
  if (typeof document === "undefined") return "";
  const meta = document.querySelector('meta[name="dlf-studio-config-url"]');
  return meta ? String(meta.getAttribute("content") || "").trim() : "";
}

export async function loadStudioConfigWithText(group) {
  const config = await loadStudioConfig();
  await loadScopedStudioText(config, group);
  return config;
}

export async function loadScopedStudioText(config, group) {
  const normalizedGroup = normalizeUiTextGroup(group);
  const targetConfig = config && typeof config === "object" ? config : {};
  if (!normalizedGroup) return targetConfig;
  if (pathValue(targetConfig, ["ui_text", normalizedGroup]) && typeof pathValue(targetConfig, ["ui_text", normalizedGroup]) === "object") {
    return targetConfig;
  }

  const url = getStudioUiTextPath(targetConfig, normalizedGroup);
  if (!url) {
    warnScopedTextFallback(normalizedGroup, "missing scoped text path");
    return targetConfig;
  }

  let request = scopedTextPromises.get(url);
  if (!request) {
    request = fetch(url, { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      });
    scopedTextPromises.set(url, request);
  }

  try {
    const payload = await request;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("expected object payload");
    }
    if (!targetConfig.ui_text || typeof targetConfig.ui_text !== "object" || Array.isArray(targetConfig.ui_text)) {
      targetConfig.ui_text = {};
    }
    targetConfig.ui_text[normalizedGroup] = payload;
  } catch (error) {
    scopedTextPromises.delete(url);
    warnScopedTextFallback(normalizedGroup, error);
  }
  return targetConfig;
}

export function getStudioDataPath(config, key) {
  const path = pathValue(config, ["paths", "data", "studio", key]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getSiteDataPath(config, key) {
  const path = pathValue(config, ["paths", "data", "site", key]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getDocsScopeDataPath(config, scope, key = "index") {
  const normalizedScope = normalize(scope);
  const path = pathValue(config, ["paths", "data", "docs", "scopes", normalizedScope, key]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getSearchScopeDataPath(config, scope, key = "index") {
  const normalizedScope = normalize(scope);
  const path = pathValue(config, ["paths", "data", "search", "scopes", normalizedScope, key]);
  if (typeof path === "string" && path.trim()) {
    return resolveSiteAssetPath(path);
  }

  if (normalizedScope === "catalogue") {
    const legacyPath = pathValue(config, ["paths", "data", "site", "search_index"]);
    if (typeof legacyPath === "string" && legacyPath.trim()) {
      return resolveSiteAssetPath(legacyPath);
    }
  }

  return "";
}

export function getSearchPolicyPath(config) {
  const path = pathValue(config, ["paths", "data", "search", "policy"]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getStudioUiTextPath(config, group) {
  const normalizedGroup = normalizeUiTextGroup(group);
  const path = pathValue(config, ["paths", "data", "ui_text", normalizedGroup]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getStudioRouteRegistry(config) {
  const routes = pathValue(config, ["app", "routes"]);
  return routes && typeof routes === "object" && !Array.isArray(routes) ? routes : {};
}

export function getStudioRouteEntry(config, key) {
  const normalizedKey = normalizeRouteKey(key);
  const routes = getStudioRouteRegistry(config);
  const entry = routes[normalizedKey];
  return entry && typeof entry === "object" && !Array.isArray(entry) ? entry : null;
}

export function getStudioRoute(config, key) {
  const routeEntry = getStudioRouteEntry(config, key);
  if (routeEntry && typeof routeEntry.path === "string" && routeEntry.path.trim()) {
    return resolveSitePath(routeEntry.path);
  }
  const path = pathValue(config, ["paths", "routes", key]);
  return resolveSitePath(typeof path === "string" ? path : "");
}

export function buildStudioRouteUrl(config, key, params = {}) {
  const route = getStudioRoute(config, key);
  if (!route) return "";
  return appendRouteParams(route, params);
}

export function getStudioText(config, key, fallback = "", tokens = null) {
  const pathKeys = ["ui_text", ...String(key || "").split(".").filter(Boolean)];
  const value = pathValue(config, pathKeys);
  const source = typeof value === "string" ? value : fallback;
  return applyTextTokens(source, tokens);
}

function normalizeUiTextGroup(value) {
  return String(value || "")
    .trim()
    .replace(/-/g, "_")
    .replace(/[^a-z0-9_]/gi, "");
}

function normalizeRouteKey(value) {
  return String(value || "")
    .trim()
    .replace(/-/g, "_")
    .toLowerCase();
}

function warnScopedTextFallback(group, detail) {
  if (typeof console === "undefined" || !console.warn) return;
  console.warn(`studio_config: scoped ui_text.${group} unavailable; using caller fallback copy`, detail);
}

function deriveSiteBasePath(importUrl) {
  const pathname = new URL(importUrl).pathname || "";
  const marker = "/studio/app/frontend/js/";
  const index = pathname.indexOf(marker);
  if (index < 0) return "";
  return pathname.slice(0, index).replace(/\/+$/, "");
}

function resolveSitePath(path) {
  if (!path) return "";
  if (/^[a-z]+:\/\//i.test(path)) return path;
  const cleanPath = `/${String(path).replace(/^\/+/, "")}`;
  return `${SITE_BASE_PATH}${cleanPath}`.replace(/\/{2,}/g, "/");
}

function resolveSiteAssetPath(path) {
  return buildAssetUrl(resolveSitePath(path));
}

function buildAssetUrl(path) {
  const resolvedPath = String(path || "");
  if (!resolvedPath) return "";

  const assetVersion = readAssetVersion(import.meta.url);
  if (!assetVersion) return resolvedPath;

  const [base, hash = ""] = resolvedPath.split("#", 2);
  const separator = base.includes("?") ? "&" : "?";
  return `${base}${separator}v=${encodeURIComponent(assetVersion)}${hash ? `#${hash}` : ""}`;
}

function appendRouteParams(route, params = {}) {
  const origin = currentOrigin();
  const url = new URL(String(route || "/"), origin);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (!key || value == null || value === "") return;
    url.searchParams.set(key, String(value));
  });
  return url.origin === origin ? `${url.pathname}${url.search}${url.hash}` : url.href;
}

function currentOrigin() {
  if (typeof window !== "undefined" && window.location && window.location.origin) {
    return window.location.origin;
  }
  return "http://127.0.0.1";
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

function pathValue(obj, keys) {
  let current = obj;
  for (const key of keys) {
    if (!current || typeof current !== "object" || !(key in current)) return undefined;
    current = current[key];
  }
  return current;
}

function applyTextTokens(text, tokens) {
  const template = typeof text === "string" ? text : "";
  if (!tokens || typeof tokens !== "object") return template;
  return template.replace(/\{([a-z0-9_]+)\}/gi, (match, key) => {
    if (!(key in tokens)) return match;
    const value = tokens[key];
    return value == null ? "" : String(value);
  });
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}
