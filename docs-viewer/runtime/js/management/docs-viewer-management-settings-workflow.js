import {
  readSourceConfigSettings
} from "./docs-viewer-management-client.js";

var SETTINGS_TEXT = {
  loadFailed: "Settings unavailable."
};

export function createDocsViewerManagementSettingsWorkflow(options = {}) {
  var state = options.state || {};
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};

  function modalController() {
    return typeof callbacks.getModalController === "function" ? callbacks.getModalController() : null;
  }

  function open() {
    var modal = modalController();
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    if (!modal || !modal.openSettingsModalShell()) return Promise.resolve(null);
    var clientOptions = typeof callbacks.managementClientOptions === "function" ? callbacks.managementClientOptions() : {};
    return readSourceConfigSettings(clientOptions)
      .then(function (payload) {
        var scopes = Array.isArray(payload && payload.scopes) ? payload.scopes : [];
        var fields = scopes[0] && Array.isArray(scopes[0].fields) ? scopes[0].fields : [];
        var field = fields.find(function (candidate) {
          return candidate && candidate.editable !== false;
        }) || null;
        modal.setSettingsField(field);
        return field;
      })
      .catch(function (error) {
        modal.setSettingsLoadError(error && error.message ? error.message : SETTINGS_TEXT.loadFailed);
        return null;
      });
  }

  function fieldState() {
    var modal = modalController();
    return modal ? modal.getSettingsFieldState() : null;
  }

  function changes() {
    var modal = modalController();
    return modal ? modal.getSettingsChanges() : null;
  }

  function close() {
    var modal = modalController();
    if (modal) modal.closeSettingsModal();
  }

  function render() {
    var modal = modalController();
    if (!refs.saveButton || !modal || !modal.settingsModalOpen()) return;
    refs.saveButton.disabled = Boolean(state.managementBusy) || !fieldState();
  }

  return {
    changes: changes,
    close: close,
    fieldState: fieldState,
    open: open,
    render: render
  };
}
