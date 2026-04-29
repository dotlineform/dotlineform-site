const SERIES_FIELD_DEFINITIONS = Object.freeze({
  series_id: Object.freeze({ key: "series_id", label: "series id", type: "text" }),
  title: Object.freeze({ key: "title", label: "title", type: "text" }),
  series_type: Object.freeze({ key: "series_type", label: "series type", type: "select", options: ["primary", "holding"] }),
  status: Object.freeze({ key: "status", label: "status", type: "text", readonly: true }),
  published_date: Object.freeze({ key: "published_date", label: "published date", type: "date" }),
  year: Object.freeze({ key: "year", label: "year", type: "number", step: "1" }),
  year_display: Object.freeze({ key: "year_display", label: "year display", type: "text" }),
  primary_work_id: Object.freeze({ key: "primary_work_id", label: "primary work id", type: "text" }),
  sort_fields: Object.freeze({ key: "sort_fields", label: "sort fields", type: "text" }),
  notes: Object.freeze({ key: "notes", label: "notes", type: "textarea" })
});

const SERIES_EDITABLE_FIELDS = Object.freeze([
  SERIES_FIELD_DEFINITIONS.title,
  SERIES_FIELD_DEFINITIONS.series_type,
  SERIES_FIELD_DEFINITIONS.status,
  SERIES_FIELD_DEFINITIONS.published_date,
  SERIES_FIELD_DEFINITIONS.year,
  SERIES_FIELD_DEFINITIONS.year_display,
  SERIES_FIELD_DEFINITIONS.primary_work_id,
  SERIES_FIELD_DEFINITIONS.sort_fields,
  SERIES_FIELD_DEFINITIONS.notes
]);

const NEW_SERIES_EDITABLE_FIELDS = Object.freeze([
  SERIES_FIELD_DEFINITIONS.series_id,
  SERIES_FIELD_DEFINITIONS.title,
  SERIES_FIELD_DEFINITIONS.series_type,
  SERIES_FIELD_DEFINITIONS.year,
  SERIES_FIELD_DEFINITIONS.year_display,
  SERIES_FIELD_DEFINITIONS.sort_fields,
  SERIES_FIELD_DEFINITIONS.notes
]);

const SERIES_READONLY_FIELDS = Object.freeze([
  Object.freeze({ key: "series_id", label: "series id" })
]);

const SERIES_STATUS_OPTIONS = new Set(["", "draft", "published"]);
const SERIES_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SERIES_TYPE_OPTIONS = Object.freeze(["primary", "holding"]);

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

function normalizeOptionValue(value) {
  return normalizeText(value).toLowerCase();
}

function dedupeOptions(items) {
  const seen = new Set();
  const out = [];
  items.forEach((item) => {
    const value = normalizeOptionValue(item);
    if (!value || seen.has(value)) return;
    seen.add(value);
    out.push(value);
  });
  return out;
}

function getSeriesTypeOptions(config) {
  const configured = config && config.catalogue && Array.isArray(config.catalogue.series_type_options)
    ? config.catalogue.series_type_options
    : null;
  const options = dedupeOptions(configured || SERIES_TYPE_OPTIONS);
  return options.length ? options : SERIES_TYPE_OPTIONS.slice();
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
  record.series_type = normalizeText(draft.series_type) || null;
  record.status = Object.prototype.hasOwnProperty.call(options, "status")
    ? options.status
    : normalizeText(draft.status).toLowerCase() || null;
  record.published_date = Object.prototype.hasOwnProperty.call(options, "publishedDate")
    ? options.publishedDate
    : normalizeText(draft.published_date) || null;
  record.year = normalizeText(draft.year) ? Number(draft.year) : null;
  record.year_display = normalizeText(draft.year_display) || null;
  record.primary_work_id = Object.prototype.hasOwnProperty.call(options, "primaryWorkId")
    ? options.primaryWorkId
    : normalizeWorkId(draft.primary_work_id) || null;
  record.sort_fields = normalizeText(draft.sort_fields) || null;
  record.notes = normalizeText(draft.notes) || null;
  return record;
}

function buildSaveSeriesPayload(state, workUpdates) {
  return {
    series_id: state.currentSeriesId,
    expected_record_hash: state.currentRecordHash,
    apply_build: Boolean(state.applyBuildNode && state.applyBuildNode.checked),
    extra_work_ids: state.pendingBuildExtraWorkIds.slice(),
    record: buildSeriesRecordFromDraft(state.draft),
    work_updates: workUpdates
  };
}

function buildCreateSeriesPayload(draft) {
  const seriesId = normalizeSeriesId(draft.series_id);
  return {
    series_id: seriesId,
    record: buildSeriesRecordFromDraft(draft, {
      status: "draft",
      publishedDate: null,
      primaryWorkId: null
    })
  };
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
  const errors = new Map();
  const t = typeof options.t === "function" ? options.t : (_key, fallback) => fallback;
  const seriesById = options.seriesById instanceof Map ? options.seriesById : new Map();
  const seriesTypeOptions = new Set(dedupeOptions(options.seriesTypeOptions || SERIES_TYPE_OPTIONS));
  const seriesId = normalizeSeriesId(draft && draft.series_id);
  if (!seriesId) {
    errors.set("series_id", t("field_required_series_id", "Enter a series id."));
  } else if (seriesById.has(seriesId)) {
    errors.set("series_id", t("field_duplicate_series_id", "Series id already exists."));
  }

  if (!normalizeText(draft && draft.title)) {
    errors.set("title", t("field_required_title", "Enter a title."));
  }

  const seriesType = normalizeOptionValue(draft && draft.series_type);
  if (!seriesType) {
    errors.set("series_type", t("field_required_series_type", "Choose a series type."));
  } else if (!seriesTypeOptions.has(seriesType)) {
    errors.set("series_type", t("field_invalid_series_type", "Choose a listed series type."));
  }

  validateRequiredSeriesMetadata(draft, errors, t);
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
  const currentMemberWorkIds = options.currentMemberWorkIds instanceof Set ? options.currentMemberWorkIds : new Set();
  const status = normalizeText(draft && draft.status).toLowerCase();
  if (!SERIES_STATUS_OPTIONS.has(status)) {
    errors.set("status", t("field_invalid_status", "Use blank, draft, or published."));
  }
  const publishedDate = normalizeText(draft && draft.published_date);
  if (publishedDate && !SERIES_DATE_RE.test(publishedDate)) {
    errors.set("published_date", t("field_invalid_published_date", "Use YYYY-MM-DD or leave blank."));
  }
  validateRequiredSeriesMetadata(draft, errors, t);
  const primaryWorkId = normalizeWorkId(draft && draft.primary_work_id);
  if (status === "published" && !primaryWorkId) {
    errors.set("primary_work_id", t("field_required_primary_work_publish", "Published series must have a primary work that belongs to this series."));
  } else if (primaryWorkId && !currentMemberWorkIds.has(primaryWorkId)) {
    errors.set("primary_work_id", t("field_invalid_primary_work", "Primary work must be a current member of this series."));
  }
  return errors;
}

export {
  NEW_SERIES_EDITABLE_FIELDS,
  SERIES_DATE_RE,
  SERIES_EDITABLE_FIELDS,
  SERIES_FIELD_DEFINITIONS,
  SERIES_READONLY_FIELDS,
  SERIES_STATUS_OPTIONS,
  SERIES_TYPE_OPTIONS,
  buildCreateSeriesPayload,
  buildSaveSeriesPayload,
  buildSeriesDraftFromRecord,
  buildSeriesRecordFromDraft,
  formatNumberText,
  getSeriesTypeOptions,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  suggestNextSeriesId,
  validateCreateSeriesDraft,
  validateSeriesDraft
};
