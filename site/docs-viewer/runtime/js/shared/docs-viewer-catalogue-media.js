import { docsViewerSafeMediaTarget, normalizeDocsViewerMediaPresentation } from "./docs-viewer-media-presentation.js";

export function catalogueMediaTarget(workId, detailId = "") {
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId)
    || typeof detailId !== "string" || (detailId && (!/^(?:\d{3}|[1-9]\d{3,})$/.test(detailId) || /^0+$/.test(detailId)))) {
    throw new Error("An exact Catalogue Work or Detail identity is required.");
  }
  return Object.freeze(detailId ? { kind: "catalogue-work-detail", id: workId + "-" + detailId, workId: workId }
    : { kind: "catalogue-work", id: workId });
}

export function catalogueMediaTargetWorkId(target) {
  var workId = target && (target.kind === "catalogue-work" ? target.id : target.workId);
  var detailId = target && target.kind === "catalogue-work-detail" && typeof target.id === "string" ? target.id.slice(6) : "";
  var exact = catalogueMediaTarget(workId, detailId);
  if (exact.kind !== target.kind || exact.id !== target.id) throw new Error("Catalogue media identity is mismatched.");
  return workId;
}

function workRecord(payload, workId) {
  var work = payload && payload.work;
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId) || !work || work.work_id !== workId) {
    throw new Error("Catalogue data does not match the selected Work.");
  }
  if (typeof work.title !== "string" || !work.title.trim()) throw new Error("Catalogue Work title is unavailable.");
  return work;
}

/** Preserve supplied Detail order and identity; never infer another record or primary image. */
export function catalogueWorkDetails(payload, workId) {
  workRecord(payload, workId);
  if (!Array.isArray(payload.sections)) throw new Error("Catalogue Detail sections are unavailable.");
  var seen = new Set();
  return payload.sections.flatMap(function (section) {
    if (!section || !Array.isArray(section.details)) throw new Error("Catalogue Details are unavailable.");
    return section.details.map(function (detail) {
      var target = catalogueMediaTarget(workId, detail && detail.detail_id);
      if (target.kind !== "catalogue-work-detail" || detail.work_id !== workId || detail.detail_uid !== target.id
        || seen.has(target.id) || typeof detail.title !== "string" || !detail.title.trim()) {
        throw new Error("Catalogue Detail identity or title is unavailable or mismatched.");
      }
      seen.add(target.id);
      return detail;
    });
  });
}

/** Build a presentation from the exact current Catalogue consumer record, locally or publicly. */
export function catalogueWorkMediaPresentation(payload, workId, detailId = "") {
  var work = workRecord(payload, workId);
  var target = catalogueMediaTarget(workId, detailId);
  var record = detailId ? catalogueWorkDetails(payload, workId).find(function (item) { return item.detail_id === detailId; }) : work;
  if (!record) throw new Error("Catalogue Detail " + target.id + " is unavailable.");
  if (!Number.isInteger(record.width_px) || record.width_px <= 0
    || !Number.isInteger(record.height_px) || record.height_px <= 0) {
    throw new Error("Catalogue image dimensions are unavailable.");
  }
  var primary = record.media && record.media.primary;
  if (!Array.isArray(primary) || !primary.length || primary.some(function (item) {
    return !item || !Number.isInteger(item.width) || item.width <= 0
      || typeof item.url !== "string" || /\s/.test(item.url) || !docsViewerSafeMediaTarget(item.url);
  })) throw new Error("Catalogue Work media is unavailable or unsafe.");
  var image = primary.reduce(function (largest, item) { return item.width > largest.width ? item : largest; });
  var metadata = detailId ? [{ label: "Work", value: work.title }] : [];
  (detailId ? [] : [["Year", "year_display"], ["Medium", "medium_caption"]]).forEach(function (entry) {
    if (typeof work[entry[1]] === "string" && work[entry[1]].trim()) {
      metadata.push({ label: entry[0], value: work[entry[1]].trim() });
    }
  });
  var dimensions = [work.height_cm, work.width_cm, work.depth_cm];
  function dimension(value) { return typeof value === "number" && Number.isFinite(value) && value > 0; }
  if (!detailId && dimensions.slice(0, 2).every(dimension)) {
    metadata.push({ label: "Dimensions", value: dimensions.filter(dimension).join(" × ") + " cm" });
  }
  metadata.push({ label: "Catalogue number", value: workId });
  if (detailId) metadata.push({ label: "Detail", value: detailId });
  var presentation = {
    schema_version: "docs_media_view_v1",
    target: target,
    label: record.title,
    image: { src: image.url, alt: record.title, width_px: record.width_px, height_px: record.height_px },
    metadata: metadata,
    new_tab_target: image.url
  };
  normalizeDocsViewerMediaPresentation(presentation);
  return presentation;
}

/** Revalidate public consumer JSON on every activation; retain no document-lifetime cache. */
export async function readPublicCatalogueWork(baseUrl, workId, fetchImpl) {
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId)) throw new Error("An exact Catalogue Work ID is required.");
  if (typeof baseUrl !== "string" || !baseUrl.startsWith("/") || baseUrl.startsWith("//")
    || !baseUrl.endsWith("/") || /[?#\\\s]/.test(baseUrl)) {
    throw new Error("Public Catalogue data is not configured.");
  }
  var response = await fetchImpl(baseUrl + workId + ".json", { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Work " + workId + " is unavailable (HTTP " + response.status + ").");
  var payload = await response.json();
  workRecord(payload, workId);
  return payload;
}
