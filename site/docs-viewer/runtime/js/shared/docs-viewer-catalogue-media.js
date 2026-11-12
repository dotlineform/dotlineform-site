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

export function catalogueAssetUrl(base, identity) {
  if (!docsViewerSafeMediaTarget(base) || !base.endsWith("/") || /[?#\s,]/.test(base)
    || typeof identity !== "string" || !identity || identity === "." || identity === ".." || /[/\\]/.test(identity)) {
    throw new Error("Catalogue asset target is unavailable or unsafe.");
  }
  return base + encodeURIComponent(identity);
}

function versionedImageUrl(base, identity, version) {
  return catalogueAssetUrl(base, identity) + "?v=" + encodeURIComponent(version);
}

export function catalogueDocumentImage(image, base) {
  var candidates = image.candidates.map(function (candidate) {
    return { src: versionedImageUrl(base, candidate.identity, image.version), width_px: candidate.width_px };
  });
  return {
    src: versionedImageUrl(base, image.default, image.version),
    candidates: candidates, srcset: candidates.map(function (candidate) {
      return candidate.src + " " + candidate.width_px + "w";
    }).join(", "),
    alt: image.alt, width_px: image.width_px, height_px: image.height_px
  };
}

export function catalogueDocumentWorkPresentation(payload, workId, primaryBase) {
  var work = payload && payload.doc_id === workId && payload.catalogue && payload.catalogue.work;
  if (!work) throw new Error("Catalogue Work " + workId + " is unavailable.");
  return {
    schema_version: "docs_media_view_v2", target: catalogueMediaTarget(workId),
    label: work.image.alt, image: catalogueDocumentImage(work.image, primaryBase),
    new_tab_target: versionedImageUrl(primaryBase, work.full_image, work.image.version),
    galleries: work.galleries.map(function (gallery) {
      return { target: catalogueGalleryTarget(gallery.id), label: gallery.label, relation: gallery.relation };
    })
  };
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
export function catalogueGalleryMediaPresentation(payload, galleryId, mediaPolicy, thumbnailBaseUrl, contextDocs = []) {
  var gallery = galleryRecord(payload, galleryId);
  var presentation = groupMediaPresentation(payload, catalogueGalleryTarget(galleryId), gallery.title, [], mediaPolicy, thumbnailBaseUrl);
  var memberIds = new Set(presentation.gallery.members.map(function (member) { return member.target.id; }));
  presentation.gallery.context_documents = contextDocs.filter(function (doc) {
    var targets = doc.catalogue_targets;
    return targets && (targets.gallery_ids.includes(galleryId)
      || targets.work_ids.some(function (id) { return memberIds.has(id); }));
  }).map(function (doc) { return Object.freeze({ doc_id: doc.doc_id, title: doc.title }); });
  return presentation;
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
