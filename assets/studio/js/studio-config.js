const DEFAULT_STUDIO_CONFIG = {
  studio_config_version: "studio_config_v1",
  updated_at_utc: "",
  paths: {
    routes: {
      studio_home: "/studio/",
      search: "/search/",
      series_tags: "/studio/series-tags/",
      series_tag_editor: "/studio/series-tag-editor/",
      tag_registry: "/studio/tag-registry/",
      tag_aliases: "/studio/tag-aliases/",
      tag_groups: "/studio/tag-groups/",
      series_page_base: "/series/",
      docs_page: "/docs/",
      library_page: "/library/",
      works_page_base: "/works/",
      site_map: "/site_map/"
    },
    data: {
      studio: {
        tag_registry: "/assets/studio/data/tag_registry.json",
        tag_aliases: "/assets/studio/data/tag_aliases.json",
        tag_assignments: "/assets/studio/data/tag_assignments.json",
        tag_groups: "/assets/studio/data/tag_groups.json"
      },
      site: {
        series_index: "/assets/data/series_index.json",
        works_index: "/assets/data/works_index.json"
      },
      search: {
        policy: "/assets/data/search/policy.json",
        scopes: {
          catalogue: {
            index: "/assets/data/search/catalogue/index.json"
          },
          library: {
            index: "/assets/data/search/library/index.json"
          },
          studio: {
            index: "/assets/data/search/studio/index.json"
          }
        }
      }
    }
  },
  analysis: {
    groups: {
      ordered: ["subject", "domain", "form", "theme"],
      coverage_groups: ["subject", "domain", "form", "theme"]
    },
    rag: {
      deprecated_statuses: ["deprecated", "candidate"],
      completeness: {
        group_coverage_denominator: 4,
        tag_bonus_max: 0.25,
        tag_bonus_cap_at_total_tags: 6,
        score_cap: 1
      },
      rules: {
        red: {
          if_total_tags_eq: 0,
          if_unknown_tags_gt: 0
        },
        amber: {
          if_groups_present_lte: 1,
          if_total_tags_lt: 3,
          if_deprecated_tags_gt: 0,
          if_missing_all_groups: ["form", "theme"]
        },
        green: {
          fallback: true
        }
      }
    }
  },
  ui_text: {
    series_tag_editor: {
      missing_series_id_error: "Tag Studio error: missing series id.",
      load_failed_error: "Failed to load tag data. Check /assets/studio/data/tag_registry.json, /assets/studio/data/tag_aliases.json, /assets/studio/data/tag_assignments.json, /assets/data/series_index.json, and /assets/data/works_index.json.",
      work_input_placeholder: "work_id(s) in this series",
      tag_input_placeholder: "tag slug or alias",
      add_button: "Add",
      save_button: "Save Tags",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Offline session",
      modal_title: "Work Tag Patch Preview",
      modal_resolved_label: "Resolved work override tags",
      modal_patch_guidance_label: "Patch guidance for tag_assignments.json",
      modal_copy_button: "Copy",
      modal_close_button: "Close",
      context_hint_default: "Select one or more works to add per-work tag overrides. Series tags shown below are context only.",
      context_hint_selected: "Monochrome pills are inherited from the series. Colored pills are saved as work-only overrides.",
      chip_caption_local: "local",
      chip_caption_delete: "delete",
      restore_deleted_tag_aria_label: "Restore {tag_id}",
      series_tag_restored: "Series tag restored.",
      work_tag_restored: "Work tag restored.",
      work_tag_restore_inherited_warning: "Cannot restore {tag_id} while it is inherited from the series.",
      save_warning_unresolved: "Resolve unknown tags before saving.",
      save_status_no_changes: "No changes to save.",
      save_status_copy: "Patch guidance copied to clipboard.",
      save_status_local_failed: "Local save failed. Switched to offline mode.",
      save_result_local_failed: "Local server save failed. Changes are now staged in the offline session.",
      save_result_offline_staged: "Changes are staged in the offline session.",
      save_result_offline_cleared: "Series matches repo data. Offline session entry cleared.",
      save_result_server_available_import: "Local server now available. Apply offline changes using Series Tags > Import.",
      save_status_success_base: "Saved {saved_count} work row{saved_plural}",
      save_status_success_removed_suffix: "; removed {removed_count} row{removed_plural}",
      save_status_success_at_suffix: " at {saved_at}."
    },
    series_tags: {
      load_failed_error: "Failed to load series tag data.",
      empty_state: "none",
      table_heading_series: "series",
      table_heading_status: "status",
      table_heading_tags: "tags",
      filter_all_tags: "All tags",
      group_info_title: "Open group descriptions in a new tab",
      group_info_aria_label: "Open group descriptions in a new tab",
      session_open_button: "Session",
      import_open_button: "Import",
      session_modal_title: "Offline session",
      import_modal_title: "Import assignments",
      modal_close_button: "Close",
      session_summary_label: "Offline session",
      session_summary_value: "{count} staged series",
      session_updated_value: "Updated: {updated_at}",
      session_updated_empty: "not yet",
      session_copy_button: "Copy JSON",
      session_download_button: "Download JSON",
      session_clear_button: "Clear session",
      session_copy_success: "Offline session JSON copied.",
      session_copy_failed: "Copy failed. Select and copy manually.",
      session_download_success: "Offline session JSON download started.",
      session_clear_success: "Offline session cleared.",
      session_import_label: "Import assignments",
      session_import_choose_button: "Choose file",
      session_import_preview_button: "Preview import",
      session_import_apply_button: "Apply import",
      session_import_selected_file: "Selected: {filename}",
      session_import_no_file: "No import file selected.",
      session_import_unavailable: "Import requires the local server.",
      session_import_invalid_json: "Import file is not valid JSON.",
      session_import_preview_success: "Import preview ready.",
      session_import_preview_failed: "Import preview failed.",
      session_import_apply_without_preview: "Preview the import before applying it.",
      session_import_apply_success: "Import applied.",
      session_import_apply_failed: "Import failed.",
      session_import_resolution_label: "resolution",
      session_import_resolution_skip: "skip",
      session_import_resolution_overwrite: "overwrite",
      chip_caption_local: "local",
      chip_caption_delete: "delete",
      session_import_invalid_work_ids: "Invalid works: {work_ids}",
      session_import_status_apply: "Ready to apply.",
      session_import_status_conflict: "Conflict with current repo row.",
      session_import_status_invalid: "Invalid staged data.",
      session_import_status_missing: "Series not found in current site data."
    },
    studio_works: {
      copy_series_button: "copy series"
    },
    search: {
      load_failed_error: "Failed to load search data.",
      loading: "loading search index…",
      prompt: "Enter a search query.",
      no_results: "No results.",
      results_count: "{count} results",
      results_count_one: "1 result",
      results_count_visible: "Showing {visible} of {count} results",
      load_more: "more",
      result_meta_separator: " • ",
      result_kind_work: "work",
      result_kind_series: "series",
      result_kind_moment: "moment"
    }
  }
};

const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
let studioConfigPromise = null;

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

export function computeStudioTagMetrics(assignedTags, registry, config) {
  const groups = getStudioGroups(config);
  const coverageGroups = getStudioCoverageGroups(config);
  const deprecatedStatuses = new Set(sanitizeStringArray(
    pathValue(config, ["analysis", "rag", "deprecated_statuses"]),
    DEFAULT_STUDIO_CONFIG.analysis.rag.deprecated_statuses
  ));
  const completenessCfg = mergeConfig(
    DEFAULT_STUDIO_CONFIG.analysis.rag.completeness,
    pathValue(config, ["analysis", "rag", "completeness"])
  );
  const counts = Object.fromEntries(groups.map((group) => [group, 0]));
  let nUnknown = 0;
  let nDeprecated = 0;
  let nTotal = 0;

  const uniqueTags = Array.from(
    new Set((Array.isArray(assignedTags) ? assignedTags : []).map((tag) => normalize(tag)).filter(Boolean))
  );

  for (const tagId of uniqueTags) {
    nTotal += 1;
    const reg = registry.get(tagId);
    if (!reg) {
      nUnknown += 1;
      continue;
    }

    if (reg.group in counts) counts[reg.group] += 1;
    if (deprecatedStatuses.has(normalize(reg.status))) nDeprecated += 1;
  }

  const presentGroups = coverageGroups.filter((group) => Number(counts[group] || 0) > 0);
  const missingGroups = coverageGroups.filter((group) => Number(counts[group] || 0) === 0);
  const groupsPresent = presentGroups.length;
  const denominator = Math.max(
    1,
    Number(completenessCfg.group_coverage_denominator) || coverageGroups.length || 1
  );
  const tagBonusCap = Math.max(1, Number(completenessCfg.tag_bonus_cap_at_total_tags) || 1);
  const tagBonusMax = Math.max(0, Number(completenessCfg.tag_bonus_max) || 0);
  const scoreCap = Math.max(0, Number(completenessCfg.score_cap) || 1);
  const completenessBase = groupsPresent / denominator;
  const tagBonus = (Math.min(nTotal, tagBonusCap) / tagBonusCap) * tagBonusMax;
  const completeness = Math.min(scoreCap, completenessBase + tagBonus);

  return {
    nTotal,
    nUnknown,
    nDeprecated,
    counts,
    groupsPresent,
    presentGroups,
    missingGroups,
    completeness
  };
}

export function computeStudioRag(metrics, config) {
  const rules = mergeConfig(
    DEFAULT_STUDIO_CONFIG.analysis.rag.rules,
    pathValue(config, ["analysis", "rag", "rules"])
  );
  const redRule = rules.red || {};
  const amberRule = rules.amber || {};
  const totalTagsEq = Number(redRule.if_total_tags_eq);
  const unknownTagsGt = Number(redRule.if_unknown_tags_gt);
  if (
    (Number.isFinite(totalTagsEq) && metrics.nTotal === totalTagsEq) ||
    (Number.isFinite(unknownTagsGt) && metrics.nUnknown > unknownTagsGt)
  ) {
    return "red";
  }

  const groupsPresentLte = Number(amberRule.if_groups_present_lte);
  const totalTagsLt = Number(amberRule.if_total_tags_lt);
  const deprecatedTagsGt = Number(amberRule.if_deprecated_tags_gt);
  const missingAllGroups = sanitizeStringArray(amberRule.if_missing_all_groups, []);
  const isMissingAll = missingAllGroups.length > 0 && missingAllGroups.every((group) => metrics.missingGroups.includes(group));
  if (
    (Number.isFinite(groupsPresentLte) && metrics.groupsPresent <= groupsPresentLte) ||
    (Number.isFinite(totalTagsLt) && metrics.nTotal < totalTagsLt) ||
    (Number.isFinite(deprecatedTagsGt) && metrics.nDeprecated > deprecatedTagsGt) ||
    isMissingAll
  ) {
    return "amber";
  }

  return "green";
}

export function buildStudioRagTooltip(metrics) {
  const groupsLabel = metrics.presentGroups.length ? metrics.presentGroups.join(", ") : "none";
  const missingLabel = metrics.missingGroups.length ? metrics.missingGroups.join(", ") : "none";
  return (
    `tags: ${metrics.nTotal}; groups: ${groupsLabel}; missing: ${missingLabel}; ` +
    `unknown: ${metrics.nUnknown}; deprecated: ${metrics.nDeprecated}; ` +
    `completeness: ${metrics.completeness.toFixed(2)}`
  );
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
