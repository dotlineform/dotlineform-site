import {
  DEFAULT_ANALYTICS_CONFIG,
  getAnalyticsCoverageGroups,
  getAnalyticsGroups
} from "./analytics-config.js";

const STUDIO_RAG_ORDER = Object.freeze({
  red: 0,
  amber: 1,
  green: 2
});

export function buildStudioTagScore(assignedTags, registry, config) {
  const metrics = computeStudioTagMetrics(assignedTags, registry, config);
  const rag = computeStudioRag(metrics, config);
  const tooltip = buildStudioRagTooltip(metrics);
  return {
    metrics,
    rag,
    ragRank: rankStudioRag(rag),
    tooltip,
    ragLabel: `status ${rag.toUpperCase()}: ${tooltip}`
  };
}

export function computeStudioTagMetrics(assignedTags, registry, config) {
  const groups = getAnalyticsGroups(config);
  const coverageGroups = getAnalyticsCoverageGroups(config);
  const completenessCfg = mergeConfig(
    DEFAULT_ANALYTICS_CONFIG.analysis.rag.completeness,
    pathValue(config, ["analysis", "rag", "completeness"])
  );
  const counts = Object.fromEntries(groups.map((group) => [group, 0]));
  let nUnknown = 0;
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
    counts,
    groupsPresent,
    presentGroups,
    missingGroups,
    completeness
  };
}

export function computeStudioRag(metrics, config) {
  const rules = mergeConfig(
    DEFAULT_ANALYTICS_CONFIG.analysis.rag.rules,
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
  const missingAllGroups = sanitizeStringArray(amberRule.if_missing_all_groups, []);
  const isMissingAll = missingAllGroups.length > 0 && missingAllGroups.every((group) => metrics.missingGroups.includes(group));
  if (
    (Number.isFinite(groupsPresentLte) && metrics.groupsPresent <= groupsPresentLte) ||
    (Number.isFinite(totalTagsLt) && metrics.nTotal < totalTagsLt) ||
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
    `unknown: ${metrics.nUnknown}; ` +
    `completeness: ${metrics.completeness.toFixed(2)}`
  );
}

export function rankStudioRag(rag) {
  const key = normalize(rag);
  return Number.isInteger(STUDIO_RAG_ORDER[key]) ? STUDIO_RAG_ORDER[key] : Number.MAX_SAFE_INTEGER;
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
