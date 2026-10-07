import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { DOCS_VIEWER_ACTION_IDS as ACTION_IDS } from "./docs-viewer-action-definitions.js";

var EDIT_ITEMS = [
  { actionId: ACTION_IDS.EDIT_DOCUMENT, label: "Source editor", artwork: "docsViewer__icon--square-code" },
  { actionId: ACTION_IDS.REBUILD_DOCUMENT, label: "Rebuild", artwork: "docsViewer__icon--refresh-cw" },
  { actionId: ACTION_IDS.OPEN_VSCODE, label: "Open in VS Code", artwork: "docsViewer__icon--file-code-corner", contextAction: true },
  { actionId: ACTION_IDS.SET_DRAFT, label: "Mark as draft", artwork: "docsViewer__icon--circle-check", checked: false, contextAction: true },
  { actionId: ACTION_IDS.SET_SELECTED, label: "Star", artwork: "docsViewer__icon--star", checked: false, contextAction: true },
  { actionId: ACTION_IDS.COPY_LINK, label: "Copy link", artwork: "docsViewer__icon--link", fallback: true },
  { actionId: ACTION_IDS.DELETE, label: "Delete", artwork: "docsViewer__icon--trash", fallback: true },
  { actionId: "assign-subject", label: "Assign Subject", artwork: "docsViewer__icon--dlf-subject", fallback: true },
  { actionId: "open-project-folder", label: "Open in Finder", artwork: "docsViewer__icon--folder-open", fallback: true }
];

/** Collection contributions retain their own handlers and live availability. */
export function createDocsViewerEditMenuItem(documentRef, item) {
  var button = documentRef.createElement("button");
  button.type = "button";
  button.className = "docsViewer__actionMenuItem";
  button.dataset.docsViewerAction = item.actionId;
  if (item.contribution) button.dataset.docsViewerEditContribution = "true";
  button.setAttribute("role", typeof item.checked === "boolean" ? "menuitemcheckbox" : "menuitem");
  if (typeof item.checked === "boolean") button.setAttribute("aria-checked", String(item.checked));
  button.setAttribute("aria-label", item.label);
  button.title = item.label;
  button.disabled = true;
  var label = documentRef.createElement("span");
  label.className = "docsViewer__actionMenuLabel";
  label.textContent = item.label;
  button.append(createDocsViewerToolbarIcon(documentRef, item.artwork), label);
  return button;
}

/** Render one stable Edit control with visible disabled fallbacks for unsupported actions. */
export function renderDocsViewerEditMenu(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerManageEditMenu")) {
    var documentRef = context.document;
    root = documentRef.createElement("div");
    root.className = "docsViewer__actionsMenuHost docsViewer__editMenuHost";
    var trigger = documentRef.createElement("button");
    trigger.id = "docsViewerManageEditButton";
    trigger.className = "docsViewer__toolbarIconButton";
    trigger.type = "button";
    trigger.setAttribute("aria-haspopup", "menu");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", "docsViewerManageEditMenu");
    trigger.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--pen"));
    var menu = documentRef.createElement("div");
    menu.id = "docsViewerManageEditMenu";
    menu.className = "docsViewer__actionsMenu docsViewer__editMenu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    EDIT_ITEMS.forEach(function (item) {
      var button = createDocsViewerEditMenuItem(documentRef, item);
      if (item.fallback) button.classList.add("docsViewer__editMenuFallback");
      menu.appendChild(button);
    });
    var contributions = documentRef.createElement("div");
    contributions.className = "docsViewer__editMenuCollectionActions";
    menu.appendChild(contributions);
    root.append(trigger, menu);
  }
  return { root: root, interactive: root.querySelector("#docsViewerManageEditButton") };
}

/**
 * Own Edit menu disclosure and ordinary-document dispatch. Mounted collection
 * menu items keep their registered exact targets, handlers and async state.
 * Target changes, busy state, Source and expanded views close the menu.
 */
export function createDocsViewerEditMenuController(options) {
  var previousTarget = "";
  function refs() {
    return {
      trigger: options.root.querySelector("#docsViewerManageEditButton"),
      menu: options.root.querySelector("#docsViewerManageEditMenu"),
      host: options.root.querySelector(".docsViewer__editMenuHost")
    };
  }
  function close(restoreFocus) {
    var current = refs();
    if (!current.menu) return;
    current.menu.hidden = true;
    current.trigger.setAttribute("aria-expanded", "false");
    if (restoreFocus && !current.trigger.disabled) current.trigger.focus({ preventScroll: true });
  }
  function currentState() {
    var context = options.documentActionContext();
    var view = options.activeViewState();
    var target = context.documentTarget;
    var record = context.documentRecord;
    var control = options.editControl();
    var available = Boolean(control && !control.state.hidden && !control.state.disabled
      && view.activeViewId === "rendered-document" && view.activeModeId === "rendered-document"
      && target && record && record.doc_id === target.doc_id);
    return { context: context, target: target, record: record, available: available };
  }
  function render() {
    var current = refs();
    if (!current.menu) return;
    var state = currentState();
    var targetKey = state.target ? (state.target.collection || "") + "/" + state.target.doc_id : "";
    if (!state.available || previousTarget !== targetKey) close(false);
    previousTarget = targetKey;
    var mount = current.menu.querySelector(".docsViewer__editMenuCollectionActions");
    var host = state.context.state === "detail" ? state.context.actionHost : null;
    if (mount.firstChild !== host) mount.replaceChildren(...(host ? [host] : []));
    var ordinary = state.available && !state.target.collection;
    var deleteState = ordinary ? options.deleteState(state.target.doc_id) : null;
    EDIT_ITEMS.forEach(function (item) {
      if (item.contextAction) return;
      var button = current.menu.querySelector(':scope > [data-docs-viewer-action="' + item.actionId + '"]');
      var enabled = item.actionId === ACTION_IDS.EDIT_DOCUMENT || item.actionId === ACTION_IDS.REBUILD_DOCUMENT ? state.available
        : item.actionId === ACTION_IDS.COPY_LINK ? ordinary
          : item.actionId === ACTION_IDS.DELETE ? ordinary && deleteState && !deleteState.disabled && !deleteState.hidden : false;
      button.disabled = !enabled;
      button.title = enabled ? item.label
        : item.actionId === ACTION_IDS.DELETE && deleteState ? deleteState.disabledReason
          : item.actionId === ACTION_IDS.DELETE && state.target?.collection === "catalogue" ? "Catalogue documents are managed through regeneration."
            : "This action is unavailable for the displayed document.";
    });
  }
  function enabledItems(menu) {
    return Array.from(menu.querySelectorAll('[role="menuitem"], [role="menuitemcheckbox"]')).filter(function (button) {
      return !button.disabled && button.getClientRects().length;
    });
  }
  function handleControl(detail) {
    if (detail.eventType !== "click") return false;
    if (!detail.actionId) {
      render();
      options.contextActions.render();
    }
    var current = refs();
    var state = currentState();
    if (!current.menu || !state.available) return false;
    var actionId = detail.actionId;
    if (!actionId) {
      options.closeOtherMenus();
      current.menu.hidden = !current.menu.hidden;
      current.trigger.setAttribute("aria-expanded", String(!current.menu.hidden));
      if (!current.menu.hidden) enabledItems(current.menu)[0]?.focus({ preventScroll: true });
      return true;
    }
    close(false);
    if (detail.actionTarget?.dataset.docsViewerEditContribution === "true") return true;
    if (detail.actionTarget?.disabled) return false;
    if (actionId === ACTION_IDS.EDIT_DOCUMENT) options.openSource(state.target);
    else if (actionId === ACTION_IDS.REBUILD_DOCUMENT) options.rebuildDocument(state.target);
    else if (options.contextActions.owns(actionId)) options.contextActions.invoke(actionId);
    else if (!state.target.collection && actionId === ACTION_IDS.COPY_LINK) options.copyLink(state.target.doc_id);
    else if (!state.target.collection && actionId === ACTION_IDS.DELETE) {
      var deletion = options.deleteState(state.target.doc_id);
      if (!deletion.disabled && !deletion.hidden) options.deleteDocument(state.target.doc_id, current.trigger);
    }
    return true;
  }
  function handleRootClick(event) {
    var current = refs();
    if (current.host && !current.host.contains(event.target)) close(false);
  }
  function handleKeydown(event) {
    var current = refs();
    if (!current.menu || current.menu.hidden) return false;
    if (event.key === "Escape") {
      event.preventDefault();
      close(true);
      return true;
    }
    if (!current.menu.contains(event.target)) return false;
    if (event.key === "Tab") { close(false); return false; }
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return false;
    event.preventDefault();
    var items = enabledItems(current.menu);
    if (!items.length) return true;
    var index = items.indexOf(event.target.closest('[role="menuitem"], [role="menuitemcheckbox"]'));
    var next = event.key === "Home" ? 0 : event.key === "End" ? items.length - 1
      : (index + (event.key === "ArrowUp" ? -1 : 1) + items.length) % items.length;
    items[next].focus({ preventScroll: true });
    return true;
  }
  return { close: close, render: render, handleControl: handleControl, handleRootClick: handleRootClick, handleKeydown: handleKeydown };
}
