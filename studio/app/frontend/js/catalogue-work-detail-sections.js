import { normalizeText } from "./catalogue-work-detail-fields.js";

const BULK_PREVIEW_LIMIT = 12;

export function buildWorkDetailRecordSummary(record) {
  const title = normalizeText(record && record.title);
  const section = normalizeText(record && record.section_title);
  if (title && section) return `${title} · ${section}`;
  return title || section || "—";
}

export function formatWorkDetailSelectionList(items) {
  const list = Array.isArray(items) ? items.slice(0, BULK_PREVIEW_LIMIT) : [];
  if (!list.length) return "";
  const more = (items.length || 0) - list.length;
  return more > 0 ? `${list.join(", ")} +${more} more` : list.join(", ");
}
