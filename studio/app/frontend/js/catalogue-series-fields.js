const SERIES_FIELD_DEFINITIONS = Object.freeze({
  series_id: Object.freeze({ key: "series_id", label: "series id", type: "text" }),
  title: Object.freeze({ key: "title", label: "title", type: "text" }),
  year: Object.freeze({ key: "year", label: "year", type: "number", step: "1" }),
  year_display: Object.freeze({ key: "year_display", label: "year display", type: "text" }),
  sort_fields: Object.freeze({ key: "sort_fields", label: "sort fields", type: "text" })
});

const SERIES_EDITABLE_FIELDS = Object.freeze([
  SERIES_FIELD_DEFINITIONS.title,
  SERIES_FIELD_DEFINITIONS.year,
  SERIES_FIELD_DEFINITIONS.year_display,
  SERIES_FIELD_DEFINITIONS.sort_fields
]);

const NEW_SERIES_EDITABLE_FIELDS = Object.freeze([
  SERIES_FIELD_DEFINITIONS.series_id,
  SERIES_FIELD_DEFINITIONS.title,
  SERIES_FIELD_DEFINITIONS.year,
  SERIES_FIELD_DEFINITIONS.year_display,
  SERIES_FIELD_DEFINITIONS.sort_fields
]);

const SERIES_READONLY_FIELDS = Object.freeze([
  Object.freeze({ key: "series_id", label: "series id" })
]);


function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeSeriesId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (digits) return digits.padStart(3, "0");
  return normalizeText(value).toLowerCase();
}

function normalizeWorkId(value) {
  const digits = normalizeText(value).replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(5, "0");
}


function formatNumberText(value) {
  return normalizeText(value);
}

function buildSeriesDraftFromRecord(record, options = {}) {
  const fields = Array.isArray(options.fields) ? options.fields : SERIES_EDITABLE_FIELDS;
  const draft = {};
  fields.forEach((field) => {
    draft[field.key] = formatNumberText(record && record[field.key]);
  });
  return draft;
}

function buildSeriesRecordFromDraft(draft, options = {}) {
  const record = {};
  if (options.includeSeriesId) {
    record.series_id = normalizeSeriesId(options.seriesId == null ? draft.series_id : options.seriesId);
  }
  record.title = normalizeText(draft.title) || null;
  record.year = normalizeText(draft.year) ? Number(draft.year) : null;
  record.year_display = normalizeText(draft.year_display) || null;
  record.sort_fields = normalizeText(draft.sort_fields) || null;
  return record;
}

function buildSaveSeriesPayload(state, workUpdates) {
  return {
    series_id: state.currentSeriesId,
    expected_record_hash: state.currentRecordHash,
    record: buildSeriesRecordFromDraft(state.draft),
    work_updates: workUpdates
  };
}

function buildCreateSeriesPayload(draft) {
  const seriesId = normalizeSeriesId(draft.series_id);
  return { series_id: seriesId, record: buildSeriesRecordFromDraft(draft, { includeSeriesId: true, seriesId }) };
}

function suggestNextSeriesId(seriesItems) {
  let maxNumericId = 0;
  seriesItems.forEach((record) => {
    const seriesId = normalizeSeriesId(record && record.series_id);
    if (!/^\d+$/.test(seriesId)) return;
    maxNumericId = Math.max(maxNumericId, Number(seriesId));
  });
  if (maxNumericId <= 0) return "001";
  return String(maxNumericId + 1).padStart(3, "0");
}

function validateCreateSeriesDraft(draft, options = {}) {
  const errors = validateSeriesDraft(draft, options);
  const id = normalizeSeriesId(draft && draft.series_id);
  if (!id) errors.set("series_id", "Enter a Series id.");
  else if (options.seriesById?.has(id)) errors.set("series_id", "Series id already exists.");
  return errors;
}

function validateRequiredSeriesMetadata(draft, errors, t) {
  const year = normalizeText(draft && draft.year);
  if (!year) {
    errors.set("year", t("field_required_year", "Enter a year."));
  } else if (!/^-?\d+$/.test(year)) {
    errors.set("year", t("field_invalid_year", "Use a whole year."));
  }

  if (!normalizeText(draft && draft.year_display)) {
    errors.set("year_display", t("field_required_year_display", "Enter a year display."));
  }
}

function validateSeriesDraft(draft, options = {}) {
  const errors = new Map();
  const t = typeof options.t === "function" ? options.t : (_key, fallback) => fallback;
  if (!normalizeText(draft && draft.title)) errors.set("title", t("field_required_title", "Enter a title."));
  validateRequiredSeriesMetadata(draft, errors, t);
  return errors;
}

export { NEW_SERIES_EDITABLE_FIELDS, SERIES_EDITABLE_FIELDS, SERIES_FIELD_DEFINITIONS, SERIES_READONLY_FIELDS, buildCreateSeriesPayload, buildSaveSeriesPayload, buildSeriesDraftFromRecord, buildSeriesRecordFromDraft, formatNumberText, normalizeSeriesId, normalizeText, normalizeWorkId, suggestNextSeriesId, validateCreateSeriesDraft, validateSeriesDraft };
