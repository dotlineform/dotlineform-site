import { docsViewerSafeMediaTarget, normalizeDocsViewerCatalogueGroupTarget } from "./docs-viewer-media-presentation.js";
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
  if (typeof work.title !== "string") throw new Error("Catalogue Work title must be a string.");
  return work;
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
        return { target: catalogueMediaTarget(member.work_id), label: member.title,
          thumbnail: catalogueWorkThumbnail(member.work_id, member.title, thumbnailSettings) };
      }) }
  };
  return presentation;
}

/** Build a presentation from the exact current Catalogue consumer record, locally or publicly. */
export function catalogueWorkMediaPresentation(payload, workId, mediaPolicy, seriesGalleriesIndex) {
  var work = workRecord(payload, workId);
  var target = catalogueMediaTarget(workId);
  var image = catalogueImageCandidates(target, work, mediaPolicy);
  var metadata = [{ label: "Year", value: work.year_display }];
  if (work.medium !== undefined && work.medium !== null) {
    metadata.push({ label: "Medium", value: work.medium });
  }
  var dimensions = [work.height_cm, work.width_cm, work.depth_cm].filter(function (value) {
    return value !== undefined && value !== null;
  });
  if (dimensions.length) {
    metadata.push({ label: "Dimensions", value: dimensions.join(" × ") + " cm" });
  }
  metadata.push({ label: "Catalogue number", value: workId });
  var directGalleries = work.galleries.map(function (gallery) {
    return { target: catalogueGalleryTarget(gallery.gallery_id), label: gallery.title, relation: "direct" };
  });
  var seenGalleryIds = new Set(directGalleries.map(function (gallery) { return gallery.target.id; }));
  var seriesGalleries = [];
  if (Object.prototype.hasOwnProperty.call(work, "series_id")) {
    var seriesId = work.series_id;
    var mapping = seriesGalleriesIndex.series_galleries;
    seriesGalleries = mapping[seriesId].flatMap(function (gallery) {
      if (seenGalleryIds.has(gallery.gallery_id)) return [];
      seenGalleryIds.add(gallery.gallery_id);
      return [{ target: catalogueGalleryTarget(gallery.gallery_id), label: gallery.title, relation: "series" }];
    });
  }
  var presentation = {
    schema_version: "docs_media_view_v1",
    target: target,
    label: work.title,
    image: { src: image.candidates[0].src, candidates: image.candidates,
      alt: work.title, width_px: work.width_px, height_px: work.height_px },
    metadata: metadata,
    galleries: directGalleries.concat(seriesGalleries),
    new_tab_target: image.largest
  };
  return presentation;
}

export async function readCatalogueWorkMediaPresentation(provider, workId) {
  var [payload, policy] = await Promise.all([provider.readCatalogueWork(workId), provider.readCatalogueMediaConfig()]);
  var work = payload.work;
  var index;
  if (Object.prototype.hasOwnProperty.call(work, "series_id")) {
    if (typeof provider.readCatalogueSeriesGalleries !== "function") {
      throw new Error("Catalogue Series-Gallery index reader is unavailable.");
    }
    index = await provider.readCatalogueSeriesGalleries();
  }
  return catalogueWorkMediaPresentation(payload, workId, policy, index);
}

/** Revalidate public consumer JSON on every activation; retain no document-lifetime cache. */
export async function readPublicCatalogueWork(baseUrl, workId, fetchImpl) {
  if (typeof workId !== "string" || !/^\d{5}$/.test(workId)) throw new Error("An exact Catalogue Work ID is required.");
  validatePublicRecordBase(baseUrl);
  var response = await fetchImpl(baseUrl + workId + ".json", { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Work " + workId + " is unavailable (HTTP " + response.status + ").");
  return response.json();
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

/** Read the selected public index with normal browser revalidation. */
export async function readPublicCatalogueSeriesGalleries(url, fetchImpl) {
  if (typeof url !== "string" || !url.startsWith("/") || url.startsWith("//")
    || !url.endsWith("/series-galleries-index.json") || /[?#\\\s]/.test(url)) {
    throw new Error("Public Catalogue Series-Gallery index is not configured.");
  }
  var response = await fetchImpl(url, { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue Series-Gallery index is unavailable (HTTP " + response.status + ").");
  return response.json();
}
