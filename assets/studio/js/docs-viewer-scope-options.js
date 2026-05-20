const DEFAULT_DOCS_VIEWER_CONFIG_URL = "/assets/docs-viewer/data/docs-viewer-config.json";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeScopeOption(scope) {
  return {
    scopeId: normalizeText(scope && scope.scope_id).toLowerCase(),
    viewerBaseUrl: normalizeText(scope && scope.viewer_base_url)
  };
}

function normalizeViewerPath(path) {
  const normalized = normalizeText(path).replace(/\/+$/, "");
  return normalized || "/";
}

export async function loadDocsViewerScopeOptions(configUrl = DEFAULT_DOCS_VIEWER_CONFIG_URL) {
  const response = await fetch(configUrl, {
    headers: { Accept: "application/json" },
    cache: "default"
  });
  if (!response.ok) {
    throw new Error(`Failed to load Docs Viewer config (${response.status})`);
  }
  const payload = await response.json();
  if (!payload || payload.schema_version !== "docs_viewer_config_v1" || !Array.isArray(payload.scopes)) {
    throw new Error("Docs Viewer config has an unsupported schema.");
  }

  const seen = new Set();
  const scopes = payload.scopes.reduce((options, rawScope) => {
    const option = normalizeScopeOption(rawScope);
    if (!option.scopeId || seen.has(option.scopeId)) return options;
    seen.add(option.scopeId);
    options.push(option);
    return options;
  }, []);
  if (!scopes.length) {
    throw new Error("Docs Viewer config does not define any scopes.");
  }

  return {
    defaultScopeId: normalizeText(payload.default_scope_id).toLowerCase() || scopes[0].scopeId,
    scopes
  };
}

export function docsViewerScopeIds(scopeConfigs) {
  return Array.isArray(scopeConfigs) ? scopeConfigs.map((scope) => scope.scopeId).filter(Boolean) : [];
}

function currentHref(fallback = "") {
  if (typeof window !== "undefined" && window.location) return window.location.href;
  return fallback;
}

export function selectedDocsViewerScopeFromUrl(scopeConfigs, fallbackScope, href = "") {
  const validScopes = docsViewerScopeIds(scopeConfigs);
  const fallback = validScopes.includes(fallbackScope) ? fallbackScope : validScopes[0] || "";
  try {
    const url = new URL(href || currentHref());
    const scope = normalizeText(url.searchParams.get("scope")).toLowerCase();
    return validScopes.includes(scope) ? scope : fallback;
  } catch (_error) {
    return fallback;
  }
}

export function normalizedDocsViewerScope(scopeConfigs, value, fallbackScope = "studio") {
  const validScopes = docsViewerScopeIds(scopeConfigs);
  const selected = normalizeText(value).toLowerCase();
  if (validScopes.includes(selected)) return selected;
  return validScopes.includes(fallbackScope) ? fallbackScope : validScopes[0] || fallbackScope;
}

export function isDocsViewerPath(pathname, scopeConfigs) {
  const path = normalizeViewerPath(pathname);
  return Array.isArray(scopeConfigs)
    ? scopeConfigs.some((scope) => normalizeViewerPath(scope && scope.viewerBaseUrl) === path)
    : false;
}
