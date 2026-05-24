const MOMENT_FIELD_DEFINITIONS = Object.freeze({
  moment_id: Object.freeze({ key: "moment_id", label: "moment id" }),
  title: Object.freeze({ key: "title", label: "title", type: "text" }),
  status: Object.freeze({ key: "status", label: "status", type: "text", readonly: true }),
  date: Object.freeze({ key: "date", label: "date", type: "date" }),
  date_display: Object.freeze({ key: "date_display", label: "date display", type: "text" }),
  published_date: Object.freeze({ key: "published_date", label: "published date", type: "date" }),
  source_image_file: Object.freeze({ key: "source_image_file", label: "source image file", type: "text" }),
  image_alt: Object.freeze({ key: "image_alt", label: "image alt", type: "text" })
});

const MOMENT_EDITABLE_FIELDS = Object.freeze([
  MOMENT_FIELD_DEFINITIONS.title,
  MOMENT_FIELD_DEFINITIONS.status,
  MOMENT_FIELD_DEFINITIONS.date,
  MOMENT_FIELD_DEFINITIONS.date_display,
  MOMENT_FIELD_DEFINITIONS.published_date,
  MOMENT_FIELD_DEFINITIONS.source_image_file,
  MOMENT_FIELD_DEFINITIONS.image_alt
]);

const MOMENT_READONLY_FIELDS = Object.freeze([
  MOMENT_FIELD_DEFINITIONS.moment_id
]);

const MOMENT_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const MOMENT_STATUS_OPTIONS = new Set(["draft", "published"]);

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeMomentId(value) {
  return normalizeText(value).toLowerCase().replace(/\.md$/, "");
}

function normalizeMomentFilename(value) {
  const raw = normalizeText(value).toLowerCase();
  if (!raw) return "";
  return raw.endsWith(".md") ? raw : `${raw}.md`;
}

function buildMomentRecordFromDraft(draft, options = {}) {
  const source = draft || {};
  const momentId = normalizeMomentId(source.moment_id || options.momentId);
  const record = {
    moment_id: momentId,
    title: normalizeText(source.title),
    status: normalizeText(source.status).toLowerCase() || "draft",
    published_date: normalizeText(source.published_date) || null,
    date: normalizeText(source.date) || null,
    date_display: normalizeText(source.date_display) || null,
    image_alt: normalizeText(source.image_alt) || null
  };
  const sourceImageFile = normalizeText(source.source_image_file);
  if (sourceImageFile && sourceImageFile !== `${momentId}.jpg`) {
    record.source_image_file = sourceImageFile;
  }
  return record;
}

function normalizeMomentRecord(momentId, record) {
  return buildMomentRecordFromDraft(record, { momentId });
}

function readMomentDraft(state, options = {}) {
  const getValue = typeof options.getFieldNodeValue === "function"
    ? options.getFieldNodeValue
    : (node) => ("value" in node ? node.value : node.textContent);
  const draft = { moment_id: state.currentMomentId };
  MOMENT_EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    draft[field.key] = node ? normalizeText(getValue(node)) : "";
  });
  return buildMomentRecordFromDraft(draft, { momentId: state.currentMomentId });
}

function buildSaveMomentPayload(state, options = {}) {
  const draft = options.draft || readMomentDraft(state, options);
  return {
    moment_id: state.currentMomentId,
    expected_record_hash: state.expectedRecordHash,
    record: draft,
    apply_build: Boolean(options.applyBuild)
  };
}

function validateMomentDraft(draft, options = {}) {
  const errors = new Map();
  const t = typeof options.t === "function" ? options.t : (_key, fallback) => fallback;
  if (!draft || !normalizeText(draft.title)) {
    errors.set("title", t("field_required_title", "Enter a title."));
  }
  if (!draft || !normalizeText(draft.date)) {
    errors.set("date", t("field_required_date", "Enter a date."));
  }
  ["date", "published_date"].forEach((key) => {
    const value = normalizeText(draft && draft[key]);
    if (value && !MOMENT_DATE_RE.test(value)) {
      errors.set(key, t("field_invalid_date", "Use YYYY-MM-DD or leave blank."));
    }
  });
  const status = normalizeText(draft && draft.status).toLowerCase();
  if (!MOMENT_STATUS_OPTIONS.has(status)) {
    errors.set("status", t("field_invalid_status", "Use draft or published."));
  }
  if (status === "published" && !normalizeText(draft && draft.published_date)) {
    errors.set("published_date", t("field_required_published_date", "Published moments require a published date."));
  }
  return errors;
}

export {
  MOMENT_DATE_RE,
  MOMENT_EDITABLE_FIELDS,
  MOMENT_FIELD_DEFINITIONS,
  MOMENT_READONLY_FIELDS,
  MOMENT_STATUS_OPTIONS,
  buildMomentRecordFromDraft,
  buildSaveMomentPayload,
  normalizeMomentFilename,
  normalizeMomentId,
  normalizeMomentRecord,
  normalizeText,
  readMomentDraft,
  validateMomentDraft
};
