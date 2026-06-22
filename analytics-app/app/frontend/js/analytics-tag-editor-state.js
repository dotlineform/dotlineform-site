import {
  buildSeriesWorkOptions,
  cloneWorkStateMap,
  compareTagDisplay,
  createResolvedEntries,
  buildEditorStateDiff,
  getSeriesAssignment,
  getSeriesIndexRow,
  normalize,
  normalizeAliasTargets,
  normalizeAssignmentRows,
  normalizeAssignmentTags,
  normalizeWorkId,
  pushMapList,
  sanitizeTag
} from "./analytics-tag-editor-domain.js";

const DEFAULT_ANALYTICS_GROUPS = ["subject", "domain", "form", "theme"];
const DEFAULT_WEIGHT = 0.6;

export function buildAnalyticsTagEditorState(options) {
  const mount = options.mount;
  const seriesId = options.seriesId;
  const registryJson = options.registryJson;
  const aliasesJson = options.aliasesJson;
  const assignmentsJson = options.assignmentsJson;
  const seriesIndexJson = options.seriesIndexJson;
  const worksIndexJson = options.worksIndexJson;
  const config = options.config;
  const offlineSession = options.offlineSession;
  const studioGroups = Array.isArray(options.studioGroups) && options.studioGroups.length
    ? options.studioGroups
    : DEFAULT_ANALYTICS_GROUPS;
  const defaultWeight = Number.isFinite(options.defaultWeight) ? options.defaultWeight : DEFAULT_WEIGHT;

  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  const tagsById = new Map();
  const slugMap = new Map();
  const labelMap = new Map();
  const tagOptions = [];

  for (const rawTag of tags) {
    const tag = sanitizeTag(rawTag);
    if (!tag) continue;

    tagsById.set(tag.tag_id, tag);
    pushMapList(slugMap, tag.slug, tag);
    pushMapList(labelMap, normalize(tag.label), tag);

    tagOptions.push(tag);
  }

  tagOptions.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
  const tagOptionsBySlug = tagOptions.slice().sort((a, b) => {
    const bySlug = a.slug.localeCompare(b.slug, undefined, { sensitivity: "base" });
    if (bySlug !== 0) return bySlug;
    return a.tag_id.localeCompare(b.tag_id);
  });

  const aliases = new Map();
  const rawAliases = aliasesJson && typeof aliasesJson.aliases === "object" ? aliasesJson.aliases : {};
  for (const [aliasInput, targetInput] of Object.entries(rawAliases)) {
    const aliasKey = normalize(aliasInput);
    if (!aliasKey) continue;
    const targetTagIds = normalizeAliasTargets(targetInput);
    if (!targetTagIds.length) continue;
    aliases.set(aliasKey, targetTagIds);
  }
  const aliasOptions = buildAliasOptions(aliases, tagsById);

  const seriesIndexMap = seriesIndexJson && typeof seriesIndexJson.series === "object" ? seriesIndexJson.series : {};
  const worksIndexMap = worksIndexJson && typeof worksIndexJson.works === "object" ? worksIndexJson.works : {};
  const seriesRow = getSeriesIndexRow(seriesIndexMap, seriesId);
  const seriesWorkOptions = buildSeriesWorkOptions(seriesId, seriesRow, worksIndexMap);
  const seriesWorkIds = new Set(seriesWorkOptions.map((item) => item.workId));

  const assignmentsSeries = assignmentsJson && typeof assignmentsJson.series === "object" ? assignmentsJson.series : {};
  const repoSeriesAssignment = getSeriesAssignment(assignmentsSeries, seriesId);
  const offlineSeriesEntry = null;
  const seriesAssignment = offlineSeriesEntry ? offlineSeriesEntry.staged_row : repoSeriesAssignment;
  const seriesEntries = createResolvedEntries(
    normalizeAssignmentTags(seriesAssignment && seriesAssignment.tags),
    tagsById
  ).entries;

  const rawWorkAssignments = seriesAssignment && typeof seriesAssignment.works === "object" ? seriesAssignment.works : {};
  const workEntriesById = new Map();
  const selectedWorkIds = [];
  const baselineWorkStateById = new Map();
  let nextEntryId = 1;

  Object.keys(rawWorkAssignments).forEach((rawWorkId) => {
    const workId = normalizeWorkId(rawWorkId);
    if (!workId) return;
    const workRow = rawWorkAssignments[rawWorkId];
    const tags = workRow && typeof workRow === "object" ? workRow.tags : [];
    const rows = normalizeAssignmentTags(tags);
    const entries = createResolvedEntries(rows, tagsById, nextEntryId);
    workEntriesById.set(workId, entries.entries);
    baselineWorkStateById.set(workId, normalizeAssignmentRows(rows));
    if (seriesWorkIds.has(workId)) {
      selectedWorkIds.push(workId);
    }
    nextEntryId = entries.nextEntryId;
  });

  return {
    mount,
    routeRoot: document.getElementById("seriesTagEditorRoot"),
    config,
    studioGroups,
    defaultWeight,
    seriesId,
    tagsById,
    slugMap,
    labelMap,
    aliases,
    tagOptionsBySlug,
    aliasOptions,
    seriesEntries,
    baselineSeriesRows: normalizeAssignmentRows(seriesAssignment && seriesAssignment.tags),
    workEntriesById,
    seriesWorkOptions,
    seriesWorkIds,
    selectedWorkIds,
    baselineWorkStateById,
    selectedWorkId: "",
    lastBroadcastSelectedWorkId: null,
    statusText: "",
    statusKind: "",
    refs: null,
    offlineSession,
    hasOfflineStagedSeries: Boolean(offlineSeriesEntry),
    offlineBaseSeriesRow: offlineSeriesEntry && offlineSeriesEntry.base_row_snapshot
      ? normalizeSeriesAssignmentRow(offlineSeriesEntry.base_row_snapshot)
      : normalizeSeriesAssignmentRow(repoSeriesAssignment),
    offlineBaseSeriesUpdatedAt: offlineSeriesEntry
      ? String(offlineSeriesEntry.base_series_updated_at_utc || "")
      : String(repoSeriesAssignment && repoSeriesAssignment.updated_at_utc || ""),
    offlineAutosaveTimer: 0,
    saveModeProbePending: false,
    lastSaveModeHealthOk: false,
    serverAvailableWhileOfflineNotified: false,
    modalSnippet: "",
    saveMode: "offline",
    saveModeResolved: false,
    isBusy: false
  };
}

function normalizeSeriesAssignmentRow(row) {
  const raw = row && typeof row === "object" ? row : {};
  const works = {};

  if (raw.works && typeof raw.works === "object") {
    Object.keys(raw.works).forEach((rawWorkId) => {
      const workId = normalizeWorkId(rawWorkId);
      if (!workId) return;
      const workRow = raw.works[rawWorkId];
      works[workId] = {
        tags: normalizeAssignmentRows(workRow && workRow.tags)
      };
    });
  }

  const out = {
    tags: normalizeAssignmentRows(raw.tags)
  };
  if (Object.keys(works).length) out.works = works;
  return out;
}

export function buildStateDiff(state) {
  return buildEditorStateDiff(state, getOrderedSelectedWorkIds(state));
}

export function buildPersistedSeriesRow(diff) {
  const row = {
    tags: normalizeAssignmentRows(diff && diff.nextSeriesRows)
  };
  const works = {};
  const nextWorkStateById = diff && diff.nextWorkStateById instanceof Map ? diff.nextWorkStateById : new Map();

  for (const [workId, tags] of Array.from(nextWorkStateById.entries()).sort((a, b) => a[0].localeCompare(b[0]))) {
    works[workId] = {
      tags: normalizeAssignmentRows(tags)
    };
  }

  if (Object.keys(works).length) row.works = works;
  return row;
}

export function applyPersistedBaseline(state, diff) {
  state.baselineSeriesRows = normalizeAssignmentRows(diff.nextSeriesRows);
  state.baselineWorkStateById = cloneWorkStateMap(diff.nextWorkStateById);
}

export function restoreSelectionFromQuery(state) {
  const searchParams = new URLSearchParams(window.location.search);
  const worksParam = String(searchParams.get("works") || "").trim();
  if (!worksParam) {
    writeSelectionToQuery(state);
    return;
  }

  const selectedWorkIds = [];
  const seen = new Set();
  for (const rawPart of worksParam.split(",")) {
    const workId = normalizeWorkId(rawPart);
    if (!workId || seen.has(workId) || !state.seriesWorkIds.has(workId)) continue;
    seen.add(workId);
    selectedWorkIds.push(workId);
    if (!state.workEntriesById.has(workId)) {
      state.workEntriesById.set(workId, []);
    }
  }

  state.selectedWorkIds = selectedWorkIds;

  const activeWorkId = normalizeWorkId(searchParams.get("active"));
  if (activeWorkId && selectedWorkIds.includes(activeWorkId)) {
    state.selectedWorkId = activeWorkId;
  } else {
    state.selectedWorkId = selectedWorkIds.length ? selectedWorkIds[0] : "";
  }

  writeSelectionToQuery(state);
}

export function writeSelectionToQuery(state) {
  if (!window.history || typeof window.history.replaceState !== "function") return;

  const url = new URL(window.location.href);
  const selectedWorkIds = getOrderedSelectedWorkIds(state);
  if (selectedWorkIds.length) {
    url.searchParams.set("works", selectedWorkIds.join(","));
    if (state.selectedWorkId && selectedWorkIds.includes(state.selectedWorkId)) {
      url.searchParams.set("active", state.selectedWorkId);
    } else {
      url.searchParams.delete("active");
    }
  } else {
    url.searchParams.delete("works");
    url.searchParams.delete("active");
  }

  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

export function getOrderedSelectedWorkOptions(state) {
  const selected = new Set(state.selectedWorkIds);
  return state.seriesWorkOptions.filter((item) => selected.has(item.workId));
}

export function getOrderedSelectedWorkIds(state) {
  return getOrderedSelectedWorkOptions(state).map((item) => item.workId);
}

function buildAliasOptions(aliases, tagsById) {
  const out = [];
  for (const [alias, targets] of aliases.entries()) {
    const resolved = [];
    const seen = new Set();
    for (const targetTagId of targets) {
      const normalizedTagId = normalize(targetTagId);
      if (!normalizedTagId || seen.has(normalizedTagId)) continue;
      const tag = tagsById.get(normalizedTagId);
      if (!tag) continue;
      seen.add(normalizedTagId);
      resolved.push({
        tagId: normalizedTagId,
        group: tag.group,
        label: tag.label
      });
    }
    if (!resolved.length) continue;
    resolved.sort(compareTagDisplay);
    out.push({ alias, targets: resolved });
  }
  out.sort((a, b) => a.alias.localeCompare(b.alias, undefined, { sensitivity: "base" }));
  return out;
}
