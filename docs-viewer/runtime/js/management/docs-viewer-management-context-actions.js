import { DOCS_VIEWER_ACTION_IDS as ACTION_IDS } from "./docs-viewer-action-definitions.js";
import { toggleManagedDocDraft } from "./docs-viewer-management-draft-workflow.js";
import { readSelectedDocuments, setManagedDocSelected } from "./docs-viewer-management-client.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
import { openDocumentThumbModal } from "./docs-viewer-management-thumb-modal.js";

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
  var ownedActions = new Set([ACTION_IDS.NEW, ACTION_IDS.OPEN_VSCODE, ACTION_IDS.SET_DRAFT, ACTION_IDS.SET_SELECTED, ACTION_IDS.THUMB]);

  function actionState() {
    var context = options.documentActionContext() || {};
    var view = options.activeViewState();
    var rendered = view.activeViewId === "rendered-document" && view.activeModeId === "rendered-document";
    var target = context.documentTarget;
    var record = context.documentRecord;
    var exact = Boolean(target && record && record.doc_id === target.doc_id);
    var report = context.collectionTarget ? context : null;
    var readyReport = report && ["list", "detail"].includes(report.state) && exact;
    var resolutions = {
      create: options.resolveAction(ACTION_IDS.NEW, report ? context.collectionTarget : target || {}),
      vscode: options.resolveAction(ACTION_IDS.OPEN_VSCODE, target),
      draft: options.resolveAction(ACTION_IDS.SET_DRAFT, target),
      selected: options.resolveAction(ACTION_IDS.SET_SELECTED, target),
      thumb: options.resolveAction(ACTION_IDS.THUMB, target)
    };
    var unavailable = !options.isManagementContext() || !management.managementAvailable;
    var blocked = unavailable || management.managementBusy;
    var reason = unavailable ? "Docs management service unavailable." : "";
    var createReason = reason || resolutions.create.disabledReason;
    var createPending = report
      ? !readyReport || typeof report.refreshDocument !== "function"
      : !exact && Boolean(options.selectedDocument.selectedDocId);
    var collection = null;
    if (!blocked && !createReason && report && !createPending) {
      collection = report.collectionTarget;
    }
    var sourceTarget = rendered && exact ? target : null;
    var documentReason = reason || (!rendered ? "Return to the document to use this action." : "");
    var draftReason = documentReason || resolutions.draft.disabledReason;
    if (!draftReason && exact && typeof record.draft !== "boolean") draftReason = "Draft readiness is unavailable for this document.";
    var vscodeReason = reason || resolutions.vscode.disabledReason || (!sourceTarget ? "Open a valid document first." : "");
    var selectedReason = documentReason || resolutions.selected.disabledReason;
    return {
      context: context, target: exact ? normalizeManagedDocumentTarget(target) : null,
      record: record, collection: collection, resolutions: resolutions,
      newReason: createReason,
      newDisabled: blocked || createPending || Boolean(createReason),
      vscodeTarget: sourceTarget,
      vscodeReason: vscodeReason, vscodeDisabled: blocked || Boolean(vscodeReason),
      draftReason: draftReason, draftDisabled: blocked || !exact || Boolean(draftReason),
      selectedReason: selectedReason, selectedDisabled: blocked || !exact || Boolean(selectedReason),
      canReadSelection: !unavailable && exact && rendered && !resolutions.selected.disabled,
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
      pending.selected = payload.docs.some(function (row) {
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
    var selectionReason = state.selectedReason || (selection && selection.error) || "";
    options.project(ACTION_IDS.NEW, {
      hidden: state.resolutions.create.hidden,
      label: "New", disabled: state.newDisabled, reason: state.newReason
        || (state.collection ? "New document in " + state.context.collectionLabel : "New document")
    });
    options.project(ACTION_IDS.OPEN_VSCODE, {
      hidden: state.resolutions.vscode.hidden,
      label: "Open in VS Code", disabled: state.vscodeDisabled, reason: state.vscodeReason
    });
    options.project(ACTION_IDS.SET_DRAFT, {
      hidden: state.resolutions.draft.hidden,
      label: draft ? "Mark ready" : "Mark as draft", checked: draft,
      artwork: draft ? "docsViewer__icon--circle-dashed-check" : "docsViewer__icon--circle-check",
      disabled: state.draftDisabled, reason: state.draftReason
    });
    options.project(ACTION_IDS.SET_SELECTED, {
      hidden: state.resolutions.selected.hidden,
      label: selected ? "Remove star" : "Star", checked: selected,
      artwork: selected ? "docsViewer__icon--star-filled" : "docsViewer__icon--star",
      disabled: state.selectedDisabled || !selection || !selection.ready || Boolean(selectionReason), reason: selectionReason
    });
    options.project(ACTION_IDS.THUMB, {
      hidden: state.resolutions.thumb.hidden,
      label: "Thumb", disabled: state.blocked || !state.target || Boolean(state.resolutions.thumb.disabledReason)
        || options.activeViewState().activeModeId !== "rendered-document",
      reason: state.resolutions.thumb.disabledReason
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
          var failures = options.commitDocumentChange({ target: target, record: response.record }) || [];
          if (failures.length) throw new Error("Draft readiness saved, but a retained list could not be updated: " + failures.map(function (error) { return error.message; }).join("; "));
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
    if (actionId === ACTION_IDS.THUMB && !state.resolutions.thumb.disabled) {
      return openDocumentThumbModal({
        root: options.root, target: state.target, record: state.record,
        mediaRoot: options.mediaRoot(), clientOptions: options.clientOptions(),
        commitDocumentChange: options.commitDocumentChange
      });
    }
    if (actionId === ACTION_IDS.NEW && !state.newDisabled) {
      return state.collection
        ? options.actions.handleCreateCollectionDocument(state.collection, { refreshAndSelect: state.context.refreshDocument })
        : options.actions.handleCreateDoc(state.target);
    }
    if (actionId === ACTION_IDS.OPEN_VSCODE && !state.vscodeDisabled) {
      return options.actions.handleOpenSource("vscode", state.vscodeTarget);
    }
    if (actionId === ACTION_IDS.SET_DRAFT && !state.draftDisabled) return saveDraft(state);
    var selection = selectionFor(state);
    if (actionId === ACTION_IDS.SET_SELECTED && !state.selectedDisabled && selection && selection.ready) return saveSelection(selection);
  }

  return { owns: function (actionId) { return ownedActions.has(actionId); }, invoke: invoke, render: render };
}
