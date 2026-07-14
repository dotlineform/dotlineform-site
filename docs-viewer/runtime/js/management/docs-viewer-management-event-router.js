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

  function scopeLifecycleController() {
    return typeof controllers.scopeLifecycle === "function" ? controllers.scopeLifecycle() : null;
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

  function bind(ref, eventName, commandName, commandOptions) {
    if (!ref) return;
    ref.addEventListener(eventName, function () {
      invoke(commandName, commandOptions);
    });
  }

  function handleRootClick(event) {
    var interaction = interactionController();
    if (interaction) interaction.handleRootClick(event);
    if (refs.manageActionsMenu && !event.target.closest(".docsViewer__manageActions")) {
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

  function wireEvents() {
    var interaction = interactionController();
    if (interaction) interaction.wireEvents();

    bind(refs.rebuildButton, "click", "rebuild", {
      hideContextMenu: true,
      hideManageActionsMenu: true
    });
    (refs.importButtons || []).forEach(function (importButton) {
      bind(importButton, "click", "openImport");
    });
    bind(refs.settingsButton, "click", "openSettings");
    (refs.publishButtons || []).forEach(function (publishButton) {
      bind(publishButton, "click", "publish", {
        hideContextMenu: true,
        hideManageActionsMenu: true
      });
    });
    bind(refs.exportButton, "click", "exportDocs", {
      hideContextMenu: true,
      hideManageActionsMenu: true
    });
    if (refs.manageActionsButton) refs.manageActionsButton.addEventListener("click", toggleManageActionsMenu);
    bind(refs.newButton, "click", "createDoc", {
      hideContextMenu: true,
      hideManageActionsMenu: true
    });
    bind(refs.editButton, "click", "editCurrent", {
      hideManageActionsMenu: true
    });
    bind(refs.sourceButton, "click", "showMarkdownSource", {
      hideContextMenu: true,
      hideManageActionsMenu: true
    });
    bind(refs.sourceSaveButton, "click", "saveMarkdownSource", {
      hideContextMenu: true,
      hideManageActionsMenu: true
    });
    bind(refs.deleteButton, "click", "deleteDoc", {
      hideContextMenu: true,
      hideManageActionsMenu: true
    });
    bind(refs.viewableButton, "click", "makeViewable", {
      hideContextMenu: true
    });
    bind(refs.draftToggle, "change", "toggleDraft", {
      hideContextMenu: true
    });

    var modal = modalController();
    if (modal) modal.wireEvents();
    var lifecycle = scopeLifecycleController();
    if (lifecycle) lifecycle.wireEvents();
  }

  return {
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideManageActionsMenu: hideManageActionsMenu,
    wireEvents: wireEvents
  };
}
