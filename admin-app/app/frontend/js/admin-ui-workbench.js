import { loadAdminConfig } from "./admin-config.js";
import {
  initializeAdminRouteState,
  setAdminRouteBusy,
  setAdminRouteReady
} from "./admin-route-state.js";

const root = document.querySelector("#adminUiWorkbenchRoot");
const appField = document.querySelector("#adminUiWorkbenchAppField");
const appSelect = document.querySelector("#adminUiWorkbenchApp");
const specimenInput = document.querySelector("#adminUiWorkbenchSpecimen");
const specimenOptions = document.querySelector("#adminUiWorkbenchSpecimenOptions");
const recipeSelect = document.querySelector("#adminUiWorkbenchRecipe");
const recipeStepField = document.querySelector("#adminUiWorkbenchRecipeStepField");
const recipeStepSelect = document.querySelector("#adminUiWorkbenchRecipeStep");
const themeSelect = document.querySelector("#adminUiWorkbenchTheme");
const viewportSelect = document.querySelector("#adminUiWorkbenchViewport");
const recipeDetail = document.querySelector("#adminUiWorkbenchRecipeDetail");
const recipeQuestion = document.querySelector("#adminUiWorkbenchRecipeQuestion");
const recipeDimensions = document.querySelector("#adminUiWorkbenchRecipeDimensions");
const statusNode = document.querySelector("#adminUiWorkbenchStatus");
const stages = document.querySelector("#adminUiWorkbenchStages");
const primaryHeading = document.querySelector("#adminUiWorkbenchPrimaryHeading");
const comparisonStage = document.querySelector("#adminUiWorkbenchComparisonStage");
const comparisonHeading = document.querySelector("#adminUiWorkbenchComparisonHeading");
const primaryFrame = document.querySelector("#adminUiWorkbenchPrimaryFrame");
const comparisonFrame = document.querySelector("#adminUiWorkbenchComparisonFrame");

let packs = [];
let activePack = null;
let specimens = [];
let recipes = [];
let selectedSpecimenId = "";
let expectedPrimaryId = "";
let expectedComparisonId = "";
let mountedPrimaryId = "";
let mountedComparisonId = "";

function text(value) {
  return String(value == null ? "" : value).trim();
}

function setStatus(message, state = "") {
  if (!statusNode) return;
  const value = text(message);
  statusNode.textContent = value;
  statusNode.hidden = !value;
  if (state) statusNode.dataset.state = state;
  else delete statusNode.dataset.state;
}

function setOptions(select, records, selectedValue = "") {
  if (!select) return;
  select.replaceChildren();
  records.forEach((record) => {
    const option = document.createElement("option");
    option.value = text(record.value);
    option.textContent = text(record.label) || option.value;
    select.append(option);
  });
  if (selectedValue && records.some((record) => text(record.value) === selectedValue)) {
    select.value = selectedValue;
  }
}

function packRecords(config) {
  const configured = config?.app?.workbench?.packs;
  if (!Array.isArray(configured)) return [];
  return configured.map((pack) => ({
    appId: text(pack?.app_id),
    label: text(pack?.label),
    entrypoint: text(pack?.entrypoint)
  })).filter((pack) => (
    pack.appId
    && pack.label
    && pack.entrypoint.startsWith("/docs-viewer/tests/workbench/")
    && pack.entrypoint.endsWith(".js")
  ));
}

function specimenRecords(value) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  return value.map((record) => ({
    id: text(record?.id),
    label: text(record?.label),
    family: text(record?.family),
    state: text(record?.state)
  })).filter((record) => {
    if (!record.id || !record.label || !record.family || !record.state || seen.has(record.id)) return false;
    seen.add(record.id);
    return true;
  });
}

function recipeRecords(value, validSpecimens) {
  if (!Array.isArray(value)) return [];
  const specimenIds = new Set(validSpecimens.map((record) => record.id));
  const seen = new Set();
  return value.map((record) => ({
    id: text(record?.id),
    label: text(record?.label),
    question: text(record?.question),
    primarySpecimenId: text(record?.primarySpecimenId),
    comparisonSpecimenId: text(record?.comparisonSpecimenId),
    dimensions: Array.isArray(record?.dimensions)
      ? record.dimensions.map(text).filter(Boolean)
      : [],
    mode: text(record?.mode)
  })).filter((record) => {
    if (
      !record.id
      || !record.label
      || !record.question
      || seen.has(record.id)
      || !specimenIds.has(record.primarySpecimenId)
      || !specimenIds.has(record.comparisonSpecimenId)
      || !record.dimensions.length
      || !["sequential", "side-by-side"].includes(record.mode)
    ) return false;
    seen.add(record.id);
    return true;
  });
}

function specimenLabel(specimen) {
  return `${specimen.label} — ${specimen.family} / ${specimen.state}`;
}

function specimenById(specimenId) {
  return specimens.find((record) => record.id === text(specimenId)) || null;
}

function specimenFromInput() {
  const value = text(specimenInput?.value);
  return specimens.find((record) => record.id === value || specimenLabel(record) === value) || null;
}

function activeRecipe() {
  return recipes.find((record) => record.id === text(recipeSelect?.value)) || null;
}

function populateSpecimens(preferredId = "") {
  if (!specimenOptions || !specimenInput) return;
  specimenOptions.replaceChildren();
  specimens.forEach((specimen) => {
    const option = document.createElement("option");
    option.value = specimenLabel(specimen);
    specimenOptions.append(option);
  });
  const preferred = specimenById(preferredId) || specimenById(selectedSpecimenId) || specimens[0] || null;
  selectedSpecimenId = preferred?.id || "";
  specimenInput.value = preferred ? specimenLabel(preferred) : "";
  specimenInput.disabled = !preferred;
}

function populateRecipes() {
  setOptions(recipeSelect, [
    { value: "", label: "Single specimen" },
    ...recipes.map((recipe) => ({ value: recipe.id, label: recipe.label }))
  ]);
  if (recipeSelect) recipeSelect.disabled = recipes.length === 0;
}

function renderRecipeDetail(recipe) {
  if (!recipeDetail || !recipeQuestion || !recipeDimensions) return;
  recipeDetail.hidden = !recipe;
  if (!recipe) {
    recipeQuestion.textContent = "";
    recipeDimensions.textContent = "";
    return;
  }
  recipeQuestion.textContent = recipe.question;
  recipeDimensions.textContent = `${recipe.mode === "side-by-side" ? "Side by side" : "Sequential"} · ${recipe.dimensions.join(" · ")}`;
}

function currentFrameState() {
  const recipe = activeRecipe();
  if (!recipe) {
    return {
      primaryId: selectedSpecimenId,
      comparisonId: "",
      recipe: null
    };
  }
  if (recipe.mode === "side-by-side") {
    return {
      primaryId: recipe.primarySpecimenId,
      comparisonId: recipe.comparisonSpecimenId,
      recipe
    };
  }
  return {
    primaryId: recipeStepSelect?.value === "comparison"
      ? recipe.comparisonSpecimenId
      : recipe.primarySpecimenId,
    comparisonId: "",
    recipe
  };
}

function frameUrl(specimenId) {
  const url = new URL("/admin/app/frontend/routes/admin-ui-workbench-frame.html", window.location.origin);
  url.searchParams.set("app", activePack.appId);
  url.searchParams.set("entrypoint", activePack.entrypoint);
  url.searchParams.set("specimen", specimenId);
  url.searchParams.set("theme", themeSelect?.value === "dark" ? "dark" : "light");
  return url.href;
}

function projectFrameShellViewport(viewport) {
  document.querySelectorAll(".adminWorkbench__frameShell").forEach((node) => {
    node.dataset.workbenchViewport = viewport;
  });
}

function renderFrames() {
  if (!activePack || !primaryFrame) return;
  const state = currentFrameState();
  const primary = specimenById(state.primaryId);
  const comparison = specimenById(state.comparisonId);
  if (!primary) {
    setStatus("Choose an exact specimen name.", "error");
    return;
  }

  const viewport = viewportSelect?.value === "narrow" ? "narrow" : "desktop";
  projectFrameShellViewport(viewport);
  renderRecipeDetail(state.recipe);
  if (recipeStepField) recipeStepField.hidden = state.recipe?.mode !== "sequential";
  if (specimenInput) {
    specimenInput.disabled = Boolean(state.recipe);
    specimenInput.value = specimenLabel(primary);
  }

  expectedPrimaryId = primary.id;
  expectedComparisonId = comparison?.id || "";
  mountedPrimaryId = "";
  mountedComparisonId = "";
  delete root.dataset.adminSpecimenMounted;
  delete root.dataset.adminCompareSpecimenMounted;
  root.dataset.adminWorkbenchBusy = "true";
  setAdminRouteBusy(root, true, { mode: "loading", recordLoaded: true });
  setStatus("");

  if (primaryHeading) primaryHeading.textContent = state.recipe?.mode === "sequential"
    ? `${recipeStepSelect?.value === "comparison" ? "B" : "A"} · ${specimenLabel(primary)}`
    : specimenLabel(primary);
  primaryFrame.src = frameUrl(primary.id);

  const comparing = Boolean(comparison);
  if (comparisonStage) comparisonStage.hidden = !comparing;
  if (stages) stages.dataset.workbenchComparing = comparing ? "true" : "false";
  if (comparing && comparisonFrame) {
    if (comparisonHeading) comparisonHeading.textContent = specimenLabel(comparison);
    comparisonFrame.src = frameUrl(comparison.id);
  } else if (comparisonFrame) {
    comparisonFrame.removeAttribute("src");
  }
}

function announceMountedIfReady() {
  if (
    mountedPrimaryId !== expectedPrimaryId
    || (expectedComparisonId && mountedComparisonId !== expectedComparisonId)
  ) return;
  root.dataset.adminWorkbenchBusy = "false";
  root.dataset.adminSpecimenMounted = mountedPrimaryId;
  root.dataset.adminCompareSpecimenMounted = mountedComparisonId;
  setAdminRouteBusy(root, false, { mode: "ready", service: "available", recordLoaded: true });
  setAdminRouteReady(root, true, { mode: "ready", service: "available", recordLoaded: true });
  setStatus("");
}

function handleFrameMessage(event) {
  if (event.origin !== window.location.origin || event.data?.source !== "admin-ui-workbench-frame") return;
  const payload = event.data?.payload && typeof event.data.payload === "object"
    ? event.data.payload
    : {};
  const specimenId = text(payload.specimenId);
  const isPrimary = event.source === primaryFrame?.contentWindow;
  const isComparison = event.source === comparisonFrame?.contentWindow;
  if (!isPrimary && !isComparison) return;

  if (event.data.type === "mounted") {
    if (isPrimary && specimenId === expectedPrimaryId) mountedPrimaryId = specimenId;
    if (isComparison && specimenId === expectedComparisonId) mountedComparisonId = specimenId;
    announceMountedIfReady();
    return;
  }

  if (event.data.type === "error") {
    if (
      (isPrimary && specimenId !== expectedPrimaryId)
      || (isComparison && specimenId !== expectedComparisonId)
    ) return;
    const message = text(payload.message) || "UI Workbench specimen failed.";
    root.dataset.adminWorkbenchBusy = "false";
    setAdminRouteBusy(root, false, { mode: "error", service: "unavailable", recordLoaded: true });
    setAdminRouteReady(root, true, { mode: "error", service: "unavailable", recordLoaded: true });
    setStatus(message, "error");
  }
}

function selectExactSpecimen() {
  if (activeRecipe()) return;
  const specimen = specimenFromInput();
  if (!specimen) {
    setStatus("Choose an exact specimen name from the list.", "error");
    return;
  }
  if (specimen.id === selectedSpecimenId && mountedPrimaryId === specimen.id) return;
  selectedSpecimenId = specimen.id;
  specimenInput.value = specimenLabel(specimen);
  renderFrames();
}

function bindControls() {
  appSelect?.addEventListener("change", () => {
    activePack = packs.find((pack) => pack.appId === text(appSelect.value)) || packs[0] || null;
    void loadSelectedPack();
  });
  specimenInput?.addEventListener("input", () => {
    if (specimenFromInput()) selectExactSpecimen();
  });
  specimenInput?.addEventListener("change", selectExactSpecimen);
  specimenInput?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    selectExactSpecimen();
  });
  recipeSelect?.addEventListener("change", () => {
    const recipe = activeRecipe();
    if (recipeStepSelect) recipeStepSelect.value = "primary";
    if (!recipe && specimenInput) {
      const specimen = specimenById(selectedSpecimenId) || specimens[0] || null;
      specimenInput.value = specimen ? specimenLabel(specimen) : "";
      specimenInput.disabled = !specimen;
    }
    renderFrames();
  });
  recipeStepSelect?.addEventListener("change", renderFrames);
  themeSelect?.addEventListener("change", renderFrames);
  viewportSelect?.addEventListener("change", renderFrames);
  window.addEventListener("message", handleFrameMessage);
}

async function loadSelectedPack() {
  if (!activePack) throw new Error("Admin config does not define a UI Workbench pack.");
  setAdminRouteBusy(root, true, { mode: "loading", recordLoaded: false });
  setStatus("");
  const packModule = await import(activePack.entrypoint);
  const pack = packModule.docsViewerWorkbenchPackRecord?.();
  if (!pack || pack.appId !== activePack.appId) {
    throw new Error(`${activePack.label} did not expose its configured Workbench pack.`);
  }
  specimens = specimenRecords(pack.specimens);
  recipes = recipeRecords(pack.recipes, specimens);
  if (!specimens.length) throw new Error(`${activePack.label} did not expose any valid specimens.`);
  if (Array.isArray(pack.recipes) && recipes.length !== pack.recipes.length) {
    throw new Error(`${activePack.label} exposed an invalid review recipe.`);
  }
  selectedSpecimenId = specimens[0].id;
  populateSpecimens(selectedSpecimenId);
  populateRecipes();
  renderFrames();
}

async function boot() {
  if (!root) return;
  initializeAdminRouteState(root, {
    route: "admin-ui-workbench",
    mode: "loading",
    service: "available",
    recordLoaded: false
  });
  setAdminRouteBusy(root, true);
  bindControls();
  try {
    packs = packRecords(await loadAdminConfig());
    if (!packs.length) throw new Error("Admin config does not define a valid UI Workbench pack.");
    setOptions(appSelect, packs.map((pack) => ({ value: pack.appId, label: pack.label })));
    if (appField) appField.hidden = packs.length <= 1;
    activePack = packs[0];
    await loadSelectedPack();
  } catch (error) {
    const message = error instanceof Error ? error.message : "UI Workbench failed to initialize.";
    setStatus(message, "error");
    setAdminRouteBusy(root, false, { mode: "error", service: "unavailable" });
    setAdminRouteReady(root, true, { mode: "error", service: "unavailable", recordLoaded: false });
    console.error("admin_ui_workbench: failed to initialize", error);
  }
}

void boot();
