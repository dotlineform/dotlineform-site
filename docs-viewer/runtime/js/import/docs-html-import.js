import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  fetchManagementJson,
  openManagedDocSource
} from "../management/docs-viewer-management-client.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "../management/docs-viewer-management-document-target.js";
import {
  openDocsImportCandidateInReview
} from "./docs-import-review-handoff.js";
import {
  clearDocsHtmlImportResult,
  resetDocsHtmlImportWarning
} from "./docs-html-import-render.js";
import {
  docsHtmlImportManagementOptions,
  docsHtmlImportSourceFormatForRecord,
  runDocsHtmlImportWorkflow
} from "./docs-html-import-workflow.js";
import {
  importText
} from "./docs-html-import-text.js";
import {
  DOCS_IMPORT_CANDIDATE_EDITED_REVIEW_SOURCE,
  DOCS_IMPORT_CANDIDATE_ORDINARY,
  DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE,
  docsImportCandidateDestinationLabel,
  docsImportCandidateDisabledMessage,
  docsImportCandidateInventory,
  docsImportCandidateTarget
} from "./docs-import-candidate-model.js";
import {
  createDocsImportCollectionController
} from "./docs-import-collection-controller.js";

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

function setText(node, value) {
  if (node) node.textContent = normalizeText(value);
}

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) node.setAttribute("data-state", state);
  else node.removeAttribute("data-state");
}

function applyRouteDetail(root, detail = {}) {
  if (!root) return;
  if (Object.prototype.hasOwnProperty.call(detail, "route")) {
    root.dataset.studioRoute = normalizeText(detail.route);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "mode")) {
    root.dataset.studioMode = normalizeText(detail.mode);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "service")) {
    root.dataset.studioService = normalizeText(detail.service);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "recordLoaded")) {
    root.dataset.studioRecordLoaded = detail.recordLoaded ? "true" : "false";
  }
}

function initializeRouteState(root) {
  if (!root) return;
  applyRouteDetail(root, { route: "docs-import" });
  root.dataset.studioReady = "false";
  root.dataset.studioBusy = "false";
}

function routeModeForState(state) {
  const collectionMode = state.collectionController && state.collectionController.mode();
  if (collectionMode && collectionMode !== "idle") return collectionMode;
  if (state.resultNode && !state.resultNode.hidden) return "result";
  if (state.warningNode && !state.warningNode.hidden) return "confirm";
  return "idle";
}

function routeStateDetail(state) {
  return {
    route: "docs-import",
    mode: routeModeForState(state),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.candidates.length)
  };
}

function syncRouteBusyState(state) {
  if (!state.root) return;
  applyRouteDetail(state.root, routeStateDetail(state));
  state.root.dataset.studioBusy = state.isRunning ? "true" : "false";
}

function markRouteReady(state, ready) {
  if (!state.root) return;
  applyRouteDetail(state.root, routeStateDetail(state));
  state.root.dataset.studioReady = ready ? "true" : "false";
  state.root.dispatchEvent(new CustomEvent("studio:ready", {
    bubbles: true,
    detail: {
      ready: Boolean(ready),
      busy: state.root.dataset.studioBusy === "true",
      route: state.root.dataset.studioRoute || "",
      mode: state.root.dataset.studioMode || "",
      service: state.root.dataset.studioService || "",
      recordLoaded: state.root.dataset.studioRecordLoaded === "true"
    }
  }));
}

function managementOptionsForState(state) {
  return docsHtmlImportManagementOptions({
    managementBaseUrl: state.managementBaseUrl
  });
}

async function fetchImportCandidates(state) {
  const payload = await fetchManagementJson(
    "/docs/import-source-files",
    "GET",
    undefined,
    managementOptionsForState(state)
  );
  return docsImportCandidateInventory(payload);
}

function selectedCandidate(state) {
  return state.candidates.find(
    (candidate) => candidate.filename === state.selectedFilename
  ) || null;
}

function selectedCandidateTarget(state) {
  return docsImportCandidateTarget(selectedCandidate(state), state.importDestination);
}

function selectedCandidateIsCollection(state) {
  const candidate = selectedCandidate(state);
  return Boolean(
    candidate
    && (
      candidate.candidateKind === DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE
      || candidate.candidateKind === DOCS_IMPORT_CANDIDATE_EDITED_REVIEW_SOURCE
    )
  );
}

function candidateRowHtml(state, candidate, index, selectedFilename) {
  const name = candidate.displayName || candidate.filename;
  const destination = docsImportCandidateDestinationLabel(
    candidate,
    state.importDestination,
    state.importDestinationLabel
  );
  const blocked = candidate.validationState === "blocked";
  const selected = candidate.filename === selectedFilename;
  return [
    `<span class="docsViewerImport__candidateRow" id="docsHtmlImportCandidate-${index + 1}"`,
    ' role="option"',
    ` data-import-candidate data-filename="${escapeHtml(candidate.filename)}"`,
    ` aria-selected="${selected ? "true" : "false"}">`,
    `<span class="docsViewerImport__candidateCell docsViewerImport__candidateCell--file" title="${escapeHtml(name)}">${escapeHtml(name)}</span>`,
    '<span class="docsViewerImport__candidateCell docsViewerImport__candidateCell--destination">',
    `<span class="docsViewerImport__candidateValue" title="${escapeHtml(destination)}">${escapeHtml(destination)}</span>`,
    `${blocked ? '<span class="docsViewerImport__candidateBlocked">Blocked</span>' : ""}`,
    "</span>",
    "</span>"
  ].join("");
}

function resetImportView(state, statusMessage = "") {
  resetDocsHtmlImportWarning(state);
  clearDocsHtmlImportResult(state);
  setStatus(state.statusNode, "", statusMessage);
}

function candidateNote(state, candidate, target) {
  if (!candidate) return "Select one staged source.";
  if (!candidate.importEnabled || !target) {
    return `Import unavailable: ${docsImportCandidateDisabledMessage(candidate, "import")}`;
  }
  if (
    candidate.candidateKind === DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE
    && !candidate.docsReviewEnabled
  ) {
    return `Docs Review unavailable: ${docsImportCandidateDisabledMessage(candidate, "review")}`;
  }
  return "";
}

function syncCandidateDetails(state) {
  const candidate = selectedCandidate(state);
  const target = selectedCandidateTarget(state);
  setText(state.candidateNoteNode, candidateNote(state, candidate, target));
}

function syncCandidateListSelection(state, options = {}) {
  let activeRow = null;
  state.candidateList.querySelectorAll("[data-import-candidate]").forEach((row) => {
    const selected = normalizeText(row.dataset.filename) === state.selectedFilename;
    row.setAttribute("aria-selected", selected ? "true" : "false");
    if (selected) activeRow = row;
  });
  if (activeRow) {
    state.candidateList.setAttribute("aria-activedescendant", activeRow.id);
    if (options.scroll === true) activeRow.scrollIntoView({ block: "nearest" });
  } else {
    state.candidateList.removeAttribute("aria-activedescendant");
  }
}

function selectCandidateFilename(state, filename, options = {}) {
  const normalizedFilename = normalizeText(filename);
  if (!state.candidates.some((candidate) => candidate.filename === normalizedFilename)) return;
  const changed = state.selectedFilename !== normalizedFilename;
  state.selectedFilename = normalizedFilename;
  syncCandidateListSelection(state, { scroll: options.scroll === true });
  if (!changed) return;
  resetImportView(state);
  state.collectionController.reset({ active: false });
  syncImportInputControls(state);
  markRouteReady(state, true);
}

function syncImportInputControls(state) {
  const candidate = selectedCandidate(state);
  const target = selectedCandidateTarget(state);
  const collection = selectedCandidateIsCollection(state);
  const actionable = Boolean(
    state.serviceAvailable
    && state.inventoryCurrent
    && candidate
    && candidate.importEnabled
    && target
  );
  const reviewable = Boolean(
    state.serviceAvailable
    && state.inventoryCurrent
    && candidate
    && candidate.candidateKind === DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE
    && candidate.docsReviewEnabled
    && target
  );
  const supportsPromptMeta = Boolean(
    candidate
    && candidate.candidateKind === DOCS_IMPORT_CANDIDATE_ORDINARY
    && docsHtmlImportSourceFormatForRecord(candidate.raw) === "html"
  );
  const listDisabled = state.isRunning || !state.candidates.length;
  state.candidateList.setAttribute("aria-disabled", listDisabled ? "true" : "false");
  state.includePromptMetaWrap.hidden = !supportsPromptMeta;
  state.includePromptMeta.disabled = state.isRunning || !actionable || !supportsPromptMeta;
  if (!supportsPromptMeta) state.includePromptMeta.checked = false;
  state.runButton.textContent = collection
    ? importText("collectionPreviewButton")
    : importText("importButton");
  state.runButton.disabled = state.isRunning || !actionable;
  state.reviewButton.disabled = state.isRunning || !reviewable;
  state.collectionController.setActive(Boolean(collection && actionable));
  syncCandidateDetails(state);
}

function renderCandidateList(state, candidates) {
  const previousFilename = state.selectedFilename;
  state.candidates = Array.from(candidates || []);
  const retained = state.candidates.some((candidate) => candidate.filename === previousFilename)
    ? previousFilename
    : state.candidates[0] && state.candidates[0].filename;
  state.selectedFilename = normalizeText(retained);
  state.candidateList.innerHTML = state.candidates.map((candidate, index) => (
    candidateRowHtml(state, candidate, index, state.selectedFilename)
  )).join("");
  syncCandidateListSelection(state);
  state.collectionController.reset({ active: false });
  resetImportView(state);
  syncImportInputControls(state);
  if (!state.candidates.length) {
    setStatus(state.statusNode, "warn", importText("noFiles"));
  }
  markRouteReady(state, true);
}

function setImportDestination(state, destination, options = {}) {
  state.importDestination = destination
    ? normalizeManagedDocumentCollectionTarget(destination)
    : null;
  state.importDestinationLabel = normalizeText(options.label);
  if (state.candidates.length) {
    renderCandidateList(state, state.candidates);
  } else {
    syncImportInputControls(state);
  }
}

function refreshStagedFiles(state) {
  if (!state.serviceAvailable || state.isRunning) {
    return Promise.resolve(state.candidates);
  }
  if (state.refreshPromise) return state.refreshPromise;
  state.inventoryCurrent = false;
  state.candidateList.setAttribute("aria-disabled", "true");
  state.runButton.disabled = true;
  state.reviewButton.disabled = true;
  setStatus(state.statusNode, "", "");
  setText(state.candidateNoteNode, "Loading staged sources...");
  state.refreshPromise = fetchImportCandidates(state)
    .then((candidates) => {
      state.inventoryCurrent = true;
      renderCandidateList(state, candidates);
      return candidates;
    })
    .catch((error) => {
      console.warn("docs_import_source: candidate refresh failed", error);
      state.inventoryCurrent = false;
      syncImportInputControls(state);
      setStatus(
        state.statusNode,
        "error",
        normalizeText(error && error.message) || importText("loadFilesFailed")
      );
      markRouteReady(state, true);
      return state.candidates;
    })
    .finally(() => {
      state.refreshPromise = null;
    });
  return state.refreshPromise;
}

async function openResultSource(state, link) {
  const scope = normalizeText(link && link.dataset ? link.dataset.scope : "");
  const subScope = normalizeText(link && link.dataset ? link.dataset.subScope : "");
  const docId = normalizeText(link && link.dataset ? link.dataset.docId : "");
  if (!scope || !docId) return;
  try {
    const target = { scope, doc_id: docId };
    if (subScope) target.sub_scope = subScope;
    await openManagedDocSource(target, "vscode", managementOptionsForState(state));
  } catch (error) {
    console.warn("docs_import_source: open source failed", error);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || importText("resultOpenSourceFailed")
    );
  }
}

async function runReview(state) {
  const candidate = selectedCandidate(state);
  const target = selectedCandidateTarget(state);
  if (
    !candidate
    || candidate.candidateKind !== DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE
    || !candidate.docsReviewEnabled
    || !target
  ) {
    setStatus(
      state.statusNode,
      "error",
      docsImportCandidateDisabledMessage(candidate, "review")
    );
    return;
  }
  state.isRunning = true;
  syncImportInputControls(state);
  syncRouteBusyState(state);
  state.onBusyChange(true);
  setStatus(state.statusNode, "busy", "Preparing the complete package for Docs Review...");
  try {
    const result = await openDocsImportCandidateInReview({
      scope: target.scope,
      stagedFilename: candidate.filename,
      review: (payload) => fetchManagementJson(
        "/docs/packages/returned/review",
        "POST",
        payload,
        managementOptionsForState(state)
      )
    });
    setStatus(
      state.statusNode,
      "success",
      normalizeText(result.payload && result.payload.summary_text)
        || "Opened the package in Docs Review."
    );
  } catch (error) {
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || "Docs Review package could not be prepared."
    );
  } finally {
    state.isRunning = false;
    syncImportInputControls(state);
    syncRouteBusyState(state);
    state.onBusyChange(false);
  }
}

async function runImport(state) {
  const candidate = selectedCandidate(state);
  const target = selectedCandidateTarget(state);
  if (!candidate || !candidate.importEnabled || !target) {
    setStatus(
      state.statusNode,
      "error",
      docsImportCandidateDisabledMessage(candidate, "import")
    );
    return;
  }
  if (selectedCandidateIsCollection(state)) {
    await state.collectionController.preview({
      file: candidate.raw,
      scope: target.scope,
      subScope: normalizeText(target.sub_scope),
      managementBaseUrl: state.managementBaseUrl
    });
    return;
  }
  await runDocsHtmlImportWorkflow(state, {
    files: [candidate.raw],
    scope: target.scope,
    subScope: normalizeText(target.sub_scope),
    includePromptMeta: Boolean(state.includePromptMeta.checked),
    routePath: state.routePath,
    managementBaseUrl: state.managementBaseUrl,
    onRunningChange: (busy) => {
      syncImportInputControls(state);
      syncRouteBusyState(state);
      state.onBusyChange(busy);
    },
    onTerminalResult: state.onTerminalResult
  });
  syncImportInputControls(state);
}

function bindImportEvents(state) {
  state.candidateList.addEventListener("click", (event) => {
    if (state.candidateList.getAttribute("aria-disabled") === "true") return;
    const row = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-import-candidate]")
      : null;
    if (!row || !state.candidateList.contains(row)) return;
    selectCandidateFilename(state, row.dataset.filename);
    state.candidateList.focus();
  });
  state.candidateList.addEventListener("keydown", (event) => {
    if (state.candidateList.getAttribute("aria-disabled") === "true") return;
    const currentIndex = state.candidates.findIndex(
      (candidate) => candidate.filename === state.selectedFilename
    );
    let nextIndex = currentIndex < 0 ? 0 : currentIndex;
    if (event.key === "ArrowDown") nextIndex = Math.min(state.candidates.length - 1, nextIndex + 1);
    else if (event.key === "ArrowUp") nextIndex = Math.max(0, nextIndex - 1);
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = state.candidates.length - 1;
    else return;
    event.preventDefault();
    const candidate = state.candidates[nextIndex];
    if (candidate) selectCandidateFilename(state, candidate.filename, { scroll: true });
  });
  state.runButton.addEventListener("click", () => {
    runImport(state).catch((error) => {
      console.warn("docs_import_source: unexpected import failure", error);
    });
  });
  state.reviewButton.addEventListener("click", () => {
    runReview(state).catch((error) => {
      console.warn("docs_import_source: unexpected Docs Review failure", error);
    });
  });
  state.resultGridNode.addEventListener("click", (event) => {
    const link = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-doc-source-link]")
      : null;
    if (!link || !state.resultGridNode.contains(link)) return;
    event.preventDefault();
    openResultSource(state, link).catch((error) => {
      console.warn("docs_import_source: unexpected open source failure", error);
    });
  });
  state.confirmButton.addEventListener("click", () => {
    if (state.pendingInteractiveOverwriteResolver) {
      state.pendingInteractiveOverwriteResolver("confirm");
      return;
    }
    runImport(state).catch((error) => {
      console.warn("docs_import_source: unexpected overwrite failure", error);
    });
  });
  state.cancelButton.addEventListener("click", () => {
    if (state.pendingInteractiveOverwriteResolver) {
      state.pendingInteractiveOverwriteResolver("cancel");
      return;
    }
    resetDocsHtmlImportWarning(state);
    setStatus(state.statusNode, "", importText("overwriteCancelled"));
  });
}

export async function initDocsHtmlImport(options = {}) {
  const bootStatus = options.bootStatus || document.getElementById("docsHtmlImportBootStatus");
  const root = options.root || document.getElementById("docsHtmlImportRoot");
  if (!bootStatus || !root) return;
  if (root.dataset.docsImportInitialized === "true") return;
  root.dataset.docsImportInitialized = "true";
  initializeRouteState(root);

  const state = {
    bootStatus,
    root,
    candidateList: document.getElementById("docsHtmlImportCandidateList"),
    candidateNoteNode: document.getElementById("docsHtmlImportCandidateNote"),
    includePromptMeta: document.getElementById("docsHtmlImportIncludePromptMeta"),
    includePromptMetaWrap: document.getElementById("docsHtmlImportIncludePromptMetaWrap"),
    includePromptMetaLabelNode: document.getElementById("docsHtmlImportIncludePromptMetaLabel"),
    reviewButton: document.getElementById("docsHtmlImportReview"),
    runButton: document.getElementById("docsHtmlImportRun"),
    confirmButton: document.getElementById("docsHtmlImportConfirm"),
    cancelButton: document.getElementById("docsHtmlImportCancel"),
    statusNode: document.getElementById("docsHtmlImportStatus"),
    warningNode: document.getElementById("docsHtmlImportWarning"),
    collisionHeadingNode: document.getElementById("docsHtmlImportCollisionHeading"),
    collisionBodyNode: document.getElementById("docsHtmlImportCollisionBody"),
    collisionMetaNode: document.getElementById("docsHtmlImportCollisionMeta"),
    resultNode: document.getElementById("docsHtmlImportResult"),
    resultTitleNode: document.getElementById("docsHtmlImportResultTitle"),
    resultGridNode: document.getElementById("docsHtmlImportResultGrid"),
    resultDocIdNode: document.getElementById("docsHtmlImportResultDocId"),
    resultCountsNode: document.getElementById("docsHtmlImportResultCounts"),
    warningsWrap: document.getElementById("docsHtmlImportWarnings"),
    warningsHeading: document.getElementById("docsHtmlImportWarningsHeading"),
    warningsList: document.getElementById("docsHtmlImportWarningsList"),
    collectionView: document.getElementById("docsImportCollectionView"),
    collectionStatusNode: document.getElementById("docsImportCollectionStatus"),
    pendingInteractiveOverwriteResolver: null,
    routePath: normalizeText(options.routePath) || "/docs/",
    managementBaseUrl: normalizeText(options.managementBaseUrl),
    serviceAvailable: false,
    inventoryCurrent: false,
    isRunning: false,
    refreshPromise: null,
    candidates: [],
    selectedFilename: "",
    importDestination: null,
    importDestinationLabel: "",
    onBusyChange: typeof options.onBusyChange === "function" ? options.onBusyChange : () => {},
    onCollectionStateChange: typeof options.onCollectionStateChange === "function"
      ? options.onCollectionStateChange
      : () => {},
    onTerminalResult: typeof options.onTerminalResult === "function"
      ? options.onTerminalResult
      : () => {}
  };
  state.collectionController = createDocsImportCollectionController({
    host: state.collectionView,
    statusNode: state.collectionStatusNode,
    previewStatusNode: state.statusNode,
    renderActions: false,
    routePath: state.routePath,
    onTerminalResult: state.onTerminalResult,
    onViewStateChange: state.onCollectionStateChange,
    onBusyChange: (busy) => {
      state.isRunning = busy;
      syncImportInputControls(state);
      syncRouteBusyState(state);
      state.onBusyChange(busy);
    }
  });

  const requiredNodes = [
    state.candidateList,
    state.candidateNoteNode,
    state.includePromptMeta,
    state.includePromptMetaWrap,
    state.includePromptMetaLabelNode,
    state.reviewButton,
    state.runButton,
    state.confirmButton,
    state.cancelButton,
    state.statusNode,
    state.warningNode,
    state.collisionHeadingNode,
    state.collisionBodyNode,
    state.collisionMetaNode,
    state.resultNode,
    state.resultTitleNode,
    state.resultGridNode,
    state.resultDocIdNode,
    state.resultCountsNode,
    state.warningsWrap,
    state.warningsHeading,
    state.warningsList,
    state.collectionView,
    state.collectionStatusNode
  ];
  if (requiredNodes.some((node) => !node)) {
    delete root.dataset.docsImportInitialized;
    throw new Error("Docs Import modal markup is incomplete.");
  }

  const importApp = {
    refreshStagedFiles: () => refreshStagedFiles(state),
    setDestination: (destination, destinationOptions = {}) => {
      setImportDestination(state, destination, destinationOptions);
    }
  };

  try {
    state.managementBaseUrl = normalizeText(options.managementBaseUrl);
    setImportDestination(state, options.initialDestination || null, {
      label: options.initialDestinationLabel
    });
    setText(state.includePromptMetaLabelNode, importText("includePromptMetaLabel"));
    setText(state.confirmButton, importText("confirmOverwriteButton"));
    setText(state.cancelButton, importText("cancelOverwriteButton"));
    state.includePromptMeta.checked = false;
    bindImportEvents(state);

    root.hidden = false;
    bootStatus.hidden = true;
    state.serviceAvailable = await fetchManagementJson(
      "/health",
      "GET",
      undefined,
      managementOptionsForState(state)
    ).then(() => true).catch(() => false);
    if (!state.serviceAvailable) {
      syncImportInputControls(state);
      setStatus(state.statusNode, "error", DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE);
      markRouteReady(state, true);
      return importApp;
    }

    await refreshStagedFiles(state);
    return importApp;
  } catch (error) {
    console.warn("docs_import_source: init failed", error);
    bootStatus.hidden = false;
    setStatus(bootStatus, "error", importText("loadFilesFailed"));
    root.hidden = false;
    state.serviceAvailable = false;
    markRouteReady(state, true);
    delete root.dataset.docsImportInitialized;
    throw error;
  }
}
