import {
  requestDocsReviewJson
} from "./docs-viewer-review-client.js";
import {
  normalizeDocsIndexTreePayload
} from "../shared/docs-viewer-tree-payload-adapter.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function createDocsViewerReturnedPackageProvider(options) {
  var settings = options || {};
  var windowRef = settings.window || window;
  var serviceContext = settings.serviceContext || {};
  var generatedDataService = serviceContext.generatedData || {};
  var sourceService = serviceContext.source || {};
  var baseUrl = cleanString(generatedDataService.baseUrl || sourceService.baseUrl);
  var selectedPackageId = cleanString(new URLSearchParams(windowRef.location.search).get("package"));
  var manifestPromise = null;

  if (!baseUrl) throw new Error("Docs Review service is unavailable. Enable DOCS_VIEWER_REVIEW_ENABLED.");

  function request(path, requestOptions) {
    return requestDocsReviewJson(path, Object.assign({
      baseUrl: baseUrl,
      fetch: windowRef.fetch.bind(windowRef)
    }, requestOptions || {}));
  }

  function preserveSelectedPackage(packageId) {
    var url = new URL(windowRef.location.href);
    url.searchParams.set("package", packageId);
    windowRef.history.replaceState(windowRef.history.state, "", url.pathname + url.search + url.hash);
  }

  function listCollections() {
    return request("/docs-review/packages").then(function (payload) {
      var packages = Array.isArray(payload.packages) ? payload.packages : [];
      var rejected = Array.isArray(payload.rejected) ? payload.rejected : [];
      if (!packages.length && rejected.length) {
        var diagnostics = rejected.slice(0, 3).map(function (record) {
          var packageId = cleanString(record && record.package_id) || "unknown package";
          var message = cleanString(record && record.error) || "validation failed";
          return packageId + ": " + message;
        });
        if (rejected.length > diagnostics.length) {
          diagnostics.push((rejected.length - diagnostics.length) + " more rejected package(s)");
        }
        throw new Error("No validated Docs Review packages are available. Rejected: " + diagnostics.join("; "));
      }
      return packages;
    });
  }

  function ensurePackage() {
    if (selectedPackageId) return Promise.resolve(selectedPackageId);
    return listCollections().then(function (packages) {
      if (!packages.length) throw new Error("No validated Docs Review packages are available.");
      selectedPackageId = cleanString(packages[0].package_id);
      preserveSelectedPackage(selectedPackageId);
      return selectedPackageId;
    });
  }

  function readIndex() {
    return ensurePackage().then(function (packageId) {
      return request("/docs-review/packages/index-tree", {
        query: { package_id: packageId }
      }).then(function (payload) {
        return normalizeDocsIndexTreePayload(payload.index_tree);
      });
    });
  }

  function readDocument(doc, optionsForRead) {
    var requestSettings = optionsForRead || {};
    var docId = cleanString(requestSettings.docId || doc && doc.doc_id);
    return ensurePackage().then(function (packageId) {
      return request("/docs-review/packages/payload", {
        query: { package_id: packageId, doc_id: docId }
      }).then(function (payload) { return payload.payload; });
    });
  }

  function readSource(docId) {
    return ensurePackage().then(function (packageId) {
      return request("/docs-review/packages/source", {
        query: { package_id: packageId, doc_id: docId }
      });
    });
  }

  function writeSource(payload) {
    return ensurePackage().then(function (packageId) {
      return request("/docs-review/packages/source", {
        body: Object.assign({}, payload || {}, { package_id: packageId })
      });
    });
  }

  function build() {
    return ensurePackage().then(function (packageId) {
      return request("/docs-review/packages/build", {
        body: { package_id: packageId }
      });
    });
  }

  function readManifest() {
    if (!manifestPromise) {
      manifestPromise = ensurePackage().then(function (packageId) {
        return request("/docs-review/packages/manifest", {
          query: { package_id: packageId }
        });
      }).catch(function (error) {
        manifestPromise = null;
        throw error;
      });
    }
    return manifestPromise;
  }

  function readAssetInventory() {
    return ensurePackage().then(function (packageId) {
      return request("/docs-review/packages/assets", {
        query: { package_id: packageId }
      });
    });
  }

  return {
    activeCollectionId: function () { return selectedPackageId; },
    build: build,
    listCollections: listCollections,
    readAssetInventory: readAssetInventory,
    readDocument: readDocument,
    readIndex: readIndex,
    readManifest: readManifest,
    readSource: readSource,
    writeSource: writeSource
  };
}
