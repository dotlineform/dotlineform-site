import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { createDocsViewerEditMenuItem } from "./docs-viewer-management-edit-menu.js";
import { mountDocsViewerPaginationControl } from "./docs-viewer-pagination-control.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  createDocsViewerCollectionSelectionOwner
} from "./docs-viewer-collection-selection.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function documentId(documentRecord) {
  return cleanString(documentRecord && documentRecord.doc_id);
}

function writeClipboardText(documentRef, text) {
  var windowRef = documentRef && documentRef.defaultView;
  if (
    windowRef
    && windowRef.navigator
    && windowRef.navigator.clipboard
    && windowRef.isSecureContext
  ) {
    return windowRef.navigator.clipboard.writeText(text);
  }
  return new Promise(function (resolve, reject) {
    var textarea = documentRef.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    textarea.style.left = "-1000px";
    documentRef.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
      if (!documentRef.execCommand("copy")) {
        throw new Error("Copy Link failed.");
      }
      resolve();
    } catch (error) {
      reject(error);
    } finally {
      textarea.remove();
    }
  });
}

/**
 * Creates the manage-only contribution for the shared collection report.
 *
 * The shared report owns collection identity and navigation. This contribution
 * only projects compact manifest row state and receives explicit lifecycle
 * events; it does not infer targets or load workflows.
 *
 * @param {Object} options
 * @returns {Object}
 */
export function createDocsViewerManagementCollectionDefaultContribution(options = {}) {
  var menuActions = [
    {
      id: DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS, label: "Export…",
      requiresSelection: true,
      buttonId: "docsViewerCollectionExportButton", artwork: "docsViewer__icon--square-arrow-right-exit",
      invoke: options.onExport, unavailableReason: "Collection Export is unavailable."
    },
    {
      id: DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE, label: "Prepare package…",
      requiresSelection: true,
      buttonId: "docsViewerCollectionPreparePackageButton", artwork: "docsViewer__icon--package",
      invoke: options.onPreparePackage, unavailableReason: "Collection package preparation is unavailable."
    },
    {
      id: DOCS_VIEWER_ACTION_IDS.IMPORT_DOC, label: "Import doc…",
      buttonId: "docsViewerCollectionImportDocButton", artwork: "docsViewer__icon--import",
      invoke: options.onImportDoc, unavailableReason: "Collection document import is unavailable."
    },
    {
      id: DOCS_VIEWER_ACTION_IDS.IMPORT, label: "Import docs…",
      buttonId: "docsViewerCollectionImportButton", artwork: "docsViewer__icon--package",
      invoke: options.onImport, unavailableReason: "Collection import is unavailable."
    }
  ];
  var onRegenerateCatalogue = typeof options.onRegenerateCatalogue === "function"
    ? options.onRegenerateCatalogue
    : null;
  var markdownLinkForDocument = typeof options.markdownLinkForDocument === "function"
    ? options.markdownLinkForDocument
    : null;
  var managementContext = Boolean(options.managementContext);
  var selectionOwner = options.selectionOwner || createDocsViewerCollectionSelectionOwner();
  var currentDocIds = [];
  var inventoryDocIds = [];
  var listToolbar = null;
  var selectionWorkflowActive = false;
  var rowSelections = new Map();
  var activeDeleteWorkflow = null;
  var deleteWorkflowRequest = 0;

  function selectionResolution(actionId) {
    return options.resolveAction(actionId, {
      ...selectionOwner.collection(), doc_ids: selectionOwner.selectedDocIds()
    });
  }

  function eligibleDocIds() {
    return currentDocIds;
  }

  function reportRoot() {
    if (listToolbar && listToolbar.root) {
      return listToolbar.root.closest(".docsViewerReport, [data-report-collection]");
    }
    for (var record of rowSelections.values()) {
      var root = record.host.closest(".docsViewerReport, [data-report-collection]");
      if (root) return root;
    }
    return null;
  }

  function hideActionsMenu(focusButton) {
    if (!listToolbar) return;
    listToolbar.menu.hidden = true;
    listToolbar.actionsButton.setAttribute("aria-expanded", "false");
    if (focusButton && typeof listToolbar.actionsButton.focus === "function") {
      listToolbar.actionsButton.focus();
    }
  }

  function projectSelection() {
    var snapshot = selectionOwner.snapshot();
    var available = selectionOwner.available();
    var resolutions = menuActions.map(function (action) { return selectionResolution(action.id); });
    var hidden = resolutions.every(function (resolution) { return resolution.hidden; });
    var active = available && snapshot.selectionModeActive && !hidden;
    var eligible = eligibleDocIds();
    var selected = new Set(snapshot.selectedDocIds);
    var allSelected = eligible.length > 0 && eligible.every(function (docId) {
      return selected.has(docId);
    });
    rowSelections.forEach(function (record, docId) {
      record.host.hidden = !active;
      record.checkbox.checked = selected.has(docId);
      record.checkbox.disabled = !active;
    });
    var root = reportRoot();
    if (root) root.dataset.reportCollectionSelection = active ? "active" : "inactive";
    if (!listToolbar) return snapshot;

    listToolbar.actionsHost.hidden = hidden;
    listToolbar.actionsButton.disabled = !available || hidden || selectionWorkflowActive;
    listToolbar.selectButton.hidden = hidden || active;
    listToolbar.selectButton.disabled = !available || selectionWorkflowActive;
    listToolbar.selectionControl.hidden = !active;
    listToolbar.selectAllButton.disabled = !active || allSelected || eligible.length === 0;
    listToolbar.clearButton.disabled = !active || selected.size === 0;
    listToolbar.doneButton.disabled = !active;

    listToolbar.menuActions.forEach(function (action, index) {
      var resolution = resolutions[index];
      var disabledReason = typeof action.invoke !== "function" ? action.unavailableReason : resolution.disabledReason;
      var accessibleLabel = disabledReason ? action.label + " " + disabledReason : action.label;
      action.button.hidden = resolution.hidden;
      action.button.disabled = selectionWorkflowActive || Boolean(disabledReason);
      action.button.title = accessibleLabel;
      action.button.setAttribute("aria-label", accessibleLabel);
      if (disabledReason) action.button.dataset.docsViewerDisabledReason = disabledReason;
      else delete action.button.dataset.docsViewerDisabledReason;
    });
    return snapshot;
  }

  function clearListToolbar() {
    if (!listToolbar) return;
    listToolbar.document.removeEventListener("click", listToolbar.handleDocumentClick);
    listToolbar.document.removeEventListener("keydown", listToolbar.handleDocumentKeydown);
    listToolbar = null;
  }

  function clearDeleteWorkflow() {
    deleteWorkflowRequest += 1;
    if (activeDeleteWorkflow && typeof activeDeleteWorkflow.destroy === "function") {
      activeDeleteWorkflow.destroy();
    }
    activeDeleteWorkflow = null;
  }

  function notify(event) {
    selectionOwner.notify(event, {
      managementContext: managementContext
    });
    if (event && event.type === "refresh") inventoryDocIds = event.docIds;
    if (event && event.type === "projection") {
      currentDocIds = event.docIds;
    }
    if (
      event
      && (
        event.type === "unmount"
        || (event.type === "state" && cleanString(event.state) !== "detail")
      )
    ) {
      clearDeleteWorkflow();
    }
    if (event && event.type === "state" && cleanString(event.state) !== "list") {
      hideActionsMenu(false);
    }
    if (event && event.type === "unmount") {
      clearListToolbar();
      rowSelections.clear();
      currentDocIds = []; inventoryDocIds = [];
    }
    projectSelection();
  }

  function renderRow(context) {
    var settings = context || {};
    var doc = settings.document || {};
    var host = settings.titlePrefixHost;
    var leadingHost = settings.leadingHost;
    var accessibleLabels = [];
    var docId = documentId(doc);
    if (leadingHost && docId) {
      var checkbox = leadingHost.ownerDocument.createElement("input");
      checkbox.className = "docsViewerReport__collectionSelectionCheckbox";
      checkbox.type = "checkbox";
      checkbox.dataset.docsCollectionSelectionCheckbox = docId;
      checkbox.setAttribute("aria-label", "Select " + (cleanString(doc.title) || docId));
      checkbox.addEventListener("click", function (event) {
        event.stopPropagation();
        if (!selectionOwner.available() || !selectionOwner.snapshot().selectionModeActive) return;
        if (event.shiftKey) {
          selectionOwner.selectRange(docId, eligibleDocIds());
        } else {
          selectionOwner.toggle(docId, checkbox.checked);
        }
        projectSelection();
      });
      leadingHost.classList.add("docsViewerReport__collectionSelectionGutter");
      leadingHost.hidden = true;
      leadingHost.appendChild(checkbox);
      rowSelections.set(docId, {
        checkbox: checkbox,
        host: leadingHost
      });
    }
    if (doc.draft === true) {
      var draftIcon = host.ownerDocument.createElement("span");
      draftIcon.className = "docsViewer__listIcon docsViewer__draftIndicator docsViewer__icon--circle-dashed-check";
      draftIcon.setAttribute("aria-hidden", "true");
      host.appendChild(draftIcon);
      accessibleLabels.push("Draft");
    }
    return { accessibleLabels: accessibleLabels };
  }

  function selectionCommandButton(documentRef, command, label) {
    var button = documentRef.createElement("button");
    button.className = "docsViewerReport__collectionSelectionButton";
    button.type = "button";
    button.dataset.docsCollectionSelectionCommand = command;
    button.textContent = label;
    return button;
  }

  function renderListToolbar(context) {
    var settings = context || {};
    var host = settings.host;
    if (!host || !settings.actionHost) return;
    clearListToolbar();
    rowSelections.clear();
    currentDocIds = settings.docIds;
    selectionOwner.syncContext({
      collection: settings.collection,
      managementContext: managementContext,
      mounted: true
    });

    var documentRef = host.ownerDocument;
    var root = documentRef.createElement("div");
    root.className = "docsViewerReport__collectionSelectionToolbar";

    var sortButton = null;
    if (settings.sort && typeof settings.sort.setMode === "function") {
      sortButton = documentRef.createElement("button");
      sortButton.className = "docsViewer__toolbarIconButton docsViewerReport__collectionSortButton";
      sortButton.type = "button";
      sortButton.dataset.docsCollectionSort = cleanString(settings.sort.mode);
      var titleMode = cleanString(settings.sort.mode) !== "last-updated-desc";
      sortButton.appendChild(createDocsViewerToolbarIcon(documentRef,
        titleMode ? "docsViewer__icon--arrow-down-a-z" : "docsViewer__icon--clock-3"));
      sortButton.setAttribute(
        "aria-label",
        titleMode
          ? "Sorted by title. Switch to recently updated."
          : "Sorted by recently updated. Switch to title."
      );
      sortButton.title = sortButton.getAttribute("aria-label");
      sortButton.addEventListener("click", function () {
        settings.sort.setMode(titleMode ? "last-updated-desc" : "title-asc");
      });
    }

    var regenerateButton = null;
    if (managementContext && onRegenerateCatalogue) {
      regenerateButton = documentRef.createElement("button");
      regenerateButton.type = "button";
      regenerateButton.className = "docsViewer__toolbarIconButton";
      regenerateButton.dataset.docsCollectionRegenerate = "true";
      regenerateButton.title = "Regenerate";
      regenerateButton.setAttribute("aria-label", "Regenerate");
      regenerateButton.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--refresh-cw"));
      var regenerateAction = settings.registerAction({
        id: "catalogue-regenerate", placement: "list-toolbar", targetKind: "collection",
        capability: true, emptyState: "enabled", refreshEffect: "collection",
        handler: function (target) {
          return onRegenerateCatalogue(target, {
            refreshCollection: settings.refreshCollection, restoreFocus: regenerateButton
          });
        }
      });
      regenerateButton.addEventListener("click", function () {
        if (regenerateButton.disabled) return;
        regenerateButton.disabled = true;
        regenerateButton.setAttribute("aria-busy", "true");
        regenerateAction.invoke().catch(function (error) {
          if (typeof options.setStatus === "function") options.setStatus(error.message, true);
        }).finally(function () {
          regenerateButton.disabled = false;
          regenerateButton.removeAttribute("aria-busy");
        });
      });
    }

    var selectButton = documentRef.createElement("button");
    selectButton.className = "docsViewer__toolbarIconButton";
    selectButton.type = "button";
    selectButton.dataset.docsCollectionSelect = "true";
    selectButton.setAttribute("aria-label", "Select");
    selectButton.title = "Select";
    selectButton.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--list-check"));

    var actionsHost = documentRef.createElement("div");
    actionsHost.className = "docsViewer__actionsMenuHost docsViewerReport__collectionActionsHost";
    var actionsButton = documentRef.createElement("button");
    actionsButton.className = "docsViewer__toolbarIconButton";
    actionsButton.type = "button";
    actionsButton.dataset.docsCollectionActions = "true";
    actionsButton.setAttribute("aria-haspopup", "menu");
    actionsButton.setAttribute("aria-expanded", "false");
    actionsButton.setAttribute("aria-label", "Actions");
    actionsButton.title = "Actions";
    actionsButton.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--wrench"));
    var menu = documentRef.createElement("div");
    menu.className = "docsViewer__actionsMenu docsViewerReport__collectionActionsMenu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    var renderedActions = menuActions.map(function (action) {
      var button = createDocsViewerEditMenuItem(documentRef, {
        actionId: action.id, label: action.label, artwork: action.artwork
      });
      button.id = action.buttonId;
      return { ...action, button: button };
    });
    menu.replaceChildren(...renderedActions.map(function (action) { return action.button; }));
    actionsHost.replaceChildren(actionsButton, menu);

    var selectionControl = documentRef.createElement("div");
    selectionControl.className = "docsViewerReport__collectionSelectionControl";
    selectionControl.setAttribute("role", "group");
    selectionControl.setAttribute("aria-label", "Collection selection");
    var selectAllButton = selectionCommandButton(documentRef, "select-all", "All");
    var clearButton = selectionCommandButton(documentRef, "clear", "Clear");
    var doneButton = selectionCommandButton(documentRef, "done", "Done");
    selectionControl.replaceChildren(selectAllButton, clearButton, doneButton);
    settings.actionHost.replaceChildren(...(regenerateButton ? [regenerateButton] : []));
    if (sortButton) root.appendChild(sortButton);
    root.appendChild(selectButton);
    root.appendChild(selectionControl);
    root.appendChild(actionsHost);
    host.appendChild(root);

    function handleDocumentClick(event) {
      if (!actionsHost.contains(event.target)) hideActionsMenu(false);
    }

    function handleDocumentKeydown(event) {
      if (event.key !== "Escape" || menu.hidden) return;
      event.preventDefault();
      hideActionsMenu(true);
    }

    listToolbar = {
      actionsButton: actionsButton,
      actionsHost: actionsHost,
      clearButton: clearButton,
      document: documentRef,
      doneButton: doneButton,
      handleDocumentClick: handleDocumentClick,
      handleDocumentKeydown: handleDocumentKeydown,
      menu: menu,
      menuActions: renderedActions,
      root: root,
      selectAllButton: selectAllButton,
      selectButton: selectButton,
      selectionControl: selectionControl
    };
    documentRef.addEventListener("click", handleDocumentClick);
    documentRef.addEventListener("keydown", handleDocumentKeydown);

    selectButton.addEventListener("click", function () {
      if (selectButton.disabled) return;
      hideActionsMenu(false);
      selectionOwner.enter();
      projectSelection();
      (selectAllButton.disabled ? doneButton : selectAllButton).focus();
    });
    actionsButton.addEventListener("click", function (event) {
      event.stopPropagation();
      if (actionsButton.disabled) return;
      if (!menu.hidden) {
        hideActionsMenu(false);
        return;
      }
      projectSelection();
      menu.hidden = false;
      actionsButton.setAttribute("aria-expanded", "true");
    });
    function runMenuAction(action) {
      if (action.button.disabled) return;
      var resolution = selectionResolution(action.id);
      if (!resolution.enabled) return;
      hideActionsMenu(true);
      selectionWorkflowActive = true;
      projectSelection();
      var definition = {
        id: action.id,
        placement: action.requiresSelection ? "selection" : "list-toolbar",
        targetKind: action.requiresSelection ? "selection" : "collection",
        capability: true,
        emptyState: action.requiresSelection ? "disabled" : "enabled",
        refreshEffect: "none",
        handler: function (target) {
          return action.invoke(target, { restoreFocus: actionsButton });
        }
      };
      var registration = action.requiresSelection ? settings.registerSelectionAction(definition, {
        active: selectionOwner.snapshot().selectionModeActive,
        checkedDocIds: resolution.targetDocIds,
        eligibleDocIds: eligibleDocIds()
      }) : settings.registerAction(definition);
      var request = registration.invoke();
      Promise.resolve(request).catch(function (error) {
        if (typeof options.setStatus === "function") {
          options.setStatus(
            error && error.message
              ? error.message
              : "Collection action failed.",
            true
          );
        }
      }).finally(function () {
        selectionWorkflowActive = false;
        projectSelection();
      });
    }
    renderedActions.forEach(function (action) {
      action.button.addEventListener("click", function () { runMenuAction(action); });
    });
    selectAllButton.addEventListener("click", function () {
      selectionOwner.selectAll(eligibleDocIds());
      projectSelection();
    });
    clearButton.addEventListener("click", function () {
      selectionOwner.clear();
      projectSelection();
    });
    doneButton.addEventListener("click", function () {
      selectionOwner.done();
      hideActionsMenu(false);
      projectSelection();
      selectButton.focus();
    });
    projectSelection();
  }

  function renderDetailToolbar(context) {
    var settings = context || {};
    var host = settings.host;
    var target = settings.target;
    if (!host || !target) return;

    var copyResolution = options.resolveAction(DOCS_VIEWER_ACTION_IDS.COPY_LINK, target);
    if (!copyResolution.hidden && markdownLinkForDocument && typeof settings.registerAction === "function") {
      var copyRegistration = settings.registerAction({
        id: DOCS_VIEWER_ACTION_IDS.COPY_LINK,
        placement: "detail-toolbar",
        targetKind: "validated-detail",
        capability: true,
        emptyState: "omitted",
        refreshEffect: "none",
        handler: function (actionTarget) {
          var resolution = options.resolveAction(DOCS_VIEWER_ACTION_IDS.COPY_LINK, actionTarget);
          if (resolution.disabled) throw new Error(resolution.disabledReason);
          var markdownLink = markdownLinkForDocument(
            actionTarget,
            settings.document || {}
          );
          if (!cleanString(markdownLink)) {
            throw new Error("Copy Link could not resolve an exact document URL.");
          }
          return writeClipboardText(host.ownerDocument, markdownLink);
        }
      });
      var copyButton = createDocsViewerEditMenuItem(host.ownerDocument, {
        actionId: DOCS_VIEWER_ACTION_IDS.COPY_LINK, label: "Copy link",
        artwork: "docsViewer__icon--link", contribution: true
      });
      copyButton.dataset.docsCollectionCopyLink = "true";
      copyButton.setAttribute("aria-label", "Copy link");
      copyButton.title = "Copy link";
      copyButton.disabled = !copyRegistration.enabled;
      copyButton.addEventListener("click", function () {
        copyRegistration.invoke().catch(function (error) {
          if (typeof options.setStatus === "function") {
            options.setStatus(
              error && error.message ? error.message : "Copy Link failed.",
              true
            );
          }
        });
      });
      host.appendChild(copyButton);
    }

    var deleteResolution = options.resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE, target);
    if (
      !managementContext
      || deleteResolution.hidden
      || typeof settings.commitDeletedDocument !== "function"
      || typeof settings.registerAction !== "function"
    ) return;
    var deleteRegistration = settings.registerAction({
      id: DOCS_VIEWER_ACTION_IDS.DELETE,
      placement: "detail-toolbar",
      targetKind: "validated-detail",
      capability: { available: deleteResolution.enabled, reason: deleteResolution.disabledReason },
      emptyState: "omitted",
      refreshEffect: "commit-deleted-document",
      handler: function (actionTarget) {
        return actionTarget;
      }
    });
    if (deleteRegistration.hidden || !deleteRegistration.target) return;

    clearDeleteWorkflow();
    var request = deleteWorkflowRequest;
    var button = createDocsViewerEditMenuItem(host.ownerDocument, {
      actionId: DOCS_VIEWER_ACTION_IDS.DELETE, label: "Delete",
      artwork: "docsViewer__icon--trash", contribution: true
    });
    button.disabled = true;
    button.dataset.docsCollectionDelete = "true";
    button.setAttribute("aria-label", "Delete");
    button.title = "Delete";
    host.appendChild(button);

    import("./docs-viewer-management-collection-delete-workflow.js")
      .then(function (module) {
        if (request !== deleteWorkflowRequest || !button.isConnected) return;
        activeDeleteWorkflow = module.createDocsViewerManagementCollectionDeleteWorkflow({
          resolveAction: options.resolveAction,
          startBusyOperation: options.startBusyOperation,
          commitDocumentChange: options.commitDocumentChange,
          button: button,
          clientOptions: options.clientOptions || {},
          commitDeletedDocument: settings.commitDeletedDocument,
          root: options.root,
          restoreFocus: function () { return options.root?.querySelector("#docsViewerManageEditButton"); },
          setStatus: options.setStatus,
          target: deleteRegistration.target,
          title: cleanString(settings.document && settings.document.title)
            || cleanString(deleteRegistration.target.doc_id)
        });
        return activeDeleteWorkflow.initialize();
      })
      .catch(function (error) {
        if (request !== deleteWorkflowRequest || !button.isConnected) return;
        button.disabled = true;
        button.title = "Collection detail Delete is unavailable.";
        if (typeof options.setStatus === "function") {
          options.setStatus(
            error && error.message ? error.message : "Collection detail Delete is unavailable.",
            true
          );
        }
      });
  }

  return {
    ...(options.paginationToggle ? {
      paginationDefault: false,
      resetSelection: selectionOwner.done,
      mountPaginationControl: function ({ host, change }) {
        return mountDocsViewerPaginationControl({ host, enabled: false, itemsLabel: "documents", change });
      }
    } : {}),
    captureListState: selectionOwner.snapshot,
    restoreListState: function (saved) { selectionOwner.restore(saved, inventoryDocIds); },
    id: "default",
    notify: notify,
    renderDetailToolbar: renderDetailToolbar,
    renderListToolbar: renderListToolbar,
    renderRow: renderRow
  };
}
