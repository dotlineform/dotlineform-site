import { catalogueMediaTarget, catalogueGalleryTarget } from "../shared/docs-viewer-catalogue-media.js";
import { catalogueImageCandidates, validateCatalogueMediaPolicy } from "../shared/docs-viewer-catalogue-media-policy.js";

/** One activation's live Working inputs and presentations; nothing survives the operation. */
export function createLiveCataloguePresentations(source, payload) {
  var reads = new Map();
  var policyRead;
  var relationshipsRead;
  var entries = new Set(((payload && payload.catalogue && payload.catalogue.references) || [])
    .filter(function (reference) { return reference.presentation === "entry"; })
    .map(function (reference) { return reference.target.id; }));

  function entryFields(work, workId) {
    var lines = [work.year_display];
    if (work.medium !== undefined && work.medium !== null) lines.push(work.medium);
    var dimensions = [work.height_cm, work.width_cm, work.depth_cm].filter(function (value) { return value !== undefined && value !== null; });
    if (dimensions.length) lines.push(dimensions.join(" × ") + " cm");
    lines.push("", "cat. " + workId);
    return { metadata_lines: lines, resources: ["downloads", "links"].flatMap(function (kind) {
      return (work[kind] || []).map(function (resource) {
        return { kind: kind === "downloads" ? "download" : "link", label: resource.label, url: resource.url };
      });
    }) };
  }

  async function resolve(workId) {
    catalogueMediaTarget(workId);
    if (!policyRead) policyRead = source.readCatalogueMediaConfig().then(validateCatalogueMediaPolicy);
    var [payload, policy] = await Promise.all([source.readCatalogueWork(workId), policyRead]);
    var work = payload.work;
    var image = catalogueImageCandidates(catalogueMediaTarget(workId), work, policy);
    var galleries = work.galleries.map(function (gallery) {
      return { target: catalogueGalleryTarget(gallery.gallery_id), label: gallery.title, relation: "direct" };
    });
    var seen = new Set(galleries.map(function (gallery) { return gallery.target.id; }));
    if (Object.prototype.hasOwnProperty.call(work, "series_id")) {
      if (!relationshipsRead) relationshipsRead = source.readCatalogueSeriesGalleries();
      var relationships = await relationshipsRead;
      relationships.series_galleries[work.series_id].forEach(function (gallery) {
        if (seen.has(gallery.gallery_id)) return;
        seen.add(gallery.gallery_id);
        galleries.push({ target: catalogueGalleryTarget(gallery.gallery_id), label: gallery.title, relation: "series" });
      });
    }
    var result = {
      schema_version: "docs_media_view_v2", target: catalogueMediaTarget(workId), label: work.title,
      image: { src: image.candidates[0].src, candidates: image.candidates, alt: work.title,
        width_px: work.width_px, height_px: work.height_px },
      new_tab_target: image.largest, galleries: galleries
    };
    if (entries.has(workId)) result.entry = entryFields(work, workId);
    return result;
  }

  return { live: true, readWork: function (workId) {
    if (!reads.has(workId)) reads.set(workId, resolve(workId));
    return reads.get(workId);
  } };
}
