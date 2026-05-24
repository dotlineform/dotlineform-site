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

export function findTagById(tags, tagId) {
  const normalizedTagId = normalize(tagId);
  return Array.isArray(tags)
    ? tags.find((tag) => tag && tag.tagId === normalizedTagId) || null
    : null;
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

export function getNewTagValidation(options) {
  const {
    newTagState,
    slugInput,
    descriptionInput,
    tags,
    tagSlugRe,
    text,
    studioGroups = STUDIO_GROUPS
  } = options || {};

  if (!newTagState) {
    return { valid: false, warning: "", group: "", slug: "", description: "", tagId: "" };
  }

  const group = normalize(newTagState.group);
  const slug = normalize(slugInput);
  const description = String(descriptionInput || "").trim();
  let warning = "";

  if (!studioGroups.includes(group)) {
    warning = text("select_group_warning", "Select a tag group.");
  } else if (!slug) {
    warning = text("tag_slug_required", "Tag slug is required.");
  } else if (!(tagSlugRe instanceof RegExp) || !tagSlugRe.test(slug)) {
    warning = text("tag_slug_invalid", "Tag slug must be lowercase letters, numbers, or hyphens.");
  } else {
    const tagId = `${group}:${slug}`;
    const exists = Array.isArray(tags) && tags.some((tag) => tag && tag.tagId === tagId);
    if (exists) warning = text("tag_exists_warning", "Tag already exists.");
  }

  return {
    valid: !warning,
    warning,
    group,
    slug,
    description,
    tagId: group && slug ? `${group}:${slug}` : ""
  };
}

export function getDemoteValidation(options) {
  const {
    demoteState,
    tags,
    maxAliasTags,
    text
  } = options || {};

  if (!demoteState) return { valid: false, tags: [], warning: "" };
  const selectedTags = Array.isArray(demoteState.tags) ? demoteState.tags.slice() : [];

  let warning = "";
  if (!selectedTags.length) {
    warning = text("demote_select_target_warning", "Select at least one target tag.");
  } else if (selectedTags.length > maxAliasTags) {
    warning = text("demote_max_tags_warning", "Select up to {max_tags} tags.", { max_tags: maxAliasTags });
  } else {
    const seenGroups = new Set();
    for (const tagId of selectedTags) {
      if (tagId === demoteState.tagId) {
        warning = text("demote_target_includes_self", "Target list must not include the demoted tag.");
        break;
      }
      const info = findTagById(tags, tagId);
      if (!info) {
        warning = text("demote_unknown_tag_warning", "Unknown tag selected: {tag_id}", { tag_id: tagId });
        break;
      }
      if (seenGroups.has(info.group)) {
        warning = text(
          "demote_one_per_group_warning",
          "Only one target tag per group is allowed ({group}).",
          { group: info.group }
        );
        break;
      }
      seenGroups.add(info.group);
    }
  }

  return {
    valid: !warning,
    tags: selectedTags,
    warning
  };
}

export function getDemoteTagMatches(options) {
  const {
    query,
    demoteState,
    registryOptions,
    cap
  } = options || {};

  const normalizedQuery = normalize(query);
  if (!normalizedQuery || !demoteState) {
    return { matches: [], truncated: false };
  }
  const selected = new Set(demoteState.tags || []);
  const allMatches = (Array.isArray(registryOptions) ? registryOptions : []).filter((item) => {
    if (selected.has(item.tagId)) return false;
    if (item.tagId === demoteState.tagId) return false;
    const slug = item.tagId.split(":", 2)[1] || "";
    return (
      normalize(item.label).startsWith(normalizedQuery) ||
      normalize(slug).startsWith(normalizedQuery)
    );
  });

  const limit = Number.isFinite(cap) ? cap : allMatches.length;
  return {
    matches: allMatches.slice(0, limit),
    truncated: allMatches.length > limit
  };
}
