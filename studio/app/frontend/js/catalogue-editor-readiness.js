function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function readinessSource(buildPreview, options = {}) {
  if (buildPreview && typeof buildPreview === "object" && buildPreview.readiness) {
    return buildPreview.readiness;
  }
  return options.fallbackReadiness || null;
}

export function catalogueReadinessTone(status, options = {}) {
  const normalized = normalizeText(status);
  if (normalized === "ready") return "ready";
  if (normalized === "unavailable") return "error";
  if (normalized === "missing_file") return normalizeText(options.missingFileTone) || "warning";
  return "warning";
}

export function catalogueReadinessItems(buildPreview, options = {}) {
  const source = readinessSource(buildPreview, options);
  const items = source && Array.isArray(source.items) ? source.items : [];
  const keys = Array.isArray(options.keys)
    ? options.keys.map((key) => normalizeText(key)).filter(Boolean)
    : [];
  if (!keys.length) return items;
  const allowed = new Set(keys);
  return items.filter((item) => allowed.has(normalizeText(item && item.key)));
}

export function catalogueReadinessItem(buildPreview, key, options = {}) {
  const normalizedKey = normalizeText(key);
  return catalogueReadinessItems(buildPreview, options).find((item) => normalizeText(item && item.key) === normalizedKey) || null;
}

export function catalogueReadinessItemSummary(item, options = {}) {
  return {
    key: normalizeText(item && item.key),
    status: normalizeText(item && item.status),
    title: normalizeText(item && item.title) || normalizeText(options.fallbackTitle) || "readiness",
    summary: normalizeText(item && item.summary) || normalizeText(options.fallbackSummary) || "-",
    sourcePath: normalizeText(item && item.source_path),
    nextStep: normalizeText(item && item.next_step),
    exists: Boolean(item && item.exists)
  };
}
