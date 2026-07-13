import {
  CATALOGUE_WRITE_ENDPOINTS,
  getJson,
  postJson
} from "./studio-transport.js";

export function saveCatalogueBulkRecords(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.bulkSave, payload);
}

export function previewCatalogueDelete(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.deletePreview, payload);
}

export function applyCatalogueDelete(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.deleteApply, payload);
}

export function previewCataloguePublication(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.publicationPreview, payload);
}

export function applyCataloguePublication(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.publicationApply, payload);
}

export function previewCatalogueMediaPublish(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.mediaPublishPreview, payload);
}

export function applyCatalogueMediaPublish(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.mediaPublishApply, payload);
}

export function createCatalogueWorkDetailSection(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.createWorkDetailSection, payload);
}

export function saveCatalogueWorkDetailSection(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.saveWorkDetailSection, payload);
}

export function createCatalogueWork(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.createWork, payload);
}

export function saveCatalogueWork(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.saveWork, payload);
}

export function createCatalogueSeries(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.createSeries, payload);
}

export function saveCatalogueSeries(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.saveSeries, payload);
}

export function previewCatalogueBuild(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.buildPreview, payload);
}

export function applyCatalogueBuild(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.buildApply, payload);
}

function queryString(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    const text = String(value == null ? "" : value).trim();
    if (text) search.set(key, text);
  });
  return search.toString();
}

export function readProjectMediaFolders(query = "") {
  const qs = queryString({ mode: "folders", q: query });
  return getJson(`${CATALOGUE_WRITE_ENDPOINTS.projectMedia}?${qs}`);
}

export function readProjectMediaFiles(options = {}) {
  const qs = queryString({
    mode: "files",
    project_folder: options.projectFolder,
    project_subfolder: options.projectSubfolder,
    q: options.query
  });
  return getJson(`${CATALOGUE_WRITE_ENDPOINTS.projectMedia}?${qs}`);
}
