import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  visibleDocsViewerIndexSelectionDocIds
} from "./docs-viewer-index-selection.js";

export function createDocsViewerManagementInteractionController(options) {
  var nav = options.nav;
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var routeSession = options.routeSession || {};
  var searchRecent = options.searchRecent || {};
  var selectedDocument = options.selectedDocument || {};
  var indexSelection = options.indexSelection || null;
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};
  var contextMenu = refs.contextMenu || document.getElementById("docsViewerContextMenu");
  var contextCopyLinkButton = contextMenu
    ? contextMenu.querySelector('[data-docs-viewer-action="' + DOCS_VIEWER_ACTION_IDS.COPY_LINK + '"]')
    : null;
  var contextMenuDocId = "";
  var suppressNextClick = false;
  var lastEditRequestDocId = "";
  var lastEditRequestTime = 0;

  function contextMenuEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !searchRecent.searchRouteActive;
  }

  function editFromIndexEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !searchRecent.searchRouteActive;
  }

  function indexSelectionEnabled() {
    return Boolean(
      indexSelection
      && indexSelection.snapshot().selectionModeActive
      && routeSession.managementContext
      && management.managementAvailable
      && !management.managementBusy
    );
  }

  function currentContextMenuDoc() {
    return documentIndex.docsById.get(contextMenuDocId) || null;
  }

  function hideContextMenu() {
    contextMenuDocId = "";
    if (contextMenu) {
      contextMenu.hidden = true;
      contextMenu.style.left = "";
      contextMenu.style.top = "";
    }
  }

  function showContextMenu(docId, clientX, clientY) {
    if (!contextMenu || !contextMenuEnabled() || !documentIndex.docsById.has(docId)) return;
    contextMenuDocId = docId;
    contextMenu.hidden = false;
    contextMenu.style.left = "0px";
    contextMenu.style.top = "0px";
    var menuRect = contextMenu.getBoundingClientRect();
    var maxLeft = Math.max(8, window.innerWidth - menuRect.width - 8);
    var maxTop = Math.max(8, window.innerHeight - menuRect.height - 8);
    contextMenu.style.left = Math.min(clientX, maxLeft) + "px";
    contextMenu.style.top = Math.min(clientY, maxTop) + "px";
  }

  function clearSelection() {
    if (!window.getSelection) return;
    var selection = window.getSelection();
    if (selection) selection.removeAllRanges();
  }

  function handleContextAction(actionId) {
    if (!contextMenuEnabled() || !currentContextMenuDoc()) return;
    if (callbacks.onContextAction) callbacks.onContextAction(actionId);
  }

  function requestEditDoc(docId) {
    var normalizedDocId = String(docId || "");
    if (!normalizedDocId || !documentIndex.docsById.has(normalizedDocId)) return;
    var now = Date.now();
    if (lastEditRequestDocId === normalizedDocId && now - lastEditRequestTime < 500) return;
    lastEditRequestDocId = normalizedDocId;
    lastEditRequestTime = now;
    clearSelection();
    hideContextMenu();
    if (callbacks.onEditDoc) callbacks.onEditDoc(normalizedDocId);
  }

  function requestEditSelectedDoc() {
    requestEditDoc(selectedDocument.selectedDocId);
  }

  function handleRootClick(event) {
    if (contextMenu && !event.target.closest("#docsViewerContextMenu")) {
      hideContextMenu();
    }
    return false;
  }

  function handleDocumentKeydown(event) {
    if (event.key === "Escape" && contextMenu && !contextMenu.hidden) {
      event.preventDefault();
      hideContextMenu();
      return true;
    }
    return false;
  }

  function wireNavEvents() {
    if (!nav) return;

    nav.addEventListener("click", function (event) {
      var selectionCheckbox = event.target.closest("[data-docs-viewer-selection-checkbox]");
      if (selectionCheckbox && nav.contains(selectionCheckbox)) {
        event.stopPropagation();
        if (!indexSelectionEnabled()) return;
        hideContextMenu();
        var docId = selectionCheckbox.dataset.docsViewerSelectionCheckbox || "";
        var nextState = event.shiftKey
          ? indexSelection.selectRange(docId, visibleDocsViewerIndexSelectionDocIds(nav))
          : indexSelection.toggle(docId);
        if (callbacks.onIndexSelectionChange) callbacks.onIndexSelectionChange(nextState);
        return;
      }
      if (event.detail >= 2 && !event.target.closest("[data-toggle-doc-id]")) {
        if (editFromIndexEnabled() && documentIndex.docsById.has(selectedDocument.selectedDocId)) {
          suppressNextClick = false;
          event.preventDefault();
          event.stopPropagation();
          requestEditSelectedDoc();
          return;
        }
      }
      if (!suppressNextClick) return;
      suppressNextClick = false;
      event.preventDefault();
      event.stopPropagation();
    }, true);

    nav.addEventListener("mousedown", function (event) {
      if (event.button === 0 && event.detail >= 2 && !event.target.closest("[data-toggle-doc-id]")) {
        if (editFromIndexEnabled() && documentIndex.docsById.has(selectedDocument.selectedDocId)) {
          suppressNextClick = true;
          event.preventDefault();
          event.stopPropagation();
          requestEditSelectedDoc();
          return;
        }
      }
      var row = event.target.closest("[data-doc-row-id]");
      if (!row || !contextMenuEnabled() || event.button !== 2) return;
      event.preventDefault();
      clearSelection();
    });

    nav.addEventListener("contextmenu", function (event) {
      var row = event.target.closest("[data-doc-row-id]");
      if (!row || !contextMenuEnabled()) return;
      event.preventDefault();
      clearSelection();
      showContextMenu(row.dataset.docRowId || "", event.clientX, event.clientY);
    });

    nav.addEventListener("dblclick", function (event) {
      if (event.target.closest("[data-toggle-doc-id]")) return;
      var row = event.target.closest("[data-doc-row-id]");
      if (!row || !editFromIndexEnabled()) return;
      if (!documentIndex.docsById.has(selectedDocument.selectedDocId)) return;
      event.preventDefault();
      requestEditSelectedDoc();
    });

  }

  function wireContextMenuEvents() {
    if (!contextMenu) return;
    contextMenu.addEventListener("click", function (event) {
      var action = event.target.closest("[data-docs-viewer-action]");
      if (!action) return;
      event.preventDefault();
      handleContextAction(action.dataset.docsViewerAction);
    });
  }

  function wireEvents() {
    wireNavEvents();
    wireContextMenuEvents();
  }

  return {
    currentContextMenuDoc: currentContextMenuDoc,
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideContextMenu: hideContextMenu,
    refs: {
      contextCopyLinkButton: contextCopyLinkButton
    },
    wireEvents: wireEvents
  };
}
