import {
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  PROJECT_STATE_ENDPOINTS,
  postJson,
  probeProjectStateCatalogueHealth,
  probeProjectStateCatalogueOpenHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState
} from "./studio-route-state.js";
import {
  applyOperationalRunButtonState,
  collectOperationalRouteElements,
  markOperationalRouteReady,
  syncOperationalRouteBusyState
} from "./studio-operational-route.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `project_state.${key}`, fallback, tokens);
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function projectStateRouteOptions() {
  return {
    route: "project-state",
    mode: (state) => state.summary ? "summary" : "idle",
    serviceAvailable: (state) => state.catalogueServerAvailable,
    isBusy: (state) => state.isBusy,
    recordLoaded: (state) => Boolean(state.summary)
  };
}

function syncRouteBusyState(state) {
  syncOperationalRouteBusyState(state, projectStateRouteOptions());
}

function markRouteReady(state, ready) {
  markOperationalRouteReady(state, ready, projectStateRouteOptions());
}

function summaryValue(summary, key) {
  return String(Number(summary && summary[key]) || 0);
}

function renderSummary(state) {
  const summary = state.summary || {};
  const fields = [
    { label: t(state, "summary_include_subfolders", "include sub-folders"), value: summary && summary.include_subfolders ? "true" : "false" },
    { label: t(state, "summary_source_folders", "source folders"), value: summaryValue(summary, "source_folder_count") },
    { label: t(state, "summary_catalogue_folders", "catalogue folders"), value: summaryValue(summary, "catalogue_project_folder_count") },
    { label: t(state, "summary_unrepresented_folders", "folders not in works.json"), value: summaryValue(summary, "unrepresented_folder_count") },
    { label: t(state, "summary_source_images", "source images"), value: summaryValue(summary, "source_image_count") },
    { label: t(state, "summary_catalogue_images", "primary images in works.json"), value: summaryValue(summary, "catalogue_project_image_count") },
    { label: t(state, "summary_unrepresented_images", "extra images in represented folders"), value: summaryValue(summary, "unrepresented_image_count") }
  ];
  state.summaryNode.innerHTML = fields.map((field) => `
    <div class="studioForm__field">
      <span class="studioForm__label">${escapeHtml(field.label)}</span>
      <span class="studioUi__input studioUi__input--readonlyDisplay">${escapeHtml(field.value)}</span>
    </div>
  `).join("");
}

function updateState(state) {
  applyOperationalRunButtonState(state.runButton, state, {
    serviceAvailable: (routeState) => routeState.catalogueServerAvailable,
    isBusy: (routeState) => routeState.isBusy
  });
  state.includeSubfoldersNode.disabled = state.isBusy;
  applyOperationalRunButtonState(state.openButton, state, {
    serviceAvailable: (routeState) => routeState.reportOpenAvailable,
    isBusy: (routeState) => routeState.isBusy
  });
  renderSummary(state);
  syncRouteBusyState(state);
}

async function runReport(state) {
  state.isBusy = true;
  updateState(state);
  setTextWithState(state.statusNode, t(state, "run_status_running", "Running project-state report..."));
  setTextWithState(state.warningNode, "");
  setTextWithState(state.resultNode, "");
  try {
    const response = await postJson(PROJECT_STATE_ENDPOINTS.report, {
      include_subfolders: Boolean(state.includeSubfoldersNode.checked),
      activity_context: buildStudioActivityContext({
        pageId: "project-state",
        actionId: "run-project-state-report",
        route: "/studio/project-state/",
        controlId: "projectStateRunButton",
        controlSelector: "#projectStateRunButton",
        recordIdField: "activity_target",
        recordId: "project-state"
      })
    });
    state.summary = response && response.summary ? response.summary : {};
    state.outputPath = normalizeText(response && response.output_path) || state.outputPath;
    state.sourceRoot = normalizeText(response && response.projects_root) || state.sourceRoot;
    state.outputPathNode.textContent = state.outputPath;
    state.sourceRootNode.textContent = state.sourceRoot;
    setTextWithState(
      state.statusNode,
      t(state, "run_status_success", "Project-state report updated."),
      "success"
    );
    setTextWithState(
      state.resultNode,
      t(state, "run_result_success", "Report written to {path}.", { path: state.outputPath }),
      "success"
    );
  } catch (error) {
    setTextWithState(
      state.statusNode,
      `${t(state, "run_status_failed", "Project-state report failed.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  } finally {
    state.isBusy = false;
    updateState(state);
  }
}

async function openReportSource(state) {
  setTextWithState(state.warningNode, "");
  try {
    await postJson(PROJECT_STATE_ENDPOINTS.openReport, {
      editor: "vscode"
    });
  } catch (error) {
    setTextWithState(
      state.warningNode,
      `${t(state, "open_failed", "Could not open the Markdown source file.")} ${normalizeText(error && error.message)}`.trim(),
      "error"
    );
  }
}

async function init() {
  const root = document.getElementById("projectStateRoot");
  const loadingNode = document.getElementById("projectStateLoading");
  const emptyNode = document.getElementById("projectStateEmpty");
  const pageHeadingNode = document.getElementById("projectStatePageHeading");
  const contextNode = document.getElementById("projectStateContext");
  const statusNode = document.getElementById("projectStateStatus");
  const warningNode = document.getElementById("projectStateWarning");
  const resultNode = document.getElementById("projectStateResult");
  const runHeadingNode = document.getElementById("projectStateRunHeading");
  const outputLabelNode = document.getElementById("projectStateOutputLabel");
  const sourceLabelNode = document.getElementById("projectStateSourceLabel");
  const outputPathNode = document.getElementById("projectStateOutputPath");
  const sourceRootNode = document.getElementById("projectStateSourceRoot");
  const includeSubfoldersNode = document.getElementById("projectStateIncludeSubfolders");
  const includeSubfoldersLabelNode = document.getElementById("projectStateIncludeSubfoldersLabel");
  const summaryHeadingNode = document.getElementById("projectStateSummaryHeading");
  const summaryNode = document.getElementById("projectStateSummary");
  const runButton = document.getElementById("projectStateRunButton");
  const openButton = document.getElementById("projectStateOpenButton");
  const required = collectOperationalRouteElements({
    root,
    loadingNode,
    emptyNode,
    pageHeadingNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    runHeadingNode,
    outputLabelNode,
    sourceLabelNode,
    outputPathNode,
    sourceRootNode,
    includeSubfoldersNode,
    includeSubfoldersLabelNode,
    summaryHeadingNode,
    summaryNode,
    runButton,
    openButton
  });
  if (!required.ok) {
    return;
  }
  initializeStudioRouteState(root, { route: "project-state" });

  try {
    const config = await loadStudioConfig();
    const catalogueServerAvailable = Boolean(await probeProjectStateCatalogueHealth());
    const reportOpenAvailable = Boolean(await probeProjectStateCatalogueOpenHealth());
    const state = {
      config,
      root,
      catalogueServerAvailable,
      reportOpenAvailable,
      isBusy: false,
      summary: null,
      outputPath: "var/studio/reports/project-state.md",
      sourceRoot: "$DOTLINEFORM_PROJECTS_BASE_DIR/projects",
      statusNode,
      warningNode,
      resultNode,
      outputPathNode,
      sourceRootNode,
      includeSubfoldersNode,
      summaryNode,
      runButton,
      openButton
    };

    pageHeadingNode.textContent = t(state, "page_heading", "project state");
    runHeadingNode.textContent = t(state, "run_heading", "report");
    outputLabelNode.textContent = t(state, "output_label", "output");
    sourceLabelNode.textContent = t(state, "source_label", "source");
    includeSubfoldersLabelNode.textContent = t(state, "include_subfolders_label", "include sub-folders");
    summaryHeadingNode.textContent = t(state, "summary_heading", "summary");
    loadingNode.textContent = t(state, "loading", "loading project state...");
    emptyNode.textContent = t(state, "empty_state", "");
    runButton.textContent = t(state, "run_button", "Run");
    openButton.textContent = t(state, "open_button", "Open file");
    setTextWithState(contextNode, t(state, "context_hint", "Scan source project folders and primary images against works.json, then write the Markdown report. Include sub-folders only when you want nested project folders in the review."));
    runButton.addEventListener("click", () => {
      runReport(state).catch((error) => console.warn("project_state: unexpected report failure", error));
    });
    openButton.addEventListener("click", () => {
      openReportSource(state).catch((error) => console.warn("project_state: unexpected open failure", error));
    });

    updateState(state);
    root.hidden = false;
    loadingNode.hidden = true;
    markRouteReady(state, true);
  } catch (error) {
    console.warn("project_state: init failed", error);
    loadingNode.textContent = "Failed to load project state.";
    root.hidden = false;
    const fallbackState = {
      root,
      catalogueServerAvailable: false,
      reportOpenAvailable: false,
      isBusy: false,
      summary: null
    };
    markRouteReady(fallbackState, true);
  }
}

init();
