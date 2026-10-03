import { DOCS_VIEWER_ACTION_IDS as ACTION_IDS } from "./docs-viewer-action-definitions.js";
import { toggleManagedDocDraft } from "./docs-viewer-management-draft-workflow.js";
import { readSelectedDocuments, setManagedDocSelected } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
import { selectedDocumentRows } from "../shared/docs-selected-documents.js";

/**
 * Own context-aware New and Edit actions' exact targets and availability.
 * Collection loading/error states never fall back to the ordinary report host.
 * Writes use management services; the mounted report projects committed draft
 * changes and owns refresh/open after collection creation. Selection reads are
 * retained for one exact target and stale completions cannot replace its state.
 */
export function createDocsViewerManagementContextActions(options) {
  var management = options.management;
  var selectedState = null;
  var ownedActions = new Set([ACTION_IDS.NEW, ACTION_IDS.OPEN_VSCODE, ACTION_IDS.SET_DRAFT, ACTION_IDS.SET_SELECTED]);

  function actionState() {
    var context = options.documentActionContext() || {};
    var view = options.activeViewState();
    var rendered = view.activeViewId === "rendered-document" && view.activeModeId === "rendered-document";
    var target = context.documentTarget;
    var record = context.documentRecord;
    var exact = Boolean(target && record && record.doc_id === target.doc_id);
    var report = context.collectionTarget ? context : null;
    var readyReport = report && ["list", "detail"].includes(report.state) && exact;
    var unavailable = !options.isManagementContext() || !management.managementAvailable;
    var blocked = unavailable || management.managementBusy;
    var reason = unavailable ? "Docs management service unavailable."
      : management.managementBusy ? "Docs management is busy." : "";
    var createReason = reason;
    var collection = null;
    if (!createReason && report) {
      if (!readyReport || typeof report.refreshDocument !== "function") createReason = "Wait for the collection document to finish loading.";
      else if (report.collectionTarget?.collection === "catalogue") createReason = "Catalogue documents are created by regeneration.";
      else collection = report.collectionTarget;
    } else if (!createReason && !exact && options.selectedDocument.selectedDocId) {
      createReason = "Wait for the selected document to finish loading.";
    }
    var sourceTarget = rendered && exact ? target : null;
    var documentReason = reason || (!rendered ? "Return to the document to use this action."
      : !exact ? "Wait for a valid document to finish loading." : "");
    var draftReason = documentReason;
    if (!draftReason && target.collection) {
      if (target.collection === "catalogue") draftReason = "Catalogue documents have fixed Publish eligibility.";
      else if (typeof context.commitDocumentDraft !== "function") draftReason = "Collection draft readiness is unavailable.";
    } else if (!draftReason) {
      var policy = options.documentIndex.docsById.get(target.doc_id);
      if (!policy || policy.publication_ignored !== false) draftReason = "Excluded from Publish by unpublishable.json.";
    }
    if (!draftReason && typeof record.draft !== "boolean") draftReason = "Draft readiness is unavailable for this document.";
    return {
      context: context, target: exact ? normalizeManagedDocumentTarget(target) : null,
      record: record, collection: collection,
      newReason: createReason,
      vscodeTarget: sourceTarget,
      vscodeReason: reason || (!sourceTarget ? "Open a valid document first." : ""),
      draftReason: draftReason, selectedReason: documentReason,
      canReadSelection: !unavailable && exact && rendered,
      blocked: blocked
    };
  }

  function loadSelection(state) {
    if (!state.canReadSelection) {
      if (!state.target || (selectedState && !managedDocumentTargetsEqual(selectedState.target, state.target))) selectedState = null;
      return;
    }
    if (selectedState && managedDocumentTargetsEqual(selectedState.target, state.target)) return;
    var pending = { target: state.target, ready: false, selected: false, error: "" };
    selectedState = pending;
    readSelectedDocuments(options.clientOptions()).then(function (payload) {
      if (selectedState !== pending) return;
      pending.selected = selectedDocumentRows(payload).some(function (row) {
        return row.doc_id === pending.target.doc_id && (row.collection || "") === (pending.target.collection || "");
      });
      pending.ready = true;
      options.render();
    }).catch(function (error) {
      if (selectedState !== pending) return;
      pending.error = error.message || "Selected Documents could not be loaded.";
      options.setMessage(pending.error, true);
      options.render();
    });
  }

  function selectionFor(state) {
    return state.target && selectedState && managedDocumentTargetsEqual(state.target, selectedState.target)
      ? selectedState : null;
  }

  function render() {
    var state = actionState();
    loadSelection(state);
    var selection = selectionFor(state);
    var draft = Boolean(state.record && state.record.draft === true);
    var selected = Boolean(selection && selection.selected);
    var selectionReason = state.selectedReason || (selection && selection.error)
      || (!selection || !selection.ready ? "Loading document selection…" : "");
    options.project(ACTION_IDS.NEW, {
      label: "New", disabled: Boolean(state.newReason), reason: state.newReason
        || (state.collection ? "New document in " + state.context.collectionLabel : "New document")
    });
    options.project(ACTION_IDS.OPEN_VSCODE, {
      label: "Open in VS Code", disabled: Boolean(state.vscodeReason), reason: state.vscodeReason
    });
    options.project(ACTION_IDS.SET_DRAFT, {
      label: draft ? "Mark ready" : "Mark as draft", checked: draft,
      artwork: draft ? "docsViewer__icon--circle-dashed-check" : "docsViewer__icon--circle-check",
      disabled: Boolean(state.draftReason), reason: state.draftReason
    });
    options.project(ACTION_IDS.SET_SELECTED, {
      label: selected ? "Remove star" : "Star", checked: selected,
      artwork: selected ? "docsViewer__icon--star-filled" : "docsViewer__icon--star",
      disabled: Boolean(selectionReason), reason: selectionReason
    });
  }

  async function saveDraft(state) {
    options.setBusy(true);
    options.setMessage("", false);
    options.render();
    try {
      await toggleManagedDocDraft(state.target, !state.record.draft, {
        clientOptions: options.clientOptions(),
        onSaved: function (target, response) {
          if (state.context.commitDocumentDraft) state.context.commitDocumentDraft(target, response.record);
          else {
            var record = options.documentIndex.docsById.get(target.doc_id);
            if (record) record.draft = response.record.draft;
            options.renderSidebar();
          }
        }
      });
    } catch (error) {
      options.setMessage(error.message || "Draft readiness could not be saved.", true);
    } finally {
      options.setBusy(false);
      options.render();
    }
  }

  async function saveSelection(selection) {
    var selected = !selection.selected;
    options.setBusy(true);
    options.setMessage("", false);
    options.render();
    try {
      var response = await setManagedDocSelected(selection.target, selected, options.clientOptions());
      if (response.ok !== true || !managedDocumentTargetsEqual(response.target, selection.target) || response.selected !== selected) {
        throw new Error("Selected Documents response did not match the requested document.");
      }
      if (selectedState === selection) selection.selected = selected;
    } catch (error) {
      options.setMessage(error.message || "Document selection could not be saved.", true);
    } finally {
      options.setBusy(false);
      options.render();
    }
  }

  function invoke(actionId) {
    var state = actionState();
    if (state.blocked) return;
    if (actionId === ACTION_IDS.NEW && !state.newReason) {
      return state.collection
        ? options.actions.handleCreateCollectionDocument(state.collection, { refreshAndSelect: state.context.refreshDocument })
        : options.actions.handleCreateDoc(state.target);
    }
    if (actionId === ACTION_IDS.OPEN_VSCODE && !state.vscodeReason) {
      return options.actions.handleOpenSource("vscode", state.vscodeTarget,
        state.record && state.record.doc_id === state.vscodeTarget.doc_id ? state.record.title : state.vscodeTarget.doc_id);
    }
    if (actionId === ACTION_IDS.SET_DRAFT && !state.draftReason) return saveDraft(state);
    var selection = selectionFor(state);
    if (actionId === ACTION_IDS.SET_SELECTED && !state.selectedReason && selection && selection.ready) return saveSelection(selection);
  }

  return { owns: function (actionId) { return ownedActions.has(actionId); }, invoke: invoke, render: render };
}
