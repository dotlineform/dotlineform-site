const WORK_FIELD_DEFINITIONS = Object.freeze({
  work_id: Object.freeze({ key: "work_id", label: "work id", type: "text" }),
  status: Object.freeze({ key: "status", label: "status", type: "text", readonly: true }),
  published_date: Object.freeze({ key: "published_date", label: "published date", type: "date" }),
  series_ids: Object.freeze({ key: "series_ids", label: "series", type: "text", description: "search by series title" }),
  project_folder: Object.freeze({ key: "project_folder", label: "project folder", type: "text" }),
  project_filename: Object.freeze({ key: "project_filename", label: "project filename", type: "text" }),
  title: Object.freeze({ key: "title", label: "title", type: "text" }),
  year: Object.freeze({ key: "year", label: "year", type: "number", step: "1" }),
  year_display: Object.freeze({ key: "year_display", label: "year display", type: "text" }),
  medium_type: Object.freeze({ key: "medium_type", label: "medium type", type: "text" }),
  medium_caption: Object.freeze({ key: "medium_caption", label: "medium caption", type: "text" }),
  duration: Object.freeze({ key: "duration", label: "duration", type: "text" }),
  height_cm: Object.freeze({ key: "height_cm", label: "height cm", type: "number", step: "any" }),
  width_cm: Object.freeze({ key: "width_cm", label: "width cm", type: "number", step: "any" }),
  depth_cm: Object.freeze({ key: "depth_cm", label: "depth cm", type: "number", step: "any" }),
  storage_location: Object.freeze({ key: "storage_location", label: "storage location", type: "text" }),
  notes: Object.freeze({ key: "notes", label: "notes", type: "textarea" }),
  provenance: Object.freeze({ key: "provenance", label: "provenance", type: "textarea" }),
  artist: Object.freeze({ key: "artist", label: "artist", type: "text" })
});

const WORK_EDITABLE_FIELDS = Object.freeze([
  WORK_FIELD_DEFINITIONS.status,
  WORK_FIELD_DEFINITIONS.published_date,
  WORK_FIELD_DEFINITIONS.series_ids,
  WORK_FIELD_DEFINITIONS.project_folder,
  WORK_FIELD_DEFINITIONS.project_filename,
  WORK_FIELD_DEFINITIONS.title,
  WORK_FIELD_DEFINITIONS.year,
  WORK_FIELD_DEFINITIONS.year_display,
  WORK_FIELD_DEFINITIONS.medium_type,
  WORK_FIELD_DEFINITIONS.medium_caption,
  WORK_FIELD_DEFINITIONS.duration,
  WORK_FIELD_DEFINITIONS.height_cm,
  WORK_FIELD_DEFINITIONS.width_cm,
  WORK_FIELD_DEFINITIONS.depth_cm,
  WORK_FIELD_DEFINITIONS.storage_location,
  WORK_FIELD_DEFINITIONS.notes,
  WORK_FIELD_DEFINITIONS.provenance,
  WORK_FIELD_DEFINITIONS.artist
]);

const NEW_WORK_EDITABLE_FIELDS = Object.freeze([
  WORK_FIELD_DEFINITIONS.work_id,
  WORK_FIELD_DEFINITIONS.title,
  WORK_FIELD_DEFINITIONS.series_ids,
  WORK_FIELD_DEFINITIONS.project_folder,
  WORK_FIELD_DEFINITIONS.project_filename,
  WORK_FIELD_DEFINITIONS.year,
  WORK_FIELD_DEFINITIONS.year_display,
  WORK_FIELD_DEFINITIONS.medium_type,
  WORK_FIELD_DEFINITIONS.medium_caption,
  WORK_FIELD_DEFINITIONS.duration,
  WORK_FIELD_DEFINITIONS.height_cm,
  WORK_FIELD_DEFINITIONS.width_cm,
  WORK_FIELD_DEFINITIONS.depth_cm,
  WORK_FIELD_DEFINITIONS.storage_location,
  WORK_FIELD_DEFINITIONS.notes,
  WORK_FIELD_DEFINITIONS.provenance,
  WORK_FIELD_DEFINITIONS.artist
]);

const WORK_READONLY_FIELDS = Object.freeze([
  Object.freeze({ key: "work_id", label: "work id" }),
  Object.freeze({ key: "width_px", label: "width px" }),
  Object.freeze({ key: "height_px", label: "height px" })
]);

const WORK_STATUS_OPTIONS = new Set(["", "draft", "published"]);
const WORK_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const WORK_SERIES_ID_RE = /^\d+$/;
const WORK_DIMENSION_FIELD_KEYS = Object.freeze(["height_cm", "width_cm", "depth_cm"]);

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}

function normalizeSeriesId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(3, "0");
}

function dedupeSeriesIds(items) {
  const seen = new Set();
  const out = [];
  items.forEach((item) => {
    if (!item || seen.has(item)) return;
    seen.add(item);
    out.push(item);
  });
  return out;
}

function parseSeriesIds(value) {
  if (Array.isArray(value)) {
    return dedupeSeriesIds(value.map((item) => normalizeSeriesId(item)).filter(Boolean));
  }
  const text = normalizeText(value);
  if (!text) return [];
  return dedupeSeriesIds(text.split(",").map((item) => normalizeSeriesId(item)).filter(Boolean));
}

function seriesIdsToText(value) {
  if (!Array.isArray(value)) return "";
  return value.map((item) => normalizeSeriesId(item)).filter(Boolean).join(", ");
}

function canonicalizeWorkScalar(field, value) {
  const text = normalizeText(value);
  if (field.key === "status") {
    return text.toLowerCase();
  }
  if (field.key === "series_ids") {
    return seriesIdsToText(parseSeriesIds(value));
  }
  if (field.type === "number") {
    return text;
  }
  return text;
}

function formatNumberText(value) {
  return normalizeText(value);
}

function normalizeEmbeddedEntries(value, fields) {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    const entry = {};
    fields.forEach((field) => {
      const text = normalizeText(item && item[field]);
      if (text) entry[field] = text;
    });
    return entry;
  }).filter((entry) => fields.some((field) => normalizeText(entry[field])));
}

function cloneEmbeddedEntries(value, fields) {
  return normalizeEmbeddedEntries(value, fields).map((entry) => ({ ...entry }));
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
  return stableStringify(normalizeEmbeddedEntries(a, fields)) === stableStringify(normalizeEmbeddedEntries(b, fields));
}

function buildWorkDraftFromRecord(record, options = {}) {
  const fields = Array.isArray(options.fields) ? options.fields : WORK_EDITABLE_FIELDS;
  const draft = {};
  fields.forEach((field) => {
    if (field.key === "series_ids") {
      draft[field.key] = seriesIdsToText(record && record[field.key]);
      return;
    }
    draft[field.key] = formatNumberText(record && record[field.key]);
  });
  if (options.downloadFields) {
    draft.downloads = cloneEmbeddedEntries(record && record.downloads, options.downloadFields);
  }
  if (options.linkFields) {
    draft.links = cloneEmbeddedEntries(record && record.links, options.linkFields);
  }
  return draft;
}

function buildWorkRecordFromDraft(draft, options = {}) {
  const record = {};
  if (options.includeWorkId) {
    record.work_id = normalizeWorkId(options.workId == null ? draft.work_id : options.workId);
  }

  record.status = Object.prototype.hasOwnProperty.call(options, "status")
    ? options.status
    : normalizeText(draft.status).toLowerCase() || null;
  record.published_date = Object.prototype.hasOwnProperty.call(options, "publishedDate")
    ? options.publishedDate
    : normalizeText(draft.published_date) || null;
  record.series_ids = parseSeriesIds(draft.series_ids);
  record.project_folder = normalizeText(draft.project_folder) || null;
  record.project_filename = normalizeText(draft.project_filename) || null;
  record.title = normalizeText(draft.title) || null;
  record.year = normalizeText(draft.year) ? Number(draft.year) : null;
  record.year_display = normalizeText(draft.year_display) || null;
  record.medium_type = normalizeText(draft.medium_type) || null;
  record.medium_caption = normalizeText(draft.medium_caption) || null;
  record.duration = normalizeText(draft.duration) || null;
  record.height_cm = normalizeText(draft.height_cm) ? Number(draft.height_cm) : null;
  record.width_cm = normalizeText(draft.width_cm) ? Number(draft.width_cm) : null;
  record.depth_cm = normalizeText(draft.depth_cm) ? Number(draft.depth_cm) : null;
  record.storage_location = normalizeText(draft.storage_location) || null;
  record.notes = normalizeText(draft.notes) || null;
  record.provenance = normalizeText(draft.provenance) || null;
  record.artist = normalizeText(draft.artist) || null;

  if (options.downloadFields) {
    record.downloads = normalizeEmbeddedEntries(draft.downloads, options.downloadFields);
  }
  if (options.linkFields) {
    record.links = normalizeEmbeddedEntries(draft.links, options.linkFields);
  }
  return record;
}

function buildCreateWorkPayload(draft) {
  const workId = normalizeWorkId(draft.work_id);
  return {
    work_id: workId,
    record: buildWorkRecordFromDraft(draft, {
      includeWorkId: true,
      workId,
      status: "draft",
      publishedDate: null
    })
  };
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

export {
  NEW_WORK_EDITABLE_FIELDS,
  WORK_DATE_RE,
  WORK_DIMENSION_FIELD_KEYS,
  WORK_EDITABLE_FIELDS,
  WORK_FIELD_DEFINITIONS,
  WORK_READONLY_FIELDS,
  WORK_SERIES_ID_RE,
  WORK_STATUS_OPTIONS,
  buildCreateWorkPayload,
  buildWorkDraftFromRecord,
  buildWorkRecordFromDraft,
  canonicalizeWorkScalar,
  cloneEmbeddedEntries,
  dedupeSeriesIds,
  embeddedEntriesEqual,
  formatNumberText,
  normalizeEmbeddedEntries,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  parseSeriesIds,
  seriesIdsToText,
  suggestNextWorkId
};
