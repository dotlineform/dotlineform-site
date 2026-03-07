let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];

export function configureTagRegistryDomain(options = {}) {
  const groups = Array.isArray(options.groups) && options.groups.length
    ? options.groups.map((group) => normalize(group)).filter(Boolean)
    : STUDIO_GROUPS.slice();
  STUDIO_GROUPS = groups;
}

export function normalizeRegistryTags(data, fallbackUpdatedAt) {
  const rawTags = Array.isArray(data && data.tags) ? data.tags : [];
  const tags = [];

  for (const raw of rawTags) {
    if (!raw || typeof raw !== "object") continue;
    const group = normalize(raw.group);
    const tagId = normalize(raw.tag_id);
    const label = normalize(raw.label) || labelFromTagId(tagId);
    const description = String(raw.description || "").trim();
    const status = normalize(raw.status || "active");
    const updatedAtUtc = normalizeTimestamp(raw.updated_at_utc) || fallbackUpdatedAt;

    if (!STUDIO_GROUPS.includes(group) || !tagId || !label) continue;
    tags.push({
      group,
      tagId,
      label,
      description,
      status,
      updatedAtUtc,
      updatedAtMs: toTimestampMs(updatedAtUtc)
    });
  }

  return tags;
}

export function buildRegistryOptions(tags) {
  const options = [];
  for (const tag of tags || []) {
    if (!tag || !tag.tagId || !STUDIO_GROUPS.includes(tag.group)) continue;
    options.push({
      tagId: tag.tagId,
      group: tag.group,
      label: normalize(tag.label) || labelFromTagId(tag.tagId) || tag.tagId
    });
  }
  options.sort((a, b) => {
    const byLabel = a.label.localeCompare(b.label, undefined, { sensitivity: "base" });
    if (byLabel !== 0) return byLabel;
    return a.tagId.localeCompare(b.tagId);
  });
  return options;
}

export function buildAliasKeySet(data) {
  const out = new Set();
  const aliasesObj = data && typeof data.aliases === "object" && data.aliases ? data.aliases : {};
  for (const rawKey of Object.keys(aliasesObj)) {
    const key = normalize(rawKey);
    if (!key) continue;
    out.add(key);
  }
  return out;
}

export function countTagsByGroup(tags) {
  const counts = { subject: 0, domain: 0, form: 0, theme: 0 };
  for (const tag of tags || []) {
    const group = normalize(tag && tag.group);
    if (STUDIO_GROUPS.includes(group)) {
      counts[group] += 1;
    }
  }
  return counts;
}

export function getVisibleSortedTags(state) {
  const filtered = state.tags.filter((tag) => {
    const groupMatch = state.filterGroup === "all" ? true : tag.group === state.filterGroup;
    if (!groupMatch) return false;
    if (!state.searchQuery) return true;
    return normalize(tag.label).startsWith(state.searchQuery);
  });

  const direction = state.sortDir === "desc" ? -1 : 1;
  filtered.sort((a, b) => direction * compareTags(a, b, state.sortKey));
  return filtered;
}

export function compareTags(a, b, sortKey) {
  if (sortKey === "description") {
    const ad = normalize(a.description);
    const bd = normalize(b.description);
    const byDescription = ad.localeCompare(bd, undefined, { sensitivity: "base" });
    if (byDescription !== 0) return byDescription;
    return compareTags(a, b, "label");
  }

  const byLabel = a.label.localeCompare(b.label, undefined, { sensitivity: "base" });
  if (byLabel !== 0) return byLabel;
  return a.tagId.localeCompare(b.tagId);
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

export function labelFromTagId(tagId) {
  const normalized = normalize(tagId);
  if (!normalized || !normalized.includes(":")) return "";
  const [, slug = ""] = normalized.split(":", 2);
  return labelFromSlug(slug);
}

export function labelFromSlug(slug) {
  return normalize(slug);
}
