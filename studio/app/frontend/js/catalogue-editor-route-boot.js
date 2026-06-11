import {
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import { loadStudioLookupJson } from "./studio-data.js";
import { probeCatalogueHealth } from "./studio-transport.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

function defaultItemsFromPayload(payload) {
  return Array.isArray(payload && payload.items) ? payload.items : [];
}

function assignLookupRecord(target, record, normalizeKey) {
  if (!target || typeof target.set !== "function" || typeof normalizeKey !== "function") return;
  if (!record || typeof record !== "object") return;
  const key = normalizeKey(record);
  if (!key) return;
  target.set(key, record);
}

export function catalogueEditorRouteMode(state, options = {}) {
  const importModeKey = options.importModeKey || "";
  if (importModeKey && state[importModeKey]) return "import";
  if (state.mode === "new") return "new";
  if (state.mode === "bulk") return "bulk";
  if (state.currentRecord) return "single";
  return "empty";
}

export function catalogueEditorRecordLoaded(state, options = {}, projectedMode = "") {
  const mode = projectedMode || catalogueEditorRouteMode(state, options);
  if (mode === "bulk") {
    const bulkIdsKey = options.bulkIdsKey || "";
    return bulkIdsKey && Array.isArray(state[bulkIdsKey]) ? state[bulkIdsKey].length > 0 : false;
  }
  if (mode === "single") return Boolean(state.currentRecord);
  return false;
}

export function createCatalogueEditorRouteStateOptions(options = {}) {
  return {
    route: options.route || "",
    mode: options.mode,
    recordLoaded: options.recordLoaded,
    bulkIdsKey: options.bulkIdsKey || "",
    importModeKey: options.importModeKey || "",
    busyKeys: Array.isArray(options.busyKeys) ? options.busyKeys.slice() : undefined
  };
}

export function setCatalogueEditorTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

export function collectRequiredElements(elementIds, rootDocument = document) {
  const elements = {};
  Object.entries(elementIds).forEach(([key, id]) => {
    elements[key] = rootDocument.getElementById(id);
  });
  return Object.values(elements).every(Boolean) ? elements : null;
}

export function initializeCatalogueEditorRoute(root, route) {
  initializeStudioRouteState(root, { route });
}

export function catalogueEditorRouteStateDetail(state, options) {
  const mode = typeof options.mode === "function" ? options.mode(state) : catalogueEditorRouteMode(state, options);
  const recordLoaded = typeof options.recordLoaded === "function"
    ? options.recordLoaded(state)
    : catalogueEditorRecordLoaded(state, options, mode);
  return {
    route: options.route,
    mode,
    service: state.serverAvailable ? "available" : "unavailable",
    recordLoaded
  };
}

export function syncCatalogueEditorRouteBusyState(state, options) {
  const busyKeys = Array.isArray(options.busyKeys) ? options.busyKeys : ["isSaving", "isBuilding", "isDeleting"];
  setStudioRouteBusy(
    state.root,
    busyKeys.some((key) => Boolean(state[key])),
    catalogueEditorRouteStateDetail(state, options)
  );
}

export function markCatalogueEditorRouteReady(state, ready, options) {
  setStudioRouteReady(state.root, ready, catalogueEditorRouteStateDetail(state, options));
}

export async function configureCatalogueEditorRouteRuntime(state, options) {
  const namespace = options.namespace;
  const configLoader = options.configLoader || loadStudioConfigWithText;
  const healthProbe = options.healthProbe || probeCatalogueHealth;
  const config = await configLoader(namespace);
  state.config = config;
  if (typeof options.applyText === "function") options.applyText(config);
  state.serverAvailable = Boolean(await healthProbe());
  return state.serverAvailable;
}

export async function loadCatalogueEditorLookupMaps(state, lookups, options = {}) {
  const lookupLoader = options.lookupLoader || loadStudioLookupJson;
  const readOptions = {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  };
  const payloads = await Promise.all(
    lookups.map((lookup) => lookupLoader(state.config, lookup.configKey, readOptions))
  );
  return payloads.map((payload, index) => {
    const lookup = lookups[index];
    const itemsFromPayload = lookup.itemsFromPayload || defaultItemsFromPayload;
    const items = itemsFromPayload(payload);
    if (lookup.target && typeof lookup.normalizeKey === "function") {
      items.forEach((record) => assignLookupRecord(lookup.target, record, lookup.normalizeKey));
    }
    if (typeof lookup.afterItems === "function") {
      lookup.afterItems(items, payload);
    }
    return items;
  });
}

export function revealCatalogueEditorRoute(state, options) {
  if (options.loadingNode) options.loadingNode.hidden = true;
  if (state.root) state.root.hidden = false;
  markCatalogueEditorRouteReady(state, true, options.routeState);
}

export async function showCatalogueEditorInitError(loadingNode, namespace, fallback, options = {}) {
  const configLoader = options.configLoader || loadStudioConfigWithText;
  const textGetter = options.textGetter || getStudioText;
  try {
    const config = await configLoader(namespace);
    loadingNode.textContent = textGetter(config, `${namespace}.load_failed_error`, fallback);
  } catch (_configError) {
    loadingNode.textContent = fallback;
  }
}
