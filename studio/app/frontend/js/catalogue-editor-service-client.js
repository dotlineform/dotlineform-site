import {
  CATALOGUE_WRITE_ENDPOINTS,
  getJson,
  postJson,
  postForm
} from "./studio-transport.js";
import { buildWorkSaveForm } from "./catalogue-work-attachments.js";

/**
 * @typedef {Object} WorkSaveMedia
 * @property {boolean} regenerateImage Confirmed picker intent, outside canonical metadata.
 * @property {Map<string, File>} pendingAttachments Draft files keyed by their displayed managed identity.
 * @property {{total_bytes: number, metadata_bytes: number}} attachmentLimits Service-owned limits.
 */

export function saveCatalogueBulkRecords(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.bulkSave, payload);
}

export function previewCatalogueDelete(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.deletePreview, payload);
}

export function applyCatalogueDelete(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.deleteApply, payload);
}

/** Create and complete one Work; canonical success can include a local completion error.
 * @param {Object} payload Canonical record and Gallery memberships.
 * @param {WorkSaveMedia} media Draft-held media operations submitted with this Save.
 */
export function createCatalogueWork(payload, media) {
  return postWorkSave(CATALOGUE_WRITE_ENDPOINTS.createWork, payload, media);
}

/** Await a revision-checked Work Save and its local media completion in one request.
 * @param {Object} payload Canonical draft, Work revision and Gallery revisions.
 * @param {WorkSaveMedia} media Draft-held media operations submitted with this Save.
 */
export function saveCatalogueWork(payload, media) {
  return postWorkSave(CATALOGUE_WRITE_ENDPOINTS.saveWork, payload, media);
}

function postWorkSave(url, payload, media) {
  const request = { ...payload, regenerate_image: media.regenerateImage };
  return media.pendingAttachments.size
    ? postForm(url, buildWorkSaveForm(request, media.pendingAttachments, media.attachmentLimits))
    : postJson(url, request);
}

/** Resolve a draft's source identity at the local Catalogue owner without saving it. */
export function openWorkProjectMedia(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.openProjectMedia, payload);
}

export function createCatalogueSeries(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.createSeries, payload);
}

export function saveCatalogueSeries(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.saveSeries, payload);
}

export function createCatalogueGallery(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.createGallery, payload);
}

export function saveCatalogueGallery(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.saveGallery, payload);
}

export function deleteCatalogueGallery(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.deleteGallery, payload);
}

export function refreshCatalogue() {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.refresh, {});
}

export function readCatalogueRefreshStatus() {
  return getJson(CATALOGUE_WRITE_ENDPOINTS.refreshStatus);
}

function queryString(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    const text = String(value == null ? "" : value).trim();
    if (text) search.set(key, text);
  });
  return search.toString();
}

export function readWorkMediaSources() {
  const qs = queryString({ mode: "sources" });
  return getJson(`${CATALOGUE_WRITE_ENDPOINTS.projectMedia}?${qs}`);
}

export function readProjectMediaFolders(mediaSourceId = "", query = "") {
  const qs = queryString({ mode: "folders", media_source_id: mediaSourceId, q: query });
  return getJson(`${CATALOGUE_WRITE_ENDPOINTS.projectMedia}?${qs}`);
}

export function readProjectMediaFiles(options = {}) {
  const qs = queryString({
    mode: "files",
    media_source_id: options.mediaSourceId,
    project_folder: options.projectFolder,
    project_subfolder: options.projectSubfolder,
    q: options.query
  });
  return getJson(`${CATALOGUE_WRITE_ENDPOINTS.projectMedia}?${qs}`);
}
