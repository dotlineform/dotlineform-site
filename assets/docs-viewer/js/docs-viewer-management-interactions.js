import {
  canDragDoc,
  canDropOnDoc,
  currentDropTargetFromEvent,
  rowDropPosition
} from "./docs-viewer-drag-drop.js";

export function createDocsViewerManagementInteractionController(options) {
  var nav = options.nav;
  var state = options.state;
  var context = options.context;
  var callbacks = options.callbacks || {};
  var contextMenu = document.getElementById("docsViewerContextMenu");
  var contextCopyLinkButton = contextMenu ? contextMenu.querySelector('[data-context-action="copy-link"]') : null;
  var contextMenuDocId = "";
  var dragDocId = "";
  var dropTargetDocId = "";
  var dropPosition = "";

  function docChildren(docId) {
    return state.childrenByParent.get(docId) || [];
  }

  function docHasChildren(docId) {
    return docChildren(docId).length > 0;
  }

  function dragEnabled() {
    return state.managementMode && state.managementAvailable && !state.managementBusy && !state.searchRouteActive;
  }

  function contextMenuEnabled() {
    return state.managementMode && state.managementAvailable && !state.managementBusy && !state.searchRouteActive;
  }

  function dragDropOptions() {
    return {
      dragDocId: dragDocId,
      dragEnabled: dragEnabled(),
      docsById: state.docsById,
      hasChildren: docHasChildren
    };
  }

  function canDragCurrentDoc(doc) {
    return canDragDoc(doc, dragDropOptions());
  }

  function currentContextMenuDoc() {
    return state.docsById.get(contextMenuDocId) || null;
  }

  function clearDragState() {
    dragDocId = "";
    dropTargetDocId = "";
    dropPosition = "";
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
    if (!contextMenu || !contextMenuEnabled() || !state.docsById.has(docId)) return;
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
    nav.querySelectorAll(".docsViewer__navRow").forEach(function (row) {
      row.classList.remove("is-dragging", "is-drop-after", "is-drop-inside");
    });
    if (dragDocId) {
      var dragRow = nav.querySelector('[data-doc-row-id="' + context.cssEscape(dragDocId) + '"]');
      if (dragRow) {
        dragRow.classList.add("is-dragging");
      }
    }
    if (dropTargetDocId && dropPosition) {
      var dropRow = nav.querySelector('[data-doc-row-id="' + context.cssEscape(dropTargetDocId) + '"]');
      if (dropRow) {
        dropRow.classList.add(dropPosition === "inside" ? "is-drop-inside" : "is-drop-after");
      }
    }
  }

  function clearSelection() {
    if (!window.getSelection) return;
    var selection = window.getSelection();
    if (selection) selection.removeAllRanges();
  }

  function handleContextAction(actionName) {
    if (!contextMenuEnabled() || !currentContextMenuDoc()) return;
    if (callbacks.onContextAction) callbacks.onContextAction(actionName);
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

    nav.addEventListener("mousedown", function (event) {
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

    nav.addEventListener("dragstart", function (event) {
      var dragHandle = event.target.closest("[data-drag-doc-id]");
      if (!dragHandle || !dragEnabled()) return;
      hideContextMenu();
      dragDocId = dragHandle.dataset.dragDocId || "";
      dropTargetDocId = "";
      dropPosition = "";
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", dragDocId);
      }
      updateNavDragState();
    });

    nav.addEventListener("dragover", function (event) {
      var row = event.target.closest("[data-doc-row-id]");
      if (!row) {
        if (dropTargetDocId || dropPosition) {
          dropTargetDocId = "";
          dropPosition = "";
          updateNavDragState();
        }
        return;
      }

      var targetDocId = row.dataset.docRowId || "";
      var dropOptions = dragDropOptions();
      var nextPosition = rowDropPosition(row, event, dropOptions);
      if (!canDropOnDoc(targetDocId, nextPosition, dropOptions)) {
        if (dropTargetDocId || dropPosition) {
          dropTargetDocId = "";
          dropPosition = "";
          updateNavDragState();
        }
        return;
      }

      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = "move";
      }
      if (dropTargetDocId !== targetDocId || dropPosition !== nextPosition) {
        dropTargetDocId = targetDocId;
        dropPosition = nextPosition;
        updateNavDragState();
      }
    });

    nav.addEventListener("drop", function (event) {
      event.preventDefault();
      var dropOptions = dragDropOptions();
      var dropTarget = currentDropTargetFromEvent(event, {
        targetDocId: dropTargetDocId,
        position: dropPosition
      }, dropOptions);
      var targetDocId = dropTarget.targetDocId;
      var position = dropTarget.position;
      if ((!targetDocId || !position) && dropTargetDocId && dropPosition) {
        targetDocId = dropTargetDocId;
        position = dropPosition;
      }
      if (!canDropOnDoc(targetDocId, position, dropOptions) || !position) {
        clearDragState();
        return;
      }
      var movingDocId = dragDocId;
      clearDragState();
      if (callbacks.onMoveDoc) callbacks.onMoveDoc(movingDocId, targetDocId, position);
    });

    nav.addEventListener("dragend", function () {
      clearDragState();
    });
  }

  function wireContextMenuEvents() {
    if (!contextMenu) return;
    contextMenu.addEventListener("click", function (event) {
      var action = event.target.closest("[data-context-action]");
      if (!action) return;
      event.preventDefault();
      handleContextAction(action.dataset.contextAction);
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
