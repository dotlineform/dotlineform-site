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

export function createCatalogueWorkDetailSection(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.createWorkDetailSection, payload);
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

export function previewCatalogueProseImport(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.previewProseImport, payload);
}

export function applyCatalogueProseImport(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.applyProseImport, payload);
}

export function previewCatalogueMomentImport(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.previewMomentImport, payload);
}

export function applyCatalogueMomentImport(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.applyMomentImport, payload);
}

export function previewCatalogueMoment(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.previewMoment, payload);
}

export function saveCatalogueMoment(payload) {
  return postJson(CATALOGUE_WRITE_ENDPOINTS.saveMoment, payload);
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
