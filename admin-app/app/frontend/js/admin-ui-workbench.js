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
const recipeSelect = document.querySelector("#adminUiWorkbenchRecipe");
const recipeStepField = document.querySelector("#adminUiWorkbenchRecipeStepField");
const recipeStepSelect = document.querySelector("#adminUiWorkbenchRecipeStep");
const themeButton = document.querySelector("#adminUiWorkbenchTheme");
const viewportButton = document.querySelector("#adminUiWorkbenchViewport");
const recipeDetail = document.querySelector("#adminUiWorkbenchRecipeDetail");
const recipeQuestion = document.querySelector("#adminUiWorkbenchRecipeQuestion");
const recipeDimensions = document.querySelector("#adminUiWorkbenchRecipeDimensions");
const statusNode = document.querySelector("#adminUiWorkbenchStatus");
const stages = document.querySelector("#adminUiWorkbenchStages");
const primaryHeading = document.querySelector("#adminUiWorkbenchPrimaryHeading");
const comparisonStage = document.querySelector("#adminUiWorkbenchComparisonStage");
const comparisonHeading = document.querySelector("#adminUiWorkbenchComparisonHeading");
const primaryRemountButton = document.querySelector("#adminUiWorkbenchPrimaryRemount");
const comparisonRemountButton = document.querySelector("#adminUiWorkbenchComparisonRemount");
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
let remountSequence = 0;

function text(value) {
  return String(value == null ? "" : value).trim();
}

function themeValue() {
  return themeButton?.dataset.value === "dark" ? "dark" : "light";
}

function viewportValue() {
  return viewportButton?.dataset.value === "narrow" ? "narrow" : "desktop";
}

function projectConditionButton(button, value, currentLabel, label, nextLabel, pressed) {
  if (!button) return;
  button.dataset.value = value;
  button.setAttribute("aria-label", `${label}: ${currentLabel}. Switch to ${nextLabel}.`);
  button.setAttribute("aria-pressed", pressed ? "true" : "false");
  const valueNode = button.querySelector("[data-workbench-toggle-value]");
  if (valueNode) valueNode.textContent = currentLabel;
}

function projectThemeButton(value) {
  const dark = value === "dark";
  const currentLabel = dark ? "dark" : "light";
  projectConditionButton(
    themeButton,
    currentLabel,
    currentLabel,
    "Theme",
    dark ? "light" : "dark",
    dark
  );
}

function projectViewportButton(value) {
  const narrow = value === "narrow";
  const currentLabel = narrow ? "390 × 844" : "desktop";
  const nextLabel = narrow ? "desktop" : "390 by 844";
  projectConditionButton(
    viewportButton,
    narrow ? "narrow" : "desktop",
    currentLabel,
    "Viewport",
    nextLabel,
    narrow
  );
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
  return specimenById(specimenInput?.value);
}

function activeRecipe() {
  return recipes.find((record) => record.id === text(recipeSelect?.value)) || null;
}

function populateRecipeSteps(recipe) {
  if (!recipeStepSelect) return;
  if (recipe?.mode !== "sequential") {
    recipeStepSelect.replaceChildren();
    return;
  }
  const selectedValue = recipeStepSelect.value === "comparison" ? "comparison" : "primary";
  const primary = specimenById(recipe.primarySpecimenId);
  const comparison = specimenById(recipe.comparisonSpecimenId);
  setOptions(recipeStepSelect, [
    { value: "primary", label: specimenLabel(primary) },
    { value: "comparison", label: specimenLabel(comparison) }
  ], selectedValue);
}

function populateSpecimens(preferredId = "") {
  if (!specimenInput) return;
  specimenInput.replaceChildren();
  specimens.forEach((specimen) => {
    const option = document.createElement("option");
    option.value = specimen.id;
    option.textContent = specimenLabel(specimen);
    specimenInput.append(option);
  });
  const preferred = specimenById(preferredId) || specimenById(selectedSpecimenId) || specimens[0] || null;
  selectedSpecimenId = preferred?.id || "";
  specimenInput.value = selectedSpecimenId;
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

function frameUrl(specimenId, remountToken = "") {
  const url = new URL("/admin/app/frontend/routes/admin-ui-workbench-frame.html", window.location.origin);
  url.searchParams.set("app", activePack.appId);
  url.searchParams.set("entrypoint", activePack.entrypoint);
  url.searchParams.set("specimen", specimenId);
  url.searchParams.set("theme", themeValue());
  if (remountToken) url.searchParams.set("remount", remountToken);
  return url.href;
}

function projectRemountButtons(disabled) {
  if (primaryRemountButton) primaryRemountButton.disabled = disabled;
  if (comparisonRemountButton) comparisonRemountButton.disabled = disabled;
}

function projectFrameShellViewport(viewport) {
  document.querySelectorAll(".adminWorkbench__frameShell").forEach((node) => {
    node.dataset.workbenchViewport = viewport;
  });
}

function renderFrames() {
  if (!activePack || !primaryFrame) return;
  populateRecipeSteps(activeRecipe());
  const state = currentFrameState();
  const primary = specimenById(state.primaryId);
  const comparison = specimenById(state.comparisonId);
  if (!primary) {
    setStatus("Choose an exact specimen name.", "error");
    return;
  }

  const viewport = viewportValue();
  projectFrameShellViewport(viewport);
  renderRecipeDetail(state.recipe);
  if (recipeStepField) recipeStepField.hidden = state.recipe?.mode !== "sequential";
  if (specimenInput) {
    specimenInput.disabled = false;
    specimenInput.value = primary.id;
  }

  expectedPrimaryId = primary.id;
  expectedComparisonId = comparison?.id || "";
  mountedPrimaryId = "";
  mountedComparisonId = "";
  delete root.dataset.adminSpecimenMounted;
  delete root.dataset.adminCompareSpecimenMounted;
  root.dataset.adminWorkbenchBusy = "true";
  projectRemountButtons(true);
  setAdminRouteBusy(root, true, { mode: "loading", recordLoaded: true });
  setStatus("");

  if (primaryHeading) primaryHeading.textContent = specimenLabel(primary);
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
  projectRemountButtons(false);
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
    projectRemountButtons(false);
    setAdminRouteBusy(root, false, { mode: "error", service: "unavailable", recordLoaded: true });
    setAdminRouteReady(root, true, { mode: "error", service: "unavailable", recordLoaded: true });
    setStatus(message, "error");
  }
}

function remountSpecimen(frameRole) {
  const primary = frameRole === "primary";
  const frame = primary ? primaryFrame : comparisonFrame;
  const specimenId = primary ? expectedPrimaryId : expectedComparisonId;
  if (!frame || !specimenId || root.dataset.adminWorkbenchBusy === "true") return;

  if (primary) {
    mountedPrimaryId = "";
    delete root.dataset.adminSpecimenMounted;
  } else {
    mountedComparisonId = "";
    delete root.dataset.adminCompareSpecimenMounted;
  }
  root.dataset.adminWorkbenchBusy = "true";
  projectRemountButtons(true);
  setAdminRouteBusy(root, true, { mode: "loading", recordLoaded: true });
  setStatus("");
  remountSequence += 1;
  frame.src = frameUrl(specimenId, String(remountSequence));
}

function selectExactSpecimen() {
  const recipeWasActive = Boolean(activeRecipe());
  if (recipeWasActive && recipeSelect) recipeSelect.value = "";
  const specimen = specimenFromInput();
  if (!specimen) {
    setStatus("Choose an exact specimen name from the list.", "error");
    return;
  }
  if (!recipeWasActive && specimen.id === selectedSpecimenId && mountedPrimaryId === specimen.id) return;
  selectedSpecimenId = specimen.id;
  specimenInput.value = specimen.id;
  renderFrames();
}

function bindControls() {
  appSelect?.addEventListener("change", () => {
    activePack = packs.find((pack) => pack.appId === text(appSelect.value)) || packs[0] || null;
    void loadSelectedPack();
  });
  specimenInput?.addEventListener("change", selectExactSpecimen);
  recipeSelect?.addEventListener("change", () => {
    const recipe = activeRecipe();
    if (recipeStepSelect) recipeStepSelect.value = "primary";
    if (!recipe && specimenInput) {
      const specimen = specimenById(selectedSpecimenId) || specimens[0] || null;
      specimenInput.value = specimen?.id || "";
      specimenInput.disabled = !specimen;
    }
    renderFrames();
  });
  recipeStepSelect?.addEventListener("change", renderFrames);
  primaryRemountButton?.addEventListener("click", () => remountSpecimen("primary"));
  comparisonRemountButton?.addEventListener("click", () => remountSpecimen("comparison"));
  themeButton?.addEventListener("click", () => {
    projectThemeButton(themeValue() === "dark" ? "light" : "dark");
    renderFrames();
  });
  viewportButton?.addEventListener("click", () => {
    projectViewportButton(viewportValue() === "narrow" ? "desktop" : "narrow");
    renderFrames();
  });
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
  projectThemeButton(themeValue());
  projectViewportButton(viewportValue());
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
