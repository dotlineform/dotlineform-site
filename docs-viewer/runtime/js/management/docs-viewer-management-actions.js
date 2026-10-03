import { publishManagedDocs } from "./docs-viewer-management-client.js";
import { openDocsViewerPositionModal } from "./docs-viewer-position-modal.js";
import {
  applyManagedDocDelete,
  createManagedDoc,
  moveManagedDoc,
  openManagedDocSource,
  previewManagedDocDelete,
  rebuildManagedDocs,
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
  buildDocsViewerDeletePreviewBody,
  docsViewerDeleteCompletionMessage,
  openDocsViewerConfirmModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modals.js";

var ACTION_TEXT = {
  cancelButton: "Cancel",
  createDocTitle: "New doc title",
  createCollectionDocTitle: "New",
  createChildDocTitle: "New child title",
  createSiblingDocTitle: "New sibling title",
  createDocLabel: "title",
  createDocDefaultTitle: "New Doc",
  createDocButton: "Create",
  createFailed: "Create failed.",
  createCommittedOpenFailed: "Document created, but could not be opened in Source.",
  settingsSaving: "Saving settings...",
  settingsSaved: "Settings saved.",
  settingsSaveFailed: "Settings save failed.",
  deployFailed: "Publish failed.",
  copyLinkFailed: "Copy link failed."
};

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
  var message = ACTION_TEXT.createCommittedOpenFailed;
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
    return detail || ACTION_TEXT.createCommittedOpenFailed;
  }
  if (!detail || detail === ACTION_TEXT.createFailed) return ACTION_TEXT.createFailed;
  return ACTION_TEXT.createFailed + " " + detail;
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
      if (error && error.committed === true) throw error;
      throw committedCreatePresentationError(target, error);
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

export function firstRemainingRootDocId(docs, deletedDocIds, resolveLoadableDocId) {
  var records = Array.isArray(docs) ? docs : [];
  var deletedIds = new Set(
    (Array.isArray(deletedDocIds) ? deletedDocIds : [deletedDocIds]).map(function (docId) {
      return String(docId || "").trim();
    }).filter(Boolean)
  );
  var remaining = records.filter(function (doc) {
    return doc && !deletedIds.has(String(doc.doc_id || "").trim());
  });
  var roots = remaining.filter(function (doc) {
    return !String(doc.parent_id || "").trim();
  });
  var candidates = roots.length ? roots : remaining;
  for (var i = 0; i < candidates.length; i += 1) {
    var docId = String(candidates[i].doc_id || "").trim();
    if (!docId) continue;
    var loadableDocId = typeof resolveLoadableDocId === "function"
      ? String(resolveLoadableDocId(docId) || "").trim()
      : docId;
    if (loadableDocId) return loadableDocId;
  }
  return "";
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

  function reloadDocsIndex(targetDocId, summaryText) {
    return callbacks.reloadDocsIndex ? callbacks.reloadDocsIndex(targetDocId, summaryText) : Promise.resolve();
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
        setManagementMessage("", false);
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
      label: ACTION_TEXT.createDocLabel,
      initialValue: ACTION_TEXT.createDocDefaultTitle,
      defaultValue: ACTION_TEXT.createDocDefaultTitle,
      compactLabel: Boolean(modalSettings.compactLabel),
      primaryLabel: ACTION_TEXT.createDocButton,
      cancelLabel: ACTION_TEXT.cancelButton
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
          throw new Error(ACTION_TEXT.copyLinkFailed);
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
    var titleResult = await openCreateTitleModal(ACTION_TEXT.createDocTitle);
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle;
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
        ? ACTION_TEXT.createChildDocTitle
        : ACTION_TEXT.createSiblingDocTitle,
      { body: "Relative to: " + baseDoc.title + " (" + baseDoc.doc_id + ")." }
    );
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle;
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
      ACTION_TEXT.createCollectionDocTitle,
      { compactLabel: true }
    );
    if (!titleResult || !titleResult.confirmed) return null;
    var fields = { title: String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle };
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

  function handleRebuildDocs() {
    setManagementBusy(true);
    setManagementMessage("Rebuilding docs and Search...", false);

    rebuildManagedDocs(managementClientOptions())
      .then(function () {
        var targetDocId = selectedDocument.selectedDocId || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(targetDocId, "");
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
      setManagementMessage(result.summary_text || "Publish complete.", false);
      if (callbacks.refreshManagementCapabilities) callbacks.refreshManagementCapabilities();
      return result;
    } catch (error) {
      var payload = error && error.payload;
      setManagementMessage(payload && payload.summary_text || error.message || "Publish failed.", true);
      return null;
    } finally {
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
    setManagementMessage(ACTION_TEXT.settingsSaving, false);
    updateSourceConfigSettings(changes, managementClientOptions())
      .then(function (payload) {
        setManagementMessage(ACTION_TEXT.settingsSaved, false);
        var defaultDocChange = payload && payload.changes ? payload.changes.default_doc_id : null;
        var proposedDefaultDocId = defaultDocChange ? String(defaultDocChange.proposed_value || "").trim() : "";
        var targetDocId = selectedDocument.selectedDocId || proposedDefaultDocId || context.defaultDocId();
        if (payload && payload.changed) {
          return reloadViewerConfiguration().then(function () {
            return callbacks.reloadDocsIndex ? callbacks.reloadDocsIndex(targetDocId) : null;
          });
        }
        if (callbacks.renderManagementUi) callbacks.renderManagementUi();
        return null;
      })
      .catch(function (error) {
        setManagementMessage(error && error.message ? error.message : ACTION_TEXT.settingsSaveFailed, true);
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

  function handleDeleteDoc(targetDocId, restoreFocus) {
    if (!targetDocId || management.managementBusy) return;
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE, targetDocId);
    var docIds = resolution && resolution.enabled
      ? resolution.targetDocIds.slice(0, 1)
      : [];
    if (!docIds.length) return;
    var doc = documentIndex.docsById.get(docIds[0]);
    if (!doc) return;

    setManagementBusy(true);
    setManagementMessage("Checking delete impact for " + doc.title + " and its descendants...", false);

    return previewManagedDocDelete(docIds, managementClientOptions())
      .then(function (preview) {
        if (!preview.allowed) {
          var blockerText = (preview.blockers || []).join("; ") || "Delete is blocked.";
          setManagementMessage(blockerText, true);
          return null;
        }
        var deleteCount = Number(preview.delete_count) || 1;
        var deleteLabel = deleteCount + " document" + (deleteCount === 1 ? "" : "s");
        setManagementBusy(false);
        setManagementMessage("", false);
        return openDocsViewerConfirmModal({
          root: root,
          restoreFocus: restoreFocus,
          title: "Delete " + deleteLabel + "?",
          body: [
            "Document: " + doc.title + " (" + doc.doc_id + ").",
            "Deletes this document and all its descendants.",
            ...buildDocsViewerDeletePreviewBody(preview)
          ],
          primaryLabel: "Delete " + deleteLabel,
          primaryTone: "danger",
          initialFocus: "cancel",
          cancelLabel: ACTION_TEXT.cancelButton
        }).then(function (confirmed) {
          if (!confirmed) {
            setManagementMessage("", false);
            return null;
          }
          setManagementBusy(true);
          setManagementMessage("Deleting " + deleteLabel + "...", false);
          return applyManagedDocDelete(docIds, managementClientOptions());
        });
      })
      .then(function (payload) {
        if (!payload) return;
        var deletedDocIds = payload.deleted_doc_ids || resolution.targetDocIds;
        var displayedRemoved = !selectedDocument.documentTarget?.collection && deletedDocIds.includes(selectedDocument.displayedDocId);
        var displayedDocId = selectedDocument.displayedDocId;
        setManagementMessage("", false);
        var configReload = payload.default_doc_id_changed ? reloadViewerConfiguration() : Promise.resolve(null);
        return configReload.then(function () {
          deletedDocIds.forEach(function (docId) {
            if (!displayedRemoved || docId !== displayedDocId) context.commitDocumentChange({ target: { doc_id: docId }, deleted: true });
          });
          if (displayedRemoved && context.commitDeletedDocument) return context.commitDeletedDocument({ doc_id: displayedDocId });
          return callbacks.refreshIndexTree();
        }).then(function (result) {
          var completionMessage = docsViewerDeleteCompletionMessage(payload);
          if (completionMessage) setManagementMessage(completionMessage, false);
          return result;
        });
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Delete failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  async function handlePositionDoc(targetDocId, restoreFocus) {
    var doc = targetDocId ? actionTargetDoc(DOCS_VIEWER_ACTION_IDS.POSITION, targetDocId) : null;
    if (!doc || management.managementBusy) return;
    hideContextMenu();
    return openDocsViewerPositionModal({
      root: root,
      restoreFocus: restoreFocus,
      doc: doc,
      docs: documentIndex.allDocs,
      onSave: async function (targetDocId, placement) {
        setManagementBusy(true);
        try {
          await moveManagedDoc(doc.doc_id, targetDocId, placement, managementClientOptions());
          await callbacks.refreshIndexTree();
        } finally {
          setManagementBusy(false);
          renderManagementUi();
        }
      }
    });
  }

  function handleOpenSource(editor, target, title) {
    var sourceTarget = normalizeManagedDocumentTarget(target);
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
        var message = error && error.message ? error.message : ACTION_TEXT.copyLinkFailed;
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
    handleSettingsSubmit: handleSettingsSubmit
  };
}
