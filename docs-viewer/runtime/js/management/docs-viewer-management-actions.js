import { publishManagedDocs } from "./docs-viewer-management-client.js";
import { openDocsViewerPositionModal } from "./docs-viewer-position-modal.js";
import {
  deleteManagedDoc,
  createManagedDoc,
  moveManagedDoc,
  openManagedDocSource,
  readManagedDocMetadata,
  rebuildManagedDocs,
  rebuildManagedDocument,
  updateSourceConfigSettings
} from "./docs-viewer-management-client.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  normalizeManagedDocumentCollectionTarget,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  openDocsViewerConfirmModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modals.js";

export function committedDocumentCreateTarget(payload) {
  var response = payload && typeof payload === "object" ? payload : {};
  var target = normalizeManagedDocumentTarget(response.target);
  var docId = String(response.doc_id || "").trim();
  var collection = String(response.collection || "").trim().toLowerCase();
  var recordDocId = String(response.record && response.record.doc_id || "").trim();
  if (docId !== target.doc_id) {
    throw new Error("Create service target does not match its committed document.");
  }
  if (collection !== String(target.collection || "")) {
    throw new Error("Create service target does not match its committed collection.");
  }
  if (recordDocId !== target.doc_id) {
    throw new Error("Create service record does not match its committed target.");
  }
  return target;
}

export function committedDocumentCreatePayload(error) {
  var payload = error && error.payload && typeof error.payload === "object"
    ? error.payload
    : null;
  return payload && payload.committed === true && payload.retry_create === false
    ? payload
    : null;
}

export function normalizeManagedCollectionCreateTarget(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Managed collection create target must be an object.");
  }
  var keys = Object.keys(value).sort();
  if (
    keys.length !== 1
    || keys[0] !== "collection"
  ) {
    throw new Error("Managed collection create target must contain only collection.");
  }
  var collection = String(value.collection || "").trim().toLowerCase();
  if (!collection) throw new Error("Managed collection create target requires a collection ID.");
  return Object.freeze({
    collection: collection
  });
}

export function requestCommittedDocumentSource(target, requestDocumentMode) {
  var sourceTarget = normalizeManagedDocumentTarget(target);
  if (typeof requestDocumentMode !== "function") {
    return Promise.reject(new Error("Source mode is unavailable."));
  }
  return new Promise(function (resolve, reject) {
    var settled = false;

    function restoreRenderedMode() {
      try {
        requestDocumentMode("rendered-document", {
          force: true,
          warn: false
        });
      } catch (_error) {
        // Preserve the committed target error when rendered-mode recovery also fails.
      }
    }

    function fail(error) {
      if (settled) return;
      settled = true;
      restoreRenderedMode();
      reject(error instanceof Error ? error : new Error("Source mode failed to load."));
    }

    function succeed() {
      if (settled) return;
      settled = true;
      resolve(sourceTarget);
    }

    var accepted;
    try {
      accepted = requestDocumentMode("markdown-source", {
        context: {
          sourceTarget: sourceTarget
        },
        onAccepted: succeed,
        onFailed: fail
      });
    } catch (error) {
      fail(error);
      return;
    }
    if (!accepted) {
      fail(new Error("Source mode did not accept the committed target."));
    }
  });
}

function committedCreatePresentationError(target, error) {
  var detail = error && error.message ? String(error.message).trim() : "";
  var message = "Document created, but could not be opened in Source.";
  if (detail && detail !== message) message += " " + detail;
  var presentationError = new Error(message);
  presentationError.committed = true;
  presentationError.target = target || null;
  presentationError.cause = error || null;
  return presentationError;
}

export function interactiveDocumentCreateErrorMessage(error) {
  var detail = error && error.message ? String(error.message).trim() : "";
  if (error && error.committed === true) {
    return detail || "Document created, but could not be opened in Source.";
  }
  if (!detail || detail === "Create failed.") return "Create failed.";
  return "Create failed. " + detail;
}

export function continueCommittedDocumentCreate(payload, options) {
  var settings = options || {};
  var target;
  try {
    target = committedDocumentCreateTarget(payload);
  } catch (error) {
    return Promise.reject(committedCreatePresentationError(null, error));
  }
  if (
    typeof settings.refreshAndSelect !== "function"
    || typeof settings.openSource !== "function"
  ) {
    return Promise.reject(committedCreatePresentationError(
      target,
      new Error("Create presentation callbacks are unavailable.")
    ));
  }
  return Promise.resolve()
    .then(function () {
      return settings.refreshAndSelect(target, payload);
    })
    .then(function () {
      return settings.openSource(target, payload);
    })
    .then(function (sourceResult) {
      if (sourceResult === false) {
        throw new Error("Source mode did not accept the committed target.");
      }
      return {
        payload: payload,
        target: target
      };
    })
    .catch(function (error) {
      var presentationError = error && error.committed === true ? error : committedCreatePresentationError(target, error);
      if (payload.ok === false && payload.error) presentationError.message = payload.error + " " + presentationError.message;
      throw presentationError;
    });
}

export function runInteractiveDocumentCreate(options) {
  var settings = options || {};
  if (typeof settings.create !== "function") {
    return Promise.reject(new Error("Interactive document create requires a create callback."));
  }
  var presentationOptions = {
    refreshAndSelect: settings.refreshAndSelect,
    openSource: settings.openSource
  };
  return Promise.resolve()
    .then(function () {
      return settings.create();
    })
    .then(
      function (payload) {
        return continueCommittedDocumentCreate(payload, presentationOptions);
      },
      function (error) {
        var committedPayload = committedDocumentCreatePayload(error);
        if (!committedPayload) throw error;
        return continueCommittedDocumentCreate(
          committedPayload,
          presentationOptions
        );
      }
    );
}

export function createDocsViewerManagementActionController(options) {
  var root = options.root;
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var selectedDocument = options.selectedDocument || {};
  var context = options.context;
  var callbacks = options.callbacks || {};
  var resolveAction = options.resolveAction;
  if (typeof resolveAction !== "function") {
    throw new Error("Docs Viewer management actions require action target resolution.");
  }

  function actionTargetDoc(actionId, targetDocId) {
    var resolution = arguments.length > 1
      ? resolveAction(actionId, targetDocId)
      : resolveAction(actionId);
    if (!resolution || !resolution.enabled || resolution.targetDocIds.length !== 1) return null;
    return documentIndex.docsById.get(resolution.targetDocIds[0]) || null;
  }

  function managementClientOptions() {
    return callbacks.managementClientOptions ? callbacks.managementClientOptions() : {};
  }

  function getSettingsWorkflow() {
    return callbacks.getSettingsWorkflow ? callbacks.getSettingsWorkflow() : null;
  }

  function hideContextMenu() {
    if (callbacks.hideContextMenu) callbacks.hideContextMenu();
  }

  function setManagementBusy(busy) {
    if (callbacks.setManagementBusy) callbacks.setManagementBusy(busy);
  }

  function setManagementMessage(message, isError) {
    if (callbacks.setManagementMessage) callbacks.setManagementMessage(message, isError);
  }

  function renderManagementUi() {
    if (callbacks.renderManagementUi) callbacks.renderManagementUi();
  }

  function reloadDocsIndex(target) {
    return callbacks.reloadDocsIndex ? callbacks.reloadDocsIndex(target) : Promise.resolve();
  }

  function reloadViewerConfiguration() {
    return callbacks.reloadViewerConfiguration ? callbacks.reloadViewerConfiguration() : Promise.resolve(null);
  }

  function openCreatedDocumentSource(target, payload) {
    if (callbacks.openCreatedDocumentSource) {
      return callbacks.openCreatedDocumentSource(target, payload);
    }
    return handleMarkdownSource(target) === false
      ? Promise.reject(new Error("Source mode is unavailable."))
      : Promise.resolve(target);
  }

  function createDocumentAndOpenSource(payload, optionsForCreate) {
    var createSettings = optionsForCreate || {};
    return runInteractiveDocumentCreate({
      create: function () {
        return createManagedDoc(
          payload,
          createSettings.clientOptions || managementClientOptions()
        );
      },
      refreshAndSelect: function (target, response) {
        if (context.commitDocumentChange) context.commitDocumentChange({ target: target, record: response.record });
        if (createSettings.refreshAndSelect) return createSettings.refreshAndSelect(target, response);
        if (target.collection) return context.routeCommands.loadDoc(target);
        return context.routeCommands.loadIndex({ preserveDocument: true }).then(function () { return context.routeCommands.loadDoc(target, { indexDocId: target.doc_id }); });
      },
      openSource: createSettings.openSource || openCreatedDocumentSource
    })
      .then(function (result) {
        var generationFailed = result.payload.ok === false;
        setManagementMessage(generationFailed ? result.payload.error || result.payload.summary_text : "", generationFailed);
        return result;
      })
      .catch(function (error) {
        setManagementMessage(interactiveDocumentCreateErrorMessage(error), true);
        return null;
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function openCreateTitleModal(title, optionsForModal) {
    var modalSettings = optionsForModal || {};
    return openDocsViewerTextInputModal({
      root: root,
      title: title,
      body: modalSettings.body,
      label: "title",
      initialValue: "New Doc",
      required: true,
      requiredMessage: "Enter a nonblank Title.",
      compactLabel: Boolean(modalSettings.compactLabel),
      primaryLabel: "Create",
      cancelLabel: "Cancel"
    });
  }

  function writeClipboardText(text) {
    if (window.navigator && window.navigator.clipboard && window.isSecureContext) {
      return window.navigator.clipboard.writeText(text);
    }

    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.top = "-1000px";
      textarea.style.left = "-1000px";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      try {
        if (!document.execCommand("copy")) {
          throw new Error("Copy link failed.");
        }
        resolve();
      } catch (error) {
        reject(error);
      } finally {
        document.body.removeChild(textarea);
      }
    });
  }

  async function handleCreateDoc(target) {
    var anchor = target ? normalizeManagedDocumentTarget(target) : null;
    if (anchor && anchor.collection) throw new Error("Ordinary document creation requires an ordinary target.");
    var titleResult = await openCreateTitleModal("New doc title");
    if (!titleResult || !titleResult.confirmed) return;

    var title = titleResult.value;
    setManagementBusy(true);
    setManagementMessage("Creating doc...", false);

    return createDocumentAndOpenSource({
      title: title,
      target_doc_id: anchor ? anchor.doc_id : "",
      placement: anchor ? "after" : "inside"
    });
  }

  async function handleCreateRelatedDoc(kind, targetDocId) {
    var actionId = kind === "child" ? DOCS_VIEWER_ACTION_IDS.NEW_CHILD : DOCS_VIEWER_ACTION_IDS.NEW_SIBLING;
    var baseDoc = targetDocId ? actionTargetDoc(actionId, targetDocId) : null;
    if (!baseDoc) return;

    var titleResult = await openCreateTitleModal(
      kind === "child"
        ? "New child title"
        : "New sibling title",
      { body: "Relative to: " + baseDoc.title + " (" + baseDoc.doc_id + ")." }
    );
    if (!titleResult || !titleResult.confirmed) return;

    var title = titleResult.value;
    var payload = {
      title: title
    };
    payload.target_doc_id = baseDoc.doc_id;
    payload.placement = kind === "child" ? "inside" : "after";

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Creating doc...", false);

    return createDocumentAndOpenSource(payload);
  }

  async function handleCreateCollectionDocument(collection, optionsForCreate) {
    var targetCollection = normalizeManagedCollectionCreateTarget(collection);
    var createSettings = optionsForCreate || {};
    if (typeof createSettings.refreshAndSelect !== "function") {
      throw new Error("Collection document creation requires report refresh ownership.");
    }
    if (management.managementBusy) {
      throw new Error("Docs management is busy.");
    }

    var titleResult = await openCreateTitleModal(
      "New",
      { compactLabel: true }
    );
    if (!titleResult || !titleResult.confirmed) return null;
    var fields = { title: titleResult.value };
    setManagementBusy(true);
    setManagementMessage("Creating doc...", false);
    return createDocumentAndOpenSource(
      {
        ...fields,
        collection: targetCollection.collection
      },
      {
        clientOptions: managementClientOptions(),
        refreshAndSelect: createSettings.refreshAndSelect
      }
    );
  }

  async function handleRegenerateCatalogue(collection, optionsForRegenerate = {}) {
    var target = normalizeManagedDocumentCollectionTarget(collection);
    if (management.managementBusy) throw new Error("Docs management is busy.");
    setManagementBusy(true);
    renderManagementUi();
    try {
      var module = await import("./docs-viewer-management-catalogue-regenerate.js");
      var result = await module.openCatalogueRegenerate({
        root: root, target: target, clientOptions: managementClientOptions(),
        onBusyChange: function (busy) {
          setManagementBusy(busy);
          renderManagementUi();
        },
        refreshCollection: optionsForRegenerate.refreshCollection,
        restoreFocus: optionsForRegenerate.restoreFocus
      });
      if (result) setManagementMessage(result.error || "", result.ok === false);
      return result;
    } finally {
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  /** Keep Rebuild busy through the targeted build and the fresh exact-document reload. */
  async function handleRebuildDocument(value) {
    var target = normalizeManagedDocumentTarget(value);
    if (options.resolveAction(DOCS_VIEWER_ACTION_IDS.REBUILD_DOCUMENT, target).disabled) return;
    setManagementBusy(true);
    setManagementMessage("Rebuilding document...", false);
    try {
      var payload = await rebuildManagedDocument(target, managementClientOptions());
      var completedTarget = normalizeManagedDocumentTarget(payload.target);
      if (completedTarget.doc_id !== target.doc_id || completedTarget.collection !== target.collection) {
        throw new Error("Rebuild response does not match the displayed document.");
      }
      if (!target.collection) await context.routeCommands.loadIndex({ preserveDocument: true });
      var metadata = await readManagedDocMetadata(completedTarget, managementClientOptions());
      if (!metadata || metadata.doc_id !== target.doc_id || (metadata.collection || "") !== (target.collection || "") || !metadata.record) {
        throw new Error("Document rebuilt, but its metadata did not match the displayed target.");
      }
      var projectionErrors = context.commitDocumentChange({ target: completedTarget, record: metadata.record }) || [];
      await context.routeCommands.refreshDocument(completedTarget);
      if (projectionErrors.length) throw new Error("Document rebuilt, but a retained list could not be updated: " + projectionErrors.map(function (error) { return error.message; }).join("; "));
      setManagementMessage("", false);
    } catch (error) {
      setManagementMessage(error.message || "Document rebuild failed.", true);
    } finally {
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  function handleRebuildDocs() {
    var target = normalizeManagedDocumentTarget(selectedDocument.documentTarget || {
      doc_id: context.defaultRouteDocId() || context.defaultDocId()
    });
    setManagementBusy(true);
    setManagementMessage("Rebuilding docs and Search...", false);

    rebuildManagedDocs(managementClientOptions())
      .then(async function () {
        await reloadDocsIndex(target);
        await context.refreshSearch();
        await context.refreshRecent();
        setManagementMessage("", false);
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Docs and Search rebuild failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  async function handlePublish() {
    setManagementBusy(true);
    setManagementMessage("Publishing documents and referenced assets...", false);
    renderManagementUi();
    try {
      var result = await publishManagedDocs(managementClientOptions());
      if (result.complete !== true) throw new Error(result.summary_text || "Publish is incomplete.");
      setManagementMessage("", false);
      if (callbacks.refreshManagementCapabilities) callbacks.refreshManagementCapabilities();
      return result;
    } catch (error) {
      var payload = error && error.payload;
      setManagementMessage(payload && payload.summary_text || error.message || "Publish failed.", true);
      return null;
    } finally {
      try {
        await context.refreshRecent();
      } catch (error) {
        setManagementMessage((management.managementMessage ? management.managementMessage + " " : "") + "Recent could not refresh: " + error.message, true);
      }
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  function handleMarkdownSource(target) {
    if (typeof context.requestDocumentMode !== "function") return false;
    var sourceTarget = normalizeManagedDocumentTarget(target);
    hideContextMenu();
    return context.requestDocumentMode("markdown-source", {
      context: {
        sourceTarget: sourceTarget
      }
    });
  }

  function handleReturnToDoc() {
    if (typeof context.requestDocumentMode !== "function") return;
    hideContextMenu();
    context.requestDocumentMode("rendered-document");
  }

  function handleMarkdownSave() {
    if (!root || typeof root.dispatchEvent !== "function") return;
    root.dispatchEvent(new CustomEvent("docs-viewer-source-editor-save", {
      bubbles: true
    }));
  }

  function handleSettingsSave() {
    var settingsWorkflow = getSettingsWorkflow();
    var settingsFieldState = settingsWorkflow ? settingsWorkflow.fieldState() : null;
    if (!settingsFieldState) {
      if (settingsWorkflow) settingsWorkflow.close();
      return;
    }
    var changes = settingsWorkflow.changes();
    if (!changes) {
      settingsWorkflow.close();
      return;
    }
    settingsWorkflow.close();
    setManagementBusy(true);
    setManagementMessage("Saving settings...", false);
    updateSourceConfigSettings(changes, managementClientOptions())
      .then(function (payload) {
        setManagementMessage("Settings saved.", false);
        var defaultDocChange = payload && payload.changes ? payload.changes.default_doc_id : null;
        var proposedDefaultDocId = defaultDocChange ? String(defaultDocChange.proposed_value || "").trim() : "";
        var target = normalizeManagedDocumentTarget(selectedDocument.documentTarget || {
          doc_id: proposedDefaultDocId || context.defaultDocId()
        });
        if (payload && payload.changed) {
          return reloadViewerConfiguration().then(function () {
            return reloadDocsIndex(target);
          });
        }
        if (callbacks.renderManagementUi) callbacks.renderManagementUi();
        return null;
      })
      .catch(function (error) {
        setManagementMessage(error && error.message ? error.message : "Settings save failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        if (callbacks.renderManagementUi) callbacks.renderManagementUi();
      });
  }

  function handleSettingsSubmit(event) {
    if (event) event.preventDefault();
    handleSettingsSave();
  }

  async function handleDeleteDoc(targetDocId, restoreFocus) {
    if (!targetDocId || management.managementBusy) return;
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE, targetDocId);
    if (!resolution.enabled || !resolution.targetDocIds.length) return;
    var doc = documentIndex.docsById.get(resolution.targetDocIds[0]);
    var count = resolution.targetDocIds.length;
    var label = count + " document" + (count === 1 ? "" : "s");
    var body = [
      "Document: " + doc.title + " (" + doc.doc_id + ").",
      "Permanently deletes this document and all its descendants, including collapsed rows.",
      "Documents to delete: " + count + "."
    ];
    if (resolution.targetDocIds.includes(context.configuredDefaultDocId())) body.push("The configured default document will be cleared.");
    var confirmed = await openDocsViewerConfirmModal({
      root: root, restoreFocus: restoreFocus, title: "Delete " + label + "?",
      body: body, primaryLabel: "Delete " + label, primaryTone: "danger",
      initialFocus: "cancel", cancelLabel: "Cancel"
    });
    if (!confirmed) return;
    setManagementBusy(true);
    setManagementMessage("Deleting " + label + "...", false);
    var completed = false;
    function projectDefault(payload) {
      if (payload.default_doc_id_changed) context.commitDefaultDocumentChange(payload.default_doc_id);
    }
    function matches(payload) {
      return payload && payload.target && payload.target.doc_id === doc.doc_id && !payload.target.collection;
    }
    try {
      var payload = await deleteManagedDoc([doc.doc_id], managementClientOptions());
      if (!matches(payload) || payload.source_deleted !== true || payload.generation_complete !== true
        || !Array.isArray(payload.deleted_doc_ids)) throw new Error("Delete did not return its completed exact target.");
      completed = true;
      projectDefault(payload);
      var displayedId = selectedDocument.displayedDocId;
      var displayedRemoved = !selectedDocument.documentTarget?.collection && payload.deleted_doc_ids.includes(displayedId);
      var failures = [];
      payload.deleted_doc_ids.forEach(function (docId) {
        if (!displayedRemoved || docId !== displayedId) failures.push(...(context.commitDocumentChange({ target: { doc_id: docId }, deleted: true }) || []));
      });
      if (displayedRemoved) await context.commitDeletedDocument({ doc_id: displayedId });
      else await callbacks.refreshIndexTree();
      if (failures.length) throw new Error(failures.map(function (error) { return error.message; }).join("; "));
      setManagementMessage("", false);
      return payload;
    } catch (error) {
      var partial = error.payload;
      var projectionFailures = [];
      if (matches(partial)) {
        projectDefault(partial);
        (Array.isArray(partial.deleted_doc_ids) ? partial.deleted_doc_ids : []).forEach(function (docId) {
          projectionFailures.push(...(context.commitDocumentChange({ target: { doc_id: docId }, deleted: true }) || []));
        });
      }
      var projectionMessage = projectionFailures.length ? " Retained views could not be updated: " + projectionFailures.map(function (failure) { return failure.message; }).join("; ") : "";
      setManagementMessage((completed ? "Documents deleted and generated state updated, but display failed: " : "") + (error.message || "Delete failed.") + projectionMessage, true);
      return null;
    } finally {
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  async function handlePositionDoc(targetDocId, restoreFocus) {
    var doc = targetDocId ? actionTargetDoc(DOCS_VIEWER_ACTION_IDS.POSITION, targetDocId) : null;
    if (!doc || management.managementBusy) return;
    hideContextMenu();
    return openDocsViewerPositionModal({
      root: root,
      restoreFocus: restoreFocus,
      doc: doc,
      docs: documentIndex.docs,
      collectionHostDocIds: options.collectionHostDocIds(),
      onSave: async function (targetDocId, placement) {
        setManagementBusy(true);
        try {
          var payload = await moveManagedDoc(doc.doc_id, targetDocId, placement, managementClientOptions());
          if (payload.target?.doc_id !== doc.doc_id || payload.target.collection
            || payload.position_saved !== true || payload.generation_complete !== true || !payload.committed_document) {
            throw new Error("Position did not return its completed exact target.");
          }
          var failures = context.commitDocumentChange(payload.committed_document) || [];
          await callbacks.refreshIndexTree();
          if (failures.length) throw new Error("Position saved, but a retained view could not be updated: " + failures.map(function (error) { return error.message; }).join("; "));
        } catch (error) {
          var partial = error.payload;
          if (partial?.target?.doc_id === doc.doc_id && !partial.target.collection && partial.position_saved && partial.committed_document) {
            var partialFailures = context.commitDocumentChange(partial.committed_document) || [];
            if (partialFailures.length) throw new Error(error.message + "; retained views could not be updated: " + partialFailures.map(function (failure) { return failure.message; }).join("; "), { cause: error });
          }
          throw error;
        } finally {
          setManagementBusy(false);
          renderManagementUi();
        }
      }
    });
  }

  function handleOpenSource(editor, target, title) {
    var sourceTarget = normalizeManagedDocumentTarget(target);
    if (options.resolveAction(editor === "vscode" ? DOCS_VIEWER_ACTION_IDS.OPEN_VSCODE : DOCS_VIEWER_ACTION_IDS.OPEN, sourceTarget).disabled) return;
    var targetTitle = String(title || sourceTarget.doc_id).trim() || sourceTarget.doc_id;

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Opening source for " + targetTitle + "...", false);
    renderManagementUi();

    return openManagedDocSource(sourceTarget, editor, managementClientOptions())
      .then(function () {
        setManagementMessage("", false);
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Open source failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleCopyLink(targetDocId) {
    var doc = targetDocId ? actionTargetDoc(DOCS_VIEWER_ACTION_IDS.COPY_LINK, targetDocId) : null;
    if (!doc || typeof context.markdownDocLink !== "function") return;
    var markdownLink = context.markdownDocLink(doc);
    if (!markdownLink) return;

    hideContextMenu();
    writeClipboardText(markdownLink)
      .catch(function (error) {
        var message = error && error.message ? error.message : "Copy link failed.";
        setManagementMessage(message, true);
      });
  }

  return {
    handleCopyLink: handleCopyLink,
    handleCreateDoc: handleCreateDoc,
    handleCreateRelatedDoc: handleCreateRelatedDoc,
    handleCreateCollectionDocument: handleCreateCollectionDocument,
    handleRegenerateCatalogue: handleRegenerateCatalogue,
    handleDeleteDoc: handleDeleteDoc,
    handleMarkdownSave: handleMarkdownSave,
    handleReturnToDoc: handleReturnToDoc,
    handlePositionDoc: handlePositionDoc,
    handleOpenSource: handleOpenSource,
    handlePublish: handlePublish,
    handleRebuildDocs: handleRebuildDocs,
    handleRebuildDocument: handleRebuildDocument,
    handleSettingsSubmit: handleSettingsSubmit
  };
}
