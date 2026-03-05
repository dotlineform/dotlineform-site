const DEFAULT_STUDIO_CONFIG = {
  studio_config_version: "studio_config_v1",
  updated_at_utc: "",
  paths: {
    routes: {
      studio_home: "/studio/",
      series_tags: "/studio/series-tags/",
      series_tag_editor: "/studio/series-tag-editor/",
      tag_registry: "/studio/tag-registry/",
      tag_aliases: "/studio/tag-aliases/",
      tag_groups: "/studio/tag-groups/",
      series_page_base: "/series/",
      works_page_base: "/works/",
      site_map: "/site_map/"
    },
    data: {
      studio: {
        tag_registry: "/assets/data/tag_registry.json",
        tag_aliases: "/assets/data/tag_aliases.json",
        tag_assignments: "/assets/data/tag_assignments.json",
        tag_groups: "/assets/data/tag_groups.json"
      },
      site: {
        series_index: "/assets/data/series_index.json",
        works_index: "/assets/data/works_index.json"
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
  }
};

const CONFIG_URL = new URL("../data/studio/studio_config.json", import.meta.url);
const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
let studioConfigPromise = null;

export {
  DEFAULT_STUDIO_CONFIG
};

export async function loadStudioConfig() {
  if (!studioConfigPromise) {
    studioConfigPromise = fetch(CONFIG_URL, { cache: "default" })
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
  return resolveSitePath(typeof path === "string" ? path : "");
}

export function getSiteDataPath(config, key) {
  const path = pathValue(config, ["paths", "data", "site", key]);
  return resolveSitePath(typeof path === "string" ? path : "");
}

export function getStudioRoute(config, key) {
  const path = pathValue(config, ["paths", "routes", key]);
  return resolveSitePath(typeof path === "string" ? path : "");
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
  const marker = "/assets/js/";
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
