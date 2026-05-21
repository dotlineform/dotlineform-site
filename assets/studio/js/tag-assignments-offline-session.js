import {
  buildOfflineAssignmentsExport,
  clearOfflineAssignmentsSession,
  equalOfflineSeriesRows,
  getOfflineAssignmentsSeriesEntry,
  normalizeOfflineSeriesRow,
  readOfflineAssignmentsSession,
  removeOfflineAssignmentsSeriesEntry,
  upsertOfflineAssignmentsSeriesEntry,
  writeOfflineAssignmentsSession
} from "./tag-assignments-offline.js";

export function readTagAssignmentsOfflineSession() {
  return readOfflineAssignmentsSession();
}

export function clearTagAssignmentsOfflineSession() {
  return clearOfflineAssignmentsSession();
}

export function buildTagAssignmentsOfflineExport(session) {
  return buildOfflineAssignmentsExport(session);
}

export async function copyTagAssignmentsOfflineSession(session, clipboard = navigator.clipboard) {
  const exportPayload = buildOfflineAssignmentsExport(session);
  await clipboard.writeText(JSON.stringify(exportPayload, null, 2));
  return exportPayload;
}

export function downloadTagAssignmentsOfflineSession(session, documentRef = document) {
  const exportPayload = buildOfflineAssignmentsExport(session);
  const blob = new Blob([`${JSON.stringify(exportPayload, null, 2)}\n`], { type: "application/json" });
  const href = URL.createObjectURL(blob);
  const link = documentRef.createElement("a");
  link.href = href;
  link.download = `tag-assignments-offline-${timestampForFilename(exportPayload.updated_at_utc)}.json`;
  documentRef.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 0);
  return exportPayload;
}

export function clearImportedOfflineAssignmentsEntries(options) {
  const importPreview = options && options.importPreview;
  const importPayload = options && options.importPayload;
  const importResolutions = options && options.importResolutions ? options.importResolutions : {};
  if (!importPreview || !importPayload || !importPayload.series) {
    return readOfflineAssignmentsSession();
  }

  let session = readOfflineAssignmentsSession();
  let changed = false;
  const updatedAt = new Date().toISOString();

  for (const row of importPreview.series || []) {
    const seriesId = normalizeSessionValue(row && row.series_id);
    if (!seriesId) continue;
    const status = String(row && row.status || "");
    if (status === "invalid" || status === "missing") continue;
    if (status === "conflict" && String(importResolutions[seriesId] || "skip") !== "overwrite") continue;

    const importedEntry = importPayload.series[seriesId];
    const localEntry = getOfflineAssignmentsSeriesEntry(session, seriesId);
    if (!importedEntry || !localEntry) continue;
    if (!equalOfflineSeriesRows(importedEntry.staged_row, localEntry.staged_row)) continue;
    session = removeOfflineAssignmentsSeriesEntry(session, seriesId, updatedAt);
    changed = true;
  }

  return changed ? writeOfflineAssignmentsSession(session) : session;
}

export function stageTagAssignmentsOfflineSeries(options) {
  const seriesId = normalizeSessionValue(options && options.seriesId);
  const stagedAt = String(options && options.stagedAt || "").trim();
  const stagedRow = normalizeOfflineSeriesRow(options && options.stagedRow);
  const baseRow = normalizeOfflineSeriesRow(options && options.baseRow);
  const baseUpdatedAt = String(options && options.baseUpdatedAt || "").trim();
  let session = readOfflineAssignmentsSession();
  let seriesCleared = false;

  if (!seriesId) {
    return {
      session,
      seriesCleared
    };
  }

  if (equalOfflineSeriesRows(stagedRow, baseRow)) {
    session = removeOfflineAssignmentsSeriesEntry(session, seriesId, stagedAt);
    seriesCleared = true;
  } else {
    session = upsertOfflineAssignmentsSeriesEntry(session, seriesId, {
      base_series_updated_at_utc: baseUpdatedAt,
      base_row_snapshot: baseRow,
      staged_row: stagedRow,
      staged_at_utc: stagedAt
    }, stagedAt);
  }

  return {
    session: writeOfflineAssignmentsSession(session),
    seriesCleared
  };
}

export function normalizeTagAssignmentsOfflineSeriesRow(row) {
  return normalizeOfflineSeriesRow(row);
}

function timestampForFilename(value) {
  const text = String(value || "").trim();
  if (!text) return "session";
  return text.replace(/[^0-9A-Za-z]+/g, "-").replace(/^-+|-+$/g, "") || "session";
}

function normalizeSessionValue(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}
