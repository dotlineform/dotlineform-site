import {
  applyManagedDocDelete,
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
  isDocHidden,
  isDocViewable
} from "./docs-viewer-tree.js";
import {
  resolveViewabilityTargetDocIds
} from "./docs-viewer-management-action-workflow.js";
import {
  buildDocsViewerDeletePreviewBody,
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modals.js";

export function createDocsViewerManagementActionController(options) {
  var root = options.root;
  var state = options.state;
  var context = options.context;
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};

  function currentSelectedDoc() {
    return callbacks.currentSelectedDoc ? callbacks.currentSelectedDoc() : null;
  }

  function currentContextMenuDoc() {
    return callbacks.currentContextMenuDoc ? callbacks.currentContextMenuDoc() : null;
  }

  function currentStatusValue(doc) {
    return callbacks.currentStatusValue ? callbacks.currentStatusValue(doc) : "";
  }

  function statusPillsCanWrite(doc) {
    return callbacks.statusPillsCanWrite ? callbacks.statusPillsCanWrite(doc) : false;
  }

  function managementClientOptions() {
    return callbacks.managementClientOptions ? callbacks.managementClientOptions() : {};
  }

  function getModalController() {
    return callbacks.getModalController ? callbacks.getModalController() : null;
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

  function renderStatusPills() {
    if (callbacks.renderStatusPills) callbacks.renderStatusPills();
  }

  function reloadDocsIndex(targetDocId, summaryText) {
    return callbacks.reloadDocsIndex ? callbacks.reloadDocsIndex(targetDocId, summaryText) : Promise.resolve();
  }

  async function viewabilityTargetDocIds(doc) {
    return resolveViewabilityTargetDocIds({
      doc: doc,
      allDocs: state.allDocs,
      findDocById: context.findAllDocById,
      confirmAncestors: function (detail) {
        var ancestorMessage = context.formatText(state.managementText.viewableAncestorPrompt, {
          titles: detail.titles
        });
        return openDocsViewerConfirmModal({
          root: root,
          title: state.managementText.viewableAncestorTitle,
          body: ancestorMessage,
          primaryLabel: state.managementText.confirmContinueButton,
          cancelLabel: state.managementText.cancelButton
        });
      },
      chooseDescendants: function () {
        return openDocsViewerChoiceModal({
          root: root,
          title: state.managementText.viewableDescendantTitle,
          body: state.managementText.viewableDescendantPrompt,
          value: "selected",
          choices: [
            { value: "selected", label: state.managementText.viewableDescendantSelectedLabel },
            { value: "all", label: state.managementText.viewableDescendantAllLabel }
          ],
          primaryLabel: state.managementText.confirmContinueButton,
          cancelLabel: state.managementText.cancelButton
        });
      },
      onInvalidChoice: function () {
        setManagementMessage(state.managementText.viewableInvalidChoice, true);
      }
    });
  }

  function metadataPayloadForStatus(doc, uiStatus) {
    return {
      doc_id: doc.doc_id,
      title: String(doc.title || "").trim(),
      summary: String(doc.summary || "").replace(/\s+/g, " ").trim(),
      ui_status: String(uiStatus || "").trim(),
      hidden: isDocHidden(doc),
      parent_id: String(doc.parent_id || "").trim()
    };
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
          throw new Error(state.managementText.copyLinkFailed);
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
      title: state.managementText.createDocTitle,
      label: state.managementText.createDocLabel,
      initialValue: state.managementText.createDocDefaultTitle,
      defaultValue: state.managementText.createDocDefaultTitle,
      primaryLabel: state.managementText.createDocButton,
      cancelLabel: state.managementText.cancelButton
    });
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || state.managementText.createDocDefaultTitle;
    var currentDoc = currentSelectedDoc();

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
    var baseDoc = currentContextMenuDoc();
    if (!baseDoc) return;

    var titleResult = await openDocsViewerTextInputModal({
      root: root,
      title: kind === "child" ? state.managementText.createChildDocTitle : state.managementText.createSiblingDocTitle,
      label: state.managementText.createDocLabel,
      initialValue: state.managementText.createDocDefaultTitle,
      defaultValue: state.managementText.createDocDefaultTitle,
      primaryLabel: state.managementText.createDocButton,
      cancelLabel: state.managementText.cancelButton
    });
    if (!titleResult || !titleResult.confirmed) return;

    var title = String(titleResult.value || "").trim() || state.managementText.createDocDefaultTitle;
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
    var doc = state.docsById.get(payload.doc_id);
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

  function handleStatusPillClick(statusValue) {
    var doc = currentSelectedDoc();
    if (!statusPillsCanWrite(doc)) return;
    var selectedStatus = String(statusValue || "").trim();
    if (!selectedStatus || !state.uiStatusByValue.has(selectedStatus)) return;

    var nextStatus = currentStatusValue(doc) === selectedStatus ? "" : selectedStatus;
    var savingText = context.formatText(state.managementText.statusPillSaving, { title: doc.title });

    setManagementBusy(true);
    setManagementMessage(savingText, false);
    renderStatusPills();

    updateManagedDocMetadata(metadataPayloadForStatus(doc, nextStatus), managementClientOptions())
      .then(function () {
        setManagementMessage("", false);
        return reloadDocsIndex(doc.doc_id, "");
      })
      .catch(function (error) {
        var failedText = error.message || state.managementText.statusPillFailed;
        setManagementMessage(failedText, true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
        renderStatusPills();
      });
  }

  function handleRebuildDocs() {
    setManagementBusy(true);
    setManagementMessage("Rebuilding docs...", false);

    rebuildManagedDocs(managementClientOptions())
      .then(function () {
        var targetDocId = state.selectedDocId || context.defaultRouteDocId() || context.defaultDocId();
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

  function handleMarkdownSource() {
    var doc = currentSelectedDoc();
    if (!doc || typeof context.requestMainView !== "function") return;
    hideContextMenu();
    context.requestMainView("markdown-source");
  }

  function handleSettingsSave() {
    var modalController = getModalController();
    var settingsFieldState = modalController ? modalController.getSettingsFieldState() : null;
    if (!refs.settingsUpdatedInput || !settingsFieldState) return;
    var nextValue = Boolean(refs.settingsUpdatedInput.checked);
    var currentValue = settingsFieldState.current_value !== false;
    if (nextValue === currentValue) {
      modalController.closeSettingsModal();
      return;
    }

    setManagementBusy(true);
    modalController.setSettingsSaving();
    setManagementMessage(state.managementText.settingsSaving, false);

    updateSourceConfigSettings({
      show_updated_date: nextValue
    }, managementClientOptions())
      .then(function (payload) {
        modalController.renderSettingsWarnings(payload.warnings || []);
        var targetDocId = state.selectedDocId || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(targetDocId, "").then(function () {
          modalController.closeSettingsModal();
        });
      })
      .catch(function (error) {
        var message = error.message || state.managementText.settingsSaveFailed;
        modalController.setSettingsSaveError(message);
        setManagementMessage(message, true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleSettingsSubmit(event) {
    if (event) event.preventDefault();
    handleSettingsSave();
  }

  function handleDeleteDoc() {
    var doc = currentSelectedDoc();
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
          title: state.managementText.deleteConfirmTitle,
          body: buildDocsViewerDeletePreviewBody(preview),
          primaryLabel: state.managementText.deleteConfirmButton,
          cancelLabel: state.managementText.cancelButton
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
        var fallbackDocId = doc.parent_id || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(fallbackDocId, "");
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
    var doc = currentSelectedDoc();
    if (!doc || isDocViewable(doc)) return;
    var targetDocIds = await viewabilityTargetDocIds(doc);
    if (!targetDocIds) return;

    setManagementBusy(true);
    var countText = targetDocIds.length === 1 ? doc.title : targetDocIds.length + " docs";
    setManagementMessage("Showing " + countText + "...", false);

    updateManagedDocsViewability(targetDocIds, false, managementClientOptions())
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
    var movingDoc = state.docsById.get(docId);
    var nextParentId = String(parentId || "").trim();
    if (!movingDoc) return;
    if (nextParentId && !state.docsById.has(nextParentId)) return;

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
    var doc = currentContextMenuDoc();
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
    var doc = currentContextMenuDoc();
    if (!doc || typeof context.markdownDocLink !== "function") return;
    var markdownLink = context.markdownDocLink(doc);
    if (!markdownLink) return;

    hideContextMenu();
    writeClipboardText(markdownLink)
      .then(function () {
        var message = context.formatText(state.managementText.copyLinkStatus, {
          title: doc.title || doc.doc_id
        });
        setManagementMessage(message, false);
      })
      .catch(function (error) {
        var message = error && error.message ? error.message : state.managementText.copyLinkFailed;
        setManagementMessage(message, true);
      });
  }

  return {
    handleCopyLink: handleCopyLink,
    handleCreateDoc: handleCreateDoc,
    handleCreateRelatedDoc: handleCreateRelatedDoc,
    handleDeleteDoc: handleDeleteDoc,
    handleEditMetadataSave: handleEditMetadataSave,
    handleMarkdownSource: handleMarkdownSource,
    handleMakeViewable: handleMakeViewable,
    handleMoveDoc: handleMoveDoc,
    handleOpenSource: handleOpenSource,
    handleRebuildDocs: handleRebuildDocs,
    handleSettingsSubmit: handleSettingsSubmit,
    handleStatusPillClick: handleStatusPillClick
  };
}
