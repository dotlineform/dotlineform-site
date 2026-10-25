import { docsViewerSafeMediaTarget, normalizeDocsViewerCatalogueGroupTarget } from "./docs-viewer-media-presentation.js";
import { catalogueThumbnailSettings } from "./docs-viewer-catalogue-media-policy.js";

const WORK_TITLE_ORDER = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

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

export function catalogueGalleryTarget(galleryId) {
  return normalizeDocsViewerCatalogueGroupTarget({ kind: "catalogue-gallery", id: galleryId });
}

function galleryRecord(payload, galleryId) {
  catalogueGalleryTarget(galleryId);
  var gallery = payload && payload.gallery;
  if (!gallery || gallery.gallery_id !== galleryId) {
    throw new Error("Catalogue data does not match the selected Gallery.");
  }
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

/** Project Gallery members in natural title order from one generated membership record. */
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
        return { target: catalogueMediaTarget(member.work_id), label: member.title,
          thumbnail: catalogueWorkThumbnail(member.work_id, member.title, thumbnailSettings) };
      }).sort(function (left, right) {
        return WORK_TITLE_ORDER.compare(left.label, right.label)
          || WORK_TITLE_ORDER.compare(left.target.id, right.target.id);
      }) }
  };
  return presentation;
}

function validatePublicRecordBase(baseUrl) {
  if (typeof baseUrl !== "string" || !baseUrl.startsWith("/") || baseUrl.startsWith("//")
    || !baseUrl.endsWith("/") || /[?#\\\s]/.test(baseUrl)) {
    throw new Error("Public Catalogue data is not configured.");
  }
}

/** Public Gallery reads remain confined to the configured static record base. */
export async function readPublicCatalogueGallery(baseUrl, galleryId, fetchImpl) {
  catalogueGalleryTarget(galleryId);
  validatePublicRecordBase(baseUrl);
  var response = await fetchImpl(baseUrl + galleryId + ".json", { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Gallery " + galleryId + " is unavailable (HTTP " + response.status + ").");
  return response.json();
}
