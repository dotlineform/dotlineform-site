import {
  prepareSourceMedia,
  readManagedDocSource,
  readManagedDocMetadata,
  readCatalogueMediaTargets,
  readCatalogueMediaConfig,
  readCatalogueWork,
  readCatalogueGallery,
  readCatalogueSeriesGalleries,
  readDocumentLinkTargets,
  saveManagedDocSource
} from "./docs-viewer-management-client.js";
import { documentTarget } from "../shared/docs-viewer-document-target.js";
import { createLiveCataloguePresentations } from "./docs-viewer-catalogue-live.js";

export function createDocsViewerManagementSourceAdapter(options) {
  var settings = options || {};
  var sourceService = settings.sourceService || null;
  var baseUrl = String(sourceService && sourceService.baseUrl || "").trim().replace(/\/+$/, "");
  if (!baseUrl) return null;

  var changeListeners = new Set();
  function commitDocumentChange(change) {
    var target = documentTarget(change.target);
    if (!change.deleted && (!change.record || change.record.doc_id !== target.doc_id)) throw new Error("Committed record did not match its target.");
    var failures = [];
    changeListeners.forEach(function (listener) {
      try { listener(Object.assign({}, change, { target: target })); } catch (error) { failures.push(error); }
    });
    if (failures.length) console.warn("Document saved; a retained list projection failed.", failures);
    return failures;
  }

  function projectSavedSource(response) {
    if (response && response.source_saved && response.committed_document) {
      try { response.projection_errors = commitDocumentChange(response.committed_document).map(function (error) { return error.message; }); }
      catch (error) { response.projection_errors = [error.message]; }
    }
    return response;
  }

  function clientOptions(overrides) {
    return Object.assign({
      baseUrl: baseUrl,
      fetch: function (url, requestOptions) {
        return settings.window.fetch(url, requestOptions);
      }
    }, overrides || {});
  }

  var adapter = {
    createCataloguePresentationOperation: function (payload) { return createLiveCataloguePresentations(adapter, payload); },
    commitDocumentChange: commitDocumentChange,
    subscribeDocumentChanges: function (listener) { changeListeners.add(listener); return function () { changeListeners.delete(listener); }; },
    readDocumentLinkTargets: function () {
      return readDocumentLinkTargets(clientOptions());
    },
    readCatalogueMediaTargets: function () {
      return readCatalogueMediaTargets( clientOptions());
    },
    readCatalogueMediaConfig: function () {
      return readCatalogueMediaConfig( clientOptions());
    },
    readCatalogueWork: function (workId) {
      return readCatalogueWork(workId,  clientOptions());
    },
    readCatalogueGallery: function (galleryId) {
      return readCatalogueGallery(galleryId,  clientOptions());
    },
    readCatalogueSeriesGalleries: function () {
      return readCatalogueSeriesGalleries(clientOptions());
    },
    readMetadata: function (target) { return readManagedDocMetadata(target, clientOptions()); },
    readSource: function (target, optionsForRead) {
      return readManagedDocSource(target, clientOptions(optionsForRead));
    },
    writeSource: function (target, payload, optionsForWrite) {
      return saveManagedDocSource(target, payload, clientOptions(optionsForWrite)).then(projectSavedSource).catch(function (error) {
        projectSavedSource(error.payload);
        throw error;
      });
    },
    prepareSourceMedia: function (payload, optionsForPrepare) {
      return prepareSourceMedia(payload, clientOptions(optionsForPrepare));
    }
  };
  return adapter;
}
