import {
  normalizeText,
  normalizeWorkId
} from "./catalogue-work-fields.js";

export function projectWorkSearchRecord(workId, record, recordHash = "") {
  const normalizedWorkId = normalizeWorkId(workId);
  return {
    work_id: normalizedWorkId,
    title: normalizeText(record && record.title),
    year_display: normalizeText(record && record.year_display),
    status: normalizeText(record && record.status),
    series_ids: Array.isArray(record && record.series_ids) ? record.series_ids.slice() : [],
    record_hash: normalizeText(recordHash)
  };
}

export function applyWorkRecordMutation(state, {
  workId,
  record,
  recordHash = "",
  updateBulk = false
} = {}) {
  const normalizedWorkId = normalizeWorkId(workId);
  if (!normalizedWorkId || !record || typeof record !== "object") return null;
  const normalizedRecordHash = normalizeText(recordHash);
  const searchRecord = projectWorkSearchRecord(normalizedWorkId, record, normalizedRecordHash);
  state.sourceWorkRecordsById.set(normalizedWorkId, record);
  state.workSearchById.set(normalizedWorkId, searchRecord);
  if (updateBulk) {
    state.bulkRecords.set(normalizedWorkId, record);
    state.bulkRecordHashes.set(normalizedWorkId, normalizedRecordHash);
  }
  return {
    workId: normalizedWorkId,
    record,
    recordHash: normalizedRecordHash,
    searchRecord
  };
}

export function applyBulkWorkRecordMutations(state, items = []) {
  if (!Array.isArray(items)) return [];
  return items
    .map((item) => applyWorkRecordMutation(state, {
      workId: item && item.work_id,
      record: item && item.record,
      recordHash: item && item.record_hash,
      updateBulk: true
    }))
    .filter(Boolean);
}
