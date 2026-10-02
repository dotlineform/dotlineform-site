import { runManagedDocsExportWorkspaceWorkflow } from "./docs-viewer-export-workspace-workflow.js";
import { staticHtmlExportCapability } from "./docs-viewer-management-capabilities.js";
import { toggleManagedDocDraft } from "./docs-viewer-management-draft-workflow.js";
import {
  createDocsViewerManagementCapabilityController,
  publishSupported
} from "./docs-viewer-management-capabilities.js";
import {
  createDocsViewerManagementEventRouter
} from "./docs-viewer-management-event-router.js";
import {
  createDocsViewerManagementInteractionController
} from "./docs-viewer-management-interactions.js";
import {
  createDocsViewerManagementImportController
} from "./docs-viewer-management-import-controller.js";
import {
  createDocsViewerManagementIndexController
} from "./docs-viewer-management-index-controller.js";
import {
  createDocsViewerManagementModalComposition
} from "./docs-viewer-management-modal-composition.js";
import {
  createDocsViewerManagementActionController,
  requestCommittedDocumentSource
} from "./docs-viewer-management-actions.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentCollectionTarget,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  docsImportResultDestination
} from "./docs-viewer-management-import-result.js";
import {
  projectDocsViewerReportControlState
} from "./docs-viewer-management-report-controls.js";
import {
  readSelectedDocuments,
  setManagedDocSelected
} from "./docs-viewer-management-client.js";
import { selectedDocumentRows } from "../shared/docs-selected-documents.js";
import {
  DOCS_VIEWER_ACTION_IDS,
  DOCS_VIEWER_ACTION_TARGETS,
  createDocsViewerActionContext,
  getDocsViewerActionDefinition,
  resolveDocsViewerAction
} from "./docs-viewer-action-definitions.js";

var MANAGEMENT_TEXT = {
  unavailableNote: "Docs management service unavailable."
};

export function createDocsViewerManagementActionContext(options = {}) {
  var selectedDocument = options.selectedDocument || {};
  var documentIndex = options.documentIndex || {};
  var displayedTarget = options.documentActionContext && options.documentActionContext.documentTarget;
  var subtreeDocIds = [];
  if (
    displayedTarget && !displayedTarget.collection
    && displayedTarget.doc_id === selectedDocument.selectedDocId
    && documentIndex.docsById.has(displayedTarget.doc_id)
  ) {
    var pending = [displayedTarget.doc_id];
    var seen = new Set();
    while (pending.length) {
      var docId = pending.pop();
      if (seen.has(docId)) continue;
      seen.add(docId);
      subtreeDocIds.push(docId);
      var children = documentIndex.childrenByParent.get(docId) || [];
      for (var i = children.length - 1; i >= 0; i -= 1) pending.push(children[i].doc_id);
    }
  }
  var contextOptions = {
    activeDocId: selectedDocument.selectedDocId,
    subtreeDocIds: subtreeDocIds
  };
  if (Object.prototype.hasOwnProperty.call(options, "invocationDocId")) {
    contextOptions.invocationDocId = options.invocationDocId;
  }
  return createDocsViewerActionContext(contextOptions);
}

export function createDocsViewerManagementActionResolver(options = {}) {
  var selectedDocument = options.selectedDocument || {};

  return function resolveAction(actionId, targetDocId) {
    var definition = getDocsViewerActionDefinition(actionId);
    var contextOptions = {
      documentIndex: options.documentIndex,
      documentActionContext: definition && definition.target === DOCS_VIEWER_ACTION_TARGETS.DOCUMENT_SUBTREE
        ? options.documentActionContext() : null,
      selectedDocument: selectedDocument
    };
    if (arguments.length > 1) contextOptions.invocationDocId = targetDocId;
    return resolveDocsViewerAction(
      actionId,
      createDocsViewerManagementActionContext(contextOptions)
    );
  };
}

export function refreshDocsImportTerminalDestination(detail, options = {}) {
  var result = detail && detail.result;
  var isCollection = Boolean(result && result.collection === true);
  var destination = docsImportResultDestination(
    result,
    { collection: isCollection }
  );
  if (String(detail && detail.destinationUrl || "").trim() !== destination.href) {
    throw new Error("Docs Import terminal destination URL does not match its result.");
  }
  var target = destination.target;
  var targetCollection = normalizeManagedDocumentCollectionTarget({
    ...(target.collection ? { collection: target.collection } : {})
  });
  var displayedCollection = normalizeManagedDocumentCollectionTarget(
    options.currentCollection
  );
  var destinationIsDisplayed = (
    String(displayedCollection.collection || "")
      === String(targetCollection.collection || "")
  );
  if (!destinationIsDisplayed) {
    return Promise.resolve({
      refreshed: false,
      target: target
    });
  }

  if (targetCollection.collection) {
    var reportState = options.reportState || {};
    var refresh = isCollection
      ? reportState.refreshCollection
      : reportState.refreshDocument;
    if (typeof refresh !== "function") {
      return Promise.reject(new Error(
        "The exact imported collection destination is no longer mounted."
      ));
    }
    return Promise.resolve(refresh(target)).then(function () {
      return { refreshed: true, target: target };
    });
  }

  if (typeof options.reloadParent !== "function") {
    return Promise.reject(new Error(
      "The exact imported parent-scope destination cannot be refreshed."
    ));
  }
  return Promise.resolve(
    options.reloadParent(isCollection ? "" : target.doc_id)
  ).then(function () {
    return { refreshed: true, target: target };
  });
}

export function initDocsViewerManagement(context) {
  var root = context.root;
  var nav = context.nav;
  var managementState = context.managementState || {};
  var domains = managementState.domains || {};
  var documentIndex = domains.documentIndex || {};
  var management = domains.management || {};
  var routeSession = domains.routeSession || {};
  var searchRecent = domains.searchRecent || {};
  var selectedDocument = domains.selectedDocument || {};
  var serviceClient = context.serviceClient || {};
  var routeReload = context.routeReload || {};
  context = Object.assign({}, context, {
    docsViewerConfigUrl: serviceClient.docsViewerConfigUrl || context.docsViewerConfigUrl,
    managementBaseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl,
    reloadViewerConfiguration: routeReload.reloadViewerConfiguration || context.reloadViewerConfiguration,
    routeCommands: routeReload.routeCommands || context.routeCommands
  });
  var shellRefs = context.managementShellRefs || {};
  function shellRef(name, id) {
    return shellRefs[name] || document.getElementById(id);
  }
  var manageRow = document.getElementById("docsViewerManageRow");
  var manageActions = manageRow ? manageRow.querySelector(".docsViewer__manageActions") : null;
  var manageActionsButton = document.getElementById("docsViewerManageActionsButton");
  var manageActionsMenu = document.getElementById("docsViewerManageActionsMenu");
  var manageRebuildButton = document.getElementById("docsViewerManageRebuildButton");
  var manageSettingsButton = document.getElementById("docsViewerManageSettingsButton");
  var managePublishButton = document.getElementById("docsViewerManagePublishButton");
  var manageToolbarPublishButton = document.getElementById("docsViewerManageToolbarPublishButton");
  var managePublishButtons = [managePublishButton, manageToolbarPublishButton].filter(Boolean);
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
  var manageToolbarImportButton = document.getElementById("docsViewerManageToolbarImportButton");
  var manageImportButtons = [manageImportButton, manageToolbarImportButton].filter(Boolean);
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var importRoot = shellRef("importRoot", "docsHtmlImportRoot");
  var importBootStatus = shellRef("importBootStatus", "docsHtmlImportBootStatus");
  var capabilityController = null;
  var eventRouter = null;
  var importController = null;
  var interactionController = null;
  var modalController = null;
  var workspaceExportActive = false;
  var workspaceExportButton = document.getElementById("docsViewerManageExportWorkspaceButton");
  var settingsWorkflow = null;
  var actionController = null;
  var resolveAction = null;
  var projectedReportControls = null;
  var collectionReportState = null;
  var selectedState = null;
  var indexController = createDocsViewerManagementIndexController({
    root: root,
    management: management,
    routeSession: routeSession,
    searchRecent: searchRecent,
    callbacks: {
      canPositionDoc: function () {
        return Boolean(currentActiveDoc()) && selectedDocument.displayMode !== "markdown-source";
      },
      handlePositionDoc: function () {
        if (actionController) return actionController.handlePositionDoc();
      },
      activeIndexViewId: function () {
        return typeof context.activeIndexViewId === "function"
          ? context.activeIndexViewId()
          : "index-tree";
      },
      handleDeleteDoc: function () {
        if (actionController) actionController.handleDeleteDoc();
      },
      hideIndexActionsMenu: function (options) {
        if (eventRouter) eventRouter.hideIndexActionsMenu(options);
      },
      managementClientOptions: managementClientOptions,
      projectIndexViewControlState: function (controlId, controlState) {
        if (typeof context.projectIndexViewControlState === "function") {
          return context.projectIndexViewControlState(controlId, controlState);
        }
        return null;
      },
      refreshManagementCapabilities: refreshManagementCapabilities,
      reloadDocsIndex: reloadDocsIndex,
      renderManagementUi: renderManagementUi,
      resolveAction: function (actionId) {
        return resolveAction ? resolveAction(actionId) : null;
      },
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
      toggleIndexActionsMenu: function () {
        if (eventRouter) eventRouter.toggleIndexActionsMenu();
      },
    }
  });
  resolveAction = createDocsViewerManagementActionResolver({
    documentIndex: documentIndex,
    documentActionContext: context.documentActionContext,
    selectedDocument: selectedDocument
  });

  function currentImportDisplayContext() {
    if (collectionReportState && collectionReportState.collectionTarget) {
      return normalizeManagedDocumentCollectionTarget(
        collectionReportState.collectionTarget
      );
    }
    return normalizeManagedDocumentCollectionTarget({
    });
  }

  function currentImportDisplayContextLabel() {
    if (collectionReportState && collectionReportState.collectionTarget) {
      return String(collectionReportState.collectionLabel || "").trim();
    }
    return "Documents";
  }

  function openAppImport(detail) {
    var eventDetail = detail && typeof detail === "object" ? detail : {};
    return importController.open({
      destination: currentImportDisplayContext(),
      destinationLabel: currentImportDisplayContextLabel(),
      restoreFocus: eventDetail.actionTarget || eventDetail.target || null
    });
  }

  async function openExportWorkspace() {
    if (workspaceExportActive || management.managementBusy) return null;
    workspaceExportActive = true;
    renderManagementUi();
    try {
      return await runManagedDocsExportWorkspaceWorkflow({
        root: root, restoreFocus: manageActionsButton,
        capabilities: management.managementCapabilities, clientOptions: managementClientOptions(),
        callbacks: { render: renderManagementUi, setBusy: setManagementBusy, setMessage: setManagementMessage }
      });
    } catch (error) {
      setManagementMessage(error.message || "Workspace export failed.", true);
      return null;
    } finally {
      workspaceExportActive = false;
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  function managementClientOptions() {
    return {
      baseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl,
      fetch: function (url, options) {
        return window.fetch(url, options);
      }
    };
  }

  function currentActiveDoc() {
    if (collectionReportState?.state === "detail") return null;
    return documentIndex.docsById.get(selectedDocument.selectedDocId) || null;
  }

  function sourceTargetForDoc(doc) {
    if (!doc || !doc.doc_id) return null;
    return normalizeManagedDocumentTarget({
      doc_id: doc.doc_id
    });
  }

  function publishCollectionReportState(value) {
    collectionReportState = value && value.parentTarget ? value : null;
    renderManagementUi();
  }

  function activeSourceTarget() {
    var services = typeof context.sourceEditorServices === "function"
      ? context.sourceEditorServices()
      : context.sourceEditorServices;
    var adapter = services && typeof services.getActiveSourceEditorContextAdapter === "function"
      ? services.getActiveSourceEditorContextAdapter()
      : null;
    return adapter && typeof adapter.getDocumentTarget === "function"
      ? adapter.getDocumentTarget()
      : null;
  }

  function openCreatedDocumentSource(target) {
    return requestCommittedDocumentSource(target, function (modeId, options) {
      return context.requestDocumentMode(modeId, options);
    });
  }

  async function openDocumentEditor(target) {
    try {
      var sourceTarget = normalizeManagedDocumentTarget(target);
      hideContextMenu();
      var services = typeof context.sourceEditorServices === "function" ? context.sourceEditorServices() : context.sourceEditorServices;
      var activeTarget = activeSourceTarget();
      if (activeTarget && managedDocumentTargetsEqual(activeTarget, sourceTarget)) {
        services.getActiveSourceEditorContextAdapter().focus();
        return;
      }
      if (!sourceTarget.collection && selectedDocument.selectedDocId !== sourceTarget.doc_id) {
        var payload = await context.routeCommands.loadDoc(sourceTarget.doc_id);
        if (!payload) return;
        if (payload.doc_id !== sourceTarget.doc_id) throw new Error("The document opened did not match the metadata target.");
      }
      await requestCommittedDocumentSource(sourceTarget, context.requestDocumentMode);
    } catch (error) {
      setManagementMessage(error.message || "Document source could not be opened.", true);
      renderManagementUi();
    }
  }

  function currentContextMenuDoc() {
    return interactionController ? interactionController.currentContextMenuDoc() : null;
  }

  function hideContextMenu() {
    if (interactionController) interactionController.hideContextMenu();
  }

  function setManagementBusy(busy) {
    management.managementBusy = Boolean(busy);
    if (root) {
      root.dataset.managementBusy = management.managementBusy ? "true" : "false";
    }
  }

  function syncManagementStatus(noteText, isError) {
    var text = String(noteText || "");
    var hasManagementStatus = Boolean(text);
    if (hasManagementStatus || management.managementStatusOwnsViewerStatus) {
      context.setStatus(text, Boolean(isError));
    }
    management.managementStatusOwnsViewerStatus = hasManagementStatus;
  }

  function projectDocumentActionButtons(hidden, disabled) {
    var actionsHidden = Boolean(hidden);
    var actionsDisabled = Boolean(disabled);
    var documentMode = root && root.dataset ? String(root.dataset.documentDisplayMode || "") : "";
    var markdownMode = documentMode === "markdown-source";
    var actionContext = context.documentActionContext();
    projectedReportControls = projectDocsViewerReportControlState({
      disabled: actionsDisabled,
      documentMode: documentMode,
      hidden: actionsHidden,
      actionContext: actionContext,
      sourceTarget: markdownMode ? activeSourceTarget() : null
    });
    if (typeof context.projectMainViewControlState === "function") {
      context.projectMainViewControlState("edit", projectedReportControls.editDocument.state);
      var draftRecord = actionContext.documentRecord;
      var draftTarget = actionContext.documentTarget;
      var draftPolicyRecord = draftTarget && !draftTarget.collection
        ? documentIndex.docsById.get(draftTarget.doc_id) : null;
      var draftIgnored = Boolean(draftPolicyRecord && draftPolicyRecord.publication_ignored === true);
      context.projectMainViewControlState("draft", {
        hidden: actionsHidden || markdownMode || !draftTarget
          || Boolean(draftTarget && draftTarget.collection),
        disabled: actionsDisabled || !draftTarget || !draftRecord || !draftPolicyRecord
          || draftPolicyRecord.publication_ignored !== false,
        pressed: Boolean(draftRecord && draftRecord.draft === true),
        label: draftIgnored ? "Excluded from Publish by unpublishable.json"
          : draftRecord && draftRecord.draft === true ? "Draft — mark ready" : "Ready — mark as draft"
      });
      projectSelectedControl(draftTarget, actionsHidden || markdownMode, actionsDisabled);
      context.projectMainViewControlState("open-vscode", projectedReportControls.openVsCode.state);
      context.projectMainViewControlState("return-to-doc", projectedReportControls.returnToDoc.state);
      context.projectMainViewControlState("save-markdown-source", {
        hidden: actionsHidden,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("source-add-image", {
        hidden: actionsHidden || !markdownMode,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("source-add-file", {
        hidden: actionsHidden || !markdownMode,
        disabled: actionsDisabled
      });
    }
  }

  function projectAppControl(controlId, controlState) {
    if (typeof context.projectAppManagementControlState === "function") {
      context.projectAppManagementControlState(controlId, controlState);
    }
  }

  function hideAppManagementControls() {
    [
      "manage-import",
      "manage-actions",
      "manage-rebuild",
      "manage-publish"
    ].forEach(function (controlId) {
      projectAppControl(controlId, { hidden: true, disabled: true });
    });
  }

  function runDraftToggle(target, draft) {
    setManagementBusy(true);
    setManagementMessage("", false);
    renderManagementUi();
    return toggleManagedDocDraft(target, draft, {
      clientOptions: managementClientOptions(),
      onSaved: function (savedTarget, response) {
        if (!savedTarget.collection) {
          var record = documentIndex.docsById.get(savedTarget.doc_id);
          if (record) record.draft = response.record.draft;
          context.renderSidebar();
        }
        renderManagementUi();
      }
    }).catch(function (error) {
      setManagementMessage(error.message || "Draft readiness could not be saved.", true);
    }).finally(function () {
      setManagementBusy(false);
      renderManagementUi();
    });
  }

  function projectSelectedControl(target, hidden, disabled) {
    if (hidden || !target) {
      selectedState = null;
      context.projectMainViewControlState("selected", { hidden: true, disabled: true });
      return;
    }
    if (!selectedState || !managedDocumentTargetsEqual(selectedState.target, target)) {
      var pending = { target: normalizeManagedDocumentTarget(target), ready: false, selected: false, error: "" };
      selectedState = pending;
      readSelectedDocuments(managementClientOptions()).then(function (payload) {
        if (selectedState !== pending) return;
        pending.selected = selectedDocumentRows(payload).some(function (row) {
          return row.doc_id === target.doc_id && (row.collection || "") === (target.collection || "");
        });
        pending.ready = true;
        renderManagementUi();
      }).catch(function (error) {
        if (selectedState !== pending) return;
        pending.error = error.message || "Selected Documents could not be loaded.";
        setManagementMessage(pending.error, true);
        renderManagementUi();
      });
    }
    context.projectMainViewControlState("selected", {
      hidden: false,
      disabled: disabled || !selectedState.ready,
      pressed: selectedState.selected,
      label: selectedState.error || (!selectedState.ready ? "Loading document selection…"
        : selectedState.selected ? "Starred — remove from Selected Documents" : "Star — add to Selected Documents")
    });
  }

  async function runSelectedToggle() {
    var state = selectedState;
    var actionContext = context.documentActionContext();
    var control = projectedReportControls && projectedReportControls.editDocument;
    if (!state || !state.ready || !control || control.state.hidden || control.state.disabled
      || management.managementBusy
      || !managedDocumentTargetsEqual(state.target, actionContext.documentTarget)) return;
    var selected = !state.selected;
    setManagementBusy(true);
    setManagementMessage("", false);
    renderManagementUi();
    try {
      var response = await setManagedDocSelected(state.target, selected, managementClientOptions());
      if (response.ok !== true || !managedDocumentTargetsEqual(response.target, state.target) || response.selected !== selected) {
        throw new Error("Selected Documents response did not match the requested document.");
      }
      if (selectedState === state) state.selected = selected;
    } catch (error) {
      setManagementMessage(error.message || "Document selection could not be saved.", true);
    } finally {
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  function toggleCollectionDocumentDraft(target, draft) {
    if (management.managementBusy
      || collectionReportState?.state !== "detail"
      || !managedDocumentTargetsEqual(target, collectionReportState.documentTarget)
    ) {
      return Promise.reject(new Error("Draft readiness is unavailable for this collection document."));
    }
    return runDraftToggle(target, draft);
  }

  function handleMainViewControl(detail) {
    var controlId = String(detail && detail.controlId || "").trim();
    var actionId = String(detail && detail.actionId || "").trim();
    if (controlId === "selected") return runSelectedToggle();
    if (controlId === "draft") {
      var draftControl = projectedReportControls && projectedReportControls.editDocument;
      if (!draftControl || draftControl.state.hidden || draftControl.state.disabled
        || !draftControl.target || draftControl.target.collection
        || management.managementBusy) return;
      var draftRecord = context.documentActionContext().documentRecord;
      var draftPolicyRecord = documentIndex.docsById.get(draftControl.target.doc_id);
      if (!draftRecord || draftRecord.doc_id !== draftControl.target.doc_id
        || !draftPolicyRecord || draftPolicyRecord.publication_ignored !== false) return;
      return runDraftToggle(draftControl.target, draftRecord.draft !== true);
    }
    var reportControlOwners = new Map([
      ["edit", {
        projection: "editDocument",
        run: function (target) {
          openDocumentEditor(target);
        }
      }],
      ["return-to-doc", {
        projection: "returnToDoc",
        run: function () {
          actionController.handleReturnToDoc();
        }
      }],
      ["open-vscode", {
        projection: "openVsCode",
        run: function (target) {
          var record = context.documentActionContext().documentRecord;
          actionController.handleOpenSource("vscode", target,
            record && record.doc_id === target.doc_id ? record.title : target.doc_id);
        }
      }]
    ]);
    var reportOwner = reportControlOwners.get(controlId);
    if (reportOwner) {
      var projected = projectedReportControls
        ? projectedReportControls[reportOwner.projection]
        : null;
      if (
        !projected
        || projected.state.hidden
        || projected.state.disabled
        || (
          reportOwner.projection !== "returnToDoc"
          && !projected.target
        )
      ) {
        return false;
      }
      reportOwner.run(projected.target);
      return true;
    }

    var resolution = actionId ? resolveAction(actionId) : null;
    if (actionId && (!resolution || !resolution.enabled)) return false;
    var owners = new Map([
      ["save-markdown-source", function () { actionController.handleMarkdownSave(); }],
      ["source-add-image", function () {
        if (root && typeof root.dispatchEvent === "function") {
          root.dispatchEvent(new CustomEvent("docs-viewer-source-editor-add-image", { bubbles: true }));
        }
      }],
      ["source-add-file", function () {
        if (root && typeof root.dispatchEvent === "function") {
          root.dispatchEvent(new CustomEvent("docs-viewer-source-editor-add-file", { bubbles: true }));
        }
      }]
    ]);
    var owner = owners.get(controlId);
    if (owner) {
      owner();
      return true;
    }
    var contributions = context.mainViewControlHandlerContributions || {};
    var contribution = typeof contributions[controlId] === "function"
      ? contributions[controlId]
      : null;
    if (!contribution) return false;
    contribution({
      detail: detail,
      resolution: resolution,
      root: root,
      setStatus: context.setStatus,
      sourceEditorServices: typeof context.sourceEditorServices === "function"
        ? context.sourceEditorServices()
        : context.sourceEditorServices
    });
    return true;
  }

  function handleAppManagementControl(detail) {
    var actionId = String(detail && detail.actionId || "").trim();
    if (actionId && !resolveAction(actionId).enabled) return false;
    return eventRouter.handleAppManagementControl(detail);
  }

  function renderManagementUi() {
    if (!manageRow) return;

    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    indexController.render();
    if (!routeSession.managementContext) {
      syncManagementStatus("", false);
      hideAppManagementControls();
      projectDocumentActionButtons(true, true);
      eventRouter.hideManageActionsMenu();
      return;
    }

    manageRow.hidden = false;
    var managementActionsHidden = !management.managementChecked || !management.managementAvailable;
    if (manageActions) {
      manageActions.hidden = !management.managementChecked || !management.managementAvailable;
      if (manageActions.hidden) {
        eventRouter.hideManageActionsMenu();
      }
    }

    var noteText;
    var noteIsError = false;
    if (!management.managementChecked) {
      noteText = "";
    } else if (!management.managementAvailable) {
      noteText = management.managementCapabilityError || MANAGEMENT_TEXT.unavailableNote;
      noteIsError = true;
    } else {
      noteText = management.managementMessage || "";
      noteIsError = management.managementMessageIsError;
    }
    syncManagementStatus(noteText, noteIsError);

    if (!manageRebuildButton || !manageNewButton) return;

    var editAction = resolveAction(DOCS_VIEWER_ACTION_IDS.EDIT_DOCUMENT);
    var editDisabled = (
      management.managementBusy ||
      !editAction.enabled
    );
    var publishAvailable = management.managementAvailable && publishSupported(
      management.managementCapabilities
    );

    projectAppControl("manage-import", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
    });
    projectAppControl("manage-actions", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
    });
    projectAppControl("manage-rebuild", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
    });
    projectAppControl("manage-publish", {
      hidden: managementActionsHidden || !publishAvailable,
      disabled: management.managementBusy || !publishAvailable
    });

    manageRebuildButton.disabled = management.managementBusy || !management.managementAvailable;
    if (manageActionsButton) {
      manageActionsButton.disabled = management.managementBusy || !management.managementAvailable;
      if (manageActionsButton.disabled) {
        eventRouter.hideManageActionsMenu();
      }
    }
    if (workspaceExportButton) {
      var exportCapability = staticHtmlExportCapability(management.managementCapabilities);
      workspaceExportButton.disabled = management.managementBusy || workspaceExportActive || !exportCapability.available;
      workspaceExportButton.title = exportCapability.available ? "Export workspace" : exportCapability.reason;
    }
    managePublishButtons.forEach(function (button) {
      button.disabled = management.managementBusy || !publishAvailable;
    });
    if (manageToolbarPublishButton) manageToolbarPublishButton.hidden = !publishAvailable;
    manageImportButtons.forEach(function (button) {
      button.disabled = management.managementBusy || !management.managementAvailable;
    });
    if (manageSettingsButton) {
      manageSettingsButton.disabled = management.managementBusy || !management.managementAvailable;
    }
    var authoringAvailable = management.managementAvailable;
    manageNewButton.hidden = !authoringAvailable;
    manageNewButton.disabled = management.managementBusy || !authoringAvailable;
    manageImportButtons.forEach(function (button) { button.hidden = !authoringAvailable; });
    if (manageSettingsButton) manageSettingsButton.hidden = !authoringAvailable;
    projectDocumentActionButtons(!management.managementChecked || !authoringAvailable, !authoringAvailable || editDisabled);
    if (settingsWorkflow) settingsWorkflow.render();
  }

  function initializeManagement() {
    if (capabilityController) capabilityController.initialize();
  }

  function refreshManagementCapabilities() {
    if (capabilityController) capabilityController.refresh();
  }

  function reloadViewerConfiguration() {
    if (typeof routeReload.reloadViewerConfiguration === "function") {
      return routeReload.reloadViewerConfiguration();
    }
    if (typeof context.reloadViewerConfiguration === "function") {
      return context.reloadViewerConfiguration();
    }
    return Promise.resolve(null);
  }

  function routeCommand(name) {
    var routeCommands = routeReload.routeCommands || context.routeCommands || {};
    return typeof routeCommands[name] === "function" ? routeCommands[name] : null;
  }

  function setRouteHistory(docId, hash, query, mode, reportParams) {
    var command = routeCommand("setHistory");
    if (command) command(docId, hash, query, mode, reportParams);
  }

  function loadRouteIndex() {
    var command = routeCommand("loadIndex");
    return command ? command() : Promise.resolve(null);
  }

  function reloadDocsIndex(targetDocId, _summaryText, reportParams) {
    selectedDocument.payloadCache.clear();
    searchRecent.searchIndex = null;
    searchRecent.searchLoaded = false;
    searchRecent.searchRequestPromise = null;
    searchRecent.recentEntries = [];
    searchRecent.recentLoaded = false;
    searchRecent.recentRequestPromise = null;
    selectedDocument.reloadNonce = String(Date.now());
    selectedDocument.reloadExpectedDocId = String(targetDocId || "").trim();
    searchRecent.searchQuery = "";
    searchRecent.searchVisibleCount = context.SEARCH_BATCH_SIZE;
    context.cancelSearchDebounce();
    if (context.searchInput) {
      context.searchInput.value = "";
    }
    context.resetIndexLists();

    if (targetDocId) {
      setRouteHistory(targetDocId, "", "", "replace", reportParams);
    }

    return loadRouteIndex().then(function () {
      context.setStatus("", false);
      renderManagementUi();
    });
  }

  function displayImportedDocument(detail) {
    return refreshDocsImportTerminalDestination(detail, {
      currentCollection: currentImportDisplayContext(),
      reportState: collectionReportState,
      reloadParent: function (targetDocId) {
        return reloadDocsIndex(targetDocId, "");
      }
    });
  }

  function setManagementMessage(message, isError) {
    management.managementMessage = String(message || "");
    management.managementMessageIsError = Boolean(isError);
    renderManagementUi();
  }

  function applyConfig() {
  }

  capabilityController = createDocsViewerManagementCapabilityController({
    management: management,
    routeSession: routeSession,
    context: context,
    callbacks: {
      managementClientOptions: managementClientOptions,
      renderManagementUi: renderManagementUi,
      renderSidebar: context.renderSidebar,
    }
  });

  interactionController = createDocsViewerManagementInteractionController({
    nav: nav,
    documentIndex: documentIndex,
    management: management,
    routeSession: routeSession,
    searchRecent: searchRecent,
    selectedDocument: selectedDocument,
    context: context,
    refs: {
      contextMenu: shellRefs.contextMenu
    },
    callbacks: {
      onContextAction: function (actionId) {
        if (!actionController) return;
        if (actionId === DOCS_VIEWER_ACTION_IDS.NEW_SIBLING) {
          actionController.handleCreateRelatedDoc("sibling");
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.NEW_CHILD) {
          actionController.handleCreateRelatedDoc("child");
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.COPY_LINK) {
          actionController.handleCopyLink();
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.OPEN_VSCODE) {
          var vscodeDoc = currentContextMenuDoc();
          if (vscodeDoc) {
            actionController.handleOpenSource(
              "vscode",
              sourceTargetForDoc(vscodeDoc),
              vscodeDoc.title
            );
          }
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.OPEN) {
          var defaultDoc = currentContextMenuDoc();
          if (defaultDoc) {
            actionController.handleOpenSource(
              "default",
              sourceTargetForDoc(defaultDoc),
              defaultDoc.title
            );
          }
        }
      },
      onEditDoc: function (docId) {
        if (!actionController) return;
        eventRouter.hideManageActionsMenu();
        var doc = documentIndex.docsById.get(docId) || null;
        var target = sourceTargetForDoc(doc);
        if (target) openDocumentEditor(target);
      },
    }
  });

  actionController = createDocsViewerManagementActionController({
    root: root,
    documentIndex: documentIndex,
    management: management,
    searchRecent: searchRecent,
    selectedDocument: selectedDocument,
    context: context,
    refs: {},
    resolveAction: resolveAction,
    callbacks: {
      currentActiveDoc: currentActiveDoc,
      currentContextMenuDoc: currentContextMenuDoc,
      getSettingsWorkflow: function () {
        return settingsWorkflow;
      },
      hideContextMenu: hideContextMenu,
      managementClientOptions: managementClientOptions,
      openCreatedDocumentSource: openCreatedDocumentSource,
      reloadDocsIndex: reloadDocsIndex,
      reloadViewerConfiguration: reloadViewerConfiguration,
      refreshManagementCapabilities: refreshManagementCapabilities,
      renderManagementUi: renderManagementUi,
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
    }
  });

  eventRouter = createDocsViewerManagementEventRouter({
    refs: {
      indexActionsButton: indexController.actionsButton,
      indexActionsMenu: indexController.actionsMenu,
      manageActionsButton: manageActionsButton,
      manageActionsMenu: manageActionsMenu
    },
    commands: {
      createDoc: function () { actionController.handleCreateDoc(); },
      exportWorkspace: openExportWorkspace,
      deleteDoc: function () { actionController.handleDeleteDoc(); },
      openImport: openAppImport,
      openSettings: function () { settingsWorkflow.open(); },
      publish: function () { actionController.handlePublish(); },
      rebuild: function () { actionController.handleRebuildDocs(); }
    },
    controllers: {
      interaction: function () { return interactionController; },
      modal: function () { return modalController; }
    }
  });

  importController = createDocsViewerManagementImportController({
    refs: {
      root: importRoot,
      bootStatus: importBootStatus
    },
    context: {
      root: root,
      docsViewerConfigUrl: serviceClient.docsViewerConfigUrl || context.docsViewerConfigUrl,
      managementBaseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl
    },
    callbacks: {
      getModalController: function () {
        return modalController;
      },
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: eventRouter.hideManageActionsMenu,
      onImportComplete: displayImportedDocument,
    }
  });

  var modalComposition = createDocsViewerManagementModalComposition({
    domains: { management: management },
    shellRefs: shellRefs,
    manageActionsButton: manageActionsButton,
    manageImportButton: manageToolbarImportButton || manageImportButton,
    manageSettingsButton: manageSettingsButton,
    callbacks: {
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: eventRouter.hideManageActionsMenu,
      onImportOpen: importController.initialize,
      onSettingsSubmit: actionController.handleSettingsSubmit,
      managementClientOptions: managementClientOptions,
    }
  });
  modalController = modalComposition.modalController;
  settingsWorkflow = modalComposition.settingsWorkflow;

  eventRouter.wireEvents();
  applyConfig(context.currentViewerConfig());

  return {
    applyConfig: applyConfig,
    createCollectionDocument: actionController.handleCreateCollectionDocument,
    regenerateCatalogue: actionController.handleRegenerateCatalogue,
    toggleCollectionDocumentDraft: toggleCollectionDocumentDraft,
    handleDocumentKeydown: eventRouter.handleDocumentKeydown,
    handleAppManagementControl: handleAppManagementControl,
    handleIndexViewChange: indexController.handleViewChange,
    handleIndexViewControl: indexController.handleControl,
    handleMainViewControl: handleMainViewControl,
    handleRootClick: eventRouter.handleRootClick,
    hideContextMenu: hideContextMenu,
    initialize: initializeManagement,
    openImportModal: importController.open,
    publishCollectionReportState: publishCollectionReportState,
    render: renderManagementUi,
  };
}
