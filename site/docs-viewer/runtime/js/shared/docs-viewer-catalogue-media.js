import { docsViewerSafeMediaTarget, normalizeDocsViewerMediaPresentation, normalizeDocsViewerCatalogueGroupTarget } from "./docs-viewer-media-presentation.js";
import { catalogueImageCandidates, catalogueThumbnailSettings } from "./docs-viewer-catalogue-media-policy.js";

/** Work image targets use only the exact five-digit Catalogue Work identity. */
export function catalogueMediaTarget(workId) {
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId)) {
    throw new Error("An exact Catalogue Work identity is required.");
  }
  return Object.freeze({ kind: "catalogue-work", id: workId });
}

export function catalogueMediaTargetWorkId(target) {
  var exact = catalogueMediaTarget(target && target.id);
  if (exact.kind !== target.kind) throw new Error("Catalogue media identity is mismatched.");
  return exact.id;
}

function workRecord(payload, workId) {
  var work = payload && payload.work;
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId) || !work || work.work_id !== workId) {
    throw new Error("Catalogue data does not match the selected Work.");
  }
  if (typeof work.title !== "string" || !work.title.trim()) throw new Error("Catalogue Work title is unavailable.");
  return work;
}

/** Series identity never depends on a document, thumbnail or selected member. */
export function catalogueSeriesTarget(seriesId) {
  return normalizeDocsViewerCatalogueGroupTarget({ kind: "catalogue-series", id: seriesId });
}

export function catalogueGalleryTarget(galleryId) {
  return normalizeDocsViewerCatalogueGroupTarget({ kind: "catalogue-gallery", id: galleryId });
}

function seriesRecord(payload, seriesId) {
  catalogueSeriesTarget(seriesId);
  var series = payload && payload.series;
  if (!series || series.series_id !== seriesId) throw new Error("Catalogue data does not match the selected Series.");
  if (typeof series.title !== "string" || !series.title.trim()) throw new Error("Catalogue Series title is unavailable.");
  if (!Array.isArray(payload.member_works)) throw new Error("Catalogue Series membership is unavailable.");
  return series;
}

function galleryRecord(payload, galleryId) {
  catalogueGalleryTarget(galleryId);
  var gallery = payload && payload.gallery;
  var header = payload && payload.header;
  if (!gallery || gallery.gallery_id !== galleryId || !header || header.gallery_id !== galleryId
    || header.schema !== "gallery_record_v1") throw new Error("Catalogue data does not match the selected Gallery.");
  if (typeof gallery.title !== "string" || !gallery.title.trim()) throw new Error("Catalogue Gallery title is unavailable.");
  if (!Array.isArray(payload.member_works) || header.count !== payload.member_works.length) {
    throw new Error("Catalogue Gallery membership is unavailable.");
  }
  var previousId = "";
  payload.member_works.forEach(function (member) {
    var target = catalogueMediaTarget(member && member.work_id);
    if (target.id <= previousId) throw new Error("Catalogue Gallery Works must be distinct and in ascending ID order.");
    previousId = target.id;
  });
  return gallery;
}

/** Resolve the established generated Work thumbnail convention from explicit route policy. */
export function catalogueWorkThumbnail(workId, title, settings) {
  catalogueMediaTarget(workId);
  var base = settings && settings.base_url;
  if (typeof base !== "string" || !docsViewerSafeMediaTarget(base) || !base.endsWith("/")
    || /[?#\s]/.test(base) || !Number.isInteger(settings.size) || settings.size <= 0
    || typeof settings.suffix !== "string" || !/^[a-z0-9-]+$/.test(settings.suffix)
    || typeof settings.format !== "string" || !/^(?:webp|avif|png|jpg)$/.test(settings.format)) {
    throw new Error("Catalogue thumbnail configuration is unavailable or unsafe.");
  }
  return { src: base + workId + "-" + settings.suffix + "-" + settings.size + "." + settings.format,
    alt: title, width_px: settings.size, height_px: settings.size };
}

/** Project ordered references only; complete Work records are obtained when selected. */
export function catalogueSeriesMediaPresentation(payload, seriesId, mediaPolicy, thumbnailBaseUrl) {
  var series = seriesRecord(payload, seriesId);
  return groupMediaPresentation(payload, catalogueSeriesTarget(seriesId), series.title,
    typeof series.year_display === "string" && series.year_display.trim()
      ? [{ label: "Year", value: series.year_display.trim() }] : [], mediaPolicy, thumbnailBaseUrl);
}

/** Gallery selection reads one generated membership record, with no Series inference. */
export function catalogueGalleryMediaPresentation(payload, galleryId, mediaPolicy, thumbnailBaseUrl) {
  var gallery = galleryRecord(payload, galleryId);
  return groupMediaPresentation(payload, catalogueGalleryTarget(galleryId), gallery.title, [], mediaPolicy, thumbnailBaseUrl);
}

function groupMediaPresentation(payload, target, title, metadata, mediaPolicy, thumbnailBaseUrl) {
  var thumbnailSettings = catalogueThumbnailSettings(mediaPolicy, thumbnailBaseUrl);
  var presentation = {
    schema_version: "docs_media_gallery_v1", target: target,
    gallery: { target: target, label: title, metadata: metadata,
      members: payload.member_works.map(function (member) {
        if (!member || typeof member.title !== "string" || !member.title.trim()) {
          throw new Error("Catalogue member Work title is unavailable.");
        }
        return { target: catalogueMediaTarget(member.work_id), label: member.title,
          thumbnail: catalogueWorkThumbnail(member.work_id, member.title, thumbnailSettings) };
      }) }
  };
  normalizeDocsViewerMediaPresentation(presentation);
  return presentation;
}

/** Build a presentation from the exact current Catalogue consumer record, locally or publicly. */
export function catalogueWorkMediaPresentation(payload, workId, mediaPolicy) {
  var work = workRecord(payload, workId);
  var target = catalogueMediaTarget(workId);
  if (!Number.isInteger(work.width_px) || work.width_px <= 0
    || !Number.isInteger(work.height_px) || work.height_px <= 0) {
    throw new Error("Catalogue image dimensions are unavailable.");
  }
  var image = catalogueImageCandidates(target, work, mediaPolicy);
  var metadata = [];
  [["Year", "year_display"], ["Medium", "medium_caption"]].forEach(function (entry) {
    if (typeof work[entry[1]] === "string" && work[entry[1]].trim()) {
      metadata.push({ label: entry[0], value: work[entry[1]].trim() });
    }
  });
  var dimensions = [work.height_cm, work.width_cm, work.depth_cm];
  function dimension(value) { return typeof value === "number" && Number.isFinite(value) && value > 0; }
  if (dimensions.slice(0, 2).every(dimension)) {
    metadata.push({ label: "Dimensions", value: dimensions.filter(dimension).join(" × ") + " cm" });
  }
  metadata.push({ label: "Catalogue number", value: workId });
  if (!Array.isArray(work.galleries)) throw new Error("Catalogue Work Gallery memberships are unavailable.");
  var presentation = {
    schema_version: "docs_media_view_v1",
    target: target,
    label: work.title,
    image: { src: image.candidates[0].src, candidates: image.candidates,
      alt: work.title, width_px: work.width_px, height_px: work.height_px },
    metadata: metadata,
    galleries: work.galleries.map(function (gallery) {
      if (!gallery || typeof gallery.title !== "string" || !gallery.title.trim()) throw new Error("Catalogue Gallery title is unavailable.");
      return { target: catalogueGalleryTarget(gallery && gallery.gallery_id), label: gallery.title };
    }),
    new_tab_target: image.largest
  };
  normalizeDocsViewerMediaPresentation(presentation);
  return presentation;
}

/** Revalidate public consumer JSON on every activation; retain no document-lifetime cache. */
export async function readPublicCatalogueWork(baseUrl, workId, fetchImpl) {
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId)) throw new Error("An exact Catalogue Work ID is required.");
  validatePublicRecordBase(baseUrl);
  var response = await fetchImpl(baseUrl + workId + ".json", { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Work " + workId + " is unavailable (HTTP " + response.status + ").");
  var payload = await response.json();
  workRecord(payload, workId);
  return payload;
}

function validatePublicRecordBase(baseUrl) {
  if (typeof baseUrl !== "string" || !baseUrl.startsWith("/") || baseUrl.startsWith("//")
    || !baseUrl.endsWith("/") || /[?#\\\s]/.test(baseUrl)) {
    throw new Error("Public Catalogue data is not configured.");
  }
}

/** Read the deployed Series record only, using the same freshness policy as Work reads. */
export async function readPublicCatalogueSeries(baseUrl, seriesId, fetchImpl) {
  catalogueSeriesTarget(seriesId);
  validatePublicRecordBase(baseUrl);
  var response = await fetchImpl(baseUrl + seriesId + ".json", { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Series " + seriesId + " is unavailable (HTTP " + response.status + ").");
  var payload = await response.json();
  seriesRecord(payload, seriesId);
  return payload;
}

/** Public Gallery reads remain confined to the configured static record base. */
export async function readPublicCatalogueGallery(baseUrl, galleryId, fetchImpl) {
  catalogueGalleryTarget(galleryId);
  validatePublicRecordBase(baseUrl);
  var response = await fetchImpl(baseUrl + galleryId + ".json", { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Gallery " + galleryId + " is unavailable (HTTP " + response.status + ").");
  var payload = await response.json();
  galleryRecord(payload, galleryId);
  return payload;
}
