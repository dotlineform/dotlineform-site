import {
  getStudioDataPath,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import { fetchJson } from "./studio-data.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeField(value) {
  return normalizeText(value).toLowerCase();
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_field_registry_review.${key}`, fallback, tokens);
}

function setTextWithState(node, text, state = "") {
  if (!node) return;
  node.textContent = text || "";
  if (state) node.dataset.state = state;
  else delete node.dataset.state;
}

function rulesForQuery(registry, query) {
  const rules = Array.isArray(registry && registry.rules) ? registry.rules : [];
  const normalizedQuery = normalizeField(query);
  if (!normalizedQuery) return null;

  const exactMatches = rules.filter((rule) => {
    const fields = Array.isArray(rule && rule.fields) ? rule.fields : [];
    return fields.some((field) => normalizeField(field) === normalizedQuery);
  });
  if (exactMatches.length) {
    return {
      mode: "exact",
      rules: exactMatches
    };
  }

  return {
    mode: "partial",
    rules: rules.filter((rule) => {
      const fields = Array.isArray(rule && rule.fields) ? rule.fields : [];
      return fields.some((field) => normalizeField(field).includes(normalizedQuery));
    })
  };
}

function registryExtract(state) {
  const query = normalizeText(state.searchNode.value);
  const matches = rulesForQuery(state.registry, query);
  if (!matches) {
    return {
      json: state.registry,
      meta: t(state, "meta_all", "Showing full registry.")
    };
  }

  const count = matches.rules.length;
  const metaKey = matches.mode === "exact" ? "meta_exact" : "meta_partial";
  const fallback = matches.mode === "exact"
    ? "Showing {count} exact rule match(es) for field `{field}`."
    : "Showing {count} partial rule match(es) for field search `{field}`.";
  return {
    json: count === 1 ? matches.rules[0] : { query, match_mode: matches.mode, rules: matches.rules },
    meta: t(state, metaKey, fallback, {
      count: String(count),
      field: query
    })
  };
}

function renderRegistry(state) {
  const extract = registryExtract(state);
  state.outputNode.value = JSON.stringify(extract.json, null, 2);
  setTextWithState(state.metaNode, extract.meta, extract.json && Array.isArray(extract.json.rules) && extract.json.rules.length === 0 ? "warn" : "");
}

async function init() {
  const root = document.getElementById("fieldRegistryReviewRoot");
  const loadingNode = document.getElementById("fieldRegistryReviewLoading");
  const emptyNode = document.getElementById("fieldRegistryReviewEmpty");
  const headingNode = document.getElementById("fieldRegistryReviewHeading");
  const contextNode = document.getElementById("fieldRegistryReviewContext");
  const statusNode = document.getElementById("fieldRegistryReviewStatus");
  const searchNode = document.getElementById("fieldRegistryReviewSearch");
  const metaNode = document.getElementById("fieldRegistryReviewMeta");
  const outputLabelNode = document.getElementById("fieldRegistryReviewOutputLabel");
  const outputNode = document.getElementById("fieldRegistryReviewOutput");
  if (!root || !loadingNode || !emptyNode || !headingNode || !contextNode || !statusNode || !searchNode || !metaNode || !outputLabelNode || !outputNode) {
    return;
  }

  try {
    const config = await loadStudioConfig();
    const state = {
      config,
      registry: null,
      searchNode,
      metaNode,
      outputNode
    };

    headingNode.textContent = t(state, "page_heading", "catalogue field registry");
    contextNode.textContent = t(state, "context_hint", "Read-only view of the active field-to-artifact registry used by catalogue build planning.");
    loadingNode.textContent = t(state, "loading", "loading catalogue field registry...");
    emptyNode.textContent = t(state, "empty_state", "");
    searchNode.placeholder = t(state, "search_placeholder", "field name");
    outputLabelNode.textContent = t(state, "output_label", "registry extract");

    const registryPath = getStudioDataPath(config, "catalogue_field_registry");
    state.registry = await fetchJson(registryPath, { cache: "no-store" });
    renderRegistry(state);
    searchNode.addEventListener("input", () => renderRegistry(state));
    setTextWithState(statusNode, t(state, "status_loaded", "Registry loaded."), "success");
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_field_registry_review: init failed", error);
    loadingNode.textContent = "Failed to load catalogue field registry.";
  }
}

init();
