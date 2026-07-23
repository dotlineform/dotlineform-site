import {
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal,
  openDocsViewerNoticeModal,
  openDocsViewerTextInputModal
} from "/docs-viewer/runtime/js/management/docs-viewer-management-modal-shell.js";
import {
  createDocsViewerManagementModalController
} from "/docs-viewer/runtime/js/management/docs-viewer-management-modals.js";
import {
  renderDocsViewerManagementShell
} from "/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js";
import {
  renderDocsHtmlImportInteractiveOverwriteWarning,
  renderDocsHtmlImportResult,
  renderDocsHtmlImportWarnings,
  resetDocsHtmlImportWarning
} from "/docs-viewer/runtime/js/import/docs-html-import-render.js";
import {
  renderDocsImportCollectionView
} from "/docs-viewer/runtime/js/import/docs-import-collection-view.js";
import {
  importText
} from "/docs-viewer/runtime/js/import/docs-html-import-text.js";

function text(value) {
  return String(value == null ? "" : value).trim();
}

function afterPaint(documentRef) {
  return new Promise((resolve) => {
    documentRef.defaultView.requestAnimationFrame(() => {
      documentRef.defaultView.requestAnimationFrame(resolve);
    });
  });
}

function resetFixture(context) {
  const root = context.root;
  root.replaceChildren();
  root.className = "docsViewer docsViewerWorkbench__fixtureRoot";
  return root;
}

async function mountDynamicConfirm(context) {
  const root = resetFixture(context);
  void openDocsViewerConfirmModal({
    root,
    title: "Delete selected document?",
    body: ["This confirmation uses the production dynamic modal shell."],
    primaryLabel: "Delete",
    cancelLabel: "Cancel"
  });
  await afterPaint(context.document);
}

async function mountDynamicChoice(context) {
  const root = resetFixture(context);
  void openDocsViewerChoiceModal({
    root,
    title: "Export format",
    body: ["Choose one production radio-group option."],
    name: "workbenchExportFormat",
    value: "jsonl",
    choices: [
      { value: "json", label: "JSON" },
      { value: "jsonl", label: "JSONL" },
      { value: "markdown", label: "Markdown" }
    ],
    primaryLabel: "Continue",
    cancelLabel: "Cancel"
  });
  await afterPaint(context.document);
}

async function mountDynamicValidation(context) {
  const root = resetFixture(context);
  void openDocsViewerTextInputModal({
    root,
    title: "New document",
    label: "Title",
    required: true,
    requiredMessage: "Enter a title.",
    primaryLabel: "Create",
    cancelLabel: "Cancel"
  });
  await afterPaint(context.document);
  const form = root.querySelector('[data-role="modal-form"]');
  form?.dispatchEvent(new context.document.defaultView.Event("submit", {
    bubbles: true,
    cancelable: true
  }));
  await afterPaint(context.document);
}

async function mountDynamicLongResult(context) {
  const root = resetFixture(context);
  void openDocsViewerNoticeModal({
    root,
    title: "Document package prepared",
    size: "wide",
    body: [
      "12 documents prepared.",
      "Output: $DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports/example.jsonl",
      "Metadata: $DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/example.meta.json",
      "Warnings remain visible in this long-content result until Close.",
      ...Array.from({ length: 14 }, (_, index) => `Result detail ${index + 1}`)
    ],
    closeLabel: "Close"
  });
  await afterPaint(context.document);
}

const METADATA_DOCS = [
  {
    doc_id: "d-workbench-current",
    title: "Modal consistency",
    summary: "Production metadata fields rendered from fixture data.",
    date: "2026-07-23",
    date_display: "23 July 2026",
    ui_status: "in-progress",
    parent_id: "d-workbench-guide",
    viewable: true
  },
  {
    doc_id: "d-workbench-guide",
    title: "Docs Viewer guide",
    summary: "",
    parent_id: "",
    viewable: true
  },
  {
    doc_id: "d-workbench-archive",
    title: "Archived delivery notes",
    summary: "",
    parent_id: "",
    viewable: false
  }
];

function metadataParentOptions() {
  return [
    { value: "", label: "Root" },
    { value: "d-workbench-guide", label: "Docs Viewer guide" },
    { value: "d-workbench-archive", label: "Archived delivery notes" }
  ];
}

function createPersistentFixture(context) {
  const root = resetFixture(context);
  const mount = context.document.createElement("div");
  mount.dataset.docsViewerManagementShellMount = "";
  root.append(mount);
  const refs = renderDocsViewerManagementShell({
    document: context.document,
    root,
    mount
  });
  const management = {
    managementBusy: false,
    metadataEditingDocId: ""
  };
  const documentIndex = {
    docsById: new Map(METADATA_DOCS.map((doc) => [doc.doc_id, doc]))
  };
  const controller = createDocsViewerManagementModalController({
    refs,
    documentIndex,
    management,
    scopeConfig: {
      uiStatuses: [
        { ui_status: "proposed", label: "Proposed", emoji: "📝" },
        { ui_status: "in-progress", label: "In progress", emoji: "🔄" },
        { ui_status: "done", label: "Done", emoji: "✅" }
      ]
    },
    callbacks: {
      currentActiveDoc: () => METADATA_DOCS[0],
      hideContextMenu: () => {},
      hideManageActionsMenu: () => {},
      isDocNonViewable: (doc) => doc?.viewable === false,
      metadataParentOptions,
      onImportOpen: () => Promise.resolve(),
      onMetadataSubmit: () => {},
      onSettingsSubmit: (event) => event?.preventDefault(),
      viewerScope: () => "studio"
    }
  });
  controller.wireEvents();
  return { root, refs, controller, management };
}

async function mountMetadataNormal(context) {
  const fixture = createPersistentFixture(context);
  void fixture.controller.openMetadataModal(METADATA_DOCS[0]);
  await afterPaint(context.document);
}

async function mountMetadataParentSuggestions(context) {
  const fixture = createPersistentFixture(context);
  void fixture.controller.openMetadataModal(METADATA_DOCS[0]);
  await afterPaint(context.document);
  fixture.refs.metadataParentInput.value = "Docs";
  fixture.refs.metadataParentInput.dispatchEvent(new context.document.defaultView.Event("input", {
    bubbles: true
  }));
  await afterPaint(context.document);
}

async function mountMetadataLong(context) {
  const fixture = createPersistentFixture(context);
  void fixture.controller.openMetadataModal({
    ...METADATA_DOCS[0],
    title: "A deliberately long document title used to inspect the standard metadata modal at its content boundary",
    summary: Array.from({ length: 8 }, (_, index) => (
      `Summary line ${index + 1} keeps the production textarea and field stack visible.`
    )).join("\n")
  });
  await afterPaint(context.document);
}

async function mountSettings(context, state) {
  const fixture = createPersistentFixture(context);
  fixture.controller.openSettingsModalShell();
  const field = {
    field: "public_base_url",
    type: "string",
    current_value: "https://example.test/docs/",
    description: "Base URL used by exported document links.",
    warnings: state === "warning"
      ? ["This value differs from the current route base.", "Existing exports are unchanged."]
      : []
  };
  if (state === "empty") fixture.controller.setSettingsField(null);
  if (state === "normal" || state === "warning") fixture.controller.setSettingsField(field);
  if (state === "busy") {
    fixture.management.managementBusy = true;
    fixture.controller.setSettingsField(field);
    fixture.controller.setSettingsSaving();
  }
  if (state === "failure") {
    fixture.controller.setSettingsLoadError("Settings could not be loaded from the scope configuration.");
  }
  await afterPaint(context.document);
}

function importNode(documentRef, id) {
  return documentRef.getElementById(id);
}

function setSelectOptions(documentRef, select, records, selectedValue = "") {
  select.replaceChildren();
  records.forEach((record) => {
    const option = documentRef.createElement("option");
    option.value = record.value;
    option.textContent = record.label;
    select.append(option);
  });
  if (selectedValue) select.value = selectedValue;
}

function importRenderState(documentRef) {
  return {
    warningNode: importNode(documentRef, "docsHtmlImportWarning"),
    collisionHeadingNode: importNode(documentRef, "docsHtmlImportCollisionHeading"),
    collisionBodyNode: importNode(documentRef, "docsHtmlImportCollisionBody"),
    collisionMetaNode: importNode(documentRef, "docsHtmlImportCollisionMeta"),
    confirmButton: importNode(documentRef, "docsHtmlImportConfirm"),
    cancelButton: importNode(documentRef, "docsHtmlImportCancel"),
    resultNode: importNode(documentRef, "docsHtmlImportResult"),
    resultTitleNode: importNode(documentRef, "docsHtmlImportResultTitle"),
    resultGridNode: importNode(documentRef, "docsHtmlImportResultGrid"),
    resultDocIdNode: importNode(documentRef, "docsHtmlImportResultDocId"),
    resultCountsNode: importNode(documentRef, "docsHtmlImportResultCounts"),
    warningsWrap: importNode(documentRef, "docsHtmlImportWarnings"),
    warningsHeading: importNode(documentRef, "docsHtmlImportWarningsHeading"),
    warningsList: importNode(documentRef, "docsHtmlImportWarningsList")
  };
}

function configureImportFixture(context, state) {
  const fixture = createPersistentFixture(context);
  const documentRef = context.document;
  fixture.refs.importRoot.hidden = false;
  fixture.refs.importRoot.dataset.studioReady = "true";
  fixture.refs.importRoot.dataset.studioBusy = state === "busy" ? "true" : "false";
  fixture.refs.importBootStatus.hidden = true;
  fixture.controller.openImportModal();

  importNode(documentRef, "docsHtmlImportTypeLabel").textContent = importText("typeLabel");
  importNode(documentRef, "docsHtmlImportFileLabel").textContent = importText("fileLabel");
  importNode(documentRef, "docsHtmlImportScopeLabel").textContent = importText("scopeLabel");
  importNode(documentRef, "docsHtmlImportIncludePromptMetaLabel").textContent = importText("includePromptMetaLabel");
  importNode(documentRef, "docsHtmlImportSelectAll").textContent = importText("selectAllButton");
  importNode(documentRef, "docsHtmlImportRun").textContent = importText("importButton");
  importNode(documentRef, "docsHtmlImportConfirm").textContent = importText("confirmOverwriteButton");
  importNode(documentRef, "docsHtmlImportCancel").textContent = importText("cancelOverwriteButton");
  setSelectOptions(documentRef, importNode(documentRef, "docsHtmlImportTypeSelect"), [
    { value: "files", label: importText("filesOption", { count: 2 }) },
    { value: "data-sharing", label: importText("dataSharingPackagesOption", { count: 1 }) }
  ], state === "collection" ? "data-sharing" : "files");
  setSelectOptions(documentRef, importNode(documentRef, "docsHtmlImportScopeSelect"), [
    { value: "studio", label: "studio" },
    { value: "library", label: "library" }
  ], "studio");

  const files = state === "empty"
    ? []
    : [
        { value: "modal-consistency.md", label: "modal-consistency.md" },
        { value: "reviewed-package.jsonl", label: "reviewed-package.jsonl" }
      ];
  setSelectOptions(
    documentRef,
    importNode(documentRef, "docsHtmlImportFileSelect"),
    files,
    state === "collection" ? "reviewed-package.jsonl" : "modal-consistency.md"
  );
  importNode(documentRef, "docsHtmlImportSelectionCount").textContent = files.length
    ? importText("selectedCount", { count: 1 })
    : "";
  return fixture;
}

function importPayload(filename = "modal-consistency.md", warnings = []) {
  return {
    ok: true,
    scope: "studio",
    doc_id: `d-workbench-${filename.replace(/\W+/g, "-")}`,
    staged_filename: filename,
    import_preview: {
      source_format: "markdown",
      source_stats: {
        chars: 1240,
        links: 4,
        images: 2,
        attachments: 1
      },
      warnings
    }
  };
}

async function mountImport(context, state) {
  const fixture = configureImportFixture(context, state);
  const documentRef = context.document;
  const statusNode = importNode(documentRef, "docsHtmlImportStatus");
  const runButton = importNode(documentRef, "docsHtmlImportRun");
  const fileSelect = importNode(documentRef, "docsHtmlImportFileSelect");

  if (state === "empty") {
    fileSelect.disabled = true;
    runButton.disabled = true;
    statusNode.textContent = importText("noFiles");
  } else if (state === "selected") {
    statusNode.textContent = importText("selectedCount", { count: 1 });
  } else if (state === "collision") {
    const renderState = importRenderState(documentRef);
    renderDocsHtmlImportInteractiveOverwriteWarning(renderState, {
      import_preview: {
        interactive_html_plans: [{ target_path: "media/interactive/modal-demo.html" }]
      }
    });
    renderState.cancelButton.addEventListener("click", () => {
      resetDocsHtmlImportWarning(renderState);
      statusNode.textContent = importText("overwriteCancelled");
      delete statusNode.dataset.state;
    });
    statusNode.textContent = "Review the interactive asset collision.";
    statusNode.dataset.state = "warn";
  } else if (state === "busy") {
    fixture.controller.projectImportBusy(true);
    runButton.disabled = true;
    fileSelect.disabled = true;
    statusNode.textContent = importText("runningStatus");
  } else if (state === "success") {
    renderDocsHtmlImportResult(importRenderState(documentRef), importPayload());
    statusNode.textContent = importText("importAllSuccess", { count: 1 });
    statusNode.dataset.state = "success";
    fixture.controller.projectImportTerminalResult();
  } else if (state === "partial") {
    const renderState = importRenderState(documentRef);
    renderDocsHtmlImportResult(renderState, [
      importPayload("modal-consistency.md"),
      importPayload("modal-review.md", ["One attachment was unavailable and its source reference was preserved."])
    ]);
    statusNode.textContent = importText("importCancelledPartial", { count: 2, total: 3 });
    statusNode.dataset.state = "warn";
    fixture.controller.projectImportTerminalResult();
  } else if (state === "failure") {
    renderDocsHtmlImportWarnings(importRenderState(documentRef), [
      "The staged source could not be converted.",
      "No document was written."
    ]);
    statusNode.textContent = importText("importFailed");
    statusNode.dataset.state = "error";
  } else if (state === "collection") {
    const records = Array.from({ length: 18 }, (_, index) => ({
      record_index: index,
      doc_id: `d-workbench-collection-${index + 1}`,
      title: `Collection document ${index + 1}`,
      action: index % 3 === 0 ? "overwrite" : "create",
      parent: index ? { parent_id: "d-workbench-collection-1" } : {},
      media_plans: index % 4 === 0 ? [{ kind: "image" }] : [],
      warnings: [],
      errors: []
    }));
    const collectionHost = importNode(documentRef, "docsImportCollectionView");
    const collectionState = {
      active: true,
      phase: "confirmation",
      plan: {
        counts: {
          records: records.length,
          creates: 12,
          collisions: 6,
          record_errors: 0,
          media_plans: 5
        },
        records,
        blockers: [],
        warnings: [{ message: "Five media assets will be copied on a best-effort basis." }]
      },
      result: null
    };
    const renderCollection = () => {
      renderDocsImportCollectionView(collectionHost, collectionState, (command) => {
        if (command?.type !== "cancel") return;
        collectionState.phase = "cancelled";
        statusNode.textContent = importText("collectionCancelledStatus");
        delete statusNode.dataset.state;
        renderCollection();
      });
    };
    renderCollection();
    statusNode.textContent = importText("collectionReadyStatus");
    statusNode.dataset.state = "success";
  }
  await afterPaint(context.document);
}

const PACK_STYLES = [
  "/docs-viewer/static/css/docs-viewer-theme.css",
  "/docs-viewer/static/css/docs-viewer.css",
  "/docs-viewer/static/css/docs-viewer-manage.css",
  "/docs-viewer/static/css/docs-viewer-source-editor.css",
  "/docs-viewer/static/css/docs-viewer-import.css"
];

const REVIEW_RECIPES = [
  {
    id: "metadata-settings-fields",
    label: "Field layout — Metadata / Settings",
    question: "Where their contracts match, do Metadata and Settings use consistent field and action-row presentation?",
    primarySpecimenId: "metadata-normal",
    comparisonSpecimenId: "settings-normal",
    dimensions: ["field structure", "spacing", "labels", "action placement"],
    mode: "side-by-side"
  },
  {
    id: "settings-import-busy",
    label: "Busy actions — Settings / Import",
    question: "Do busy states distinguish disabled actions and each workflow's valid cancellation policy?",
    primarySpecimenId: "settings-busy",
    comparisonSpecimenId: "import-busy",
    dimensions: ["busy feedback", "disabled actions", "cancellation", "status"],
    mode: "side-by-side"
  },
  {
    id: "settings-import-failure",
    label: "Failure feedback — Settings / Import",
    question: "Do failure states present status and terminal actions consistently?",
    primarySpecimenId: "settings-failure",
    comparisonSpecimenId: "import-failure",
    dimensions: ["error status", "terminal actions", "hierarchy", "contrast"],
    mode: "side-by-side"
  },
  {
    id: "metadata-parent-lifecycle",
    label: "Nested control — Metadata parent picker",
    question: "Does the parent picker retain its nested keyboard contract without changing the enclosing Metadata modal?",
    primarySpecimenId: "metadata-parent-selected",
    comparisonSpecimenId: "metadata-normal",
    dimensions: ["initial focus", "arrow navigation", "nested Escape", "focus return"],
    mode: "sequential"
  }
];

const REGISTRY = [
  {
    id: "dynamic-confirm-normal",
    label: "Confirmation",
    family: "dynamic",
    state: "normal",
    mount: mountDynamicConfirm
  },
  {
    id: "dynamic-choice-selected",
    label: "Choice with selection",
    family: "dynamic",
    state: "selected",
    mount: mountDynamicChoice
  },
  {
    id: "dynamic-text-validation",
    label: "Required text validation",
    family: "dynamic",
    state: "validation",
    mount: mountDynamicValidation
  },
  {
    id: "dynamic-result-long",
    label: "Long result",
    family: "dynamic",
    state: "long-content",
    mount: mountDynamicLongResult
  },
  {
    id: "metadata-normal",
    label: "Metadata fields",
    family: "metadata",
    state: "normal",
    mount: mountMetadataNormal
  },
  {
    id: "metadata-parent-selected",
    label: "Parent suggestions",
    family: "metadata",
    state: "selected",
    mount: mountMetadataParentSuggestions
  },
  {
    id: "metadata-long",
    label: "Long metadata",
    family: "metadata",
    state: "long-content",
    mount: mountMetadataLong
  },
  {
    id: "settings-loading",
    label: "Settings loading",
    family: "settings",
    state: "loading",
    mount: (context) => mountSettings(context, "loading")
  },
  {
    id: "settings-empty",
    label: "Settings empty",
    family: "settings",
    state: "empty",
    mount: (context) => mountSettings(context, "empty")
  },
  {
    id: "settings-normal",
    label: "Settings field",
    family: "settings",
    state: "normal",
    mount: (context) => mountSettings(context, "normal")
  },
  {
    id: "settings-warning",
    label: "Settings warnings",
    family: "settings",
    state: "validation",
    mount: (context) => mountSettings(context, "warning")
  },
  {
    id: "settings-busy",
    label: "Settings saving",
    family: "settings",
    state: "busy",
    mount: (context) => mountSettings(context, "busy")
  },
  {
    id: "settings-failure",
    label: "Settings load failure",
    family: "settings",
    state: "failure",
    mount: (context) => mountSettings(context, "failure")
  },
  {
    id: "import-empty",
    label: "Import empty",
    family: "import",
    state: "empty",
    mount: (context) => mountImport(context, "empty")
  },
  {
    id: "import-selected",
    label: "Import selected file",
    family: "import",
    state: "selected",
    mount: (context) => mountImport(context, "selected")
  },
  {
    id: "import-collision-validation",
    label: "Interactive asset collision",
    family: "import",
    state: "validation",
    mount: (context) => mountImport(context, "collision")
  },
  {
    id: "import-busy",
    label: "Import busy",
    family: "import",
    state: "busy",
    mount: (context) => mountImport(context, "busy")
  },
  {
    id: "import-success",
    label: "Import success",
    family: "import",
    state: "success",
    mount: (context) => mountImport(context, "success")
  },
  {
    id: "import-partial-result",
    label: "Import partial result",
    family: "import",
    state: "partial",
    mount: (context) => mountImport(context, "partial")
  },
  {
    id: "import-failure",
    label: "Import failure",
    family: "import",
    state: "failure",
    mount: (context) => mountImport(context, "failure")
  },
  {
    id: "import-collection-long",
    label: "Collection confirmation",
    family: "import",
    state: "long-content",
    mount: (context) => mountImport(context, "collection")
  }
];

export const docsViewerWorkbenchRegistry = Object.freeze(REGISTRY.map((record) => Object.freeze(record)));
export const docsViewerWorkbenchReviewRecipes = Object.freeze(
  REVIEW_RECIPES.map((record) => Object.freeze({
    ...record,
    dimensions: Object.freeze([...record.dimensions])
  }))
);
export const docsViewerWorkbenchStyles = Object.freeze([...PACK_STYLES]);

export function docsViewerWorkbenchSpecimenRecords() {
  return docsViewerWorkbenchRegistry.map(({ mount: _mount, ...record }) => ({ ...record }));
}

export function validateDocsViewerWorkbenchRegistry(records = docsViewerWorkbenchRegistry) {
  if (!Array.isArray(records) || !records.length) {
    throw new Error("Docs Viewer UI Workbench registry must contain specimens");
  }
  const ids = new Set();
  records.forEach((record) => {
    if (!text(record?.id) || !text(record?.label) || !text(record?.family) || !text(record?.state)) {
      throw new Error("Docs Viewer UI Workbench specimens require id, label, family, and state");
    }
    if (ids.has(record.id)) throw new Error(`Duplicate Docs Viewer UI Workbench specimen: ${record.id}`);
    if (typeof record.mount !== "function") throw new Error(`Specimen ${record.id} is missing its production mount`);
    ids.add(record.id);
  });
  return true;
}

export function validateDocsViewerWorkbenchReviewRecipes(
  recipes = docsViewerWorkbenchReviewRecipes,
  specimens = docsViewerWorkbenchRegistry
) {
  if (!Array.isArray(recipes)) throw new Error("Docs Viewer UI Workbench recipes must be an array");
  const specimenIds = new Set(specimens.map((record) => record.id));
  const recipeIds = new Set();
  recipes.forEach((recipe) => {
    if (
      !text(recipe?.id)
      || !text(recipe?.label)
      || !text(recipe?.question)
      || !text(recipe?.primarySpecimenId)
      || !text(recipe?.comparisonSpecimenId)
    ) {
      throw new Error("Docs Viewer UI Workbench recipes require ids, labels, questions, and exact A/B specimens");
    }
    if (recipeIds.has(recipe.id)) {
      throw new Error(`Duplicate Docs Viewer UI Workbench recipe: ${recipe.id}`);
    }
    if (!specimenIds.has(recipe.primarySpecimenId) || !specimenIds.has(recipe.comparisonSpecimenId)) {
      throw new Error(`Recipe ${recipe.id} references an unknown specimen`);
    }
    if (!["sequential", "side-by-side"].includes(recipe.mode)) {
      throw new Error(`Recipe ${recipe.id} has an unknown review mode`);
    }
    if (!Array.isArray(recipe.dimensions) || !recipe.dimensions.length || recipe.dimensions.some((value) => !text(value))) {
      throw new Error(`Recipe ${recipe.id} requires review dimensions`);
    }
    recipeIds.add(recipe.id);
  });
  return true;
}

export function docsViewerWorkbenchPackRecord() {
  validateDocsViewerWorkbenchRegistry();
  validateDocsViewerWorkbenchReviewRecipes();
  return {
    appId: "docs-viewer",
    label: "Docs Viewer",
    styles: [...docsViewerWorkbenchStyles],
    specimens: docsViewerWorkbenchSpecimenRecords(),
    recipes: docsViewerWorkbenchReviewRecipes.map((record) => ({
      ...record,
      dimensions: [...record.dimensions]
    }))
  };
}

export async function mountDocsViewerWorkbenchSpecimen(specimenId, context) {
  const specimen = docsViewerWorkbenchRegistry.find((record) => record.id === text(specimenId));
  if (!specimen) throw new Error(`Unknown Docs Viewer UI Workbench specimen: ${specimenId}`);
  await specimen.mount(context);
  return specimen;
}
