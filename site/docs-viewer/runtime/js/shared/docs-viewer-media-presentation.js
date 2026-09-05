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

  if (!Array.isArray(value.metadata)) {
    throw new Error("Media View requires ordered metadata.");
  }
  var metadata = value.metadata.map(function (entry) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      throw new Error("Media View metadata entries must be objects.");
    }
    return Object.freeze({
      label: normalizedTextField(entry.label, "a metadata label"),
      value: normalizedTextField(entry.value, "a metadata value")
    });
  });

  var newTabTarget = docsViewerSafeMediaTarget(value.new_tab_target);
  if (!newTabTarget) throw new Error("Media View new-tab target is unsupported.");

  return Object.freeze({
    schemaVersion: "docs_media_view_v1",
    target: Object.freeze({ kind: targetKind, id: targetId }),
    label: normalizedTextField(value.label, "a label"),
    image: Object.freeze({
      src: imageSrc,
      alt: normalizedTextField(imageSource.alt, "image alternative text"),
      widthPx: imageWidth,
      heightPx: imageHeight
    }),
    metadata: Object.freeze(metadata),
    newTabTarget: newTabTarget
  });
}

function normalizedSeriesTarget(value) {
  if (!value || value.kind !== "catalogue-series" || typeof value.id !== "string" || !/^\d{3}$/.test(value.id)) {
    throw new Error("Media View requires an exact Catalogue Series target.");
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
    return matches(entry.work.target);
  });
  return member ? member.work : null;
}

/**
 * Validate either a single Work or an embedded gallery proof with an explicit entry target.
 * Both remain immutable; the gallery's member order and complete Work records own navigation.
 * This fixture contract does not prescribe production loading or token syntax.
 */
export function normalizeDocsViewerMediaPresentation(value) {
  if (!value || value.schema_version !== "docs_media_gallery_v1") {
    return normalizeWorkPresentation(value);
  }
  var source = value.gallery;
  if (!source || !Array.isArray(source.members) || !source.members.length) {
    throw new Error("Media View requires a gallery with supplied members.");
  }
  var ids = new Set();
  var members = source.members.map(function (entry) {
    var work = normalizeWorkPresentation(entry && entry.work);
    if (ids.has(work.target.id)) throw new Error("Media View gallery has a duplicate Work target.");
    ids.add(work.target.id);
    return Object.freeze({ work: work, thumbnail: normalizeThumbnail(entry.thumbnail) });
  });
  var gallery = Object.freeze({
    target: normalizedSeriesTarget(source.target),
    label: normalizedTextField(source.label, "a gallery label"),
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
