import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

import {
  DOCS_VIEWER_ACTION_IDS,
  createDocsViewerActionContext,
  resolveDocsViewerAction
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

function documentIds(documents) {
  var seen = new Set();
  return (Array.isArray(documents) ? documents : []).map(documentId).filter(function (docId) {
    if (!docId || seen.has(docId)) return false;
    seen.add(docId);
    return true;
  });
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
  var onPreparePackage = typeof options.onPreparePackage === "function"
    ? options.onPreparePackage
    : null;
  var onToggleDraft = typeof options.onToggleDraft === "function"
    ? options.onToggleDraft
    : null;
  var onCreateDocument = typeof options.onCreateDocument === "function"
    ? options.onCreateDocument
    : null;
  var onRegenerateCatalogue = typeof options.onRegenerateCatalogue === "function"
    ? options.onRegenerateCatalogue
    : null;
  var markdownLinkForDocument = typeof options.markdownLinkForDocument === "function"
    ? options.markdownLinkForDocument
    : null;
  var managementContext = Boolean(options.managementContext);
  var selectionOwner = options.selectionOwner || createDocsViewerCollectionSelectionOwner();
  var currentDocuments = [];
  var listToolbar = null;
  var createInFlight = false;
  var prepareInFlight = false;
  var rowSelections = new Map();
  var activeDeleteWorkflow = null;
  var deleteWorkflowRequest = 0;
  var publishSelection = null;

  function prepareResolution() {
    return resolveDocsViewerAction(
      DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE,
      createDocsViewerActionContext({
        selectedDocIds: selectionOwner.selectedDocIds()
      })
    );
  }

  function eligibleDocIds() {
    return documentIds(currentDocuments);
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
    var active = available && snapshot.selectionModeActive;
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
    var contributionSnapshot = {
      active: active,
      checkedDocIds: snapshot.selectedDocIds.slice(),
      eligibleDocIds: eligible.slice()
    };
    if (publishSelection) {
      publishSelection(contributionSnapshot, "selection-projected");
    }
    if (!listToolbar) return snapshot;

    if (listToolbar.createButton) {
      listToolbar.createButton.disabled = createInFlight;
      if (createInFlight) {
        listToolbar.createButton.setAttribute("aria-busy", "true");
      } else {
        listToolbar.createButton.removeAttribute("aria-busy");
      }
    }
    listToolbar.actionsButton.disabled = !available;
    listToolbar.selectionControl.hidden = !active;
    listToolbar.selectAllButton.disabled = !active || allSelected || eligible.length === 0;
    listToolbar.clearButton.disabled = !active || selected.size === 0;
    listToolbar.doneButton.disabled = !active;

    var resolution = prepareResolution();
    var disabledReason = !onPreparePackage
      ? "Collection package preparation is unavailable."
      : !resolution.enabled
        ? resolution.disabledReason
        : prepareInFlight ? "Collection package preparation is in progress." : "";
    var label = "Prepare package…";
    var accessibleLabel = disabledReason ? label + " " + disabledReason : label;
    listToolbar.prepareButton.disabled = Boolean(disabledReason);
    listToolbar.prepareButton.title = accessibleLabel;
    listToolbar.prepareButton.setAttribute("aria-label", accessibleLabel);
    if (disabledReason) {
      listToolbar.prepareButton.dataset.docsViewerDisabledReason = disabledReason;
    } else {
      delete listToolbar.prepareButton.dataset.docsViewerDisabledReason;
    }
    return snapshot;
  }

  function clearListToolbar() {
    if (!listToolbar) return;
    listToolbar.document.removeEventListener("click", listToolbar.handleDocumentClick);
    listToolbar.document.removeEventListener("keydown", listToolbar.handleDocumentKeydown);
    listToolbar = null;
    publishSelection = null;
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
    if (event && (event.type === "refresh" || event.type === "projection")) {
      currentDocuments = Array.isArray(event.documents) ? event.documents.slice() : [];
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
    currentDocuments = Array.isArray(settings.documents) ? settings.documents.slice() : [];
    publishSelection = typeof settings.publishSelection === "function"
      ? settings.publishSelection
      : null;
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

    var createButton = null;
    var createRegistration = null;
    if (managementContext && onCreateDocument) {
      createButton = documentRef.createElement("button");
      createButton.className = (
        "docsViewer__toolbarIconButton "
        + "docsViewerReport__collectionNewButton"
      );
      createButton.type = "button";
      createButton.dataset.docsCollectionNew = "true";
      createButton.setAttribute("aria-label", "New");
      createButton.title = "New";
      createButton.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--file"));
      if (typeof settings.registerAction === "function") {
        createRegistration = settings.registerAction({
          id: DOCS_VIEWER_ACTION_IDS.NEW,
          placement: "list-toolbar",
          targetKind: "collection",
          capability: true,
          emptyState: "enabled",
          refreshEffect: "open-created-document",
          handler: function (target) {
            return onCreateDocument(target, {
              refreshAndOpenDocument: settings.refreshAndOpenDocument,
              restoreFocus: createButton
            });
          }
        });
      }
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

    var actionsHost = documentRef.createElement("div");
    actionsHost.className = "docsViewer__actionsMenuHost docsViewerReport__collectionActionsHost";
    actionsHost.hidden = selectionOwner.collection().stage !== "working";
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
    var prepareButton = documentRef.createElement("button");
    prepareButton.className = "docsViewer__actionMenuItem";
    prepareButton.type = "button";
    prepareButton.id = "docsViewerCollectionPreparePackageButton";
    prepareButton.setAttribute("role", "menuitem");
    prepareButton.dataset.docsViewerAction = DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE;
    var prepareIcon = createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--package");
    var prepareLabel = documentRef.createElement("span");
    prepareLabel.className = "docsViewer__actionMenuLabel";
    prepareLabel.textContent = "Prepare package…";
    prepareButton.replaceChildren(prepareIcon, prepareLabel);
    menu.replaceChildren(prepareButton);
    actionsHost.replaceChildren(actionsButton, menu);

    var selectionControl = documentRef.createElement("div");
    selectionControl.className = "docsViewerReport__collectionSelectionControl";
    selectionControl.setAttribute("role", "group");
    selectionControl.setAttribute("aria-label", "Collection selection");
    var selectAllButton = selectionCommandButton(documentRef, "select-all", "All");
    var clearButton = selectionCommandButton(documentRef, "clear", "Clear");
    var doneButton = selectionCommandButton(documentRef, "done", "Done");
    selectionControl.replaceChildren(selectAllButton, clearButton, doneButton);
    settings.actionHost.replaceChildren.apply(
      settings.actionHost,
      (createButton ? [createButton] : [])
        .concat(regenerateButton ? [regenerateButton] : [])
        .concat([actionsHost])
    );
    if (sortButton) root.appendChild(sortButton);
    root.appendChild(selectionControl);
    host.appendChild(root);

    function handleDocumentClick(event) {
      if (!settings.actionHost.contains(event.target)) hideActionsMenu(false);
    }

    function handleDocumentKeydown(event) {
      if (event.key !== "Escape" || menu.hidden) return;
      event.preventDefault();
      hideActionsMenu(true);
    }

    listToolbar = {
      actionsButton: actionsButton,
      clearButton: clearButton,
      createButton: createButton,
      document: documentRef,
      doneButton: doneButton,
      handleDocumentClick: handleDocumentClick,
      handleDocumentKeydown: handleDocumentKeydown,
      menu: menu,
      prepareButton: prepareButton,
      root: root,
      selectAllButton: selectAllButton,
      selectionControl: selectionControl
    };
    documentRef.addEventListener("click", handleDocumentClick);
    documentRef.addEventListener("keydown", handleDocumentKeydown);

    if (createButton) {
      createButton.addEventListener("click", function () {
        if (createButton.disabled || createInFlight) return;
        createInFlight = true;
        projectSelection();
        var createRequest = createRegistration.invoke();
        Promise.resolve(createRequest).catch(function (error) {
          if (typeof options.setStatus === "function") {
            options.setStatus(
              error && error.message
                ? error.message
                : "Collection document creation failed.",
              true
            );
          }
        }).finally(function () {
          createInFlight = false;
          projectSelection();
        });
      });
    }
    actionsButton.addEventListener("click", function (event) {
      event.stopPropagation();
      if (actionsButton.disabled) return;
      if (!menu.hidden) {
        hideActionsMenu(false);
        return;
      }
      if (!selectionOwner.snapshot().selectionModeActive) selectionOwner.enter();
      projectSelection();
      menu.hidden = false;
      actionsButton.setAttribute("aria-expanded", "true");
    });
    prepareButton.addEventListener("click", function () {
      if (prepareButton.disabled || !onPreparePackage) return;
      var resolution = prepareResolution();
      if (!resolution.enabled) return;
      hideActionsMenu(true);
      prepareInFlight = true;
      projectSelection();
      var prepareRequest = settings.registerSelectionAction({
        id: DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE,
        placement: "selection",
        targetKind: "selection",
        capability: Boolean(onPreparePackage),
        emptyState: "disabled",
        refreshEffect: "none",
        handler: function (target) {
          return onPreparePackage(target, { restoreFocus: actionsButton });
        }
      }, {
        active: selectionOwner.snapshot().selectionModeActive,
        checkedDocIds: resolution.targetDocIds,
        eligibleDocIds: eligibleDocIds()
      }).invoke();
      Promise.resolve(prepareRequest).catch(function (error) {
        if (typeof options.setStatus === "function") {
          options.setStatus(
            error && error.message
              ? error.message
              : "Collection package preparation failed.",
            true
          );
        }
      }).finally(function () {
        prepareInFlight = false;
        projectSelection();
      });
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
      hideActionsMenu(true);
      projectSelection();
    });
    projectSelection();
  }

  function renderDetailToolbar(context) {
    var settings = context || {};
    var host = settings.host;
    var target = settings.target;
    if (!host || !target) return;

    if (managementContext && target.stage === "working"
      && onToggleDraft && typeof settings.registerAction === "function"
      && typeof settings.commitDocumentDraft === "function") {
      var draft = settings.document?.draft === true;
      var draftRegistration = settings.registerAction({
        id: "set-draft",
        placement: "detail-toolbar",
        targetKind: "validated-detail",
        capability: true,
        emptyState: "omitted",
        refreshEffect: "none",
        handler: function (draftTarget) {
          return onToggleDraft(draftTarget, !draft);
        }
      });
      var draftButton = host.ownerDocument.createElement("button");
      draftButton.className = "docsViewer__toolbarIconButton";
      draftButton.type = "button";
      draftButton.dataset.docsCollectionDraft = "true";
      draftButton.title = draft ? "Draft — mark ready" : "Ready — mark as draft";
      draftButton.setAttribute("aria-label", draftButton.title);
      draftButton.setAttribute("aria-pressed", String(draft));
      draftButton.appendChild(createDocsViewerToolbarIcon(host.ownerDocument,
        draft ? "docsViewer__icon--circle-dashed-check" : "docsViewer__icon--circle-check"));
      draftButton.disabled = !draftRegistration.enabled;
      draftButton.addEventListener("click", function () {
        if (draftButton.disabled) return;
        draftButton.disabled = true;
        draftRegistration.invoke().then(function (response) {
          if (!response || response.ok !== true) return;
          settings.commitDocumentDraft(response.target, response.record.draft);
          draft = response.record.draft;
          draftButton.title = draft ? "Draft — mark ready" : "Ready — mark as draft";
          draftButton.setAttribute("aria-label", draftButton.title);
          draftButton.setAttribute("aria-pressed", String(draft));
          draftButton.replaceChildren(createDocsViewerToolbarIcon(host.ownerDocument,
            draft ? "docsViewer__icon--circle-dashed-check" : "docsViewer__icon--circle-check"));
        }).catch(function (error) {
          if (typeof options.setStatus === "function") {
            options.setStatus(error.message || "Draft readiness could not be saved.", true);
          }
        }).finally(function () {
          draftButton.disabled = !draftRegistration.enabled;
        });
      });
      host.appendChild(draftButton);
    }

    if (markdownLinkForDocument && typeof settings.registerAction === "function") {
      var copyRegistration = settings.registerAction({
        id: DOCS_VIEWER_ACTION_IDS.COPY_LINK,
        placement: "detail-toolbar",
        targetKind: "validated-detail",
        capability: true,
        emptyState: "omitted",
        refreshEffect: "none",
        handler: function (actionTarget) {
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
      var copyButton = host.ownerDocument.createElement("button");
      copyButton.className = "docsViewer__toolbarIconButton docsReportDetail__copyLink";
      copyButton.type = "button";
      copyButton.dataset.docsCollectionCopyLink = "true";
      copyButton.setAttribute("aria-label", "Copy link");
      copyButton.title = "Copy link";
      copyButton.appendChild(createDocsViewerToolbarIcon(host.ownerDocument, "docsViewer__icon--link"));
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

    if (
      !managementContext
      || typeof settings.commitDeletedDocument !== "function"
      || typeof settings.registerAction !== "function"
    ) return;
    var deleteRegistration = settings.registerAction({
      id: DOCS_VIEWER_ACTION_IDS.DELETE,
      placement: "detail-toolbar",
      targetKind: "validated-detail",
      capability: true,
      emptyState: "omitted",
      refreshEffect: "commit-deleted-document",
      handler: function (actionTarget) {
        return actionTarget;
      }
    });
    if (deleteRegistration.hidden || !deleteRegistration.target) return;

    clearDeleteWorkflow();
    var request = deleteWorkflowRequest;
    var button = host.ownerDocument.createElement("button");
    button.className = "docsViewer__toolbarIconButton docsReportDetail__delete";
    button.type = "button";
    button.disabled = true;
    button.dataset.docsCollectionDelete = "true";
    button.appendChild(createDocsViewerToolbarIcon(host.ownerDocument, "docsViewer__icon--trash"));
    button.setAttribute("aria-label", "Delete. Checking Delete availability.");
    button.title = "Checking Delete availability.";
    host.appendChild(button);

    import("./docs-viewer-management-collection-delete-workflow.js")
      .then(function (module) {
        if (request !== deleteWorkflowRequest || !button.isConnected) return;
        activeDeleteWorkflow = module.createDocsViewerManagementCollectionDeleteWorkflow({
          button: button,
          clientOptions: options.clientOptions || {},
          commitDeletedDocument: settings.commitDeletedDocument,
          root: options.root,
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
    id: "default",
    notify: notify,
    renderDetailToolbar: renderDetailToolbar,
    renderListToolbar: renderListToolbar,
    renderRow: renderRow
  };
}
