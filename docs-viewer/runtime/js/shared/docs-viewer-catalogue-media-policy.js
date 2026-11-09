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
  variant(policy.thumbnails, "sizes");
  return policy;
}

/** Combine producer-owned thumbnail naming with the explicit route-owned base. */
export function catalogueThumbnailSettings(policy, baseUrl) {
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
  return response.json();
}
