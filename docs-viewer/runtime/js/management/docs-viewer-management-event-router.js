export function createDocsViewerManagementEventRouter(options = {}) {
  var refs = options.refs || {};
  var commands = options.commands || {};
  var controllers = options.controllers || {};

  function interactionController() {
    return typeof controllers.interaction === "function" ? controllers.interaction() : null;
  }

  function modalController() {
    return typeof controllers.modal === "function" ? controllers.modal() : null;
  }

  function hideContextMenu() {
    var interaction = interactionController();
    if (interaction) interaction.hideContextMenu();
  }

  function hideManageActionsMenu() {
    if (!refs.manageActionsMenu || !refs.manageActionsButton) return;
    refs.manageActionsMenu.hidden = true;
    refs.manageActionsButton.setAttribute("aria-expanded", "false");
  }

  function toggleManageActionsMenu() {
    if (!refs.manageActionsMenu || !refs.manageActionsButton || refs.manageActionsButton.disabled) return;
    if (refs.manageActionsMenu.hidden) {
      refs.manageActionsMenu.hidden = false;
      refs.manageActionsButton.setAttribute("aria-expanded", "true");
      return;
    }
    hideManageActionsMenu();
  }

  function invoke(commandName, options = {}) {
    if (options.hideContextMenu) hideContextMenu();
    if (options.hideManageActionsMenu) hideManageActionsMenu();
    if (typeof commands[commandName] === "function") commands[commandName]();
  }

  function handleRootClick(event) {
    var interaction = interactionController();
    if (interaction) interaction.handleRootClick(event);
    if (refs.manageActionsMenu && !event.target.closest('[data-docs-viewer-control="manage-actions"]')) {
      hideManageActionsMenu();
    }
    var modal = modalController();
    return modal ? modal.handleRootClick(event) : false;
  }

  function handleDocumentKeydown(event) {
    var interaction = interactionController();
    if (interaction && interaction.handleDocumentKeydown(event)) return true;
    if (event.key === "Escape" && refs.manageActionsMenu && !refs.manageActionsMenu.hidden) {
      event.preventDefault();
      hideManageActionsMenu();
      return true;
    }
    var modal = modalController();
    return modal ? modal.handleDocumentKeydown(event) : false;
  }

  function handleAppManagementControl(detail) {
    var controlId = String(detail && detail.controlId || "").trim();
    var actionId = String(detail && detail.actionId || "").trim();
    if (controlId === "manage-actions" && !actionId && detail.eventType === "click") {
      toggleManageActionsMenu();
      return true;
    }
    var commandsByAction = new Map([
      ["rebuild-docs", ["rebuild", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["import", ["openImport", {}]],
      ["settings", ["openSettings", {}]],
      ["prepare-document-package", ["preparePackage", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["publish-docs", ["publish", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["export-docs", ["exportDocs", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["new", ["createDoc", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["delete", ["deleteDoc", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["show", ["makeViewable", { hideContextMenu: true }]],
      ["new-scope", ["createScope", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["rename-scope", ["renameScope", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["delete-scope", ["deleteScope", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["new-sub-scope", ["createSubScope", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["delete-sub-scope", ["deleteSubScope", { hideContextMenu: true, hideManageActionsMenu: true }]]
    ]);
    var command = commandsByAction.get(actionId);
    if (!command || detail.eventType !== "click") return false;
    invoke(command[0], command[1]);
    return true;
  }

  function wireEvents() {
    var interaction = interactionController();
    if (interaction) interaction.wireEvents();
    var modal = modalController();
    if (modal) modal.wireEvents();
  }

  return {
    handleAppManagementControl: handleAppManagementControl,
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideManageActionsMenu: hideManageActionsMenu,
    wireEvents: wireEvents
  };
}
