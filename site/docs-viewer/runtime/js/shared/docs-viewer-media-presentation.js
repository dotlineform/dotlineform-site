function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function positiveInteger(value) {
  var number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : 0;
}

/** Return a supported browser media target without resolving or rewriting it. */
export function docsViewerSafeMediaTarget(value) {
  var target = cleanString(value);
  var unsupportedCharacter = Array.from(target).some(function (character) {
    var code = character.charCodeAt(0);
    return character === "\\" || code <= 31 || code === 127;
  });
  if (!target || unsupportedCharacter) return "";
  if (target.startsWith("/") && !target.startsWith("//")) return target;
  try {
    var parsed = new URL(target);
    if (parsed.protocol !== "https:" || !parsed.hostname || parsed.username || parsed.password) {
      return "";
    }
    return target;
  } catch (_error) {
    return "";
  }
}

function normalizedTextField(value, fieldName) {
  var normalized = cleanString(value);
  if (!normalized) throw new Error("Media View requires " + fieldName + ".");
  return normalized;
}

function normalizedMetadata(value) {
  if (!Array.isArray(value)) throw new Error("Media View requires ordered metadata.");
  return Object.freeze(value.map(function (entry) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      throw new Error("Media View metadata entries must be objects.");
    }
    return Object.freeze({
      label: normalizedTextField(entry.label, "a metadata label"),
      value: normalizedTextField(entry.value, "a metadata value")
    });
  }));
}

/** Validate and freeze one complete browser-ready Media View presentation. */
function normalizeWorkPresentation(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Media View requires an object payload.");
  }
  if (cleanString(value.schema_version) !== "docs_media_view_v1") {
    throw new Error("Media View requires schema docs_media_view_v1.");
  }

  var targetSource = value.target;
  if (!targetSource || typeof targetSource !== "object" || Array.isArray(targetSource)) {
    throw new Error("Media View requires an exact target.");
  }
  var targetKind = cleanString(targetSource.kind);
  var targetId = cleanString(targetSource.id);
  if (targetKind !== "catalogue-work" || !/^\d{5}$/.test(targetId)) {
    throw new Error("Media View requires an exact Catalogue Work target.");
  }

  var imageSource = value.image;
  if (!imageSource || typeof imageSource !== "object" || Array.isArray(imageSource)) {
    throw new Error("Media View requires image metadata.");
  }
  var imageSrc = docsViewerSafeMediaTarget(imageSource.src);
  var imageWidth = positiveInteger(imageSource.width_px);
  var imageHeight = positiveInteger(imageSource.height_px);
  if (!imageSrc) throw new Error("Media View image target is unsupported.");
  if (!imageWidth || !imageHeight) throw new Error("Media View image dimensions must be positive integers.");
  var candidates = imageSource.candidates;
  var srcset = "";
  if (candidates !== undefined) {
    var seenWidths = new Set();
    if (!Array.isArray(candidates) || !candidates.length) throw new Error("Media View image candidates are unavailable.");
    srcset = candidates.map(function (candidate) {
      var src = candidate && candidate.src;
      var width = candidate && candidate.width_px;
      if (typeof src !== "string" || /[\s,]/.test(src) || !docsViewerSafeMediaTarget(src)
        || !Number.isInteger(width) || width <= 0 || width > imageWidth || seenWidths.has(width)) {
        throw new Error("Media View image candidate is unsafe or has invalid dimensions.");
      }
      seenWidths.add(width);
      return src + " " + width + "w";
    }).join(", ");
  }

  var metadata = normalizedMetadata(value.metadata);
  var galleryIds = new Set();
  var galleries = value.galleries === undefined ? [] : value.galleries;
  if (!Array.isArray(galleries)) throw new Error("Media View requires an array of Gallery links.");
  galleries = galleries.map(function (entry) {
    var target = normalizeDocsViewerCatalogueGroupTarget(entry && entry.target);
    if (target.kind !== "catalogue-gallery" || galleryIds.has(target.id)) throw new Error("Media View Gallery links are invalid or duplicated.");
    galleryIds.add(target.id);
    return Object.freeze({ target: target, label: normalizedTextField(entry.label, "a Gallery label") });
  });

  var newTabTarget = docsViewerSafeMediaTarget(value.new_tab_target);
  if (!newTabTarget) throw new Error("Media View new-tab target is unsupported.");

  return Object.freeze({
    schemaVersion: "docs_media_view_v1",
    target: Object.freeze({ kind: targetKind, id: targetId }),
    label: normalizedTextField(value.label, "a label"),
    image: Object.freeze({
      src: imageSrc,
      srcset: srcset,
      alt: normalizedTextField(imageSource.alt, "image alternative text"),
      widthPx: imageWidth,
      heightPx: imageHeight
    }),
    metadata: metadata,
    galleries: Object.freeze(galleries),
    newTabTarget: newTabTarget
  });
}

/** Keep Series and Gallery identity separate even when their numeric IDs match. */
export function normalizeDocsViewerCatalogueGroupTarget(value) {
  var pattern = value && (value.kind === "catalogue-series" ? /^[0-9]{3}$/
    : value.kind === "catalogue-gallery" ? /^(?:[0-9]{3}|[1-9][0-9]{3,})$/ : null);
  if (!pattern || typeof value.id !== "string" || value.id !== value.id.trim() || !pattern.test(value.id)) {
    throw new Error("Media View requires an exact Catalogue Series or Gallery target.");
  }
  return Object.freeze({ kind: value.kind, id: value.id });
}

function normalizeThumbnail(value) {
  var src = value && docsViewerSafeMediaTarget(value.src);
  var width = value && positiveInteger(value.width_px);
  var height = value && positiveInteger(value.height_px);
  if (!src || !width || !height) throw new Error("Media View requires a safe thumbnail and dimensions.");
  return Object.freeze({
    src: src,
    alt: normalizedTextField(value.alt, "thumbnail alternative text"),
    widthPx: width,
    heightPx: height
  });
}

/** Resolve a target only inside the supplied presentation, without identity inference. */
export function docsViewerMediaPresentationForTarget(supplied, target) {
  if (!target) return null;
  function matches(candidate) {
    return candidate.kind === target.kind && candidate.id === target.id;
  }
  if (!supplied.gallery) return matches(supplied.target) ? supplied : null;
  if (matches(supplied.gallery.target)) return supplied.gallery;
  var member = supplied.gallery.members.find(function (entry) {
    return matches(entry.target);
  });
  return member ? member.work : null;
}

/**
 * Freeze a Work or an ordered gallery. Gallery members explicitly supply either a complete
 * Work presentation (existing supplied callers) or an exact reference for on-demand loading.
 */
export function normalizeDocsViewerMediaPresentation(value) {
  if (!value || value.schema_version !== "docs_media_gallery_v1") {
    return normalizeWorkPresentation(value);
  }
  var source = value.gallery;
  if (!source || !Array.isArray(source.members)) {
    throw new Error("Media View requires a gallery with supplied members.");
  }
  var ids = new Set();
  var members = source.members.map(function (entry) {
    if (!entry || typeof entry !== "object") throw new Error("Media View requires a gallery member.");
    var work = Object.prototype.hasOwnProperty.call(entry, "work") ? normalizeWorkPresentation(entry.work) : null;
    if (work && (entry.target || entry.label)) throw new Error("Media View member must supply one Work identity.");
    var target = work ? work.target : entry.target;
    if (!target || target.kind !== "catalogue-work" || typeof target.id !== "string" || !/^\d{5}$/.test(target.id)) {
      throw new Error("Media View gallery members require an exact Catalogue Work target.");
    }
    if (ids.has(target.id)) throw new Error("Media View gallery has a duplicate Work target.");
    ids.add(target.id);
    return Object.freeze({ target: Object.freeze({ kind: target.kind, id: target.id }),
      label: work ? work.label : normalizedTextField(entry.label, "a Work label"),
      work: work, thumbnail: normalizeThumbnail(entry.thumbnail) });
  });
  var gallery = Object.freeze({
    target: normalizeDocsViewerCatalogueGroupTarget(source.target),
    label: normalizedTextField(source.label, "a gallery label"),
    metadata: normalizedMetadata(source.metadata === undefined ? [] : source.metadata),
    members: Object.freeze(members),
    newTabTarget: ""
  });
  var supplied = { gallery: gallery };
  var entryPresentation = docsViewerMediaPresentationForTarget(supplied, value.target);
  if (!entryPresentation) throw new Error("Media View entry target is not in the supplied gallery.");
  return Object.freeze({
    schemaVersion: "docs_media_gallery_v1",
    target: entryPresentation.target,
    label: entryPresentation.label,
    newTabTarget: entryPresentation.newTabTarget,
    gallery: gallery
  });
}
