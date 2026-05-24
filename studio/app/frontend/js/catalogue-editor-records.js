function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

export function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export async function computeRecordHash(record) {
  const cryptoApi = globalThis.crypto;
  if (!cryptoApi || !cryptoApi.subtle) return "";
  const json = stableStringify(record);
  const bytes = new TextEncoder().encode(json);
  const digest = await cryptoApi.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
}

export function displayValue(value, options = {}) {
  const emptyText = Object.prototype.hasOwnProperty.call(options, "emptyText") ? options.emptyText : "—";
  const text = normalizeText(value);
  return text || emptyText;
}

export function recordsEqual(a, b) {
  return stableStringify(a || {}) === stableStringify(b || {});
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
