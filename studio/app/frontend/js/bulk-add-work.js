import {
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  BULK_ADD_WORK_ENDPOINTS,
  postJson,
  probeBulkAddWorkCatalogueHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState
} from "./studio-route-state.js";
import {
  collectOperationalRouteElements,
  markOperationalRouteReady,
  renderOperationalServiceStatus,
  syncOperationalRouteBusyState
} from "./studio-operational-route.js";
import {
  applyBulkAddWorkRunState,
  applyBulkAddWorkStatusProjection,
  normalizeBulkAddWorkText,
  projectBulkAddWorkApplyBlocked,
  projectBulkAddWorkApplyFailure,
  projectBulkAddWorkApplyStart,
  projectBulkAddWorkApplySuccess,
  projectBulkAddWorkPreviewFailure,
  projectBulkAddWorkPreviewStart,
  projectBulkAddWorkPreviewSuccess,
  renderBulkAddWorkPreviewState
} from "./bulk-add-work-workflow.js";
import { buildSaveModeText } from "./studio-save-utils.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

function normalizeText(value) {
  return normalizeBulkAddWorkText(value);
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `bulk_add_work.${key}`, fallback, tokens);
}

function syncRouteBusyState(state) {
  syncOperationalRouteBusyState(state, bulkAddWorkRouteOptions());
}

function markRouteReady(state, ready) {
  markOperationalRouteReady(state, ready, bulkAddWorkRouteOptions());
}

function bulkAddWorkRouteOptions() {
  return {
    route: "bulk-add-work",
    mode: (state) => state.preview ? "preview" : "idle",
    serviceAvailable: (state) => state.serverAvailable,
    isBusy: (state) => state.isBusy,
    recordLoaded: (state) => Boolean(state.preview)
  };
}

function workflowTextOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  };
}

function updateState(state) {
  applyBulkAddWorkRunState(state);
  renderBulkAddWorkPreviewState(state, workflowTextOptions(state));
  syncRouteBusyState(state);
}

function clearPreview(state) {
  state.preview = null;
  updateState(state);
}

async function runPreview(state) {
  state.isBusy = true;
  updateState(state);
  applyBulkAddWorkStatusProjection(state, projectBulkAddWorkPreviewStart(workflowTextOptions(state)));
  try {
    const response = await postJson(BULK_ADD_WORK_ENDPOINTS.importPreview, { mode: state.mode });
    state.preview = response && response.preview ? response.preview : null;
    applyBulkAddWorkStatusProjection(state, projectBulkAddWorkPreviewSuccess(state, state.preview, workflowTextOptions(state)));
  } catch (error) {
    applyBulkAddWorkStatusProjection(state, projectBulkAddWorkPreviewFailure(error, workflowTextOptions(state)));
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

async function applyImport(state) {
  const blocked = projectBulkAddWorkApplyBlocked(state, workflowTextOptions(state));
  if (blocked) {
    applyBulkAddWorkStatusProjection(state, blocked);
    return;
  }

  state.isBusy = true;
  updateState(state);
  applyBulkAddWorkStatusProjection(state, projectBulkAddWorkApplyStart(workflowTextOptions(state)));
  try {
    const response = await postJson(BULK_ADD_WORK_ENDPOINTS.importApply, {
      mode: state.mode,
      activity_context: buildStudioActivityContext({
        pageId: "bulk-add-work",
        actionId: "import-workbook-records",
        route: "/studio/bulk-add-work/",
        controlId: "bulkAddWorkApply",
        controlSelector: "#bulkAddWorkApply",
        recordIdField: "import_mode",
        recordId: state.mode
      })
    });
    state.preview = response && response.preview ? response.preview : state.preview;
    applyBulkAddWorkStatusProjection(state, projectBulkAddWorkApplySuccess(state, response, workflowTextOptions(state)));
  } catch (error) {
    const projection = projectBulkAddWorkApplyFailure(error, workflowTextOptions(state));
    if (projection.preview) {
      state.preview = projection.preview;
    }
    applyBulkAddWorkStatusProjection(state, projection);
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

async function init() {
  const root = document.getElementById("bulkAddWorkRoot");
  const loadingNode = document.getElementById("bulkAddWorkLoading");
  const emptyNode = document.getElementById("bulkAddWorkEmpty");
  const pageHeadingNode = document.getElementById("bulkAddWorkPageHeading");
  const importHeadingNode = document.getElementById("bulkAddWorkImportHeading");
  const modeLabelNode = document.getElementById("bulkAddWorkModeLabel");
  const worksOptionNode = document.getElementById("bulkAddWorkModeWorks");
  const workDetailsOptionNode = document.getElementById("bulkAddWorkModeWorkDetails");
  const workbookLabelNode = document.getElementById("bulkAddWorkWorkbookLabel");
  const summaryHeadingNode = document.getElementById("bulkAddWorkSummaryHeading");
  const detailsHeadingNode = document.getElementById("bulkAddWorkDetailsHeading");
  const modeNode = document.getElementById("bulkAddWorkMode");
  const saveModeNode = document.getElementById("bulkAddWorkSaveMode");
  const contextNode = document.getElementById("bulkAddWorkContext");
  const statusNode = document.getElementById("bulkAddWorkStatus");
  const warningNode = document.getElementById("bulkAddWorkWarning");
  const resultNode = document.getElementById("bulkAddWorkResult");
  const workbookNode = document.getElementById("bulkAddWorkWorkbook");
  const summaryNode = document.getElementById("bulkAddWorkSummary");
  const previewDetailsNode = document.getElementById("bulkAddWorkPreviewDetails");
  const previewButton = document.getElementById("bulkAddWorkPreview");
  const applyButton = document.getElementById("bulkAddWorkApply");
  const required = collectOperationalRouteElements({
    root,
    loadingNode,
    emptyNode,
    pageHeadingNode,
    importHeadingNode,
    modeLabelNode,
    worksOptionNode,
    workDetailsOptionNode,
    workbookLabelNode,
    summaryHeadingNode,
    detailsHeadingNode,
    modeNode,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    workbookNode,
    summaryNode,
    previewDetailsNode,
    previewButton,
    applyButton
  });
  if (!required.ok) {
    return;
  }

  const state = {
    config: null,
    root,
    mode: "works",
    preview: null,
    serverAvailable: false,
    isBusy: false,
    statusNode,
    warningNode,
    resultNode,
    workbookNode,
    summaryNode,
    previewDetailsNode,
    previewButton,
    applyButton,
    workbookPath: normalizeText(root.dataset.workbookPath) || "data/works_bulk_import.xlsx"
  };
  initializeStudioRouteState(root, { route: "bulk-add-work" });

  try {
    const config = await loadStudioConfigWithText("bulk_add_work");
    state.config = config;
    state.serverAvailable = Boolean(await probeBulkAddWorkCatalogueHealth());
    pageHeadingNode.textContent = t(state, "page_heading", "bulk add work");
    importHeadingNode.textContent = t(state, "import_heading", "import");
    modeLabelNode.textContent = t(state, "mode_label", "mode");
    worksOptionNode.textContent = t(state, "mode_option_works", "works");
    workDetailsOptionNode.textContent = t(state, "mode_option_work_details", "work details");
    workbookLabelNode.textContent = t(state, "workbook_label", "workbook");
    summaryHeadingNode.textContent = t(state, "summary_heading", "preview summary");
    detailsHeadingNode.textContent = t(state, "details_heading", "preview details");
    loadingNode.textContent = t(state, "loading", "loading bulk add work…");
    emptyNode.textContent = t(state, "empty_state", "");
    previewButton.textContent = t(state, "preview_button", "Preview");
    applyButton.textContent = t(state, "apply_button", "Import");
    saveModeNode.textContent = buildSaveModeText(config, state.serverAvailable ? "post" : "offline", (cfg, key, fallback, tokens) => getStudioText(cfg, `bulk_add_work.${key}`, fallback, tokens));
    workbookNode.textContent = state.workbookPath;
    setTextWithState(
      contextNode,
      t(state, "context_hint", "Bulk import is one-way from {workbook} into canonical JSON. Use works mode for new works and work details mode for new detail rows.", { workbook: state.workbookPath })
    );
    if (!state.serverAvailable) {
      renderOperationalServiceStatus(statusNode, state, {
        serviceAvailable: (routeState) => routeState.serverAvailable,
        unavailableText: () => t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Import is disabled."),
        unavailableState: "warn"
      });
    }

    modeNode.addEventListener("change", () => {
      state.mode = normalizeText(modeNode.value) || "works";
      setTextWithState(state.resultNode, "");
      setTextWithState(state.warningNode, "");
      clearPreview(state);
    });
    previewButton.addEventListener("click", () => {
      runPreview(state).catch((error) => console.warn("bulk_add_work: unexpected preview failure", error));
    });
    applyButton.addEventListener("click", () => {
      applyImport(state).catch((error) => console.warn("bulk_add_work: unexpected apply failure", error));
    });

    updateState(state);
    root.hidden = false;
    loadingNode.hidden = true;
    markRouteReady(state, true);
  } catch (error) {
    console.warn("bulk_add_work: init failed", error);
    loadingNode.textContent = "Failed to load bulk add work.";
    root.hidden = false;
    state.serverAvailable = false;
    updateState(state);
    markRouteReady(state, true);
  }
}

init();
