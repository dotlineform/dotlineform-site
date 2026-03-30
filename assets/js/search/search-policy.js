const DEFAULT_SEARCH_POLICY = {
  search_policy_version: "search_policy_v1",
  updated_at_utc: "",
  runtime: {
    live_search: true,
    enter_runs_search: true,
    min_query_length: 1,
    debounce_ms: 140,
    results: {
      initial_batch_size: 50,
      batch_increment_size: 50
    }
  },
  scopes: {
    catalogue: {
      enabled: true,
      scope_label: "catalogue",
      back_label: "← works",
      back_route_key: "series_page_base",
      input_aria_label: "Search works, series, and moments",
      input_placeholder: "search works, series, moments"
    },
    library: {
      enabled: false,
      scope_label: "library",
      back_label: "← library",
      back_route_key: "library_page",
      input_aria_label: "Search library",
      input_placeholder: "search library"
    },
    studio: {
      enabled: false,
      scope_label: "studio",
      back_label: "← studio",
      back_route_key: "studio_home",
      input_aria_label: "Search Studio docs",
      input_placeholder: "search studio docs"
    }
  },
  messages: {
    missing_scope_error: "Search is unavailable without a valid search scope.",
    unsupported_scope_error: "Search is not yet available for this scope."
  }
};

export { DEFAULT_SEARCH_POLICY };

export async function loadSearchPolicy(policyUrl, options = {}) {
  const resolvedUrl = String(policyUrl || "").trim();
  if (!resolvedUrl) {
    return cloneJson(DEFAULT_SEARCH_POLICY);
  }

  try {
    const response = await fetch(resolvedUrl, { cache: String(options.cache || "default") });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return mergePolicy(DEFAULT_SEARCH_POLICY, data);
  } catch (error) {
    console.warn("search_policy: using defaults after policy load failure", error);
    return cloneJson(DEFAULT_SEARCH_POLICY);
  }
}

export function getSearchRuntimePolicy(policy) {
  const source = policy && typeof policy === "object" ? policy : DEFAULT_SEARCH_POLICY;
  const runtime = source.runtime && typeof source.runtime === "object" ? source.runtime : {};
  const results = runtime.results && typeof runtime.results === "object" ? runtime.results : {};
  return {
    liveSearch: sanitizeBoolean(runtime.live_search, DEFAULT_SEARCH_POLICY.runtime.live_search),
    enterRunsSearch: sanitizeBoolean(runtime.enter_runs_search, DEFAULT_SEARCH_POLICY.runtime.enter_runs_search),
    minQueryLength: sanitizePositiveInteger(runtime.min_query_length, DEFAULT_SEARCH_POLICY.runtime.min_query_length),
    debounceMs: sanitizePositiveInteger(runtime.debounce_ms, DEFAULT_SEARCH_POLICY.runtime.debounce_ms),
    initialBatchSize: sanitizePositiveInteger(results.initial_batch_size, DEFAULT_SEARCH_POLICY.runtime.results.initial_batch_size),
    batchIncrementSize: sanitizePositiveInteger(results.batch_increment_size, DEFAULT_SEARCH_POLICY.runtime.results.batch_increment_size)
  };
}

export function getSearchScopePolicy(policy, scope) {
  const normalizedScope = normalize(scope);
  if (!normalizedScope) return null;

  const scopes = policy && typeof policy === "object" && policy.scopes && typeof policy.scopes === "object"
    ? policy.scopes
    : DEFAULT_SEARCH_POLICY.scopes;
  const raw = scopes[normalizedScope];
  if (!raw || typeof raw !== "object") return null;

  return {
    scope: normalizedScope,
    enabled: sanitizeBoolean(raw.enabled, false),
    scopeLabel: sanitizeText(raw.scope_label, normalizedScope),
    backLabel: sanitizeText(raw.back_label, ""),
    backRouteKey: sanitizeText(raw.back_route_key, ""),
    inputAriaLabel: sanitizeText(raw.input_aria_label, "Search"),
    inputPlaceholder: sanitizeText(raw.input_placeholder, "")
  };
}

export function getSearchMessage(policy, key, fallback = "") {
  const messages = policy && typeof policy === "object" && policy.messages && typeof policy.messages === "object"
    ? policy.messages
    : DEFAULT_SEARCH_POLICY.messages;
  const value = messages && typeof messages[key] === "string" ? messages[key].trim() : "";
  return value || fallback;
}

function mergePolicy(base, override) {
  const merged = cloneJson(base);
  if (!override || typeof override !== "object") {
    return merged;
  }

  if (typeof override.search_policy_version === "string") {
    merged.search_policy_version = override.search_policy_version.trim() || merged.search_policy_version;
  }
  if (typeof override.updated_at_utc === "string") {
    merged.updated_at_utc = override.updated_at_utc.trim();
  }

  if (override.runtime && typeof override.runtime === "object") {
    const runtime = override.runtime;
    if ("live_search" in runtime) merged.runtime.live_search = runtime.live_search;
    if ("enter_runs_search" in runtime) merged.runtime.enter_runs_search = runtime.enter_runs_search;
    if ("min_query_length" in runtime) merged.runtime.min_query_length = runtime.min_query_length;
    if ("debounce_ms" in runtime) merged.runtime.debounce_ms = runtime.debounce_ms;
    if (runtime.results && typeof runtime.results === "object") {
      if ("initial_batch_size" in runtime.results) {
        merged.runtime.results.initial_batch_size = runtime.results.initial_batch_size;
      }
      if ("batch_increment_size" in runtime.results) {
        merged.runtime.results.batch_increment_size = runtime.results.batch_increment_size;
      }
    }
  }

  if (override.scopes && typeof override.scopes === "object") {
    for (const [scope, value] of Object.entries(override.scopes)) {
      const normalizedScope = normalize(scope);
      if (!normalizedScope || !value || typeof value !== "object") continue;
      merged.scopes[normalizedScope] = {
        ...(merged.scopes[normalizedScope] || {}),
        ...value
      };
    }
  }

  if (override.messages && typeof override.messages === "object") {
    merged.messages = {
      ...merged.messages,
      ...override.messages
    };
  }

  return merged;
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function sanitizeBoolean(value, fallback) {
  return typeof value === "boolean" ? value : fallback;
}

function sanitizePositiveInteger(value, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(1, Math.round(number));
}

function sanitizeText(value, fallback) {
  const text = typeof value === "string" ? value.trim() : "";
  return text || fallback;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}
