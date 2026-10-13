function cleanString(value) {
  return String(value == null ? "" : value).trim();
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

function suppliedTextField(value, fieldName) {
  if (typeof value !== "string") throw new Error("Media View " + fieldName + " must be a string.");
  return value;
}

function normalizedMetadata(value) {
  if (!Array.isArray(value)) throw new Error("Media View requires ordered metadata.");
  return Object.freeze(value.map(function (entry) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      throw new Error("Media View metadata entries must be objects.");
    }
    return Object.freeze({
      label: normalizedTextField(entry.label, "a metadata label"),
      value: suppliedTextField(entry.value, "metadata value")
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
  var imageWidth = imageSource.width_px;
  var imageHeight = imageSource.height_px;
  if (!imageSrc) throw new Error("Media View image target is unsupported.");
  var candidates = imageSource.candidates;
  var srcset = "";
  if (candidates !== undefined) {
    if (!Array.isArray(candidates) || !candidates.length) throw new Error("Media View image candidates are unavailable.");
    srcset = candidates.map(function (candidate) {
      var src = candidate && candidate.src;
      var width = candidate && candidate.width_px;
      if (typeof src !== "string" || /[\s,]/.test(src) || !docsViewerSafeMediaTarget(src)) {
        throw new Error("Media View image candidate is unsafe.");
      }
      return src + " " + width + "w";
    }).join(", ");
  }

  var metadata = normalizedMetadata(value.metadata);
  if (value.series !== undefined) throw new Error("Media View Series links are unsupported.");
  var galleries = value.galleries;
  if (!Array.isArray(galleries)) throw new Error("Media View requires an array of Gallery links.");
  galleries = galleries.map(function (entry) {
    var target = normalizeDocsViewerCatalogueGroupTarget(entry && entry.target);
    return Object.freeze({ target: target, label: suppliedTextField(entry.label, "Gallery title"), relation: entry.relation });
  });

  var newTabTarget = docsViewerSafeMediaTarget(value.new_tab_target);
  if (!newTabTarget) throw new Error("Media View new-tab target is unsupported.");

  return Object.freeze({
    schemaVersion: "docs_media_view_v1",
    target: Object.freeze({ kind: targetKind, id: targetId }),
    label: suppliedTextField(value.label, "Work title"),
    image: Object.freeze({
      src: imageSrc,
      srcset: srcset,
      alt: suppliedTextField(imageSource.alt, "Work title"),
      widthPx: imageWidth,
      heightPx: imageHeight
    }),
    metadata: metadata,
    galleries: Object.freeze(galleries),
    newTabTarget: newTabTarget
  });
}

/** Gallery identity uses its exact canonical spelling. */
export function normalizeDocsViewerCatalogueGroupTarget(value) {
  var pattern = value && value.kind === "catalogue-gallery" ? /^(?:[0-9]{3}|[1-9][0-9]{3,})$/ : null;
  if (!pattern || typeof value.id !== "string" || value.id !== value.id.trim() || !pattern.test(value.id)) {
    throw new Error("Media View requires an exact Catalogue Gallery target.");
  }
  return Object.freeze({ kind: value.kind, id: value.id });
}

function normalizeThumbnail(value) {
  var src = value && docsViewerSafeMediaTarget(value.src);
  if (!src) throw new Error("Media View requires a safe thumbnail.");
  return Object.freeze({
    src: src,
    alt: suppliedTextField(value.alt, "Work title"),
    widthPx: value.width_px,
    heightPx: value.height_px
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
 * Work titles and title-derived labels/alt text retain their supplied strings; the UI owns completion.
 * Intrinsic image pixels and derived candidate widths are consumed without validating Save's measurements.
 */
export function normalizeDocsViewerMediaPresentation(value) {
  if (!value || value.schema_version !== "docs_media_gallery_v1") {
    return normalizeWorkPresentation(value);
  }
  var source = value.gallery;
  if (!source || !Array.isArray(source.members)) {
    throw new Error("Media View requires a gallery with supplied members.");
  }
  var members = source.members.map(function (entry) {
    if (!entry || typeof entry !== "object") throw new Error("Media View requires a gallery member.");
    var work = Object.prototype.hasOwnProperty.call(entry, "work") ? normalizeWorkPresentation(entry.work) : null;
    if (work && (entry.target || entry.label)) throw new Error("Media View member must supply one Work identity.");
    var target = work ? work.target : entry.target;
    if (!target || target.kind !== "catalogue-work" || typeof target.id !== "string" || !/^\d{5}$/.test(target.id)) {
      throw new Error("Media View gallery members require an exact Catalogue Work target.");
    }
    return Object.freeze({ target: Object.freeze({ kind: target.kind, id: target.id }),
      label: work ? work.label : suppliedTextField(entry.label, "Work title"),
      work: work, thumbnail: normalizeThumbnail(entry.thumbnail) });
  });
  var gallery = Object.freeze({
    target: normalizeDocsViewerCatalogueGroupTarget(source.target),
    label: suppliedTextField(source.label, "Gallery title"),
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
