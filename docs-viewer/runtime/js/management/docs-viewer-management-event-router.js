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

  function ref(name) {
    return typeof refs[name] === "function" ? refs[name]() : refs[name];
  }

  function hideContextMenu() {
    var interaction = interactionController();
    if (interaction) interaction.hideContextMenu();
  }

  function hideManageActionsMenu() {
    var menu = ref("manageActionsMenu");
    var button = ref("manageActionsButton");
    if (!menu || !button) return;
    menu.hidden = true;
    button.setAttribute("aria-expanded", "false");
  }

  function toggleManageActionsMenu() {
    var menu = ref("manageActionsMenu");
    var button = ref("manageActionsButton");
    if (!menu || !button || button.disabled) return;
    if (menu.hidden) {
      menu.hidden = false;
      button.setAttribute("aria-expanded", "true");
      return;
    }
    hideManageActionsMenu();
  }

  function hideIndexActionsMenu(options = {}) {
    var menu = ref("indexActionsMenu");
    var button = ref("indexActionsButton");
    if (!menu || !button) return;
    menu.hidden = true;
    button.setAttribute("aria-expanded", "false");
    if (options.focusButton && typeof button.focus === "function") button.focus();
  }

  function toggleIndexActionsMenu() {
    var menu = ref("indexActionsMenu");
    var button = ref("indexActionsButton");
    if (!menu || !button) return;
    if (menu.hidden) {
      menu.hidden = false;
      button.setAttribute("aria-expanded", "true");
      return;
    }
    hideIndexActionsMenu();
  }

  function invoke(commandName, options = {}) {
    if (options.hideContextMenu) hideContextMenu();
    if (options.hideManageActionsMenu) hideManageActionsMenu();
    if (typeof commands[commandName] === "function") commands[commandName]();
  }

  function handleRootClick(event) {
    var interaction = interactionController();
    if (interaction) interaction.handleRootClick(event);
    if (ref("manageActionsMenu") && !event.target.closest('[data-docs-viewer-control="manage-actions"]')) {
      hideManageActionsMenu();
    }
    if (ref("indexActionsMenu") && !event.target.closest('[data-docs-viewer-control="index-actions"]')) {
      hideIndexActionsMenu();
    }
    var modal = modalController();
    return modal ? modal.handleRootClick(event) : false;
  }

  function handleDocumentKeydown(event) {
    var interaction = interactionController();
    if (interaction && interaction.handleDocumentKeydown(event)) return true;
    var indexMenu = ref("indexActionsMenu");
    if (event.key === "Escape" && indexMenu && !indexMenu.hidden) {
      event.preventDefault();
      hideIndexActionsMenu({ focusButton: true });
      return true;
    }
    var manageMenu = ref("manageActionsMenu");
    if (event.key === "Escape" && manageMenu && !manageMenu.hidden) {
      event.preventDefault();
      hideManageActionsMenu();
      return true;
    }
    return false;
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
      ["review-document-package", ["reviewPackage", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["publish-docs", ["publish", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["export-docs", ["exportDocs", { hideContextMenu: true, hideManageActionsMenu: true }]],
      ["new", ["createDoc", { hideContextMenu: true, hideManageActionsMenu: true }]],
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
    hideIndexActionsMenu: hideIndexActionsMenu,
    hideManageActionsMenu: hideManageActionsMenu,
    toggleIndexActionsMenu: toggleIndexActionsMenu,
    wireEvents: wireEvents
  };
}
