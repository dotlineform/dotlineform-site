import {
  applyManagedDocDelete,
  applyManagedDocsPublish,
  confirmManagedDocsPublish,
  createManagedDoc,
  moveManagedDoc,
  openManagedDocSource,
  previewManagedDocDelete,
  rebuildManagedDocs,
  updateSourceConfigSettings,
  updateManagedDocMetadata
} from "./docs-viewer-management-client.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  buildDocsViewerDeletePreviewBody,
  openDocsViewerConfirmModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modals.js";

var ACTION_TEXT = {
  cancelButton: "Cancel",
  createDocTitle: "New doc title",
  createSubscopeDocTitle: "New",
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
  publishChecking: "Checking publish changes...",
  publishConfirmTitle: "Publish to site assets",
  publishConfirmButton: "Publish",
  publishApplying: "Copying docs to site assets...",
  publishApplied: "Docs copied to site assets.",
  publishFailed: "Publish failed.",
  copyLinkFailed: "Copy link failed."
};

export function committedDocumentCreateTarget(payload) {
  var response = payload && typeof payload === "object" ? payload : {};
  var target = normalizeManagedDocumentTarget(response.target);
  var docId = String(response.doc_id || "").trim();
  var scope = String(response.scope || "").trim().toLowerCase();
  var subScope = String(response.sub_scope || "").trim().toLowerCase();
  var recordDocId = String(response.record && response.record.doc_id || "").trim();
  if (docId !== target.doc_id) {
    throw new Error("Create service target does not match its committed document.");
  }
  if (scope !== target.scope) {
    throw new Error("Create service target does not match its committed scope.");
  }
  if (subScope !== String(target.sub_scope || "")) {
    throw new Error("Create service target does not match its committed sub-scope.");
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

export function normalizeManagedSubscopeCollection(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Managed sub-scope collection must be an object.");
  }
  var keys = Object.keys(value).sort();
  if (
    keys.length !== 2
    || keys[0] !== "scope"
    || keys[1] !== "sub_scope"
  ) {
    throw new Error("Managed sub-scope collection must contain exactly scope and sub_scope.");
  }
  var scope = String(value.scope || "").trim().toLowerCase();
  var subScope = String(value.sub_scope || "").trim().toLowerCase();
  if (!scope) throw new Error("Managed sub-scope collection scope is required.");
  if (!subScope) throw new Error("Managed sub-scope collection sub_scope is required.");
  return Object.freeze({
    scope: scope,
    sub_scope: subScope
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
  var searchRecent = options.searchRecent || {};
  var selectedDocument = options.selectedDocument || {};
  var context = options.context;
  var callbacks = options.callbacks || {};
  var resolveAction = options.resolveAction;
  if (typeof resolveAction !== "function") {
    throw new Error("Docs Viewer management actions require action target resolution.");
  }

  function currentActiveDoc() {
    return callbacks.currentActiveDoc ? callbacks.currentActiveDoc() : null;
  }

  function currentContextMenuDoc() {
    return callbacks.currentContextMenuDoc ? callbacks.currentContextMenuDoc() : null;
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

  function clearDragState() {
    if (callbacks.clearDragState) callbacks.clearDragState();
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
      refreshAndSelect: createSettings.refreshAndSelect || function (target) {
        return reloadDocsIndex(target.doc_id, "");
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
      label: ACTION_TEXT.createDocLabel,
      initialValue: ACTION_TEXT.createDocDefaultTitle,
      defaultValue: ACTION_TEXT.createDocDefaultTitle,
      compactLabel: Boolean(modalSettings.compactLabel),
      primaryLabel: ACTION_TEXT.createDocButton,
      cancelLabel: ACTION_TEXT.cancelButton
    });
  }

  function committedMoveRecord(response, expectedDocId) {
    var record = response && response.record && typeof response.record === "object" ? response.record : null;
    var docId = String(record && record.doc_id || "").trim();
    if (!record || !Object.prototype.hasOwnProperty.call(record, "parent_id") || docId !== expectedDocId) {
      throw new Error("Move service returned an invalid committed move record.");
    }
    return record;
  }

  function invalidateCommittedMoveCaches(record) {
    var docId = String(record && record.doc_id || "").trim();
    if (docId && selectedDocument.payloadCache && typeof selectedDocument.payloadCache.delete === "function") {
      selectedDocument.payloadCache.delete(docId);
    }
    searchRecent.searchEntries = [];
    searchRecent.searchLoaded = false;
    searchRecent.searchRequestPromise = null;
    searchRecent.recentEntries = [];
    searchRecent.recentLoaded = false;
    searchRecent.recentRequestPromise = null;
  }

  function recoverCommittedMoveProjection(error) {
    var detail = error && error.message ? error.message : "unknown local projection failure";
    if (window.console && typeof window.console.error === "function") {
      window.console.error("docs_viewer: committed move projection failed", error);
    }
    setManagementMessage("Move committed, but the local index update failed. Reloading the index...", true);
    return reloadDocsIndex(selectedDocument.selectedDocId, "")
      .then(function () {
        setManagementMessage("Move committed. The index was reloaded after a local update failed.", true);
      })
      .catch(function (recoveryError) {
        var recoveryDetail = recoveryError && recoveryError.message ? recoveryError.message : "index reload failed";
        throw new Error("Move committed, but local projection failed (" + detail + ") and recovery failed (" + recoveryDetail + ").");
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

  async function handleCreateDoc() {
    var titleResult = await openCreateTitleModal(ACTION_TEXT.createDocTitle);
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle;
    var currentDoc = currentActiveDoc();

    setManagementBusy(true);
    setManagementMessage("Creating doc...", false);

    return createDocumentAndOpenSource({
      title: title,
      parent_id: currentDoc ? String(currentDoc.parent_id || "").trim() : ""
    });
  }

  async function handleCreateRelatedDoc(kind) {
    var contextDoc = currentContextMenuDoc();
    var actionId = kind === "child" ? DOCS_VIEWER_ACTION_IDS.NEW_CHILD : DOCS_VIEWER_ACTION_IDS.NEW_SIBLING;
    var baseDoc = contextDoc ? actionTargetDoc(actionId, contextDoc.doc_id) : null;
    if (!baseDoc) return;

    var titleResult = await openCreateTitleModal(
      kind === "child"
        ? ACTION_TEXT.createChildDocTitle
        : ACTION_TEXT.createSiblingDocTitle
    );
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle;
    var payload = {
      title: title
    };
    if (kind === "child") {
      payload.parent_id = baseDoc.doc_id;
    } else {
      payload.parent_id = String(baseDoc.parent_id || "").trim();
    }

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Creating doc...", false);

    return createDocumentAndOpenSource(payload);
  }

  async function handleCreateSubscopeDocument(collection, optionsForCreate) {
    var targetCollection = normalizeManagedSubscopeCollection(collection);
    var createSettings = optionsForCreate || {};
    var currentScope = String(
      callbacks.viewerScope ? callbacks.viewerScope() : ""
    ).trim().toLowerCase();
    if (currentScope !== targetCollection.scope) {
      throw new Error("Mounted sub-scope collection does not match the active scope.");
    }
    if (typeof createSettings.refreshAndSelect !== "function") {
      throw new Error("Sub-scope document creation requires report refresh ownership.");
    }
    if (management.managementBusy) {
      throw new Error("Docs management is busy.");
    }

    var titleResult = await openCreateTitleModal(
      ACTION_TEXT.createSubscopeDocTitle,
      { compactLabel: true }
    );
    if (!titleResult || !titleResult.confirmed) return null;

    var title = String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle;
    setManagementBusy(true);
    setManagementMessage("Creating doc...", false);
    return createDocumentAndOpenSource(
      {
        title: title,
        sub_scope: targetCollection.sub_scope
      },
      {
        clientOptions: Object.assign({}, managementClientOptions(), {
          scope: targetCollection.scope
        }),
        refreshAndSelect: createSettings.refreshAndSelect
      }
    );
  }

  function handleEditMetadataSave(target, payload) {
    if (!target || !payload) return Promise.resolve(null);
    var normalizedTarget = normalizeManagedDocumentTarget(target);
    var doc = documentIndex.docsById.get(normalizedTarget.doc_id);
    var title = doc && doc.title ? doc.title : payload.title;

    setManagementBusy(true);
    renderManagementUi();
    setManagementMessage("Saving metadata for " + title + "...", false);

    return updateManagedDocMetadata(normalizedTarget, payload, managementClientOptions())
      .then(function (response) {
        setManagementMessage("", false);
        if (normalizedTarget.sub_scope) {
          return callbacks.reloadMetadataTarget
            ? callbacks.reloadMetadataTarget(normalizedTarget, response)
            : response;
        }
        return reloadDocsIndex(normalizedTarget.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Metadata update failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleRebuildDocs() {
    setManagementBusy(true);
    setManagementMessage("Rebuilding docs...", false);

    rebuildManagedDocs(managementClientOptions())
      .then(function () {
        var targetDocId = selectedDocument.selectedDocId || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(targetDocId, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Docs rebuild failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function publishConfirmBody(preview) {
    var changed = Number(preview && preview.changed_count || 0);
    var removed = Number(preview && preview.removed_count || 0);
    var paths = preview && preview.paths ? preview.paths : {};
    return [
      "Copy reviewed working docs to the site assets for this public route?",
      "",
      "Changed files: " + changed,
      "Stale files to remove: " + removed,
      "",
      "From: " + String(paths.working_docs_root || ""),
      "To: " + String(paths.published_docs_root || "")
    ].join("\n");
  }

  function publishHasChanges(preview) {
    var changed = Number(preview && preview.changed_count || 0);
    var removed = Number(preview && preview.removed_count || 0);
    return changed + removed > 0;
  }

  function handlePublishDocs() {
    setManagementBusy(true);
    setManagementMessage(ACTION_TEXT.publishChecking, false);

    confirmManagedDocsPublish(managementClientOptions())
      .then(function (preview) {
        setManagementBusy(false);
        return openDocsViewerConfirmModal({
          root: root,
          title: ACTION_TEXT.publishConfirmTitle,
          body: publishConfirmBody(preview),
          primaryLabel: ACTION_TEXT.publishConfirmButton,
          cancelLabel: ACTION_TEXT.cancelButton,
          primaryDisabled: !publishHasChanges(preview)
        });
      })
      .then(function (confirmed) {
        if (!confirmed) {
          setManagementMessage("", false);
          return null;
        }
        setManagementBusy(true);
        setManagementMessage(ACTION_TEXT.publishApplying, false);
        return applyManagedDocsPublish(managementClientOptions());
      })
      .then(function (payload) {
        if (!payload) return;
        setManagementMessage(payload.summary_text || ACTION_TEXT.publishApplied, false);
        if (callbacks.refreshManagementCapabilities) callbacks.refreshManagementCapabilities();
      })
      .catch(function (error) {
        setManagementMessage(error.message || ACTION_TEXT.publishFailed, true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
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

  function handleDeleteDoc() {
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE);
    var checkedDocIds = resolution && resolution.enabled
      ? resolution.targetDocIds.slice()
      : [];
    if (!checkedDocIds.length) return;
    var checkedCount = checkedDocIds.length;
    var checkedLabel = checkedCount === 1
      ? "the selected document"
      : checkedCount + " checked documents";

    setManagementBusy(true);
    setManagementMessage("Checking delete impact for " + checkedLabel + "...", false);

    previewManagedDocDelete(checkedDocIds, managementClientOptions())
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
          title: "Delete " + deleteLabel + "?",
          body: buildDocsViewerDeletePreviewBody(preview),
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
          return applyManagedDocDelete(checkedDocIds, managementClientOptions());
        });
      })
      .then(function (payload) {
        if (!payload) return;
        var fallbackDocId = firstRemainingRootDocId(
          documentIndex.allDocs,
          payload.deleted_doc_ids || checkedDocIds,
          context.resolveLoadableDocId
        );
        setManagementMessage("", false);
        var configReload = payload.default_doc_id_changed
          ? reloadViewerConfiguration()
          : Promise.resolve(null);
        return configReload.then(function () {
          return reloadDocsIndex(fallbackDocId, "");
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

  function handleMoveDoc(docId, parentId) {
    var movingDocId = String(docId || "").trim();
    if (!movingDocId) return;
    var movingDoc = documentIndex.docsById.get(movingDocId) || null;
    var nextParentId = String(parentId || "").trim();
    if (!movingDoc) return;
    if (nextParentId && !documentIndex.docsById.has(nextParentId)) return;

    setManagementBusy(true);
    clearDragState();
    setManagementMessage("Moving " + movingDoc.title + "...", false);

    return moveManagedDoc(movingDoc.doc_id, nextParentId, managementClientOptions())
      .then(function (response) {
        var record;
        setManagementBusy(false);
        try {
          record = committedMoveRecord(response, movingDoc.doc_id);
          if (typeof callbacks.projectCommittedMove !== "function") {
            throw new Error("Docs Viewer local move projection is unavailable.");
          }
          callbacks.projectCommittedMove(record);
          invalidateCommittedMoveCaches(record);
        } catch (error) {
          setManagementBusy(true);
          return recoverCommittedMoveProjection(error);
        }
        setManagementMessage("", false);
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Move failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleOpenSource(editor, target, title) {
    var sourceTarget = normalizeManagedDocumentTarget(target);
    var targetTitle = String(title || sourceTarget.doc_id).trim() || sourceTarget.doc_id;

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Opening source for " + targetTitle + "...", false);

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

  function handleCopyLink() {
    var contextDoc = currentContextMenuDoc();
    var doc = contextDoc ? actionTargetDoc(DOCS_VIEWER_ACTION_IDS.COPY_LINK, contextDoc.doc_id) : null;
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
    handleCreateSubscopeDocument: handleCreateSubscopeDocument,
    handleDeleteDoc: handleDeleteDoc,
    handleEditMetadataSave: handleEditMetadataSave,
    handleMarkdownSave: handleMarkdownSave,
    handleMarkdownSource: handleMarkdownSource,
    handleReturnToDoc: handleReturnToDoc,
    handleMoveDoc: handleMoveDoc,
    handleOpenSource: handleOpenSource,
    handlePublishDocs: handlePublishDocs,
    handleRebuildDocs: handleRebuildDocs,
    handleSettingsSubmit: handleSettingsSubmit
  };
}
