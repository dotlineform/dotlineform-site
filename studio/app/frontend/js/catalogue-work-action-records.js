/** Carry saved fields and media version into the live search and member lists. */
export function projectWorkSearchRecord(workId, record) {
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId)) {
    throw new Error("Saved Work identity must use its exact five-digit spelling.");
  }
  return {
    work_id: workId,
    title: record.title,
    medium: record.medium ?? null,
    year: record.year,
    year_display: record.year_display,
    series_id: record.series_id,
    media_version: record.media_version,
    image_staged: record.image_staged,
    gallery_ids: record.gallery_ids.slice()
  };
}

export function applyWorkRecordMutation(state, {
  workId,
  record,
  updateBulk = false
} = {}) {
  if (!record || typeof record !== "object" || Array.isArray(record)) {
    throw new Error("Saved Work record must be an object.");
  }
  const searchRecord = projectWorkSearchRecord(workId, record);
  state.sourceWorkRecordsById.set(workId, record);
  state.workSearchById.set(workId, searchRecord);
  if (updateBulk) {
    state.bulkRecords.set(workId, record);
  }
  return {
    workId,
    record,
    searchRecord
  };
}

export function applyBulkWorkRecordMutations(state, items, expectedIds) {
  if (!Array.isArray(items)) {
    throw new Error("Saved Work response is missing records or Gallery memberships.");
  }
  const remaining = new Set(expectedIds);
  for (const item of items) {
    if (!item?.record || typeof item.record !== "object" || Array.isArray(item.record) || !Array.isArray(item.gallery_ids)) {
      throw new Error("Saved Work response is missing records or Gallery memberships.");
    }
    if (!remaining.delete(item.work_id)) throw new Error("Saved Work response does not match the selected Works.");
  }
  if (remaining.size) {
    throw new Error("Saved Work response does not match the selected Works.");
  }
  return items
    .map((item) => applyWorkRecordMutation(state, {
      workId: item.work_id,
      record: { ...item.record, gallery_ids: item.gallery_ids },
      updateBulk: state.bulkRecords.has(item.work_id)
    }));
}
