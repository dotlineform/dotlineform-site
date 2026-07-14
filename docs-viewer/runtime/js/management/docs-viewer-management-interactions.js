import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  canDragDoc,
  canDropOnParent,
  currentDropTargetFromEvent,
  rowDropParentIdFromEvent,
  terminalRootDropTargetFromEvent
} from "./docs-viewer-drag-drop.js";

export function createDocsViewerManagementInteractionController(options) {
  var nav = options.nav;
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var routeSession = options.routeSession || {};
  var searchRecent = options.searchRecent || {};
  var selectedDocument = options.selectedDocument || {};
  var context = options.context;
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};
  var contextMenu = refs.contextMenu || document.getElementById("docsViewerContextMenu");
  var contextCopyLinkButton = contextMenu
    ? contextMenu.querySelector('[data-docs-viewer-action="' + DOCS_VIEWER_ACTION_IDS.COPY_LINK + '"]')
    : null;
  var contextMenuDocId = "";
  var dragDocId = "";
  var dropTargetParentId = "";
  var hasDropTarget = false;
  var suppressNextClick = false;
  var lastEditRequestDocId = "";
  var lastEditRequestTime = 0;

  function docChildren(docId) {
    return documentIndex.childrenByParent.get(docId) || [];
  }

  function docHasChildren(docId) {
    return docChildren(docId).length > 0;
  }

  function dragEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !searchRecent.searchRouteActive;
  }

  function contextMenuEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !searchRecent.searchRouteActive;
  }

  function editFromIndexEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !searchRecent.searchRouteActive;
  }

  function dragDropOptions() {
    return {
      dragDocId: dragDocId,
      dragEnabled: dragEnabled(),
      docsById: documentIndex.docsById,
      hasChildren: docHasChildren,
      nav: nav
    };
  }

  function canDragCurrentDoc(doc) {
    return canDragDoc(doc, dragDropOptions());
  }

  function currentContextMenuDoc() {
    return documentIndex.docsById.get(contextMenuDocId) || null;
  }

  function clearDragState() {
    dragDocId = "";
    dropTargetParentId = "";
    hasDropTarget = false;
    updateNavDragState();
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

  function updateNavDragState() {
    if (!nav) return;
    nav.classList.remove("is-drop-root");
    nav.querySelectorAll(".docsViewer__navRow").forEach(function (row) {
      row.classList.remove("is-dragging", "is-drop-after", "is-drop-inside", "is-drop-inside-start");
    });
    if (dragDocId) {
      var dragRow = nav.querySelector('[data-doc-row-id="' + context.cssEscape(dragDocId) + '"]');
      if (dragRow) {
        dragRow.classList.add("is-dragging");
      }
    }
    if (hasDropTarget) {
      if (!dropTargetParentId) {
        nav.classList.add("is-drop-root");
        return;
      }
      var dropRow = nav.querySelector('[data-doc-row-id="' + context.cssEscape(dropTargetParentId) + '"]');
      if (dropRow) {
        dropRow.classList.add("is-drop-inside");
      }
    }
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

    nav.addEventListener("dragstart", function (event) {
      var dragHandle = event.target.closest("[data-drag-doc-id]");
      if (!dragHandle || !dragEnabled()) return;
      hideContextMenu();
      dragDocId = dragHandle.dataset.dragDocId || "";
      dropTargetParentId = "";
      hasDropTarget = false;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", dragDocId);
      }
      updateNavDragState();
    });

    nav.addEventListener("dragover", function (event) {
      var row = event.target.closest("[data-doc-row-id]");
      if (!row) {
        var terminalTarget = terminalRootDropTargetFromEvent(event, dragDropOptions());
        if (terminalTarget && canDropOnParent(terminalTarget.parentId, dragDropOptions())) {
          event.preventDefault();
          if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "move";
          }
          if (!hasDropTarget || dropTargetParentId !== terminalTarget.parentId) {
            dropTargetParentId = terminalTarget.parentId;
            hasDropTarget = true;
            updateNavDragState();
          }
          return;
        }
        if (hasDropTarget) {
          dropTargetParentId = "";
          hasDropTarget = false;
          updateNavDragState();
        }
        return;
      }

      var dropOptions = dragDropOptions();
      var nextParentId = rowDropParentIdFromEvent(row, event, dropOptions);
      if (!canDropOnParent(nextParentId, dropOptions)) {
        if (hasDropTarget) {
          dropTargetParentId = "";
          hasDropTarget = false;
          updateNavDragState();
        }
        return;
      }

      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = "move";
      }
      if (!hasDropTarget || dropTargetParentId !== nextParentId) {
        dropTargetParentId = nextParentId;
        hasDropTarget = true;
        updateNavDragState();
      }
    });

    nav.addEventListener("drop", function (event) {
      event.preventDefault();
      var dropOptions = dragDropOptions();
      var dropTarget = currentDropTargetFromEvent(event, {
        parentId: dropTargetParentId
      }, dropOptions);
      var parentId = dropTarget.parentId;
      if (!canDropOnParent(parentId, dropOptions)) {
        clearDragState();
        return;
      }
      var movingDocId = dragDocId;
      clearDragState();
      if (callbacks.onMoveDoc) callbacks.onMoveDoc(movingDocId, parentId);
    });

    nav.addEventListener("dragend", function () {
      clearDragState();
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
    canDragCurrentDoc: canDragCurrentDoc,
    clearDragState: clearDragState,
    currentContextMenuDoc: currentContextMenuDoc,
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideContextMenu: hideContextMenu,
    refs: {
      contextCopyLinkButton: contextCopyLinkButton
    },
    updateNavDragState: updateNavDragState,
    wireEvents: wireEvents
  };
}
