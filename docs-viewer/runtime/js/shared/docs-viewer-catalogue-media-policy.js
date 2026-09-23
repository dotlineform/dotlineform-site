import { docsViewerSafeMediaTarget } from "./docs-viewer-media-presentation.js";

function mediaBase(value) {
  if (typeof value !== "string" || !docsViewerSafeMediaTarget(value) || !value.endsWith("/") || /[?#\s,]/.test(value)) {
    throw new Error("Catalogue media base URL is unavailable or unsafe.");
  }
  return value;
}

function variant(value, key) {
  if (!value || !Array.isArray(value[key]) || !value[key].length
    || value[key].some(function (size) { return !Number.isInteger(size) || size <= 0; })
    || typeof value.suffix !== "string" || !/^[a-z0-9-]+$/.test(value.suffix)) {
    throw new Error("Catalogue rendition policy is unavailable.");
  }
}

/** Validate only the shared consumer projection, never the private pipeline configuration. */
export function validateCatalogueMediaPolicy(policy) {
  if (!policy || !policy.header || policy.header.schema !== "catalogue_media_config_v1"
    || !/^(?:webp|avif|png|jpg)$/.test(policy.format)) {
    throw new Error("Catalogue media configuration is unavailable.");
  }
  variant(policy.primary, "widths");
  variant(policy.thumbnails, "sizes");
  if (policy.primary.version_query_parameter !== "v" || !policy.primary.base_urls) {
    throw new Error("Catalogue image version policy is unavailable.");
  }
  mediaBase(policy.primary.base_urls.works);
  mediaBase(policy.primary.base_urls.work_details);
  return policy;
}

/** Resolve unchanged filenames; descriptors use actual widths because the producer never upscales. */
export function catalogueImageCandidates(target, record, policy) {
  validateCatalogueMediaPolicy(policy);
  if (!Number.isInteger(record.media_version) || record.media_version <= 0) {
    throw new Error("Catalogue image media version is unavailable.");
  }
  var primary = policy.primary;
  var family = target.kind === "catalogue-work-detail" ? "work_details" : "works";
  var widths = Array.from(new Set(primary.widths)).sort(function (a, b) { return a - b; });
  function url(width) {
    return primary.base_urls[family] + target.id + "-" + primary.suffix + "-" + width + "." + policy.format
      + "?" + primary.version_query_parameter + "=" + record.media_version;
  }
  var candidates = new Map();
  widths.forEach(function (width) {
    var actualWidth = Math.min(width, record.width_px);
    if (!candidates.has(actualWidth)) candidates.set(actualWidth, { src: url(width), width_px: actualWidth });
  });
  return { candidates: Array.from(candidates.values()), largest: url(widths[widths.length - 1]) };
}

/** Combine producer-owned thumbnail naming with the explicit route-owned base. */
export function catalogueThumbnailSettings(policy, baseUrl) {
  validateCatalogueMediaPolicy(policy);
  return { base_url: mediaBase(baseUrl), size: Math.min(...policy.thumbnails.sizes),
    suffix: policy.thumbnails.suffix, format: policy.format };
}

/** Read public policy through the configured static route; failures have no local fallback. */
export async function readPublicCatalogueMediaConfig(url, fetchImpl) {
  if (typeof url !== "string" || !url.startsWith("/") || url.startsWith("//") || /[?#\\\s]/.test(url)) {
    throw new Error("Public Catalogue media configuration is not configured.");
  }
  var response = await fetchImpl(url, { cache: "no-cache", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Catalogue media configuration is unavailable (HTTP " + response.status + ").");
  return validateCatalogueMediaPolicy(await response.json());
}
