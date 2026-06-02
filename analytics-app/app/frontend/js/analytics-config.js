const DEFAULT_ANALYTICS_CONFIG = {
  "analytics_config_version": "analytics_config_v1",
  "updated_at_utc": "2026-05-30T00:00:00Z",
  "app": {
    "routes": {
      "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/analytics/tag-groups/",
        "script": "/analytics/app/frontend/js/tag-groups.js",
        "nav": false
      },
      "tag_registry": {
        "label": "registry",
        "title": "Tag Registry",
        "path": "/analytics/tag-registry/",
        "script": "/analytics/app/frontend/js/tag-registry.js",
        "nav": false
      },
      "tag_aliases": {
        "label": "aliases",
        "title": "Tag Aliases",
        "path": "/analytics/tag-aliases/",
        "script": "/analytics/app/frontend/js/tag-aliases.js",
        "nav": false
      },
      "series_tags": {
        "label": "series tags",
        "title": "Series Tags",
        "path": "/analytics/series-tags/",
        "script": "/analytics/app/frontend/js/series-tags.js",
        "nav": false
      },
      "series_tag_editor": {
        "label": "tag editor",
        "title": "Series Tag Editor",
        "path": "/analytics/series-tag-editor/",
        "script": "/analytics/app/frontend/js/series-tag-editor-page.js",
        "nav": false
      },
      "data_sharing_prepare": {
        "label": "prepare share",
        "title": "Prepare Share Package",
        "path": "/analytics/data-sharing/prepare/?mode=manage",
        "script": "/analytics/app/frontend/js/data-sharing-prepare.js",
        "nav": false
      },
      "data_sharing_review": {
        "label": "review share",
        "title": "Review Returned Package",
        "path": "/analytics/data-sharing/review/?mode=manage",
        "script": "/analytics/app/frontend/js/data-sharing-review.js",
        "nav": false
      }
    }
  },
  "paths": {
    "data": {
      "site": {
        "series_index": "/assets/data/series_index.json",
        "works_index": "/assets/data/works_index.json"
      },
      "ui_text": {
        "tag_registry": "/analytics/app/frontend/config/ui-text/tag-registry.json",
        "tag_aliases": "/analytics/app/frontend/config/ui-text/tag-aliases.json",
        "data_sharing_review": "/analytics/app/frontend/config/ui-text/data-sharing-review.json",
        "data_sharing_prepare": "/analytics/app/frontend/config/ui-text/data-sharing-prepare.json",
        "series_tag_editor": "/analytics/app/frontend/config/ui-text/series-tag-editor.json",
        "series_tags": "/analytics/app/frontend/config/ui-text/series-tags.json",
        "tag_groups": "/analytics/app/frontend/config/ui-text/tag-groups.json"
      }
    }
  },
  "analysis": {
    "groups": {
      "ordered": [
        "subject",
        "domain",
        "form",
        "theme"
      ],
      "coverage_groups": [
        "subject",
        "domain",
        "form",
        "theme"
      ]
    },
    "rag": {
      "deprecated_statuses": [
        "deprecated",
        "candidate"
      ],
      "completeness": {
        "group_coverage_denominator": 4,
        "tag_bonus_max": 0.25,
        "tag_bonus_cap_at_total_tags": 6,
        "score_cap": 1.0
      },
      "rules": {
        "red": {
          "if_total_tags_eq": 0,
          "if_unknown_tags_gt": 0
        },
        "amber": {
          "if_groups_present_lte": 1,
          "if_total_tags_lt": 3,
          "if_deprecated_tags_gt": 0,
          "if_missing_all_groups": [
            "form",
            "theme"
          ]
        },
        "green": {
          "fallback": true
        }
      }
    }
  }
};

const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
let analyticsConfigPromise = null;
const scopedTextPromises = new Map();

export {
  DEFAULT_ANALYTICS_CONFIG
};

export async function loadAnalyticsConfig() {
  if (!analyticsConfigPromise) {
    analyticsConfigPromise = fetch(resolveAnalyticsConfigUrl(), { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => mergeConfig(DEFAULT_ANALYTICS_CONFIG, data));
  }
  return analyticsConfigPromise;
}

function resolveAnalyticsConfigUrl() {
  const configuredUrl = readConfiguredAnalyticsConfigUrl();
  if (configuredUrl) {
    return buildAssetUrl(resolveSitePath(configuredUrl));
  }
  throw new Error('Analytics runtime config meta tag is required: meta[name="dlf-analytics-config-url"]');
}

function readConfiguredAnalyticsConfigUrl() {
  if (typeof document === "undefined") return "";
  const meta = document.querySelector('meta[name="dlf-analytics-config-url"]');
  return meta ? String(meta.getAttribute("content") || "").trim() : "";
}

export async function loadAnalyticsConfigWithText(group) {
  const config = await loadAnalyticsConfig();
  await loadScopedAnalyticsText(config, group);
  return config;
}

export async function loadScopedAnalyticsText(config, group) {
  const normalizedGroup = normalizeUiTextGroup(group);
  const targetConfig = config && typeof config === "object" ? config : {};
  if (!normalizedGroup) return targetConfig;
  if (pathValue(targetConfig, ["ui_text", normalizedGroup]) && typeof pathValue(targetConfig, ["ui_text", normalizedGroup]) === "object") {
    return targetConfig;
  }

  const url = getAnalyticsUiTextPath(targetConfig, normalizedGroup);
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

export function getAnalyticsGroups(config) {
  const fallback = DEFAULT_ANALYTICS_CONFIG.analysis.groups.ordered;
  return sanitizeStringArray(pathValue(config, ["analysis", "groups", "ordered"]), fallback);
}

export function getAnalyticsCoverageGroups(config) {
  const fallback = getAnalyticsGroups(config);
  return sanitizeStringArray(pathValue(config, ["analysis", "groups", "coverage_groups"]), fallback);
}

export function getSiteDataPath(config, key) {
  const path = pathValue(config, ["paths", "data", "site", key]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getAnalyticsUiTextPath(config, group) {
  const normalizedGroup = normalizeUiTextGroup(group);
  const path = pathValue(config, ["paths", "data", "ui_text", normalizedGroup]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getAnalyticsRoute(config, key) {
  const path = pathValue(config, ["app", "routes", key, "path"]);
  return resolveSitePath(typeof path === "string" ? path : "");
}

export function buildAnalyticsRouteUrl(config, key, params = {}) {
  const route = getAnalyticsRoute(config, key);
  if (!route) return "";
  return appendRouteParams(route, params);
}

export function getAnalyticsText(config, key, fallback = "", tokens = null) {
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

function warnScopedTextFallback(group, detail) {
  if (typeof console === "undefined" || !console.warn) return;
  console.warn(`analytics_config: scoped ui_text.${group} unavailable; using caller fallback copy`, detail);
}

function deriveSiteBasePath(importUrl) {
  const pathname = new URL(importUrl).pathname || "";
  const marker = "/analytics/app/frontend/js/";
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

function sanitizeStringArray(value, fallback) {
  const source = Array.isArray(value) ? value : fallback;
  const out = [];
  const seen = new Set();
  for (const raw of source) {
    const item = normalize(raw);
    if (!item || seen.has(item)) continue;
    seen.add(item);
    out.push(item);
  }
  return out;
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

function mergeConfig(base, override) {
  const baseValue = cloneJson(base);
  if (!override || typeof override !== "object" || Array.isArray(override)) return baseValue;
  const output = baseValue;
  for (const [key, value] of Object.entries(override)) {
    if (Array.isArray(value)) {
      output[key] = value.slice();
      continue;
    }
    if (value && typeof value === "object") {
      output[key] = mergeConfig(output[key] || {}, value);
      continue;
    }
    output[key] = value;
  }
  return output;
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}
