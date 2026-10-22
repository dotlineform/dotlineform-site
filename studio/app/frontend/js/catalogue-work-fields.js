const WORK_FIELD_DEFINITIONS = Object.freeze({
  work_id: Object.freeze({ key: "work_id", label: "work id", type: "text", required: "new" }),
  series_id: Object.freeze({ key: "series_id", label: "series", type: "text", required: true }),
  gallery_ids: Object.freeze({ key: "gallery_ids", label: "galleries", type: "galleries" }),
  media_source_id: Object.freeze({ key: "media_source_id", label: "media source", type: "media-source" }),
  project_folder: Object.freeze({ key: "project_folder", label: "project folder", type: "text" }),
  project_subfolder: Object.freeze({ key: "project_subfolder", label: "project subfolder", type: "text" }),
  project_filename: Object.freeze({ key: "project_filename", label: "project filename", type: "text" }),
  title: Object.freeze({ key: "title", label: "title", type: "text", required: true }),
  year: Object.freeze({ key: "year", label: "year", type: "number", step: "1", required: true }),
  year_display: Object.freeze({ key: "year_display", label: "year display", type: "text", required: true }),
  medium: Object.freeze({ key: "medium", label: "medium", type: "text" }),
  duration: Object.freeze({ key: "duration", label: "duration", type: "text" }),
  height_cm: Object.freeze({ key: "height_cm", label: "height cm", type: "number", step: "any" }),
  width_cm: Object.freeze({ key: "width_cm", label: "width cm", type: "number", step: "any" }),
  depth_cm: Object.freeze({ key: "depth_cm", label: "depth cm", type: "number", step: "any" }),
  storage_location: Object.freeze({ key: "storage_location", label: "storage location", type: "text" })
});

const WORK_EDITABLE_FIELDS = Object.freeze([
  WORK_FIELD_DEFINITIONS.series_id,
  WORK_FIELD_DEFINITIONS.gallery_ids,
  WORK_FIELD_DEFINITIONS.media_source_id,
  WORK_FIELD_DEFINITIONS.project_folder,
  WORK_FIELD_DEFINITIONS.project_subfolder,
  WORK_FIELD_DEFINITIONS.project_filename,
  WORK_FIELD_DEFINITIONS.title,
  WORK_FIELD_DEFINITIONS.year,
  WORK_FIELD_DEFINITIONS.year_display,
  WORK_FIELD_DEFINITIONS.medium,
  WORK_FIELD_DEFINITIONS.duration,
  WORK_FIELD_DEFINITIONS.height_cm,
  WORK_FIELD_DEFINITIONS.width_cm,
  WORK_FIELD_DEFINITIONS.depth_cm,
  WORK_FIELD_DEFINITIONS.storage_location
]);

const NEW_WORK_EDITABLE_FIELDS = Object.freeze([
  WORK_FIELD_DEFINITIONS.work_id,
  WORK_FIELD_DEFINITIONS.title,
  WORK_FIELD_DEFINITIONS.series_id,
  WORK_FIELD_DEFINITIONS.gallery_ids,
  WORK_FIELD_DEFINITIONS.media_source_id,
  WORK_FIELD_DEFINITIONS.project_folder,
  WORK_FIELD_DEFINITIONS.project_subfolder,
  WORK_FIELD_DEFINITIONS.project_filename,
  WORK_FIELD_DEFINITIONS.year,
  WORK_FIELD_DEFINITIONS.year_display,
  WORK_FIELD_DEFINITIONS.medium,
  WORK_FIELD_DEFINITIONS.duration,
  WORK_FIELD_DEFINITIONS.height_cm,
  WORK_FIELD_DEFINITIONS.width_cm,
  WORK_FIELD_DEFINITIONS.depth_cm,
  WORK_FIELD_DEFINITIONS.storage_location
]);

const WORK_READONLY_FIELDS = Object.freeze([]);

const BULK_WORK_METADATA_FIELDS = Object.freeze([
  WORK_FIELD_DEFINITIONS.title,
  WORK_FIELD_DEFINITIONS.year,
  WORK_FIELD_DEFINITIONS.year_display,
  WORK_FIELD_DEFINITIONS.medium,
  WORK_FIELD_DEFINITIONS.height_cm,
  WORK_FIELD_DEFINITIONS.width_cm,
  WORK_FIELD_DEFINITIONS.storage_location
]);

const WORK_SERIES_ID_RE = /^\d+$/;
const WORK_DIMENSION_FIELD_KEYS = Object.freeze(["height_cm", "width_cm", "depth_cm"]);

/**
 * Bulk required-field feedback applies only to explicitly edited metadata.
 * @param {{key: string, required?: boolean | "new"}} field True requires the field; "new" limits it to creation.
 * @param {"single" | "new" | "bulk"} mode Current Work editor mode.
 * @param {Set<string>} [touchedFields] Explicit bulk edits; untouched fields retain each saved value.
 * @returns {boolean} Whether the editable field must have a value before Save.
 */
function isWorkFieldRequired(field, mode, touchedFields) {
  if (mode === "bulk") return field.required === true && BULK_WORK_METADATA_FIELDS.includes(field) && Boolean(touchedFields?.has(field.key));
  return field.required === true || (field.required === "new" && mode === "new");
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}

function normalizeSeriesId(value) {
  const text = normalizeText(value);
  return /^\d+$/.test(text) ? text.padStart(3, "0") : "";
}


function canonicalizeWorkScalar(field, value) {
  if (field.key === "gallery_ids") return JSON.stringify((value || []).slice().sort());
  return field.key === "series_id" ? normalizeSeriesId(value) : normalizeText(value);
}

function draftScalarValue(field, value) {
  if (value === undefined || value === null) return "";
  if (field.type === "number") {
    if (typeof value !== "number") throw new Error("Saved Work " + field.key + " must be numeric or absent.");
    return String(value);
  }
  if (typeof value !== "string") throw new Error("Saved Work " + field.key + " must be text or absent.");
  return value;
}

/** Copy authored fields unchanged; absence is optional, malformed arrays/entries fail. */
function cloneEmbeddedEntries(value, fields) {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error("Work resource entries must be an array.");
  return value.map((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      throw new Error("Each Work resource entry must be an object.");
    }
    if (fields === undefined) return { ...item };
    return Object.fromEntries(fields.map(field => [field, item[field]]));
  });
}

function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function embeddedEntriesEqual(a, b, fields) {
  return stableStringify(cloneEmbeddedEntries(a, fields)) === stableStringify(cloneEmbeddedEntries(b, fields));
}

/** Load saved values into controls unchanged; numeric controls need text and optional absence is blank. */
function buildWorkDraftFromRecord(record, options = {}) {
  const fields = Array.isArray(options.fields) ? options.fields : WORK_EDITABLE_FIELDS;
  const galleryIds = record?.gallery_ids;
  if (galleryIds !== undefined && (!Array.isArray(galleryIds) || galleryIds.some(id => typeof id !== "string"))) {
    throw new Error("Saved Work Gallery IDs must be an array of strings.");
  }
  const draft = Object.fromEntries(fields.filter(field => field.key !== "gallery_ids").map(field => [field.key,
    draftScalarValue(field, record?.[field.key])
  ]));
  draft.gallery_ids = galleryIds === undefined ? [] : galleryIds.slice().sort();
  if (options.downloadFields) draft.downloads = cloneEmbeddedEntries(record?.downloads, options.downloadFields);
  if (options.linkFields) draft.links = cloneEmbeddedEntries(record?.links, options.linkFields);
  return draft;
}

function buildWorkRecordFromDraft(draft, options = {}) {
  const record = {};
  if (options.includeWorkId) {
    record.work_id = normalizeWorkId(options.workId == null ? draft.work_id : options.workId);
  }

  record.series_id = normalizeSeriesId(draft.series_id) || null;
  record.media_source_id = normalizeText(draft.media_source_id) || null;
  record.project_folder = draft.project_folder || null;
  record.project_subfolder = draft.project_subfolder || null;
  record.project_filename = draft.project_filename || null;
  record.title = normalizeText(draft.title) || null;
  record.year = normalizeText(draft.year) ? Number(draft.year) : null;
  record.year_display = normalizeText(draft.year_display) || null;
  record.medium = normalizeText(draft.medium) || null;
  record.duration = normalizeText(draft.duration) || null;
  record.height_cm = normalizeText(draft.height_cm) ? Number(draft.height_cm) : null;
  record.width_cm = normalizeText(draft.width_cm) ? Number(draft.width_cm) : null;
  record.depth_cm = normalizeText(draft.depth_cm) ? Number(draft.depth_cm) : null;
  record.storage_location = normalizeText(draft.storage_location) || null;

  if (options.downloadFields) {
    record.downloads = cloneEmbeddedEntries(draft.downloads, options.downloadFields);
  }
  if (options.linkFields) {
    record.links = cloneEmbeddedEntries(draft.links, options.linkFields);
  }
  return record;
}

function buildCreateWorkPayload(draft) {
  const workId = normalizeWorkId(draft.work_id);
  return { work_id: workId, record: buildWorkRecordFromDraft(draft, { includeWorkId: true, workId }), gallery_ids: draft.gallery_ids.slice() };
}

function suggestNextWorkId(workItems) {
  let maxNumericId = 0;
  workItems.forEach((record) => {
    const workId = normalizeWorkId(record && record.work_id);
    if (!/^\d+$/.test(workId)) return;
    maxNumericId = Math.max(maxNumericId, Number(workId));
  });
  if (maxNumericId <= 0) return "00001";
  return String(maxNumericId + 1).padStart(5, "0");
}

export { BULK_WORK_METADATA_FIELDS, NEW_WORK_EDITABLE_FIELDS, WORK_DIMENSION_FIELD_KEYS, WORK_EDITABLE_FIELDS, WORK_FIELD_DEFINITIONS, WORK_READONLY_FIELDS, WORK_SERIES_ID_RE, buildCreateWorkPayload, buildWorkDraftFromRecord, buildWorkRecordFromDraft, canonicalizeWorkScalar, cloneEmbeddedEntries, embeddedEntriesEqual, isWorkFieldRequired, normalizeSeriesId, normalizeText, normalizeWorkId, suggestNextWorkId };
