var IMPORT_ROUTE_PATH = "/docs/";
var DEFAULT_CONFIG_URL = "/docs-viewer/config/defaults/docs-viewer-config.json";

export function createDocsViewerManagementImportController(options = {}) {
  var refs = options.refs || {};
  var context = options.context || {};
  var callbacks = options.callbacks || {};
  var importRequestPromise = null;
  var initialized = false;

  function viewerScope() {
    return typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
  }

  function importModule() {
    if (typeof callbacks.loadImportModule === "function") {
      return callbacks.loadImportModule();
    }
    return import("../import/docs-html-import.js");
  }

  function setBootError(error) {
    console.warn("docs_viewer: docs import modal failed to initialize", error);
    if (!refs.bootStatus) return;
    refs.bootStatus.hidden = false;
    refs.bootStatus.textContent = error && error.message ? error.message : "Failed to initialize docs import.";
    refs.bootStatus.dataset.state = "error";
  }

  function projectTerminalResult() {
    var modalController = typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
    if (modalController && typeof modalController.projectImportTerminalResult === "function") {
      modalController.projectImportTerminalResult();
    }
  }

  function initialize(scope) {
    if (!refs.root || !refs.bootStatus || initialized) return Promise.resolve();
    if (importRequestPromise) return importRequestPromise;

    importRequestPromise = importModule()
      .then(function (module) {
        if (!module || typeof module.initDocsHtmlImport !== "function") {
          throw new Error("Docs Import module did not expose initDocsHtmlImport().");
        }
        return module.initDocsHtmlImport({
          root: refs.root,
          bootStatus: refs.bootStatus,
          initialScope: scope || viewerScope(),
          docsViewerConfigUrl: context.docsViewerConfigUrl || context.root && context.root.dataset.docsViewerConfigUrl || DEFAULT_CONFIG_URL,
          managementBaseUrl: context.managementBaseUrl,
          reviewPackageId: context.root && context.root.dataset
            ? context.root.dataset.docsImportReviewPackageId || ""
            : "",
          routePath: IMPORT_ROUTE_PATH,
          onTerminalResult: projectTerminalResult
        });
      })
      .then(function () {
        initialized = true;
      })
      .catch(setBootError)
      .finally(function () {
        importRequestPromise = null;
      });

    return importRequestPromise;
  }

  function open() {
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    var modalController = typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
    if (modalController) modalController.openImportModal();
  }

  return {
    initialize: initialize,
    open: open
  };
}
