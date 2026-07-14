import {
  fetchManagementJson
} from "../management/docs-viewer-management-client.js";
import {
  renderDocsImportCollectionView
} from "./docs-import-collection-view.js";
import {
  importText
} from "./docs-html-import-text.js";
import {
  buildDocsImportActivityContext
} from "./docs-html-import-workflow.js";

export const DOCS_IMPORT_COLLECTION_SOURCE_FORMAT = "data_sharing_documents";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) node.dataset.state = state;
  else node.removeAttribute("data-state");
}

function managementOptions(baseUrl) {
  return {
    baseUrl: normalizeText(baseUrl),
    fetch: (url, options) => window.fetch(url, options)
  };
}

function unresolvedRecords(state) {
  const records = state.plan && Array.isArray(state.plan.records) ? state.plan.records : [];
  return records.filter((record) => (
    record
    && record.action === "decision-required"
    && !state.decisions[record.record_index]
  ));
}

function viewState(state) {
  return {
    active: state.active,
    phase: state.phase,
    plan: state.plan,
    decisions: { ...state.decisions },
    result: state.result,
    currentDecision: state.phase === "decision" && unresolvedRecords(state).length
      ? { record: unresolvedRecords(state)[0] }
      : null
  };
}

export function isDocsImportCollectionRecord(record) {
  return normalizeText(record && record.source_format) === DOCS_IMPORT_COLLECTION_SOURCE_FORMAT;
}

export function createDocsImportCollectionController(options = {}) {
  const host = options.host || null;
  const statusNode = options.statusNode || null;
  const onBusyChange = typeof options.onBusyChange === "function" ? options.onBusyChange : () => {};
  const onTerminalResult = typeof options.onTerminalResult === "function" ? options.onTerminalResult : () => {};
  const state = {
    active: false,
    phase: "idle",
    stagedFilename: "",
    scope: "",
    plan: null,
    decisions: {},
    notes: {},
    result: null,
    managementBaseUrl: "",
    busy: false
  };

  function render() {
    renderDocsImportCollectionView(host, viewState(state), chooseDecision);
  }

  function setBusy(busy) {
    state.busy = Boolean(busy);
    onBusyChange(state.busy);
  }

  function setActive(active) {
    state.active = Boolean(active);
    if (!state.active) {
      state.phase = "idle";
      state.plan = null;
      state.decisions = {};
      state.notes = {};
      state.result = null;
    }
    render();
  }

  function reset({ active = state.active, message = "" } = {}) {
    state.active = Boolean(active);
    state.phase = "idle";
    state.stagedFilename = "";
    state.scope = "";
    state.plan = null;
    state.decisions = {};
    state.notes = {};
    state.result = null;
    render();
    if (message) setStatus(statusNode, "", message);
  }

  function chooseDecision({ type = "decision", action, applyToAll = false, note = "" } = {}) {
    if (type === "confirm") {
      confirmApply().catch((error) => console.warn("docs_import_collection: apply failed", error));
      return;
    }
    if (type === "cancel" && state.phase === "confirmation") {
      state.phase = "cancelled";
      setStatus(statusNode, "", importText("collectionCancelledStatus"));
      render();
      return;
    }
    const current = unresolvedRecords(state)[0];
    if (!current) return;
    const normalizedAction = normalizeText(action);
    if (normalizedAction === "cancel") {
      state.phase = "cancelled";
      state.decisions = {};
      setStatus(statusNode, "", importText("collectionCancelledStatus"));
      render();
      return;
    }
    if (!Array.isArray(current.allowed_actions) || !current.allowed_actions.includes(normalizedAction)) return;
    state.decisions[current.record_index] = normalizedAction;
    if (current.decision_kind === "invalid-record" && normalizedAction === "skip") {
      state.notes[current.record_index] = normalizeText(note);
    }
    if (applyToAll && current.decision_kind === "collision") {
      unresolvedRecords(state).forEach((record) => {
        if (
          record.decision_kind === "collision"
          && Array.isArray(record.allowed_actions)
          && record.allowed_actions.includes(normalizedAction)
        ) {
          state.decisions[record.record_index] = normalizedAction;
        }
      });
    }
    if (!unresolvedRecords(state).length) {
      state.phase = "confirmation";
      setStatus(statusNode, "success", importText("collectionReadyStatus"));
    }
    render();
  }

  async function preview({ file, scope, managementBaseUrl = "" } = {}) {
    const stagedFilename = normalizeText(file && file.filename);
    const normalizedScope = normalizeText(scope).toLowerCase();
    if (!stagedFilename || !normalizedScope || !isDocsImportCollectionRecord(file)) {
      throw new Error(importText("collectionRequired"));
    }
    state.active = true;
    state.phase = "preview";
    state.stagedFilename = stagedFilename;
    state.scope = normalizedScope;
    state.managementBaseUrl = normalizeText(managementBaseUrl);
    state.plan = null;
    state.decisions = {};
    state.notes = {};
    state.result = null;
    setBusy(true);
    setStatus(statusNode, "", importText("collectionPlanningStatus", { filename: stagedFilename }));
    render();
    try {
      const payload = await fetchManagementJson("/docs/import-source", "POST", {
        scope: normalizedScope,
        staged_filename: stagedFilename,
        preview_only: true
      }, managementOptions(managementBaseUrl));
      if (!payload || payload.collection !== true || payload.source_format !== DOCS_IMPORT_COLLECTION_SOURCE_FORMAT) {
        throw new Error(importText("collectionUnsupportedPreview"));
      }
      state.plan = payload;
      if (Array.isArray(payload.blockers) && payload.blockers.length) {
        state.phase = "blocked";
        setStatus(statusNode, "error", importText("collectionBlockedStatus"));
      } else if (payload.requires_decisions) {
        state.phase = "decision";
        setStatus(statusNode, "warn", importText("collectionDecisionsStatus"));
      } else {
        state.phase = "confirmation";
        setStatus(statusNode, "success", importText("collectionReadyStatus"));
      }
      render();
      return payload;
    } catch (error) {
      state.phase = "error";
      state.plan = null;
      render();
      setStatus(statusNode, "error", normalizeText(error && error.message) || importText("collectionFailedStatus"));
      throw error;
    } finally {
      setBusy(false);
    }
  }

  async function confirmApply() {
    if (state.phase !== "confirmation" || !state.plan) return null;
    const packageIdentity = state.plan.package && typeof state.plan.package === "object"
      ? state.plan.package
      : {};
    const decisions = (Array.isArray(state.plan.records) ? state.plan.records : [])
      .filter((record) => state.decisions[record.record_index])
      .map((record) => ({
        record_index: record.record_index,
        action: state.decisions[record.record_index],
        target_doc_id: record.decision_kind === "collision"
          ? normalizeText(record.collision && record.collision.doc_id)
          : "",
        note: state.notes[record.record_index] || ""
      }));
    state.phase = "applying";
    setBusy(true);
    setStatus(statusNode, "", importText("collectionApplyingStatus"));
    render();
    try {
      const payload = await fetchManagementJson("/docs/import-source", "POST", {
        scope: state.scope,
        staged_filename: state.stagedFilename,
        preview_only: false,
        confirm: true,
        export_id: normalizeText(packageIdentity.export_id),
        source_sha256: normalizeText(packageIdentity.source_sha256),
        decisions,
        activity_context: buildDocsImportActivityContext({
          pageId: "docs-import",
          actionId: "import-docs-collection",
          route: normalizeText(options.routePath) || "/docs/",
          controlId: "docsImportCollectionConfirm",
          controlSelector: "[data-collection-command=confirm]",
          recordIdField: "staged_filename",
          recordId: state.stagedFilename
        })
      }, managementOptions(state.managementBaseUrl));
      if (payload && payload.preview_only === true) {
        state.plan = payload;
        state.decisions = {};
        state.notes = {};
        const blocked = Array.isArray(payload.blockers) && payload.blockers.length;
        state.phase = blocked ? "blocked" : payload.requires_decisions ? "decision" : "confirmation";
        setStatus(
          statusNode,
          blocked ? "error" : "warn",
          blocked ? importText("collectionBlockedStatus") : importText("collectionRefreshedStatus")
        );
      } else if (payload && payload.collection === true) {
        state.result = payload;
        state.phase = "result";
        setStatus(statusNode, payload.outcome === "completed" ? "success" : "warn", importText("collectionResultStatus", {
          outcome: normalizeText(payload.outcome) || "unknown"
        }));
        const displayedRecord = (Array.isArray(payload.records) ? payload.records : []).find((record) => (
          record && (record.status === "created" || record.status === "overwritten") && normalizeText(record.doc_id)
        )) || null;
        try {
          await onTerminalResult({
            scope: state.scope,
            docId: normalizeText(displayedRecord && displayedRecord.doc_id),
            result: payload
          });
        } catch (error) {
          console.warn("docs_import_collection: terminal result projection failed", error);
        }
      } else {
        throw new Error(importText("collectionUnsupportedPreview"));
      }
      render();
      return payload;
    } catch (error) {
      state.phase = "confirmation";
      setStatus(statusNode, "error", normalizeText(error && error.message) || importText("collectionApplyFailedStatus"));
      render();
      throw error;
    } finally {
      setBusy(false);
    }
  }

  return {
    mode: () => state.active ? state.phase : "idle",
    preview,
    confirmApply,
    reset,
    setActive,
    snapshot: () => ({
      active: state.active,
      phase: state.phase,
      stagedFilename: state.stagedFilename,
      scope: state.scope,
      decisions: { ...state.decisions },
      busy: state.busy
    })
  };
}
