function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

const MANAGEMENT_CUSTOMISATION_LOADERS = Object.freeze({
  pre_publish_works: function () {
    return import("./docs-viewer-management-collection-working-subjects.js").then(function (module) {
      return module.createDocsViewerManagementCollectionPrePublishWorks;
    });
  },
  working_works: function () {
    return import("./docs-viewer-management-collection-working-subjects.js").then(function (module) {
      return module.createDocsViewerManagementCollectionWorkingWorks;
    });
  },
  working_processing: function () {
    return import("./docs-viewer-management-collection-working-subjects.js").then(function (module) {
      return module.createDocsViewerManagementCollectionWorkingProcessing;
    });
  }
});

export function listManagementDocsCollectionCustomisationIds() {
  return Object.freeze(Object.keys(MANAGEMENT_CUSTOMISATION_LOADERS).sort());
}

export function resolveManagementDocsCollectionCustomisation(descriptor, options = {}) {
  if (descriptor == null) return Promise.resolve(null);
  var customisationId = cleanString(descriptor && descriptor.id);
  var loader = MANAGEMENT_CUSTOMISATION_LOADERS[customisationId];
  if (!customisationId || typeof loader !== "function") {
    return Promise.reject(new Error(
      "Manage Docs collection customisation is unavailable: "
      + (customisationId || "missing identity")
    ));
  }
  return Promise.resolve(loader()).then(function (factory) {
    if (typeof factory !== "function") {
      throw new Error(
        "Manage Docs collection customisation factory is unavailable: "
        + customisationId
      );
    }
    return factory(Object.assign({}, options, { descriptor: descriptor }));
  });
}
