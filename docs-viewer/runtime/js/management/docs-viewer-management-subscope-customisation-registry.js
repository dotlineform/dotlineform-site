function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

const MANAGEMENT_CUSTOMISATION_LOADERS = Object.freeze({
  analysis_tags: function () {
    return import("./docs-viewer-management-subscope-analysis-tags.js").then(function (module) {
      return module.createDocsViewerManagementSubscopeAnalysisTags;
    });
  },
  dotlineform_projects: function () {
    return import("./docs-viewer-management-subscope-dotlineform-projects.js").then(function (module) {
      return module.createDocsViewerManagementSubscopeDotlineformProjects;
    });
  }
});

export function listManagementDocsSubscopeCustomisationIds() {
  return Object.freeze(Object.keys(MANAGEMENT_CUSTOMISATION_LOADERS).sort());
}

export function resolveManagementDocsSubscopeCustomisation(descriptor, options = {}) {
  if (descriptor == null) return Promise.resolve(null);
  var customisationId = cleanString(descriptor && descriptor.id);
  var loader = MANAGEMENT_CUSTOMISATION_LOADERS[customisationId];
  if (!customisationId || typeof loader !== "function") {
    return Promise.reject(new Error(
      "Manage Docs sub-scope customisation is unavailable: "
      + (customisationId || "missing identity")
    ));
  }
  return Promise.resolve(loader()).then(function (factory) {
    if (typeof factory !== "function") {
      throw new Error(
        "Manage Docs sub-scope customisation factory is unavailable: "
        + customisationId
      );
    }
    return factory(Object.assign({}, options, { descriptor: descriptor }));
  });
}
