let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INDEX = new Map(STUDIO_GROUPS.map((group, index) => [group, index]));
let WEIGHT_VALUES = [0.3, 0.6, 0.9];
let DEFAULT_WEIGHT = 0.6;

export function configureTagStudioDomain(options = {}) {
  const groups = Array.isArray(options.groups) && options.groups.length
    ? options.groups.map((group) => normalize(group)).filter(Boolean)
    : STUDIO_GROUPS.slice();
  STUDIO_GROUPS = groups;
  GROUP_INDEX = new Map(STUDIO_GROUPS.map((group, index) => [group, index]));

  const weightValues = Array.isArray(options.weightValues) && options.weightValues.length
    ? options.weightValues.map((value) => Number(value)).filter((value) => Number.isFinite(value))
    : WEIGHT_VALUES.slice();
  WEIGHT_VALUES = weightValues.length ? weightValues : WEIGHT_VALUES.slice();

  const defaultWeight = Number(options.defaultWeight);
  if (Number.isFinite(defaultWeight)) {
    DEFAULT_WEIGHT = defaultWeight;
  }
}

export function sanitizeTag(rawTag) {
  if (!rawTag || typeof rawTag !== "object") return null;

  const tagId = normalize(rawTag.tag_id);
  const group = normalize(rawTag.group);
  const label = String(rawTag.label || "").trim();
  const status = normalize(rawTag.status || "active");

  if (!tagId || !group || !label) return null;
  if (!GROUP_INDEX.has(group)) return null;

  const splitIndex = tagId.indexOf(":");
  const slug = splitIndex >= 0 ? tagId.slice(splitIndex + 1) : tagId;

  return {
    tag_id: tagId,
    group,
    label,
    status,
    slug
  };
}

export function pushMapList(map, key, value) {
  if (!key) return;
  if (!map.has(key)) map.set(key, []);
  map.get(key).push(value);
}

export function getSeriesIndexRow(seriesMap, seriesId) {
  if (seriesMap[seriesId]) return seriesMap[seriesId];

  const normalizedSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(seriesMap)) {
    if (normalize(key) === normalizedSeriesId) return value;
  }
  return null;
}

export function getSeriesAssignment(seriesAssignments, seriesId) {
  if (seriesAssignments[seriesId]) return seriesAssignments[seriesId];

  const lowerSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(seriesAssignments)) {
    if (normalize(key) === lowerSeriesId) return value;
  }
  return null;
}

export function buildSeriesWorkOptions(seriesId, seriesRow, worksIndexMap) {
  const works = Array.isArray(seriesRow && seriesRow.works) ? seriesRow.works : [];
  const out = [];
  const seen = new Set();

  for (const rawWorkId of works) {
    const workId = normalizeWorkId(rawWorkId);
    if (!workId || seen.has(workId)) continue;
    seen.add(workId);
    const workMeta = getWorkIndexRow(worksIndexMap, workId);
    const title = String(workMeta && workMeta.title || "").trim();
    const shortWorkId = String(Number(workId));
    out.push({
      workId,
      shortWorkId,
      title,
      seriesId,
      titleKey: normalize(title)
    });
  }

  return out;
}

export function getWorkIndexRow(worksMap, workId) {
  if (worksMap[workId]) return worksMap[workId];
  for (const [key, value] of Object.entries(worksMap)) {
    if (normalizeWorkId(key) === workId) return value;
  }
  return null;
}

export function createResolvedEntries(rows, tagsById, nextEntryId = 1) {
  const entries = [];
  let cursor = nextEntryId;
  for (const row of rows) {
    const tag = tagsById.get(row.tagId);
    if (!tag) continue;
    entries.push(makeResolvedEntry(cursor++, row.tagId, tag, row.wManual));
  }
  return { entries, nextEntryId: cursor };
}

export function makeResolvedEntry(entryId, rawInput, tag, wManual) {
  const manual = normalizeManualWeight(wManual, DEFAULT_WEIGHT);
  return {
    entryId,
    rawInput: String(rawInput || "").trim(),
    canonicalId: normalize(tag.tag_id),
    group: normalize(tag.group),
    label: String(tag.label || tag.tag_id).trim(),
    wManual: manual
  };
}

export function getCanonicalTagAssignments(state, inheritedTagIds, selectedEntries = []) {
  const seen = new Set();
  const tags = [];

  for (const entry of selectedEntries) {
    if (!entry || !entry.canonicalId) continue;
    if (inheritedTagIds.has(entry.canonicalId) || seen.has(entry.canonicalId)) continue;
    seen.add(entry.canonicalId);
    tags.push({
      tag_id: entry.canonicalId,
      w_manual: entry.wManual
    });
  }

  tags.sort(compareAssignmentRows);
  return tags;
}

export function getCanonicalTagAssignmentsForWork(state, workId, inheritedTagIds) {
  const entries = state.workEntriesById.get(workId) || [];
  const seen = new Set();
  const tags = [];

  for (const entry of entries) {
    if (!entry || !entry.canonicalId) continue;
    if (inheritedTagIds.has(entry.canonicalId) || seen.has(entry.canonicalId)) continue;
    seen.add(entry.canonicalId);
    tags.push({
      tag_id: entry.canonicalId,
      w_manual: entry.wManual
    });
  }

  return normalizeAssignmentRows(tags);
}

export function buildCurrentPersistWorkState(state, orderedSelectedWorkIds, inheritedTagIds) {
  const out = new Map();
  if (!orderedSelectedWorkIds.length) return out;

  if (state.selectedWorkId) {
    const activeAssignments = getCanonicalTagAssignmentsForWork(state, state.selectedWorkId, inheritedTagIds);
    for (const workId of orderedSelectedWorkIds) {
      out.set(workId, activeAssignments.map((row) => ({ ...row })));
    }
    return out;
  }

  for (const workId of orderedSelectedWorkIds) {
    out.set(workId, getCanonicalTagAssignmentsForWork(state, workId, inheritedTagIds));
  }
  return out;
}

export function buildWorkStateDiff(state, orderedSelectedWorkIds, inheritedTagIds) {
  const nextWorkStateById = buildCurrentPersistWorkState(state, orderedSelectedWorkIds, inheritedTagIds);
  const baseline = state.baselineWorkStateById instanceof Map ? state.baselineWorkStateById : new Map();
  const keys = new Set([...baseline.keys(), ...nextWorkStateById.keys()]);
  const changedWorkIds = [];

  for (const workId of Array.from(keys).sort()) {
    const prevRows = baseline.has(workId) ? baseline.get(workId) : null;
    const nextRows = nextWorkStateById.has(workId) ? nextWorkStateById.get(workId) : null;
    if (!equalAssignmentRows(prevRows, nextRows)) {
      changedWorkIds.push(workId);
    }
  }

  return { changedWorkIds, nextWorkStateById };
}

export function cloneWorkStateMap(map) {
  const out = new Map();
  if (!(map instanceof Map)) return out;
  for (const [workId, rows] of map.entries()) {
    out.set(workId, normalizeAssignmentRows(rows));
  }
  return out;
}

export function syncWorkEntriesFromPersistedState(state, workStateById) {
  const nextSelectedWorkIds = [];
  const nextWorkEntriesById = new Map();
  let nextId = 1;

  for (const option of state.seriesWorkOptions) {
    if (!(workStateById instanceof Map) || !workStateById.has(option.workId)) continue;
    const rows = workStateById.get(option.workId) || [];
    const resolved = createResolvedEntries(rows, state.tagsById, nextId);
    nextSelectedWorkIds.push(option.workId);
    nextWorkEntriesById.set(option.workId, resolved.entries);
    nextId = resolved.nextEntryId;
  }

  state.selectedWorkIds = nextSelectedWorkIds;
  state.workEntriesById = nextWorkEntriesById;
  if (state.selectedWorkId && !nextWorkEntriesById.has(state.selectedWorkId)) {
    state.selectedWorkId = "";
  }
}

export function workStateMapToObject(map) {
  const out = {};
  if (!(map instanceof Map)) return out;
  for (const [workId, rows] of map.entries()) {
    out[workId] = normalizeAssignmentRows(rows);
  }
  return out;
}

export function normalizeAssignmentRows(rows) {
  const list = Array.isArray(rows) ? rows : [];
  const seen = new Set();
  const out = [];
  for (const raw of list) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id || raw.tagId);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push({
      tag_id: tagId,
      w_manual: normalizeManualWeight(raw.w_manual ?? raw.wManual, DEFAULT_WEIGHT)
    });
  }
  out.sort(compareAssignmentRows);
  return out;
}

export function equalAssignmentRows(left, right) {
  const a = normalizeAssignmentRows(left);
  const b = normalizeAssignmentRows(right);
  if (a.length !== b.length) return false;
  for (let index = 0; index < a.length; index += 1) {
    if (a[index].tag_id !== b[index].tag_id) return false;
    if (a[index].w_manual !== b[index].w_manual) return false;
  }
  return true;
}

export function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

export function normalizeWorkId(value) {
  const text = String(value || "").trim();
  if (!/^\d{1,5}$/.test(text)) return "";
  return text.padStart(5, "0");
}

export function splitWorkInputTokens(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function normalizeAliasTargets(value) {
  const rawTargets = (value && typeof value === "object" && !Array.isArray(value))
    ? value.tags
    : value;

  if (Array.isArray(rawTargets)) {
    const out = [];
    const seen = new Set();
    for (const item of rawTargets) {
      const normalized = normalize(item);
      if (!normalized || seen.has(normalized)) continue;
      seen.add(normalized);
      out.push(normalized);
    }
    return out;
  }

  const single = normalize(rawTargets);
  return single ? [single] : [];
}

export function normalizeAssignmentTags(rawTags) {
  if (!Array.isArray(rawTags)) return [];
  const out = [];
  const seen = new Set();
  for (const raw of rawTags) {
    if (typeof raw === "string") {
      const tagId = normalize(raw);
      if (!tagId || seen.has(tagId)) continue;
      seen.add(tagId);
      out.push({
        tagId,
        wManual: DEFAULT_WEIGHT
      });
      continue;
    }
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push({
      tagId,
      wManual: normalizeManualWeight(raw.w_manual, DEFAULT_WEIGHT)
    });
  }
  return out;
}

export function normalizeManualWeight(raw, fallback = DEFAULT_WEIGHT) {
  const value = typeof raw === "number" ? raw : Number(raw);
  if (!Number.isFinite(value)) return fallback;
  let closest = WEIGHT_VALUES[0];
  let diff = Math.abs(value - closest);
  for (const candidate of WEIGHT_VALUES) {
    const currentDiff = Math.abs(value - candidate);
    if (currentDiff < diff) {
      closest = candidate;
      diff = currentDiff;
    }
  }
  return closest;
}

export function nextWeight(value) {
  const normalized = normalizeManualWeight(value, DEFAULT_WEIGHT);
  const index = WEIGHT_VALUES.indexOf(normalized);
  if (index < 0) return DEFAULT_WEIGHT;
  return WEIGHT_VALUES[(index + 1) % WEIGHT_VALUES.length];
}

export function groupFromTagId(tagId) {
  const normalized = normalize(tagId);
  const splitIndex = normalized.indexOf(":");
  return splitIndex >= 0 ? normalized.slice(0, splitIndex) : normalized;
}

export function slugFromTagId(tagId) {
  const normalized = normalize(tagId);
  const splitIndex = normalized.indexOf(":");
  return splitIndex >= 0 ? normalized.slice(splitIndex + 1) : normalized;
}

export function compareEntries(a, b) {
  if (b.wManual !== a.wManual) return b.wManual - a.wManual;
  return slugFromTagId(a.canonicalId).localeCompare(slugFromTagId(b.canonicalId), undefined, { sensitivity: "base" });
}

export function compareTagDisplay(a, b) {
  const aIndex = GROUP_INDEX.has(a.group) ? GROUP_INDEX.get(a.group) : Number.MAX_SAFE_INTEGER;
  const bIndex = GROUP_INDEX.has(b.group) ? GROUP_INDEX.get(b.group) : Number.MAX_SAFE_INTEGER;
  if (aIndex !== bIndex) return aIndex - bIndex;
  return a.tagId.localeCompare(b.tagId);
}

export function compareAssignmentRows(a, b) {
  const ga = groupFromTagId(a.tag_id);
  const gb = groupFromTagId(b.tag_id);
  const ia = GROUP_INDEX.has(ga) ? GROUP_INDEX.get(ga) : Number.MAX_SAFE_INTEGER;
  const ib = GROUP_INDEX.has(gb) ? GROUP_INDEX.get(gb) : Number.MAX_SAFE_INTEGER;
  if (ia !== ib) return ia - ib;
  if (b.w_manual !== a.w_manual) return b.w_manual - a.w_manual;
  return slugFromTagId(a.tag_id).localeCompare(slugFromTagId(b.tag_id), undefined, { sensitivity: "base" });
}
