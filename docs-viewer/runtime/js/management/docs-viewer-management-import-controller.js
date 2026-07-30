import {
  normalizeManagedDocumentCollectionTarget
} from "./docs-viewer-management-document-target.js";

var IMPORT_ROUTE_PATH = "/docs/";
var DEFAULT_CONFIG_URL = "/docs-viewer/config/defaults/docs-viewer-config.json";

export function createDocsViewerManagementImportController(options = {}) {
  var refs = options.refs || {};
  var context = options.context || {};
  var callbacks = options.callbacks || {};
  var importRequestPromise = null;
  var importApp = null;
  var initialized = false;
  var activeOpen = {
    destination: null,
    destinationLabel: "",
    onComplete: null,
    restoreFocus: null
  };

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

  function projectTerminalResult(detail) {
    var modalController = typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
    if (modalController && typeof modalController.projectImportTerminalResult === "function") {
      modalController.projectImportTerminalResult();
    }
    if (typeof activeOpen.onComplete === "function") {
      return activeOpen.onComplete(detail || {});
    }
    if (typeof callbacks.onImportComplete === "function") {
      return callbacks.onImportComplete(detail || {});
    }
    return Promise.resolve();
  }

  function projectBusy(busy) {
    var modalController = typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
    if (modalController && typeof modalController.projectImportBusy === "function") {
      modalController.projectImportBusy(busy);
    }
  }

  function projectCollectionState(viewState, onCommand) {
    var modalController = typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
    if (modalController && typeof modalController.projectImportCollectionState === "function") {
      modalController.projectImportCollectionState(viewState, onCommand);
    }
  }

  function initialize() {
    if (!refs.root || !refs.bootStatus) return Promise.resolve();
    if (importRequestPromise) return importRequestPromise;
    if (initialized) {
      if (importApp && typeof importApp.setDestination === "function") {
        importApp.setDestination(activeOpen.destination, {
          label: activeOpen.destinationLabel
        });
      }
      return importApp && typeof importApp.refreshStagedFiles === "function"
        ? importApp.refreshStagedFiles()
        : Promise.resolve();
    }

    importRequestPromise = importModule()
      .then(function (module) {
        if (!module || typeof module.initDocsHtmlImport !== "function") {
          throw new Error("Docs Import module did not expose initDocsHtmlImport().");
        }
        return module.initDocsHtmlImport({
          root: refs.root,
          bootStatus: refs.bootStatus,
          initialDestination: activeOpen.destination,
          initialDestinationLabel: activeOpen.destinationLabel,
          docsViewerConfigUrl: context.docsViewerConfigUrl || context.root && context.root.dataset.docsViewerConfigUrl || DEFAULT_CONFIG_URL,
          managementBaseUrl: context.managementBaseUrl,
          routePath: IMPORT_ROUTE_PATH,
          onBusyChange: projectBusy,
          onCollectionStateChange: projectCollectionState,
          onTerminalResult: projectTerminalResult
        });
      })
      .then(function (initializedApp) {
        importApp = initializedApp || null;
        initialized = true;
      })
      .catch(setBootError)
      .finally(function () {
        importRequestPromise = null;
      });

    return importRequestPromise;
  }

  function open(options = {}) {
    var destination = normalizeManagedDocumentCollectionTarget(
      options.destination
    );
    activeOpen = {
      destination: destination,
      destinationLabel: String(options.destinationLabel || "").trim(),
      onComplete: typeof options.onComplete === "function"
        ? options.onComplete
        : null,
      restoreFocus: options.restoreFocus || null
    };
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    var modalController = typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
    if (!modalController) return Promise.resolve();
    return modalController.openImportModal({
      restoreFocus: activeOpen.restoreFocus
    });
  }

  function openForCollection(collection, options = {}) {
    var destination = normalizeManagedDocumentCollectionTarget(collection);
    if (!destination.sub_scope) {
      return Promise.reject(
        new Error("Sub-scope report Import requires a configured child collection.")
      );
    }
    return open({
      destination: destination,
      destinationLabel: options.destinationLabel,
      onComplete: options.onComplete,
      restoreFocus: options.restoreFocus
    });
  }

  return {
    initialize: initialize,
    open: open,
    openForCollection: openForCollection
  };
}
