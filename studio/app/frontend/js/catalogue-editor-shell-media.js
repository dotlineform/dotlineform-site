function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function readObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function readArray(value, fallback) {
  return Array.isArray(value) ? value : fallback;
}

function joinBasePath(base, path) {
  return `${normalizeText(base)}${normalizeText(path)}/`;
}

export function readCatalogueEditorMediaAttrs(config) {
  const runtime = readObject(readObject(config && config.app).runtime);
  const media = readObject(runtime.media);
  const mediaConfig = readObject(media.media);
  const thumbsConfig = readObject(media.thumbs);
  const pipeline = readObject(runtime.pipeline);
  const variants = readObject(pipeline.variants);
  const primary = readObject(variants.primary);
  const compatibility = readObject(variants.compatibility);
  const thumb = readObject(variants.thumb);
  const encoding = readObject(pipeline.encoding);
  const renderWidths = readArray(compatibility.render_widths, readArray(primary.widths, [800, 1200, 1600]));
  const thumbSizes = readArray(thumb.sizes, [96, 192]);
  const displayWidth = renderWidths.length ? renderWidths[0] : 800;
  const fullWidth = primary.preferred_width || (renderWidths.length ? renderWidths[renderWidths.length - 1] : 1600);

  return {
    worksPrimaryBase: joinBasePath(mediaConfig.base, mediaConfig.works_images || "/works/img"),
    stagedWorksPrimaryBase: "/studio/media/catalogue/works/srcset_images/primary/",
    thumbWorksBase: joinBasePath(thumbsConfig.base, thumbsConfig.works || "/assets/works/img"),
    thumbWorkDetailsBase: joinBasePath(thumbsConfig.base, thumbsConfig.work_details || "/assets/work_details/img"),
    primaryDisplayWidth: displayWidth,
    primaryFullWidth: fullWidth,
    primarySuffix: normalizeText(primary.suffix) || "primary",
    thumbSizes,
    thumbSuffix: normalizeText(thumb.suffix) || "thumb",
    assetFormat: normalizeText(encoding.format) || "webp"
  };
}

export function renderMediaAttrs(attrs, keys) {
  const values = attrs || {};
  const output = [];
  keys.forEach((key) => {
    const value = values[key];
    if (value == null) return;
    const attr = key.replace(/[A-Z]/g, (match) => `-${match.toLowerCase()}`);
    const rendered = Array.isArray(value) ? JSON.stringify(value) : String(value);
    output.push(`data-${attr}="${escapeHtml(rendered, true)}"`);
  });
  return output.join("\n          ");
}

export function applyCatalogueEditorMediaAttrs(root, config, keys) {
  if (!root || !root.dataset) return;
  const attrs = readCatalogueEditorMediaAttrs(config);
  keys.forEach((key) => {
    const value = attrs[key];
    const datasetKey = key;
    if (value == null) {
      delete root.dataset[datasetKey];
      return;
    }
    root.dataset[datasetKey] = Array.isArray(value) ? JSON.stringify(value) : String(value);
  });
}

export function escapeHtml(value, attribute = false) {
  const text = String(value == null ? "" : value);
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return attribute
    ? escaped.replace(/"/g, "&quot;").replace(/'/g, "&#39;")
    : escaped;
}
