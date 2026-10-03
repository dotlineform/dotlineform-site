export function createDocsViewerManagementInteractionController(options) {
  var nav = options.nav;
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var routeSession = options.routeSession || {};
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};
  var contextMenu = refs.contextMenu || document.getElementById("docsViewerContextMenu");
  var contextMenuDocId = "";
  var contextMenuRow = null;
  var contextMenuRestoreFocus = null;
  var suppressNextClick = false;
  var lastEditRequestDocId = "";
  var lastEditRequestTime = 0;

  function contextMenuEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !nav.closest("[hidden]");
  }

  function editFromIndexEnabled() {
    return routeSession.managementContext && management.managementAvailable && !management.managementBusy && !nav.hidden;
  }

  function currentContextMenuDoc() {
    return documentIndex.docsById.get(contextMenuDocId) || null;
  }

  function hideContextMenu(options = {}) {
    var restoreFocus = contextMenuRestoreFocus;
    if (contextMenuRow) contextMenuRow.classList.remove("is-context-target");
    contextMenuRow = null;
    contextMenuRestoreFocus = null;
    contextMenuDocId = "";
    if (contextMenu) {
      contextMenu.hidden = true;
      contextMenu.style.left = "";
      contextMenu.style.top = "";
    }
    var focusTarget = options.restoreFocus && restoreFocus ? restoreFocus() : null;
    if (focusTarget) {
      focusTarget.focus({ preventScroll: true });
    }
  }

  function renderContextMenu() {
    if (!contextMenu || contextMenu.hidden) return;
    var doc = currentContextMenuDoc();
    if (!doc || !contextMenuEnabled() || !contextMenuRow || !contextMenuRow.isConnected) {
      hideContextMenu();
      return;
    }
    var states = callbacks.contextActionStates(doc.doc_id);
    contextMenu.setAttribute("aria-label", "Index actions for " + doc.title + " (" + doc.doc_id + ")");
    contextMenu.querySelectorAll("[data-docs-viewer-action]").forEach(function (button) {
      var state = states[button.dataset.docsViewerAction] || {};
      var reason = String(state.disabledReason || "");
      button.disabled = Boolean(state.disabled);
      button.hidden = Boolean(state.hidden);
      button.title = reason;
      button.setAttribute("aria-label", button.textContent + (reason ? ". " + reason : ""));
    });
  }

  function menuItems() {
    return Array.from(contextMenu.querySelectorAll("[data-docs-viewer-action]")).filter(function (button) {
      return !button.disabled && !button.hidden;
    });
  }

  function showContextMenu(row, clientX, clientY) {
    var docId = row.dataset.docRowId || "";
    if (!contextMenu || !contextMenuEnabled() || !documentIndex.docsById.has(docId)) return;
    hideContextMenu();
    contextMenuDocId = docId;
    contextMenuRow = row;
    var originalLink = row.querySelector("[data-doc-id]");
    contextMenuRestoreFocus = function () {
      if (originalLink && originalLink.isConnected && originalLink.getClientRects().length) return originalLink;
      var targetLink = Array.from(nav.querySelectorAll("[data-doc-id]")).find(function (link) {
        return link.dataset.docId === docId && link.getClientRects().length;
      });
      return targetLink || nav.querySelector('[aria-current="page"]');
    };
    row.classList.add("is-context-target");
    contextMenu.hidden = false;
    renderContextMenu();
    contextMenu.style.left = "0px";
    contextMenu.style.top = "0px";
    var menuRect = contextMenu.getBoundingClientRect();
    var maxLeft = Math.max(8, window.innerWidth - menuRect.width - 8);
    var maxTop = Math.max(8, window.innerHeight - menuRect.height - 8);
    contextMenu.style.left = Math.max(8, Math.min(clientX, maxLeft)) + "px";
    contextMenu.style.top = Math.max(8, Math.min(clientY, maxTop)) + "px";
    var firstItem = menuItems()[0];
    if (firstItem) firstItem.focus({ preventScroll: true });
  }

  function clearSelection() {
    if (!window.getSelection) return;
    var selection = window.getSelection();
    if (selection) selection.removeAllRanges();
  }

  function handleContextAction(actionId) {
    if (!contextMenuEnabled() || !currentContextMenuDoc()) return;
    var targetDocId = contextMenuDocId;
    var restoreFocus = contextMenuRestoreFocus;
    hideContextMenu({ restoreFocus: true });
    if (callbacks.onContextAction) callbacks.onContextAction(actionId, targetDocId, restoreFocus);
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

  function handleRootClick(event) {
    if (contextMenu && !event.target.closest("#docsViewerContextMenu")) {
      hideContextMenu();
    }
    return false;
  }

  function handleDocumentKeydown(event) {
    if (!contextMenu || contextMenu.hidden) return false;
    if (event.key === "Escape") {
      event.preventDefault();
      hideContextMenu({ restoreFocus: true });
      return true;
    }
    if (!contextMenu.contains(event.target)) return false;
    if (event.key === "Tab") {
      hideContextMenu({ restoreFocus: true });
      return true;
    }
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      var items = menuItems();
      if (!items.length) return true;
      var index = items.indexOf(document.activeElement);
      var next = event.key === "Home" ? 0 : event.key === "End" ? items.length - 1
        : (index + (event.key === "ArrowUp" ? -1 : 1) + items.length) % items.length;
      items[next].focus({ preventScroll: true });
      return true;
    }
    return false;
  }

  function wireNavEvents() {
    if (!nav) return;

    nav.addEventListener("click", function (event) {
      if (event.detail >= 2 && !event.target.closest("[data-toggle-doc-id]")) {
        if (editFromIndexEnabled() && documentIndex.docsById.has(event.target.closest("[data-doc-row-id]")?.dataset.docRowId)) {
          suppressNextClick = false;
          event.preventDefault();
          event.stopPropagation();
          requestEditDoc(event.target.closest("[data-doc-row-id]").dataset.docRowId);
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
        if (editFromIndexEnabled() && documentIndex.docsById.has(event.target.closest("[data-doc-row-id]")?.dataset.docRowId)) {
          suppressNextClick = true;
          event.preventDefault();
          event.stopPropagation();
          requestEditDoc(event.target.closest("[data-doc-row-id]").dataset.docRowId);
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
      showContextMenu(row, event.clientX, event.clientY);
    });

    nav.addEventListener("keydown", function (event) {
      if (event.key !== "ContextMenu" && !(event.shiftKey && event.key === "F10")) return;
      var row = event.target.closest("[data-doc-row-id]");
      if (!row || !contextMenuEnabled()) return;
      event.preventDefault();
      var bounds = row.getBoundingClientRect();
      showContextMenu(row, bounds.left, bounds.bottom);
    });

    nav.addEventListener("dblclick", function (event) {
      if (event.target.closest("[data-toggle-doc-id]")) return;
      var row = event.target.closest("[data-doc-row-id]");
      if (!row || !editFromIndexEnabled()) return;
      if (!documentIndex.docsById.has(event.target.closest("[data-doc-row-id]")?.dataset.docRowId)) return;
      event.preventDefault();
      requestEditDoc(row.dataset.docRowId);
    });

  }

  function wireContextMenuEvents() {
    if (!contextMenu) return;
    contextMenu.querySelectorAll("[data-docs-viewer-action]").forEach(function (button) {
      button.setAttribute("role", "menuitem");
      button.tabIndex = -1;
    });
    contextMenu.addEventListener("click", function (event) {
      var action = event.target.closest("[data-docs-viewer-action]");
      if (!action || action.disabled || action.hidden) return;
      event.preventDefault();
      handleContextAction(action.dataset.docsViewerAction);
    });
  }

  function wireEvents() {
    wireNavEvents();
    wireContextMenuEvents();
  }

  return {
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideContextMenu: hideContextMenu,
    render: renderContextMenu,
    wireEvents: wireEvents
  };
}
