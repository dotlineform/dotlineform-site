const WORK_DETAIL_FIELD_DEFINITIONS = Object.freeze({
  detail_uid: Object.freeze({ key: "detail_uid", label: "detail id" }),
  work_id: Object.freeze({ key: "work_id", label: "work id", type: "text" }),
  detail_id: Object.freeze({ key: "detail_id", label: "detail id", type: "text" }),
  details_subfolder: Object.freeze({ key: "details_subfolder", label: "details subfolder", type: "text" }),
  section_id: Object.freeze({ key: "section_id", label: "section id", type: "text", readonly: true }),
  section_title: Object.freeze({ key: "section_title", label: "section title", type: "text" }),
  sort_order: Object.freeze({ key: "sort_order", label: "section sort order", type: "text" }),
  project_filename: Object.freeze({ key: "project_filename", label: "project filename", type: "text" }),
  title: Object.freeze({ key: "title", label: "title", type: "text" }),
  status: Object.freeze({ key: "status", label: "status", type: "text", readonly: true }),
  published_date: Object.freeze({ key: "published_date", label: "published date" }),
  width_px: Object.freeze({ key: "width_px", label: "width px" }),
  height_px: Object.freeze({ key: "height_px", label: "height px" })
});

const WORK_DETAIL_EDITABLE_FIELDS = Object.freeze([
  WORK_DETAIL_FIELD_DEFINITIONS.details_subfolder,
  WORK_DETAIL_FIELD_DEFINITIONS.section_title,
  WORK_DETAIL_FIELD_DEFINITIONS.sort_order,
  WORK_DETAIL_FIELD_DEFINITIONS.project_filename,
  WORK_DETAIL_FIELD_DEFINITIONS.title,
  WORK_DETAIL_FIELD_DEFINITIONS.status
]);

const NEW_WORK_DETAIL_EDITABLE_FIELDS = Object.freeze([
  WORK_DETAIL_FIELD_DEFINITIONS.work_id,
  WORK_DETAIL_FIELD_DEFINITIONS.detail_id,
  WORK_DETAIL_FIELD_DEFINITIONS.title,
  WORK_DETAIL_FIELD_DEFINITIONS.section_title,
  WORK_DETAIL_FIELD_DEFINITIONS.details_subfolder,
  WORK_DETAIL_FIELD_DEFINITIONS.sort_order,
  WORK_DETAIL_FIELD_DEFINITIONS.project_filename
]);

const WORK_DETAIL_READONLY_FIELDS = Object.freeze([
  WORK_DETAIL_FIELD_DEFINITIONS.detail_uid,
  Object.freeze({ key: "work_id", label: "work id" }),
  Object.freeze({ key: "detail_id", label: "detail row id" }),
  WORK_DETAIL_FIELD_DEFINITIONS.section_id,
  WORK_DETAIL_FIELD_DEFINITIONS.published_date,
  WORK_DETAIL_FIELD_DEFINITIONS.width_px,
  WORK_DETAIL_FIELD_DEFINITIONS.height_px
]);

const WORK_DETAIL_STATUS_OPTIONS = new Set(["", "draft", "published"]);

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}

function normalizeDetailId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

function normalizeDetailUid(value, detailId = null, options = {}) {
  if (detailId != null) {
    const normalizedWorkId = normalizeWorkId(value);
    const normalizedDetailId = normalizeDetailId(detailId);
    if (!normalizedWorkId || !normalizedDetailId) return "";
    return `${normalizedWorkId}-${normalizedDetailId}`;
  }

  const text = normalizeText(value);
  if (!text) return "";
  const match = text.match(/^(\d{5})-(\d{3})$/);
  if (match) return `${match[1]}-${match[2]}`;
  const digits = text.replace(/\D/g, "");
  if (digits.length === 8) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`;
  }
  const currentWorkId = normalizeWorkId(options.currentWorkId);
  if (currentWorkId && digits && digits.length <= 3) {
    return `${currentWorkId}-${digits.padStart(3, "0")}`;
  }
  return "";
}

function canonicalizeWorkDetailScalar(_field, value) {
  return normalizeText(value);
}

function normalizeSortOrder(value) {
  const text = normalizeText(value);
  if (!text) return "";
  return /^-?\d+$/.test(text) ? String(Number(text)) : text;
}

function buildWorkDetailDraftFromRecord(record, options = {}) {
  const fields = Array.isArray(options.fields) ? options.fields : WORK_DETAIL_EDITABLE_FIELDS;
  const draft = {};
  fields.forEach((field) => {
    if (field.key === "details_subfolder") {
      draft[field.key] = normalizeText(record && (record.details_subfolder || record.project_subfolder));
    } else if (field.key === "section_title") {
      draft[field.key] = normalizeText(record && (record.section_title || record.project_subfolder));
    } else if (field.key === "sort_order") {
      draft[field.key] = normalizeSortOrder(record && record.sort_order);
    } else {
      draft[field.key] = normalizeText(record && record[field.key]);
    }
  });
  return draft;
}

function buildWorkDetailRecordFromDraft(draft, options = {}) {
  const source = draft || {};
  const workId = normalizeWorkId(options.workId == null ? source.work_id : options.workId);
  const detailId = normalizeDetailId(options.detailId == null ? source.detail_id : options.detailId);
  const detailUid = normalizeDetailUid(options.detailUid) || normalizeDetailUid(workId, detailId);
  const record = {
    detail_uid: detailUid,
    work_id: workId,
    detail_id: detailId,
    details_subfolder: normalizeText(source.details_subfolder) || null,
    section_title: normalizeText(source.section_title) || null,
    sort_order: normalizeSortOrder(source.sort_order) || null,
    project_filename: normalizeText(source.project_filename) || null,
    title: normalizeText(source.title) || null,
    status: Object.prototype.hasOwnProperty.call(options, "status")
      ? options.status
      : normalizeText(source.status).toLowerCase() || null
  };
  const sectionId = normalizeText(options.sectionId == null ? source.section_id : options.sectionId);
  if (sectionId) record.section_id = sectionId;
  return record;
}

function buildSaveWorkDetailPayload(state) {
  const draft = state.draft || {};
  return {
    detail_uid: state.currentDetailUid,
    expected_record_hash: state.currentRecordHash,
    apply_build: Boolean(Object.prototype.hasOwnProperty.call(state, "applyBuild") ? state.applyBuild : state.applyBuildNode && state.applyBuildNode.checked),
    record: buildWorkDetailRecordFromDraft(draft, {
      detailUid: state.currentDetailUid,
      workId: state.currentWorkId,
      detailId: state.currentRecord && state.currentRecord.detail_id,
      sectionId: state.currentRecord && state.currentRecord.section_id
    })
  };
}

function buildCreateWorkDetailPayload(draft) {
  const workId = normalizeWorkId(draft && draft.work_id);
  const detailId = normalizeDetailId(draft && draft.detail_id);
  const detailUid = normalizeDetailUid(workId, detailId);
  return {
    work_id: workId,
    detail_id: detailId,
    detail_uid: detailUid,
    record: {
      detail_uid: detailUid,
      work_id: workId,
      detail_id: detailId,
      title: normalizeText(draft && draft.title) || null,
      section_title: normalizeText(draft && draft.section_title) || null,
      details_subfolder: normalizeText(draft && draft.details_subfolder) || null,
      sort_order: normalizeSortOrder(draft && draft.sort_order) || null,
      project_filename: normalizeText(draft && draft.project_filename) || null,
      status: "draft"
    }
  };
}

function suggestNextDetailId(detailItems, workId) {
  const normalizedWorkId = normalizeWorkId(workId);
  if (!normalizedWorkId) return "";
  let maxDetailId = 0;
  detailItems.forEach((record) => {
    const detailUid = normalizeDetailUid(record && record.detail_uid) || normalizeDetailUid(record && record.work_id, record && record.detail_id);
    if (!detailUid.startsWith(`${normalizedWorkId}-`)) return;
    const detailId = Number(normalizeDetailId(record && record.detail_id));
    maxDetailId = Math.max(maxDetailId, detailId);
  });
  return String(maxDetailId + 1).padStart(3, "0");
}

function validateCreateWorkDetailDraft(draft, options = {}) {
  const errors = new Map();
  const t = typeof options.t === "function" ? options.t : (_key, fallback) => fallback;
  const workById = options.workById instanceof Map ? options.workById : new Map();
  const detailByUid = options.detailByUid instanceof Map ? options.detailByUid : new Map();
  const workId = normalizeWorkId(draft && draft.work_id);
  if (!workId) {
    errors.set("work_id", t("field_required_work_id", "Enter a parent work id."));
  } else if (!workById.has(workId)) {
    errors.set("work_id", t("field_unknown_work_id", "Unknown work id: {work_id}.", { work_id: workId }));
  } else if (options.requirePublishedParent && normalizeText(workById.get(workId) && workById.get(workId).status).toLowerCase() !== "published") {
    errors.set("work_id", t("field_parent_work_unpublished", "Publish the parent work before adding work details."));
  }

  const detailId = normalizeDetailId(draft && draft.detail_id);
  if (!detailId) {
    errors.set("detail_id", t("field_required_detail_id", "Enter a detail id."));
  } else if (workId && detailByUid.has(`${workId}-${detailId}`)) {
    errors.set("detail_id", t("field_duplicate_detail_id", "Detail id already exists for this work."));
  }

  if (!normalizeText(draft && draft.title)) {
    errors.set("title", t("field_required_title", "Enter a title."));
  }
  if (!normalizeText(draft && draft.section_title)) {
    errors.set("section_title", t("field_required_section_title", "Enter a section title."));
  }
  const rawSortOrder = normalizeText(draft && draft.sort_order);
  if (rawSortOrder && !/^\d+$/.test(rawSortOrder)) {
    errors.set("sort_order", t("field_invalid_sort_order", "Use a whole number or leave blank."));
  }
  return errors;
}

export {
  NEW_WORK_DETAIL_EDITABLE_FIELDS,
  WORK_DETAIL_EDITABLE_FIELDS,
  WORK_DETAIL_FIELD_DEFINITIONS,
  WORK_DETAIL_READONLY_FIELDS,
  WORK_DETAIL_STATUS_OPTIONS,
  buildCreateWorkDetailPayload,
  buildSaveWorkDetailPayload,
  buildWorkDetailDraftFromRecord,
  buildWorkDetailRecordFromDraft,
  canonicalizeWorkDetailScalar,
  normalizeDetailId,
  normalizeDetailUid,
  normalizeText,
  normalizeWorkId,
  suggestNextDetailId,
  validateCreateWorkDetailDraft
};
