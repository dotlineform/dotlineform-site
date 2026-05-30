const DEFAULT_STUDIO_CONFIG = {
  "studio_config_version": "studio_config_v1",
  "updated_at_utc": "2026-05-12T00:00:00Z",
  "app": {
    "routes": {
      "docs": {
        "label": "docs",
        "title": "Docs",
        "path": "/docs/?mode=manage",
        "doc_id": "docs-viewer",
        "nav": true,
        "shell_type": "external",
        "ready_state_route_id": ""
      },
      "studio_audits": {
        "label": "audits",
        "title": "Studio Audits",
        "path": "/studio/audits/?mode=manage",
        "script": "/studio/app/frontend/js/studio-audits.js",
        "doc_id": "studio-audits",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "studio-audits"
      },
      "project_state": {
        "label": "project state",
        "title": "Project State",
        "path": "/studio/project-state/?mode=manage",
        "script": "/studio/app/frontend/js/project-state.js",
        "doc_id": "project-state-page",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "project-state"
      },
      "bulk_add_work": {
        "label": "bulk add",
        "title": "Bulk Add Work",
        "path": "/studio/bulk-add-work/?mode=manage",
        "script": "/studio/app/frontend/js/bulk-add-work.js",
        "doc_id": "bulk-add-work",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "bulk-add-work"
      },
      "activity": {
        "label": "activity",
        "title": "Studio Activity",
        "path": "/studio/activity/?mode=manage",
        "script": "/studio/app/frontend/js/activity-log.js",
        "doc_id": "studio-activity",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "studio-activity"
      },
      "catalogue_field_registry": {
        "label": "field registry",
        "title": "Catalogue Field Registry",
        "path": "/studio/catalogue-field-registry/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-field-registry-review.js",
        "doc_id": "catalogue-field-registry-review",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "catalogue-field-registry"
      },
      "catalogue_status": {
        "label": "drafts",
        "title": "Catalogue Drafts",
        "path": "/studio/catalogue-status/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-status.js",
        "doc_id": "catalogue-status",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "catalogue-status"
      },
      "studio_works": {
        "label": "works",
        "title": "Studio Works",
        "path": "/studio/studio-works/?mode=manage",
        "script": "/studio/app/frontend/js/studio-works.js",
        "doc_id": "studio-works",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "studio-works"
      },
      "catalogue_series_editor": {
        "label": "series editor",
        "title": "Catalogue Series Editor",
        "path": "/studio/catalogue-series/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-series-editor.js",
        "doc_id": "catalogue-series-editor",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "catalogue-series"
      },
      "catalogue_work_editor": {
        "label": "work editor",
        "title": "Catalogue Work Editor",
        "path": "/studio/catalogue-work/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-work-editor.js",
        "doc_id": "catalogue-work-editor",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "catalogue-work"
      },
      "catalogue_work_detail_editor": {
        "label": "detail editor",
        "title": "Catalogue Work Detail Editor",
        "path": "/studio/catalogue-work-detail/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-work-detail-editor.js",
        "doc_id": "catalogue-work-detail-editor",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "catalogue-work-detail"
      },
      "catalogue_moment_editor": {
        "label": "moment editor",
        "title": "Catalogue Moment Editor",
        "path": "/studio/catalogue-moment/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-moment-editor.js",
        "doc_id": "catalogue-moment-editor",
        "nav": false,
        "shell_type": "javascript",
        "ready_state_route_id": "catalogue-moment"
      }
    }
  },
  "paths": {
    "routes": {
      "search": "/catalogue/search/",
      "series_page_base": "/series/",
      "library_page": "/library/",
      "analysis_page": "/analysis/",
      "moments_page_base": "/moments/",
      "works_page_base": "/works/",
      "work_details_page_base": "/work_details/"
    },
    "data": {
      "studio": {
        "activity_log": "/studio/data/generated/activity/activity-log.json",
        "catalogue_works": "/studio/data/canonical/catalogue/works.json",
        "catalogue_work_details": "/studio/data/canonical/catalogue/work_details.json",
        "catalogue_series": "/studio/data/canonical/catalogue/series.json",
        "catalogue_moments": "/studio/data/canonical/catalogue/moments.json",
        "catalogue_lookup_work_search": "/studio/data/generated/catalogue-lookup/work_search.json",
        "catalogue_lookup_series_search": "/studio/data/generated/catalogue-lookup/series_search.json",
        "catalogue_lookup_work_detail_search": "/studio/data/generated/catalogue-lookup/work_detail_search.json",
        "catalogue_lookup_meta": "/studio/data/generated/catalogue-lookup/meta.json",
        "catalogue_lookup_work_base": "/studio/data/generated/catalogue-lookup/works/",
        "catalogue_lookup_work_detail_base": "/studio/data/generated/catalogue-lookup/work_details/",
        "catalogue_lookup_series_base": "/studio/data/generated/catalogue-lookup/series/",
        "catalogue_field_registry": "/studio/data/config/catalogue/catalogue-field-registry.json"
      },
      "site": {
        "series_index": "/assets/data/series_index.json",
        "works_index": "/assets/data/works_index.json"
      },
      "docs": {
        "scopes": {
          "library": {
            "index": "/assets/data/docs/scopes/library/index.json"
          },
          "studio": {
            "index": "/docs-viewer/generated/docs/studio/index.json"
          }
        }
      },
      "search": {
        "policy": "/assets/data/search/policy.json",
        "scopes": {
          "catalogue": {
            "index": "/assets/data/search/catalogue/index.json"
          },
          "library": {
            "index": "/assets/data/search/library/index.json"
          },
          "studio": {
            "index": "/docs-viewer/generated/search/studio/index.json"
          },
          "analysis": {
            "index": "/assets/data/search/analysis/index.json"
          }
        }
      },
      "ui_text": {
        "catalogue_work_editor": "/studio/app/frontend/config/ui-text/catalogue-work-editor.json",
        "catalogue_work_detail_editor": "/studio/app/frontend/config/ui-text/catalogue-work-detail-editor.json",
        "catalogue_series_editor": "/studio/app/frontend/config/ui-text/catalogue-series-editor.json",
        "catalogue_moment_editor": "/studio/app/frontend/config/ui-text/catalogue-moment-editor.json",
        "docs_viewer": "/docs-viewer/config/ui-text/ui-text.json",
        "activity_log": "/studio/app/frontend/config/ui-text/activity-log.json",
        "bulk_add_work": "/studio/app/frontend/config/ui-text/bulk-add-work.json",
        "catalogue_field_registry_review": "/studio/app/frontend/config/ui-text/catalogue-field-registry-review.json",
        "catalogue_status": "/studio/app/frontend/config/ui-text/catalogue-status.json",
        "project_state": "/studio/app/frontend/config/ui-text/project-state.json",
        "site_series_index": "/studio/app/frontend/config/ui-text/site-series-index.json",
        "studio_audits": "/studio/app/frontend/config/ui-text/studio-audits.json",
        "studio_works": "/studio/app/frontend/config/ui-text/studio-works.json"
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
  },
  "external_links": {
    "docs_viewer": {
      "base_url": "http://127.0.0.1:8776",
      "docs_path": "/docs/",
      "default_mode": "manage",
      "doc_scope": "studio"
    }
  },
  "docs_viewer": {
    "recently_added_limit": 10,
    "hidden_nav_color": "var(--muted)",
    "doc_hidden_emoji": "🚫",
    "ui_statuses_by_scope": {
      "studio": [
        {
          "ui_status": "draft",
          "label": "Draft",
          "emoji": "📝"
        },
        {
          "ui_status": "done",
          "label": "Done",
          "emoji": "✅"
        },
        {
          "ui_status": "urgent",
          "label": "Urgent",
          "emoji": "❗"
        },
        {
          "ui_status": "in-progress",
          "label": "In progress",
          "emoji": "🔄"
        }
      ],
      "library": [
        {
          "ui_status": "draft",
          "label": "Draft",
          "emoji": "📝"
        }
      ],
      "analysis": [
        {
          "ui_status": "draft",
          "label": "Draft",
          "emoji": "📝"
        }
      ]
    }
  },
  "catalogue": {
    "series_type_options": [
      "primary",
      "holding"
    ]
  }
};

const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
let studioConfigPromise = null;
const scopedTextPromises = new Map();

export {
  DEFAULT_STUDIO_CONFIG
};

export async function loadStudioConfig() {
  if (!studioConfigPromise) {
    studioConfigPromise = fetch(resolveStudioConfigUrl(), { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => mergeConfig(DEFAULT_STUDIO_CONFIG, data));
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

export function getStudioGroups(config) {
  const fallback = DEFAULT_STUDIO_CONFIG.analysis.groups.ordered;
  return sanitizeStringArray(pathValue(config, ["analysis", "groups", "ordered"]), fallback);
}

export function getStudioCoverageGroups(config) {
  const fallback = getStudioGroups(config);
  return sanitizeStringArray(pathValue(config, ["analysis", "groups", "coverage_groups"]), fallback);
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
