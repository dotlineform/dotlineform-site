import {
  applyManagedDocDelete,
  applyManagedDocsStaticHtmlExport,
  applyManagedDocsPublish,
  confirmManagedDocsPublish,
  createManagedDoc,
  moveManagedDoc,
  openManagedDocSource,
  previewManagedDocDelete,
  rebuildManagedDocs,
  updateSourceConfigSettings,
  updateManagedDocMetadata,
  updateManagedDocsViewability
} from "./docs-viewer-management-client.js";
import {
  isDocNonViewable,
  isDocViewable
} from "../shared/docs-viewer-tree.js";
import {
  resolveViewabilityTargetDocIds
} from "./docs-viewer-management-action-workflow.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  buildDocsViewerDeletePreviewBody,
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modals.js";

var ACTION_TEXT = {
  cancelButton: "Cancel",
  confirmContinueButton: "Continue",
  viewableAncestorPrompt: "Showing this doc also requires showing these parent docs:\n\n{titles}\n\nContinue?",
  viewableAncestorTitle: "Show parent docs",
  viewableDescendantPrompt: "Choose whether to show only this doc or include its descendant docs.",
  viewableDescendantTitle: "Show descendants",
  viewableDescendantSelectedLabel: "Selected doc only",
  viewableDescendantAllLabel: "Selected doc and descendants",
  viewableInvalidChoice: "Show update cancelled: expected `all` or `selected`.",
  createDocTitle: "New doc title",
  createChildDocTitle: "New child title",
  createSiblingDocTitle: "New sibling title",
  createDocLabel: "title",
  createDocDefaultTitle: "New Doc",
  createDocButton: "Create",
  deleteConfirmTitle: "Confirm delete",
  deleteConfirmButton: "Delete",
  settingsSaving: "Saving settings...",
  settingsSaved: "Settings saved.",
  settingsSaveFailed: "Settings save failed.",
  publishChecking: "Checking publish changes...",
  publishConfirmTitle: "Publish to site assets",
  publishConfirmButton: "Publish",
  publishApplying: "Copying docs to site assets...",
  publishApplied: "Docs copied to site assets.",
  publishFailed: "Publish failed.",
  exportConfirmTitle: "Export docs",
  exportConfirmButton: "Export",
  exportApplying: "Exporting docs as static HTML...",
  exportApplied: "Docs exported as static HTML.",
  exportFailed: "Static HTML export failed.",
  copyLinkFailed: "Copy link failed."
};

export function firstRemainingRootDocId(docs, deletedDocId, resolveLoadableDocId) {
  var records = Array.isArray(docs) ? docs : [];
  var remaining = records.filter(function (doc) {
    return doc && doc.doc_id !== deletedDocId;
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
  var refs = options.refs || {};
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

  async function viewabilityTargetDocIds(doc) {
    return resolveViewabilityTargetDocIds({
      doc: doc,
      allDocs: documentIndex.allDocs,
      findDocById: context.findAllDocById,
      confirmAncestors: function (detail) {
        var ancestorMessage = context.formatText(ACTION_TEXT.viewableAncestorPrompt, {
          titles: detail.titles
        });
        return openDocsViewerConfirmModal({
          root: root,
          title: ACTION_TEXT.viewableAncestorTitle,
          body: ancestorMessage,
          primaryLabel: ACTION_TEXT.confirmContinueButton,
          cancelLabel: ACTION_TEXT.cancelButton
        });
      },
      chooseDescendants: function () {
        return openDocsViewerChoiceModal({
          root: root,
          title: ACTION_TEXT.viewableDescendantTitle,
          body: ACTION_TEXT.viewableDescendantPrompt,
          value: "selected",
          choices: [
            { value: "selected", label: ACTION_TEXT.viewableDescendantSelectedLabel },
            { value: "all", label: ACTION_TEXT.viewableDescendantAllLabel }
          ],
          primaryLabel: ACTION_TEXT.confirmContinueButton,
          cancelLabel: ACTION_TEXT.cancelButton
        });
      },
      onInvalidChoice: function () {
        setManagementMessage(ACTION_TEXT.viewableInvalidChoice, true);
      }
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
    var titleResult = await openDocsViewerTextInputModal({
      root: root,
      title: ACTION_TEXT.createDocTitle,
      label: ACTION_TEXT.createDocLabel,
      initialValue: ACTION_TEXT.createDocDefaultTitle,
      defaultValue: ACTION_TEXT.createDocDefaultTitle,
      primaryLabel: ACTION_TEXT.createDocButton,
      cancelLabel: ACTION_TEXT.cancelButton
    });
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || ACTION_TEXT.createDocDefaultTitle;
    var currentDoc = currentActiveDoc();

    setManagementBusy(true);
    setManagementMessage("Creating doc...", false);

    createManagedDoc({
      title: title,
      parent_id: currentDoc ? String(currentDoc.parent_id || "").trim() : ""
    }, managementClientOptions())
      .then(function (payload) {
        setManagementMessage("", false);
        return reloadDocsIndex(payload.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Create failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  async function handleCreateRelatedDoc(kind) {
    var contextDoc = currentContextMenuDoc();
    var actionId = kind === "child" ? DOCS_VIEWER_ACTION_IDS.NEW_CHILD : DOCS_VIEWER_ACTION_IDS.NEW_SIBLING;
    var baseDoc = contextDoc ? actionTargetDoc(actionId, contextDoc.doc_id) : null;
    if (!baseDoc) return;

    var titleResult = await openDocsViewerTextInputModal({
      root: root,
      title: kind === "child" ? ACTION_TEXT.createChildDocTitle : ACTION_TEXT.createSiblingDocTitle,
      label: ACTION_TEXT.createDocLabel,
      initialValue: ACTION_TEXT.createDocDefaultTitle,
      defaultValue: ACTION_TEXT.createDocDefaultTitle,
      primaryLabel: ACTION_TEXT.createDocButton,
      cancelLabel: ACTION_TEXT.cancelButton
    });
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

    createManagedDoc(payload, managementClientOptions())
      .then(function (response) {
        setManagementMessage("", false);
        return reloadDocsIndex(response.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Create failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleEditMetadataSave(payload) {
    if (!payload) return;
    var doc = documentIndex.docsById.get(payload.doc_id);
    var title = doc && doc.title ? doc.title : payload.title;

    setManagementBusy(true);
    renderManagementUi();
    setManagementMessage("Saving metadata for " + title + "...", false);

    updateManagedDocMetadata(payload, managementClientOptions())
      .then(function () {
        setManagementMessage("", false);
        return reloadDocsIndex(payload.doc_id, "");
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

  function currentScopeExportDetail() {
    var scopeId = typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
    var capabilities = management.managementCapabilities || {};
    var scopeCaps = capabilities.scopes && scopeId ? capabilities.scopes[scopeId] : null;
    return scopeCaps && scopeCaps.static_html_export ? scopeCaps.static_html_export : {};
  }

  function exportConfirmBody() {
    var scopeId = typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
    var detail = currentScopeExportDetail();
    var docCount = Number(detail.document_count || 0);
    var defaultDocId = String(detail.default_doc_id || "").trim() || "(none)";
    var destination = String(detail.destination || "").trim() || "/docs-export/" + scopeId + "/";
    return [
      "Source scope: " + scopeId,
      "Documents: " + docCount,
      "Default document: " + defaultDocId,
      "Destination folder: " + destination
    ].join("\n");
  }

  function handleExportDocs() {
    openDocsViewerConfirmModal({
      root: root,
      title: ACTION_TEXT.exportConfirmTitle,
      body: exportConfirmBody(),
      primaryLabel: ACTION_TEXT.exportConfirmButton,
      cancelLabel: ACTION_TEXT.cancelButton
    })
      .then(function (confirmed) {
        if (!confirmed) {
          setManagementMessage("", false);
          return null;
        }
        setManagementBusy(true);
        setManagementMessage(ACTION_TEXT.exportApplying, false);
        return applyManagedDocsStaticHtmlExport(managementClientOptions());
      })
      .then(function (payload) {
        if (!payload) return;
        setManagementMessage(payload.summary_text || ACTION_TEXT.exportApplied, false);
        if (callbacks.refreshManagementCapabilities) callbacks.refreshManagementCapabilities();
      })
      .catch(function (error) {
        setManagementMessage(error.message || ACTION_TEXT.exportFailed, true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleMarkdownSource() {
    var doc = actionTargetDoc(DOCS_VIEWER_ACTION_IDS.MARKDOWN_SOURCE);
    if (!doc || typeof context.requestDocumentMode !== "function") return;
    hideContextMenu();
    var activeMode = root && root.dataset ? String(root.dataset.documentDisplayMode || "") : "";
    context.requestDocumentMode(activeMode === "markdown-source" ? "rendered-document" : "markdown-source");
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
    var doc = actionTargetDoc(DOCS_VIEWER_ACTION_IDS.DELETE);
    if (!doc) return;

    setManagementBusy(true);
    setManagementMessage("Checking delete impact for " + doc.title + "...", false);

    previewManagedDocDelete(doc.doc_id, managementClientOptions())
      .then(function (preview) {
        if (!preview.allowed) {
          var blockerText = (preview.blockers || []).join("; ") || "Delete is blocked.";
          setManagementMessage(blockerText, true);
          return null;
        }
        setManagementBusy(false);
        setManagementMessage("", false);
        return openDocsViewerConfirmModal({
          root: root,
          title: ACTION_TEXT.deleteConfirmTitle,
          body: buildDocsViewerDeletePreviewBody(preview),
          primaryLabel: ACTION_TEXT.deleteConfirmButton,
          cancelLabel: ACTION_TEXT.cancelButton
        }).then(function (confirmed) {
          if (!confirmed) {
            setManagementMessage("", false);
            return null;
          }
          setManagementBusy(true);
          setManagementMessage("Deleting " + doc.title + "...", false);
          return applyManagedDocDelete(doc.doc_id, managementClientOptions());
        });
      })
      .then(function (payload) {
        if (!payload) return;
        var fallbackDocId = firstRemainingRootDocId(
          documentIndex.allDocs,
          doc.doc_id,
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

  async function handleMakeViewable() {
    var doc = actionTargetDoc(DOCS_VIEWER_ACTION_IDS.SHOW);
    if (!doc || isDocViewable(doc)) return;
    var targetDocIds = await viewabilityTargetDocIds(doc);
    if (!targetDocIds) return;

    setManagementBusy(true);
    var countText = targetDocIds.length === 1 ? doc.title : targetDocIds.length + " docs";
    setManagementMessage("Showing " + countText + "...", false);

    updateManagedDocsViewability(targetDocIds, true, managementClientOptions())
      .then(function () {
        setManagementMessage("", false);
        return reloadDocsIndex(doc.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Viewability update failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleMoveDoc(docId, parentId) {
    if (!docId) return;
    var movingDoc = actionTargetDoc(DOCS_VIEWER_ACTION_IDS.MOVE, docId);
    var nextParentId = String(parentId || "").trim();
    if (!movingDoc) return;
    if (nextParentId && !documentIndex.docsById.has(nextParentId)) return;

    setManagementBusy(true);
    clearDragState();
    setManagementMessage("Moving " + movingDoc.title + "...", false);

    moveManagedDoc(movingDoc.doc_id, nextParentId, managementClientOptions())
      .then(function () {
        setManagementMessage("", false);
        return reloadDocsIndex(movingDoc.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Move failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleOpenSource(editor) {
    var contextDoc = currentContextMenuDoc();
    var actionId = editor === "vscode" ? DOCS_VIEWER_ACTION_IDS.OPEN_VSCODE : DOCS_VIEWER_ACTION_IDS.OPEN;
    var doc = contextDoc ? actionTargetDoc(actionId, contextDoc.doc_id) : null;
    if (!doc) return;

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Opening source for " + doc.title + "...", false);

    openManagedDocSource(doc.doc_id, editor, managementClientOptions())
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
      .then(function () {
        var message = "Copied link for " + (doc.title || doc.doc_id) + ".";
        setManagementMessage(message, false);
      })
      .catch(function (error) {
        var message = error && error.message ? error.message : ACTION_TEXT.copyLinkFailed;
        setManagementMessage(message, true);
      });
  }

  return {
    handleCopyLink: handleCopyLink,
    handleCreateDoc: handleCreateDoc,
    handleCreateRelatedDoc: handleCreateRelatedDoc,
    handleDeleteDoc: handleDeleteDoc,
    handleEditMetadataSave: handleEditMetadataSave,
    handleMarkdownSave: handleMarkdownSave,
    handleMarkdownSource: handleMarkdownSource,
    handleMakeViewable: handleMakeViewable,
    handleMoveDoc: handleMoveDoc,
    handleOpenSource: handleOpenSource,
    handleExportDocs: handleExportDocs,
    handlePublishDocs: handlePublishDocs,
    handleRebuildDocs: handleRebuildDocs,
    handleSettingsSubmit: handleSettingsSubmit
  };
}
