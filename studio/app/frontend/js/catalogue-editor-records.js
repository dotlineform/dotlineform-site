function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

export function displayValue(value, options = {}) {
  const emptyText = Object.prototype.hasOwnProperty.call(options, "emptyText") ? options.emptyText : "—";
  const text = normalizeText(value);
  return text || emptyText;
}

export function buildChangedFieldNames(options = {}) {
  const fields = Array.isArray(options.fields) ? options.fields : [];
  const draft = options.draft || {};
  const baselineDraft = options.baselineDraft || {};
  const canonicalizeScalar = typeof options.canonicalizeScalar === "function"
    ? options.canonicalizeScalar
    : (_field, value) => normalizeText(value);
  const changedFields = [];

  fields.forEach((field) => {
    const key = normalizeText(field && field.key);
    if (!key) return;
    if (canonicalizeScalar(field, draft[key]) !== canonicalizeScalar(field, baselineDraft[key])) {
      changedFields.push(key);
    }
  });

  const extraComparisons = Array.isArray(options.extraComparisons) ? options.extraComparisons : [];
  extraComparisons.forEach((comparison) => {
    const key = normalizeText(comparison && comparison.key);
    if (!key || typeof comparison.changed !== "function") return;
    if (comparison.changed({ draft, baselineDraft })) changedFields.push(key);
  });

  return changedFields;
}
