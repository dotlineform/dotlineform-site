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
export const DOCS_IMPORT_EDITED_REVIEW_SOURCE_FORMAT = "edited_review_sources";
const DOCS_IMPORT_COLLECTION_SOURCE_FORMATS = new Set([
  DOCS_IMPORT_COLLECTION_SOURCE_FORMAT,
  DOCS_IMPORT_EDITED_REVIEW_SOURCE_FORMAT
]);

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

function viewState(state) {
  return {
    active: state.active,
    phase: state.phase,
    plan: state.plan,
    result: state.result
  };
}

export function isDocsImportCollectionRecord(record) {
  return DOCS_IMPORT_COLLECTION_SOURCE_FORMATS.has(
    normalizeText(record && record.source_format)
  );
}

export function createDocsImportCollectionController(options = {}) {
  const host = options.host || null;
  const statusNode = options.statusNode || null;
  const previewStatusNode = options.previewStatusNode || statusNode;
  const onBusyChange = typeof options.onBusyChange === "function" ? options.onBusyChange : () => {};
  const onTerminalResult = typeof options.onTerminalResult === "function" ? options.onTerminalResult : () => {};
  const onViewStateChange = typeof options.onViewStateChange === "function"
    ? options.onViewStateChange
    : () => {};
  const state = {
    active: false,
    phase: "idle",
    stagedFilename: "",
    sourceFormat: "",
    scope: "",
    subScope: "",
    plan: null,
    result: null,
    terminalDetail: null,
    managementBaseUrl: "",
    busy: false
  };

  function render() {
    const projectedState = viewState(state);
    renderDocsImportCollectionView(host, projectedState, handleCommand, {
      renderActions: options.renderActions !== false
    });
    onViewStateChange(projectedState, handleCommand);
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
      state.result = null;
      state.terminalDetail = null;
    }
    render();
  }

  function reset({ active = state.active, message = "" } = {}) {
    state.active = Boolean(active);
    state.phase = "idle";
    state.stagedFilename = "";
    state.sourceFormat = "";
    state.scope = "";
    state.subScope = "";
    state.plan = null;
    state.result = null;
    state.terminalDetail = null;
    render();
    if (message) setStatus(statusNode, "", message);
  }

  function handleCommand({ type = "" } = {}) {
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
    if (
      type === "close"
      && ["blocked", "result", "projection_error", "cancelled"].includes(state.phase)
    ) {
      reset({ active: false });
      return;
    }
    if (type === "retry-refresh" && state.phase === "projection_error") {
      retryTerminalProjection().catch((error) => (
        console.warn("docs_import_collection: report refresh retry failed", error)
      ));
    }
  }

  async function projectTerminalDetail(detail, { retry = false } = {}) {
    state.terminalDetail = detail;
    if (retry) {
      setBusy(true);
      setStatus(statusNode, "busy", importText("collectionRefreshingReportStatus"));
      render();
    }
    try {
      await onTerminalResult(detail);
      state.phase = "result";
      setStatus(statusNode, "success", importText("collectionResultStatus", {
        outcome: normalizeText(state.result && state.result.outcome) || "unknown"
      }));
      render();
      return true;
    } catch (error) {
      state.phase = "projection_error";
      setStatus(statusNode, "error", importText("collectionRefreshFailedStatus"));
      render();
      throw error;
    } finally {
      if (retry) setBusy(false);
    }
  }

  function retryTerminalProjection() {
    if (state.phase !== "projection_error" || !state.terminalDetail) {
      return Promise.resolve(false);
    }
    return projectTerminalDetail(state.terminalDetail, { retry: true });
  }

  function exactCollectionTarget(payload, context) {
    const target = payload && payload.target;
    const targetScope = normalizeText(target && target.scope).toLowerCase();
    const targetSubScope = normalizeText(target && target.sub_scope).toLowerCase();
    const targetDocId = normalizeText(target && target.doc_id);
    if (
      targetScope !== state.scope
      || targetDocId
      || (
        state.subScope
          ? targetSubScope !== state.subScope
          : Boolean(targetSubScope)
      )
    ) {
      throw new Error(`Docs Import ${context} did not match the requested collection.`);
    }
    return {
      scope: targetScope,
      ...(targetSubScope ? { sub_scope: targetSubScope } : {})
    };
  }

  async function preview({ file, scope, subScope = "", managementBaseUrl = "" } = {}) {
    const stagedFilename = normalizeText(file && file.filename);
    const normalizedScope = normalizeText(scope).toLowerCase();
    const normalizedSubScope = normalizeText(subScope).toLowerCase();
    const sourceFormat = normalizeText(file && file.source_format);
    if (!stagedFilename || !normalizedScope || !isDocsImportCollectionRecord(file)) {
      throw new Error(importText("collectionRequired"));
    }
    if (
      normalizedSubScope
      && (
        normalizeText(file && file.scope).toLowerCase() !== normalizedScope
        || normalizeText(file && file.sub_scope).toLowerCase() !== normalizedSubScope
        || file.supports_return_import !== true
      )
    ) {
      throw new Error(importText("collectionRequired"));
    }
    state.active = true;
    state.phase = "preview";
    state.stagedFilename = stagedFilename;
    state.sourceFormat = sourceFormat;
    state.scope = normalizedScope;
    state.subScope = normalizedSubScope;
    state.managementBaseUrl = normalizeText(managementBaseUrl);
    state.plan = null;
    state.result = null;
    setBusy(true);
    setStatus(previewStatusNode, "busy", importText("collectionPlanningStatus", { filename: stagedFilename }));
    if (previewStatusNode !== statusNode) setStatus(statusNode, "", "");
    render();
    try {
      const payload = await fetchManagementJson("/docs/import-source", "POST", {
        scope: normalizedScope,
        ...(normalizedSubScope ? { sub_scope: normalizedSubScope } : {}),
        staged_filename: stagedFilename,
        preview_only: true
      }, managementOptions(managementBaseUrl));
      if (
        !payload
        || payload.collection !== true
        || normalizeText(payload.source_format) !== state.sourceFormat
      ) {
        throw new Error(importText("collectionUnsupportedPreview"));
      }
      exactCollectionTarget(payload, "preview");
      state.plan = payload;
      if (Array.isArray(payload.blockers) && payload.blockers.length) {
        state.phase = "blocked";
        setStatus(statusNode, "error", importText("collectionBlockedStatus"));
      } else {
        state.phase = "confirmation";
        setStatus(statusNode, "success", importText("collectionReadyStatus"));
      }
      if (previewStatusNode !== statusNode) setStatus(previewStatusNode, "", "");
      render();
      return payload;
    } catch (error) {
      state.phase = "error";
      state.plan = null;
      render();
      setStatus(
        previewStatusNode,
        "error",
        normalizeText(error && error.message) || importText("collectionFailedStatus")
      );
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
    state.phase = "applying";
    setBusy(true);
    setStatus(statusNode, "busy", importText("collectionApplyingStatus"));
    render();
    try {
      const payload = await fetchManagementJson("/docs/import-source", "POST", {
        scope: state.scope,
        ...(state.subScope ? { sub_scope: state.subScope } : {}),
        staged_filename: state.stagedFilename,
        preview_only: false,
        confirm: true,
        export_id: normalizeText(packageIdentity.export_id),
        source_sha256: normalizeText(packageIdentity.source_sha256),
        ...(normalizeText(packageIdentity.trusted_metadata_sha256) ? {
          trusted_metadata_sha256: normalizeText(packageIdentity.trusted_metadata_sha256)
        } : {}),
        planned_identities: Array.isArray(state.plan.planned_identities)
          ? state.plan.planned_identities
          : [],
        planned_actions: Array.isArray(state.plan.planned_actions)
          ? state.plan.planned_actions
          : [],
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
        if (normalizeText(payload.source_format) !== state.sourceFormat) {
          throw new Error(importText("collectionUnsupportedPreview"));
        }
        exactCollectionTarget(payload, "refreshed preview");
        state.plan = payload;
        const blocked = Array.isArray(payload.blockers) && payload.blockers.length;
        state.phase = blocked ? "blocked" : "confirmation";
        setStatus(
          statusNode,
          blocked ? "error" : "warn",
          blocked ? importText("collectionBlockedStatus") : importText("collectionRefreshedStatus")
        );
      } else if (payload && payload.collection === true) {
        if (normalizeText(payload.source_format) !== state.sourceFormat) {
          throw new Error(importText("collectionUnsupportedPreview"));
        }
        const target = exactCollectionTarget(payload, "result");
        state.result = payload;
        const completed = payload.outcome === "completed";
        state.phase = state.subScope && !completed ? "confirmation" : "result";
        setStatus(statusNode, completed ? "success" : "error", importText("collectionResultStatus", {
          outcome: normalizeText(payload.outcome) || "unknown"
        }));
        if (!state.subScope || completed) {
          const displayedRecord = (Array.isArray(payload.records) ? payload.records : []).find((record) => (
            record && (record.status === "created" || record.status === "overwritten") && normalizeText(record.doc_id)
          )) || null;
          const terminalDetail = {
            scope: state.scope,
            subScope: state.subScope,
            docId: normalizeText(displayedRecord && displayedRecord.doc_id),
            target,
            result: payload
          };
          try {
            if (state.subScope) {
              await projectTerminalDetail(terminalDetail);
            } else {
              await onTerminalResult(terminalDetail);
            }
          } catch (error) {
            console.warn("docs_import_collection: terminal result projection failed", error);
          }
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
    retryTerminalProjection,
    handleCommand,
    reset,
    setActive,
    snapshot: () => ({
      active: state.active,
      phase: state.phase,
      stagedFilename: state.stagedFilename,
      sourceFormat: state.sourceFormat,
      scope: state.scope,
      subScope: state.subScope,
      busy: state.busy
    })
  };
}
