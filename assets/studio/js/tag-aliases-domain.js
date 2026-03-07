let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let MAX_ALIAS_TAGS = 4;
const TAG_ID_RE = /^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$/;

export function configureTagAliasesDomain(options = {}) {
  const groups = Array.isArray(options.groups) && options.groups.length
    ? options.groups.map((group) => normalize(group)).filter(Boolean)
    : STUDIO_GROUPS.slice();
  STUDIO_GROUPS = groups;

  const maxAliasTags = Number(options.maxAliasTags);
  if (Number.isInteger(maxAliasTags) && maxAliasTags > 0) {
    MAX_ALIAS_TAGS = maxAliasTags;
  }
}

export function buildRegistryLookup(data) {
  const map = new Map();
  const tags = Array.isArray(data && data.tags) ? data.tags : [];
  for (const raw of tags) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    const group = normalize(raw.group);
    const label = normalize(raw.label);
    if (!tagId || !STUDIO_GROUPS.includes(group) || !label) continue;
    map.set(tagId, { group, label });
  }
  return map;
}

export function buildGroupDescriptionMap(data) {
  const out = new Map();
  const groups = Array.isArray(data && data.groups) ? data.groups : [];
  for (const raw of groups) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalize(raw.group_id);
    const description = String(raw.description || "").trim();
    if (!STUDIO_GROUPS.includes(groupId) || !description) continue;
    out.set(groupId, description);
  }
  return out;
}

export function normalizeAliases(data, fallbackUpdatedAt, registryById, text) {
  const aliasesObj = data && typeof data.aliases === "object" && data.aliases ? data.aliases : {};
  const entries = [];

  for (const [rawAlias, rawValue] of Object.entries(aliasesObj)) {
    const alias = normalize(rawAlias);
    if (!alias) continue;
    let normalizedValue = null;
    try {
      normalizedValue = normalizeAliasValue(rawValue, text);
    } catch (error) {
      continue;
    }

    const targets = normalizedValue.targets;
    const resolvedTargets = targets.map((tagId) => {
      const info = registryById.get(tagId);
      return {
        tagId,
        group: info ? info.group : "",
        label: info ? info.label : tagId,
        known: Boolean(info)
      };
    });
    const groups = Array.from(new Set(resolvedTargets.filter((item) => item.known).map((item) => item.group)));
    const hasUnknown = resolvedTargets.some((item) => !item.known);
    const updatedAtUtc = fallbackUpdatedAt;

    entries.push({
      alias,
      value: normalizedValue.value,
      description: normalizedValue.description,
      targets,
      resolvedTargets,
      groups,
      hasUnknown,
      updatedAtUtc,
      updatedAtMs: toTimestampMs(updatedAtUtc)
    });
  }

  return entries;
}

export function normalizeAliasValue(rawValue, text) {
  if (rawValue && typeof rawValue === "object" && !Array.isArray(rawValue)) {
    const description = String(rawValue.description || "").trim();
    const tags = normalizeAliasTagsArray(rawValue.tags, text);
    return {
      description,
      value: { description, tags },
      targets: tags.slice()
    };
  }

  if (typeof rawValue === "string") {
    const value = normalize(rawValue);
    if (!TAG_ID_RE.test(value)) {
      throw new Error(textValue(text, "alias_value_invalid_tag_id", "Invalid alias tag_id value."));
    }
    return {
      description: "",
      value: { description: "", tags: [value] },
      targets: [value]
    };
  }

  const out = normalizeAliasTagsArray(rawValue, text);
  return {
    description: "",
    value: { description: "", tags: out },
    targets: out.slice()
  };
}

export function normalizeAliasTagsArray(rawValue, text) {
  if (!Array.isArray(rawValue)) {
    throw new Error(textValue(text, "alias_tags_array_required", "Alias tags must be an array."));
  }
  if (!rawValue.length) {
    throw new Error(textValue(text, "alias_tags_required", "Alias tags must include at least one tag_id."));
  }
  if (rawValue.length > MAX_ALIAS_TAGS) {
    throw new Error(textValue(text, "alias_tags_max", "Alias tags may include at most {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS }));
  }

  const out = [];
  const seen = new Set();
  const seenGroups = new Set();
  for (const raw of rawValue) {
    const value = normalize(raw);
    if (!value || !TAG_ID_RE.test(value)) {
      throw new Error(textValue(text, "alias_tag_array_invalid_value", "Invalid alias tag_id array value."));
    }
    if (seen.has(value)) continue;
    const group = value.split(":", 1)[0];
    if (seenGroups.has(group)) {
      throw new Error(textValue(text, "alias_tags_one_per_group", "Alias tags may include only one tag per group: {group}", { group }));
    }
    seen.add(value);
    seenGroups.add(group);
    out.push(value);
  }
  if (!out.length) {
    throw new Error(textValue(text, "alias_tags_required", "Alias tags must include at least one tag_id."));
  }
  return out;
}

export function buildRegistryOptions(registryById) {
  const out = [];
  for (const [tagId, info] of registryById.entries()) {
    if (!info || !STUDIO_GROUPS.includes(info.group)) continue;
    out.push({
      tagId,
      group: info.group,
      label: normalize(info.label) || tagId.split(":", 2)[1] || tagId
    });
  }
  out.sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
  return out;
}

export function countAliasesByGroup(aliases) {
  const counts = { subject: 0, domain: 0, form: 0, theme: 0 };
  for (const entry of aliases || []) {
    for (const group of entry.groups || []) {
      if (STUDIO_GROUPS.includes(group)) {
        counts[group] += 1;
      }
    }
  }
  return counts;
}

export function getVisibleAliases(state) {
  const filtered = state.aliases.filter((entry) => {
    const searchMatch = !state.searchQuery || normalize(entry.alias).startsWith(state.searchQuery);
    if (!searchMatch) return false;
    if (state.filterGroup === "all") return true;
    return Array.isArray(entry.groups) && entry.groups.includes(state.filterGroup);
  });

  const direction = state.sortDir === "desc" ? -1 : 1;
  filtered.sort((a, b) => direction * compareAliases(a, b));
  return filtered;
}

export function compareAliases(a, b) {
  return a.alias.localeCompare(b.alias, undefined, { sensitivity: "base" });
}

export function findAliasEntry(aliases, aliasKey) {
  const normalizedAlias = normalize(aliasKey);
  return Array.isArray(aliases)
    ? aliases.find((entry) => normalize(entry.alias) === normalizedAlias) || null
    : null;
}

export function sameStringArray(a, b) {
  const left = Array.isArray(a) ? a.map((item) => normalize(item)).slice().sort() : [];
  const right = Array.isArray(b) ? b.map((item) => normalize(item)).slice().sort() : [];
  if (left.length !== right.length) return false;
  for (let idx = 0; idx < left.length; idx += 1) {
    if (left[idx] !== right[idx]) return false;
  }
  return true;
}

export function parseTagIdCsv(input, text) {
  const values = String(input || "")
    .split(",")
    .map((item) => normalize(item))
    .filter(Boolean);
  const out = [];
  const seen = new Set();
  for (const value of values) {
    if (!TAG_ID_RE.test(value)) {
      throw new Error(textValue(text, "target_tag_invalid", "Invalid tag_id: {value}", { value }));
    }
    if (seen.has(value)) continue;
    seen.add(value);
    out.push(value);
  }
  if (!out.length) {
    throw new Error(textValue(text, "target_tag_required", "At least one canonical target tag_id is required."));
  }
  if (out.length > MAX_ALIAS_TAGS) {
    throw new Error(textValue(text, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: MAX_ALIAS_TAGS }));
  }
  const seenGroups = new Set();
  for (const value of out) {
    const group = value.split(":", 1)[0];
    if (seenGroups.has(group)) {
      throw new Error(textValue(text, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group }));
    }
    seenGroups.add(group);
  }
  return out;
}

export function normalizeImportAliasRows(rawAliases, text) {
  if (!rawAliases || typeof rawAliases !== "object") return [];
  const out = [];
  const seen = new Set();
  for (const [rawAlias, rawValue] of Object.entries(rawAliases)) {
    const alias = normalize(rawAlias);
    if (!alias) continue;
    let normalizedValue = null;
    try {
      normalizedValue = normalizeAliasValue(rawValue, text);
    } catch (error) {
      continue;
    }
    if (seen.has(alias)) {
      const idx = out.findIndex((item) => item.alias === alias);
      if (idx >= 0) out[idx] = { alias, value: normalizedValue.value, targets: normalizedValue.targets };
      continue;
    }
    seen.add(alias);
    out.push({ alias, value: normalizedValue.value, targets: normalizedValue.targets });
  }
  return out;
}

export function toTimestampMs(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isFinite(ms) ? ms : null;
}

export function normalizeTimestamp(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const ms = Date.parse(raw);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

export function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function textValue(text, key, fallback, tokens) {
  return typeof text === "function" ? text(key, fallback, tokens) : fallback;
}
