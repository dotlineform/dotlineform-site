const DEFAULT_STUDIO_CONFIG = {
  "studio_config_version": "studio_config_v1",
  "updated_at_utc": "2026-05-08T16:08:10Z",
  "paths": {
    "routes": {
      "studio_home": "/studio/",
      "studio_audits": "/studio/audits/",
      "search": "/search/",
      "series_tags": "/studio/analytics/series-tags/",
      "series_tag_editor": "/studio/analytics/series-tag-editor/",
      "catalogue_field_registry_review": "/studio/catalogue-field-registry/",
      "docs_broken_links": "/studio/docs-broken-links/",
      "project_state": "/studio/project-state/",
      "docs_html_import": "/studio/docs-import/",
      "library_documents": "/studio/library-documents/",
      "data_export": "/studio/export/",
      "data_import": "/studio/import/",
      "catalogue_status": "/studio/catalogue-status/",
      "activity": "/studio/activity/",
      "bulk_add_work": "/studio/bulk-add-work/",
      "catalogue_moment_import": "/studio/catalogue-moment/",
      "catalogue_moment_editor": "/studio/catalogue-moment/",
      "catalogue_work_editor": "/studio/catalogue-work/",
      "catalogue_work_detail_editor": "/studio/catalogue-work-detail/",
      "catalogue_series_editor": "/studio/catalogue-series/",
      "tag_registry": "/studio/analytics/tag-registry/",
      "tag_aliases": "/studio/analytics/tag-aliases/",
      "tag_groups": "/studio/analytics/tag-groups/",
      "series_page_base": "/series/",
      "docs_page": "/docs/",
      "library_page": "/library/",
      "analysis_page": "/analysis/",
      "moments_page_base": "/moments/",
      "works_page_base": "/works/",
      "work_details_page_base": "/work_details/"
    },
    "data": {
      "studio": {
        "tag_registry": "/assets/studio/data/tag_registry.json",
        "tag_aliases": "/assets/studio/data/tag_aliases.json",
        "tag_assignments": "/assets/studio/data/tag_assignments.json",
        "tag_groups": "/assets/studio/data/tag_groups.json",
        "activity_log": "/assets/studio/data/activity_log.json",
        "catalogue_works": "/assets/studio/data/catalogue/works.json",
        "catalogue_work_details": "/assets/studio/data/catalogue/work_details.json",
        "catalogue_series": "/assets/studio/data/catalogue/series.json",
        "catalogue_moments": "/assets/studio/data/catalogue/moments.json",
        "catalogue_lookup_work_search": "/assets/studio/data/catalogue_lookup/work_search.json",
        "catalogue_lookup_series_search": "/assets/studio/data/catalogue_lookup/series_search.json",
        "catalogue_lookup_work_detail_search": "/assets/studio/data/catalogue_lookup/work_detail_search.json",
        "catalogue_lookup_meta": "/assets/studio/data/catalogue_lookup/meta.json",
        "catalogue_lookup_work_base": "/assets/studio/data/catalogue_lookup/works/",
        "catalogue_lookup_work_detail_base": "/assets/studio/data/catalogue_lookup/work_details/",
        "catalogue_lookup_series_base": "/assets/studio/data/catalogue_lookup/series/",
        "catalogue_field_registry": "/assets/studio/data/catalogue_field_registry.json",
        "export_import_adapters": "/assets/studio/data/export_import_adapters.json",
        "library_export_configs": "/assets/studio/data/library_export_configs.json"
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
            "index": "/assets/data/docs/scopes/studio/index.json"
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
            "index": "/assets/data/search/studio/index.json"
          },
          "analysis": {
            "index": "/assets/data/search/analysis/index.json"
          }
        }
      },
      "ui_text": {
        "catalogue_work_editor": "/assets/studio/data/ui_text/catalogue-work-editor.json",
        "catalogue_work_detail_editor": "/assets/studio/data/ui_text/catalogue-work-detail-editor.json",
        "catalogue_series_editor": "/assets/studio/data/ui_text/catalogue-series-editor.json",
        "catalogue_moment_editor": "/assets/studio/data/ui_text/catalogue-moment-editor.json",
        "tag_registry": "/assets/studio/data/ui_text/tag-registry.json",
        "tag_aliases": "/assets/studio/data/ui_text/tag-aliases.json",
        "data_import": "/assets/studio/data/ui_text/data-import.json",
        "data_export": "/assets/studio/data/ui_text/data-export.json",
        "docs_viewer": "/assets/studio/data/ui_text/docs-viewer.json",
        "activity_log": "/assets/studio/data/ui_text/activity-log.json",
        "bulk_add_work": "/assets/studio/data/ui_text/bulk-add-work.json",
        "catalogue_field_registry_review": "/assets/studio/data/ui_text/catalogue-field-registry-review.json",
        "catalogue_moment_import": "/assets/studio/data/ui_text/catalogue-moment-import.json",
        "catalogue_status": "/assets/studio/data/ui_text/catalogue-status.json",
        "docs_broken_links": "/assets/studio/data/ui_text/docs-broken-links.json",
        "docs_html_import": "/assets/studio/data/ui_text/docs-html-import.json",
        "library_documents": "/assets/studio/data/ui_text/library-documents.json",
        "project_state": "/assets/studio/data/ui_text/project-state.json",
        "series_tag_editor": "/assets/studio/data/ui_text/series-tag-editor.json",
        "series_tags": "/assets/studio/data/ui_text/series-tags.json",
        "site_series_index": "/assets/studio/data/ui_text/site-series-index.json",
        "studio_audits": "/assets/studio/data/ui_text/studio-audits.json",
        "studio_works": "/assets/studio/data/ui_text/studio-works.json",
        "tag_groups": "/assets/studio/data/ui_text/tag-groups.json"
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
    studioConfigPromise = fetch(buildAssetUrl(new URL("../data/studio_config.json", import.meta.url).href), { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => mergeConfig(DEFAULT_STUDIO_CONFIG, data))
      .catch((error) => {
        console.warn("studio_config: using defaults after config load failure", error);
        return cloneJson(DEFAULT_STUDIO_CONFIG);
      });
  }
  return studioConfigPromise;
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

export function getStudioRoute(config, key) {
  const path = pathValue(config, ["paths", "routes", key]);
  return resolveSitePath(typeof path === "string" ? path : "");
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

function warnScopedTextFallback(group, detail) {
  if (typeof console === "undefined" || !console.warn) return;
  console.warn(`studio_config: scoped ui_text.${group} unavailable; using caller fallback copy`, detail);
}

function deriveSiteBasePath(importUrl) {
  const pathname = new URL(importUrl).pathname || "";
  const marker = "/assets/studio/js/";
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
