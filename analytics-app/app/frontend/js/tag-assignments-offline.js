import {
  normalize,
  normalizeAssignmentRows,
  normalizeWorkId
} from "./tag-studio-domain.js";

const STORAGE_KEY = "dotlineform.studio.tagAssignmentsOffline.v1";
const SESSION_VERSION = "tag_assignments_offline_v1";

export {
  SESSION_VERSION,
  STORAGE_KEY
};

export function createEmptyOfflineAssignmentsSession() {
  return {
    version: SESSION_VERSION,
    updated_at_utc: "",
    series: {}
  };
}

export function cloneOfflineAssignmentsSession(session) {
  return normalizeOfflineAssignmentsSession(session);
}

export function normalizeOfflineAssignmentsSession(session) {
  const rawSeries = session && typeof session === "object" && session.series && typeof session.series === "object"
    ? session.series
    : {};
  const series = {};

  Object.keys(rawSeries).forEach((rawSeriesId) => {
    const seriesId = normalize(rawSeriesId);
    if (!seriesId) return;
    const entry = normalizeOfflineAssignmentsSeriesEntry(rawSeries[rawSeriesId]);
    if (!entry) return;
    series[seriesId] = entry;
  });

  return {
    version: SESSION_VERSION,
    updated_at_utc: String(session && session.updated_at_utc || ""),
    series
  };
}

export function normalizeOfflineAssignmentsSeriesEntry(entry) {
  if (!entry || typeof entry !== "object") return null;

  const stagedRow = normalizeOfflineSeriesRow(entry.staged_row);
  const baseRowSnapshot = normalizeOfflineSeriesRow(entry.base_row_snapshot);
  const baseSeriesUpdatedAt = String(entry.base_series_updated_at_utc || "").trim();
  const stagedAt = String(entry.staged_at_utc || "").trim();

  if (!stagedRow) return null;

  return {
    base_series_updated_at_utc: baseSeriesUpdatedAt,
    base_row_snapshot: baseRowSnapshot,
    staged_row: stagedRow,
    staged_at_utc: stagedAt
  };
}

export function normalizeOfflineSeriesRow(row) {
  const raw = row && typeof row === "object" ? row : {};
  const tags = normalizeAssignmentRows(raw.tags);
  const works = {};

  if (raw.works && typeof raw.works === "object") {
    Object.keys(raw.works).forEach((rawWorkId) => {
      const workId = normalizeWorkId(rawWorkId);
      if (!workId) return;
      const workRow = raw.works[rawWorkId];
      if (!workRow || typeof workRow !== "object") return;
      works[workId] = {
        tags: normalizeAssignmentRows(workRow.tags)
      };
    });
  }

  const out = { tags };
  if (Object.keys(works).length) out.works = works;
  return out;
}

export function equalOfflineSeriesRows(left, right) {
  const a = normalizeOfflineSeriesRow(left);
  const b = normalizeOfflineSeriesRow(right);

  if (!equalNormalizedAssignmentRows(a.tags, b.tags)) return false;

  const aWorks = a.works && typeof a.works === "object" ? a.works : {};
  const bWorks = b.works && typeof b.works === "object" ? b.works : {};
  const workIds = Array.from(new Set([...Object.keys(aWorks), ...Object.keys(bWorks)])).sort();

  for (const workId of workIds) {
    const aRow = aWorks[workId];
    const bRow = bWorks[workId];
    if (!aRow || !bRow) return false;
    if (!equalNormalizedAssignmentRows(aRow.tags, bRow.tags)) return false;
  }

  return true;
}

export function readOfflineAssignmentsSession() {
  const storage = getStorage();
  if (!storage) return createEmptyOfflineAssignmentsSession();
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return createEmptyOfflineAssignmentsSession();
    return normalizeOfflineAssignmentsSession(JSON.parse(raw));
  } catch (error) {
    return createEmptyOfflineAssignmentsSession();
  }
}

export function writeOfflineAssignmentsSession(session) {
  const storage = getStorage();
  const normalized = normalizeOfflineAssignmentsSession(session);
  if (!storage) return normalized;
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify(normalized));
  } catch (error) {
    return normalized;
  }
  return normalized;
}

export function clearOfflineAssignmentsSession() {
  const storage = getStorage();
  if (storage) {
    try {
      storage.removeItem(STORAGE_KEY);
    } catch (error) {
      // Ignore storage write failures.
    }
  }
  return createEmptyOfflineAssignmentsSession();
}

export function getOfflineAssignmentsSeriesEntry(session, seriesId) {
  const normalized = normalizeOfflineAssignmentsSession(session);
  const key = normalize(seriesId);
  return key && normalized.series[key] ? normalized.series[key] : null;
}

export function upsertOfflineAssignmentsSeriesEntry(session, seriesId, entry, updatedAtUtc = "") {
  const normalized = normalizeOfflineAssignmentsSession(session);
  const key = normalize(seriesId);
  if (!key) return normalized;
  const normalizedEntry = normalizeOfflineAssignmentsSeriesEntry(entry);
  if (!normalizedEntry) return normalized;
  normalized.series[key] = normalizedEntry;
  normalized.updated_at_utc = String(updatedAtUtc || normalizedEntry.staged_at_utc || normalized.updated_at_utc || "").trim();
  return normalized;
}

export function removeOfflineAssignmentsSeriesEntry(session, seriesId, updatedAtUtc = "") {
  const normalized = normalizeOfflineAssignmentsSession(session);
  const key = normalize(seriesId);
  if (!key || !normalized.series[key]) return normalized;
  delete normalized.series[key];
  normalized.updated_at_utc = String(updatedAtUtc || normalized.updated_at_utc || "").trim();
  return normalized;
}

export function buildOfflineAssignmentsExport(session) {
  return normalizeOfflineAssignmentsSession(session);
}

function equalNormalizedAssignmentRows(left, right) {
  const a = normalizeAssignmentRows(left);
  const b = normalizeAssignmentRows(right);
  if (a.length !== b.length) return false;

  for (let index = 0; index < a.length; index += 1) {
    if (a[index].tag_id !== b[index].tag_id) return false;
    if (a[index].w_manual !== b[index].w_manual) return false;
    if ((a[index].alias || "") !== (b[index].alias || "")) return false;
  }

  return true;
}

function getStorage() {
  if (typeof window === "undefined" || !window.localStorage) return null;
  try {
    return window.localStorage;
  } catch (error) {
    return null;
  }
}
