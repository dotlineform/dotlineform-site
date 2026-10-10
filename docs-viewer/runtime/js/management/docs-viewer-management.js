import { runManagedDocsExportWorkspaceWorkflow } from "./docs-viewer-export-workspace-workflow.js";
import { staticHtmlExportCapability } from "./docs-viewer-management-capabilities.js";
import { createDocsViewerEditMenuController } from "./docs-viewer-management-edit-menu.js";
import { createDocsViewerManagementContextActions } from "./docs-viewer-management-context-actions.js";
import { projectDocsViewerManagementActionMenuItem } from "./docs-viewer-management-actions-renderer.js";
import { managedDocumentActionState } from "./docs-viewer-management-document-actions.js";
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
  var invocationDocId = String(options.invocationDocId || "").trim();
  var subtreeDocIds = [];
  if (
    options.includeSubtree && invocationDocId && documentIndex.docsById.has(invocationDocId)
  ) {
    var pending = [invocationDocId];
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
      includeSubtree: definition && definition.target === DOCS_VIEWER_ACTION_TARGETS.DOCUMENT_SUBTREE,
      selectedDocument: selectedDocument
    };
    if (arguments.length > 1) contextOptions.invocationDocId = targetDocId;
    var resolution = resolveDocsViewerAction(
      actionId,
      createDocsViewerManagementActionContext(contextOptions)
    );
    if (definition && definition.target !== DOCS_VIEWER_ACTION_TARGETS.WORKSPACE) {
      var target = arguments.length > 1 ? { doc_id: targetDocId }
        : selectedDocument.documentTarget || { doc_id: selectedDocument.selectedDocId };
      var policy = options.documentActionState(actionId, target);
      resolution.hidden = policy.hidden;
      if (policy.disabled) {
        resolution.enabled = false;
        resolution.disabledReason = policy.reason;
      }
    }
    return resolution;
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
  function documentActionState(actionId, target) {
    return managedDocumentActionState(management.managementCapabilities, actionId, target);
  }
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
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
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
  var contextActions = null;
  var editMenuController = null;
  var indexController = createDocsViewerManagementIndexController({
    root: root,
    management: management,
    callbacks: {
      documentActionState: documentActionState,
      sourceEditingActive: function () {
        return selectedDocument.displayMode === "markdown-source";
      },
      handlePositionDoc: function (docId, restoreFocus) {
        if (actionController) return actionController.handlePositionDoc(docId, restoreFocus);
      },
      activeIndexViewId: function () {
        return typeof context.activeIndexViewId === "function"
          ? context.activeIndexViewId()
          : "index-tree";
      },
      handleDeleteDoc: function (docId, restoreFocus) {
        if (actionController) return actionController.handleDeleteDoc(docId, restoreFocus);
      },
      managementClientOptions: managementClientOptions,
      indexDocument: function (docId) {
        return documentIndex.docsById.get(docId) || null;
      },
      refreshManagementCapabilities: refreshManagementCapabilities,
      renderManagementUi: renderManagementUi,
      resolveAction: function (actionId, docId) {
        return resolveAction ? resolveAction(actionId, docId) : null;
      },
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
    }
  });
  resolveAction = createDocsViewerManagementActionResolver({
    documentIndex: documentIndex,
    selectedDocument: selectedDocument,
    documentActionState: documentActionState
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

  function sourceTargetForDoc(doc) {
    if (!doc || !doc.doc_id) return null;
    return normalizeManagedDocumentTarget({
      doc_id: doc.doc_id
    });
  }

  function publishCollectionReportState(value) {
    collectionReportState = value && value.collectionTarget ? value : null;
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
      if (documentActionState(DOCS_VIEWER_ACTION_IDS.EDIT_DOCUMENT, sourceTarget).disabled) return;
      hideContextMenu();
      var services = typeof context.sourceEditorServices === "function" ? context.sourceEditorServices() : context.sourceEditorServices;
      var activeTarget = activeSourceTarget();
      if (activeTarget && managedDocumentTargetsEqual(activeTarget, sourceTarget)) {
        services.getActiveSourceEditorContextAdapter().focus();
        return;
      }
      if (!selectedDocument.documentTarget || !managedDocumentTargetsEqual(selectedDocument.documentTarget, sourceTarget) || !selectedDocument.displayedPayload) {
        var payload = await context.routeCommands.loadDoc(sourceTarget);
        if (!payload) return;
        if (payload.doc_id !== sourceTarget.doc_id) throw new Error("The document opened did not match the metadata target.");
      }
      await requestCommittedDocumentSource(sourceTarget, context.requestDocumentMode);
    } catch (error) {
      setManagementMessage(error.message || "Document source could not be opened.", true);
      renderManagementUi();
    }
  }

  function hideContextMenu(options) {
    if (interactionController) interactionController.hideContextMenu(options);
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
      actionContext: actionContext
    });
    if (typeof context.projectMainViewControlState === "function") {
      context.projectMainViewControlState("edit", projectedReportControls.editDocument.state);
      context.projectMainViewControlState("return-to-doc", projectedReportControls.returnToDoc.state);
      context.projectMainViewControlState("save-markdown-source", {
        hidden: actionsHidden,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("source-directives", {
        hidden: actionsHidden || !markdownMode,
        disabled: actionsDisabled
      });
    }
    if (editMenuController) editMenuController.render();
    if (contextActions) contextActions.render();
  }

  function projectAppControl(controlId, controlState) {
    if (typeof context.projectAppManagementControlState === "function") {
      context.projectAppManagementControlState(controlId, controlState);
    }
  }

  function hideAppManagementControls() {
    projectAppControl("manage-actions", { hidden: true, disabled: true });
  }

  function handleMainViewControl(detail) {
    var controlId = String(detail && detail.controlId || "").trim();
    var actionId = String(detail && detail.actionId || "").trim();
    if (controlId === "edit") return editMenuController.handleControl(detail);
    var reportControlOwners = new Map([
      ["return-to-doc", {
        projection: "returnToDoc",
        run: function () {
          actionController.handleReturnToDoc();
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
    if (controlId === "save-markdown-source") {
      actionController.handleMarkdownSave();
      return true;
    }
    if (controlId === "source-directives" && management.managementBusy) return false;
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
      openSourceInVsCode: function (target) { return actionController.handleOpenSource("vscode", target); },
      sourceEditorServices: typeof context.sourceEditorServices === "function"
        ? context.sourceEditorServices()
        : context.sourceEditorServices
    });
    return true;
  }

  function handleAppManagementControl(detail) {
    var actionId = String(detail && detail.actionId || "").trim();
    if (detail.eventType === "click") editMenuController.close(false);
    if (actionId === DOCS_VIEWER_ACTION_IDS.NEW) {
      if (detail.eventType !== "click") return false;
      hideContextMenu();
      eventRouter.hideManageActionsMenu();
      contextActions.invoke(actionId);
      return true;
    }
    if (actionId && !resolveAction(actionId).enabled) return false;
    return eventRouter.handleAppManagementControl(detail);
  }

  function renderManagementUi() {
    if (!manageRow) return;

    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    if (interactionController) interactionController.render();
    if (!routeSession.managementContext) {
      syncManagementStatus("", false);
      hideAppManagementControls();
      context.projectIndexViewControlState("open-recent-exclusions", { hidden: true });
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

    context.projectIndexViewControlState("open-recent-exclusions", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
    });

    if (!manageRebuildButton || !manageNewButton) return;

    var editDisabled = (
      management.managementBusy ||
      !context.documentActionContext().documentTarget
    );
    var publishAvailable = management.managementAvailable && publishSupported(
      management.managementCapabilities
    );

    projectAppControl("manage-actions", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
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
    if (managePublishButton) {
      managePublishButton.disabled = management.managementBusy || !publishAvailable;
      managePublishButton.title = publishAvailable ? "Publish" : "Publish is unavailable for this workspace.";
    }
    if (manageImportButton) {
      manageImportButton.disabled = management.managementBusy || !management.managementAvailable;
    }
    if (manageSettingsButton) {
      manageSettingsButton.disabled = management.managementBusy || !management.managementAvailable;
    }
    var authoringAvailable = management.managementAvailable;
    projectDocumentActionButtons(!management.managementChecked || !authoringAvailable, !authoringAvailable || editDisabled);
    context.documentActionContext().projectDocumentActions?.();
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

  function loadRouteIndex(options) {
    var command = routeCommand("loadIndex");
    return command ? command(options) : Promise.resolve(null);
  }

  function refreshIndexTree() {
    return loadRouteIndex({ preserveDocument: true }).then(function () {
      renderManagementUi();
    });
  }

  /** Reload reader data while retaining the exact ordinary or collection owner. */
  async function reloadDocsIndex(target) {
    var reloadTarget = target ? normalizeManagedDocumentTarget(target) : null;
    await context.routeCommands.loadIndex({ preserveDocument: true });
    if (reloadTarget) {
      if (selectedDocument.documentTarget && managedDocumentTargetsEqual(reloadTarget, selectedDocument.documentTarget)) {
        await context.routeCommands.refreshDocument(reloadTarget);
      } else {
        var loaded = await context.routeCommands.loadDoc(reloadTarget, { force: true, historyMode: "replace" });
        if (!loaded) throw new Error("Updated document could not be displayed.");
      }
    }
    context.setStatus("", false);
    renderManagementUi();
  }

  async function displayImportedDocument(detail) {
    var results = Array.isArray(detail.results) ? detail.results : [detail.result];
    var displayedChanged = false;
    var projectionErrors = [];
    results.filter(Boolean).forEach(function (result) {
      if (result.dry_run || result.preview_only) return;
      if (result.collection === true) {
        (result.records || []).forEach(function (item) {
          if (["created", "overwritten"].includes(item.status) && item.committed_document) {
            projectionErrors.push(...(context.commitDocumentChange(item.committed_document) || []));
            if (selectedDocument.documentTarget && managedDocumentTargetsEqual(item.committed_document.target, selectedDocument.documentTarget)) displayedChanged = true;
          }
        });
      }
    });
    if (results.some(function (result) { return result && !result.target?.collection; })) {
      await context.routeCommands.loadIndex({ preserveDocument: true });
    }
    var result = detail.result;
    var loaded;
    if (result && result.collection !== true && result.target) {
      loaded = selectedDocument.documentTarget && managedDocumentTargetsEqual(result.target, selectedDocument.documentTarget)
        ? result.target : await context.routeCommands.loadDoc(result.target, { force: true });
      if (!loaded) throw new Error("Imported document could not be displayed.");
    } else if (displayedChanged) {
      await context.routeCommands.refreshDocument(selectedDocument.documentTarget);
    } else {
      var report = context.documentActionContext();
      if (result && result.collection === true && report && report.state === "list"
        && (report.collectionTarget?.collection || "") === (result.target?.collection || "")) {
        await report.refreshCollection(result.target);
      }
    }
    if (projectionErrors.length) throw new Error("Documents imported, but a retained list could not be updated: " + projectionErrors.map(function (error) { return error.message; }).join("; "));
    return loaded;
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
      contextActionStates: indexController.actionStates,
      documentActionState: documentActionState,
      onContextAction: function (actionId, targetDocId, restoreFocus) {
        if (!actionController) return;
        if (documentActionState(actionId, { doc_id: targetDocId }).disabled) return;
        if (indexController.handleAction(actionId, targetDocId, restoreFocus)) return;
        if (actionId === DOCS_VIEWER_ACTION_IDS.NEW_SIBLING) {
          actionController.handleCreateRelatedDoc("sibling", targetDocId);
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.NEW_CHILD) {
          actionController.handleCreateRelatedDoc("child", targetDocId);
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.COPY_LINK) {
          actionController.handleCopyLink(targetDocId);
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.OPEN_VSCODE) {
          var vscodeDoc = documentIndex.docsById.get(targetDocId);
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
          var defaultDoc = documentIndex.docsById.get(targetDocId);
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
    documentActionState: documentActionState,
    callbacks: {
      getSettingsWorkflow: function () {
        return settingsWorkflow;
      },
      hideContextMenu: hideContextMenu,
      managementClientOptions: managementClientOptions,
      openCreatedDocumentSource: openCreatedDocumentSource,
      reloadDocsIndex: reloadDocsIndex,
      refreshIndexTree: refreshIndexTree,
      reloadViewerConfiguration: reloadViewerConfiguration,
      refreshManagementCapabilities: refreshManagementCapabilities,
      renderManagementUi: renderManagementUi,
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
    }
  });

  contextActions = createDocsViewerManagementContextActions({
    management: management,
    selectedDocument: selectedDocument,
    documentIndex: documentIndex,
    actions: actionController,
    documentActionState: documentActionState,
    documentActionContext: context.documentActionContext,
    activeViewState: context.activeViewState,
    isManagementContext: context.isManagementContext,
    clientOptions: managementClientOptions,
    project: function (actionId, state) {
      var menu = actionId === DOCS_VIEWER_ACTION_IDS.NEW
        ? manageActionsMenu : root.querySelector("#docsViewerManageEditMenu");
      projectDocsViewerManagementActionMenuItem(menu, actionId, state);
    },
    render: renderManagementUi,
    renderSidebar: context.renderSidebar,
    setBusy: setManagementBusy,
    setMessage: setManagementMessage
  });

  editMenuController = createDocsViewerEditMenuController({
    root: root,
    contextActions: contextActions,
    documentActionState: documentActionState,
    documentActionContext: context.documentActionContext,
    activeViewState: context.activeViewState,
    editControl: function () { return projectedReportControls?.editDocument; },
    deleteState: function (docId) { return indexController.actionControlState(DOCS_VIEWER_ACTION_IDS.DELETE, docId); },
    openSource: openDocumentEditor,
    rebuildDocument: actionController.handleRebuildDocument,
    copyLink: actionController.handleCopyLink,
    deleteDocument: actionController.handleDeleteDoc,
    closeOtherMenus: function () { hideContextMenu(); eventRouter.hideManageActionsMenu(); }
  });

  eventRouter = createDocsViewerManagementEventRouter({
    refs: {
      manageActionsButton: manageActionsButton,
      manageActionsMenu: manageActionsMenu
    },
    commands: {
      exportWorkspace: openExportWorkspace,
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
      onCommittedResult: async function (result) {
        if (result.dry_run || result.preview_only || !result.target || !result.record) return;
        var projectionErrors = context.commitDocumentChange({ target: result.target, record: result.record }) || [];
        if (selectedDocument.documentTarget && managedDocumentTargetsEqual(result.target, selectedDocument.documentTarget)) {
          try {
            await context.routeCommands.refreshDocument(result.target);
          } catch (error) {
            throw new Error("Document imported, but reader refresh failed: " + error.message, { cause: error });
          }
        }
        if (projectionErrors.length) throw new Error("Document imported, but a retained list could not be updated: " + projectionErrors.map(function (error) { return error.message; }).join("; "));
      },
      onImportComplete: displayImportedDocument,
    }
  });

  var modalComposition = createDocsViewerManagementModalComposition({
    domains: { management: management },
    shellRefs: shellRefs,
    manageActionsButton: manageActionsButton,
    manageImportButton: manageImportButton,
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
    documentActionState: documentActionState,
    regenerateCatalogue: actionController.handleRegenerateCatalogue,
    handleDocumentKeydown: function (event) {
      return editMenuController.handleKeydown(event) || eventRouter.handleDocumentKeydown(event);
    },
    handleAppManagementControl: handleAppManagementControl,
    handleIndexViewControl: indexController.handleIndexViewControl,
    handleIndexViewChange: function (viewId) {
      if (viewId !== "index-tree") hideContextMenu();
    },
    handleMainViewControl: handleMainViewControl,
    handleRootClick: function (event) {
      editMenuController.handleRootClick(event);
      return eventRouter.handleRootClick(event);
    },
    hideContextMenu: hideContextMenu,
    initialize: initializeManagement,
    openImportModal: importController.open,
    publishCollectionReportState: publishCollectionReportState,
    render: renderManagementUi,
  };
}
