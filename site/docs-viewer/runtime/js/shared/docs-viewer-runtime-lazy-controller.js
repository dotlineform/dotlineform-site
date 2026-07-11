export function createDocsViewerManagementRuntimeAdapter(options) {
  var settings = options || {};
  var managementController = null;
  var managementControllerRequestPromise = null;

  function context() {
    return Object.assign({}, settings.constants || {}, settings.context || {});
  }

  function load() {
    if (!settings.managementUi) return Promise.resolve(null);
    if (managementController) return Promise.resolve(managementController);
    if (managementControllerRequestPromise) return managementControllerRequestPromise;
    var importManagement = settings.importManagement || function () {
      return import("../management/docs-viewer-management.js");
    };

    managementControllerRequestPromise = settings.appShellReady
      .then(function () {
        return importManagement();
      })
      .then(function (module) {
        managementController = module.initDocsViewerManagement(context());
        if (typeof settings.onLoaded === "function") {
          settings.onLoaded(managementController);
        }
        return managementController;
      })
      .catch(function (error) {
        var logger = settings.logger || console;
        if (logger && typeof logger.warn === "function") {
          logger.warn("docs_viewer: management controller unavailable", error);
        }
        return null;
      })
      .finally(function () {
        managementControllerRequestPromise = null;
      });

    return managementControllerRequestPromise;
  }

  return {
    controller: function () { return managementController; },
    load: load
  };
}
