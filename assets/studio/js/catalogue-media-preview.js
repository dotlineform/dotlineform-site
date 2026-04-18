function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function parseSizes(value, fallback) {
  try {
    const parsed = JSON.parse(String(value || "[]"));
    if (!Array.isArray(parsed)) return fallback.slice();
    const items = parsed
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item > 0)
      .map((item) => Math.floor(item));
    return items.length ? items : fallback.slice();
  } catch (_error) {
    return fallback.slice();
  }
}

function joinAssetPath(base, stem, suffix, size, format) {
  const root = normalizeText(base);
  if (!root) return "";
  return `${root}${stem}-${suffix}-${size}.${format}`;
}

function buildSrcset(urlBuilder, sizes) {
  return sizes.map((size) => `${urlBuilder(size)} ${size}w`).join(", ");
}

export function loadCatalogueMediaConfig(root) {
  const dataset = root && root.dataset ? root.dataset : {};
  const thumbSizes = parseSizes(dataset.thumbSizes, [96, 192]);
  return {
    worksPrimaryBase: normalizeText(dataset.worksPrimaryBase),
    worksThumbBase: normalizeText(dataset.thumbWorksBase),
    workDetailsThumbBase: normalizeText(dataset.thumbWorkDetailsBase),
    primaryDisplayWidth: Number(dataset.primaryDisplayWidth || 800) || 800,
    primaryFullWidth: Number(dataset.primaryFullWidth || dataset.primaryDisplayWidth || 1600) || 1600,
    primarySuffix: normalizeText(dataset.primarySuffix) || "primary",
    thumbSuffix: normalizeText(dataset.thumbSuffix) || "thumb",
    assetFormat: normalizeText(dataset.assetFormat) || "webp",
    thumbSizes
  };
}

export function buildWorkPrimaryPreview(config, workId) {
  const stem = normalizeText(workId);
  const width = Number(config && config.primaryDisplayWidth) || 800;
  const fullWidth = Number(config && config.primaryFullWidth) || width;
  const suffix = normalizeText(config && config.primarySuffix) || "primary";
  const format = normalizeText(config && config.assetFormat) || "webp";
  const src = joinAssetPath(config && config.worksPrimaryBase, stem, suffix, width, format);
  const fullSrc = joinAssetPath(config && config.worksPrimaryBase, stem, suffix, fullWidth, format);
  return {
    src,
    fullSrc,
    width,
    height: width,
    srcset: src ? `${src} ${width}w` : ""
  };
}

export function buildWorkThumbPreview(config, workId) {
  const stem = normalizeText(workId);
  const sizes = Array.isArray(config && config.thumbSizes) && config.thumbSizes.length ? config.thumbSizes : [96, 192];
  const format = normalizeText(config && config.assetFormat) || "webp";
  const suffix = normalizeText(config && config.thumbSuffix) || "thumb";
  const primarySize = sizes[0];
  return {
    src: joinAssetPath(config && config.worksThumbBase, stem, suffix, primarySize, format),
    srcset: buildSrcset((size) => joinAssetPath(config && config.worksThumbBase, stem, suffix, size, format), sizes),
    width: primarySize,
    height: primarySize
  };
}

export function buildDetailThumbPreview(config, detailUid) {
  const stem = normalizeText(detailUid);
  const sizes = Array.isArray(config && config.thumbSizes) && config.thumbSizes.length ? config.thumbSizes : [96, 192];
  const format = normalizeText(config && config.assetFormat) || "webp";
  const suffix = normalizeText(config && config.thumbSuffix) || "thumb";
  const primarySize = sizes[0];
  return {
    src: joinAssetPath(config && config.workDetailsThumbBase, stem, suffix, primarySize, format),
    srcset: buildSrcset((size) => joinAssetPath(config && config.workDetailsThumbBase, stem, suffix, size, format), sizes),
    width: primarySize,
    height: primarySize
  };
}

export function bindPreviewImages(container) {
  if (!container || !container.querySelectorAll) return;
  const images = Array.from(container.querySelectorAll("[data-preview-image]"));
  images.forEach((image) => {
    if (image.dataset.previewBound === "true") return;
    image.dataset.previewBound = "true";
    const frame = image.closest("[data-preview-state]");
    const setLoaded = () => {
      if (frame) frame.dataset.previewState = "ready";
    };
    const setFallback = () => {
      if (frame) frame.dataset.previewState = frame.dataset.previewFallback || "missing-generated";
    };
    image.addEventListener("load", setLoaded, { once: true });
    image.addEventListener("error", setFallback, { once: true });
    if (image.complete) {
      if (image.naturalWidth > 0) setLoaded();
      else setFallback();
    }
  });
}
