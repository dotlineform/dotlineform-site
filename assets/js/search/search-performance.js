const STORAGE_KEY = "dlf.search.performance";
const ENABLED_VALUES = new Set(["1", "true", "on", "yes", "panel", "console", "log"]);
const CONSOLE_VALUES = new Set(["console", "log"]);

export function createSearchPerformanceInstrumentation(options = {}) {
  const mode = resolveInstrumentationMode(options.location || (typeof window !== "undefined" ? window.location : null));
  const enabled = Boolean(mode);
  const panel = options.panel || null;
  const report = options.report || null;
  const summary = options.summary || null;
  const startedAt = now();
  const records = {
    phases: [],
    scopes: [],
    queries: []
  };

  if (!enabled) {
    if (panel) panel.hidden = true;
    return createDisabledInstrumentation();
  }

  if (panel) panel.hidden = false;

  function recordPhase(name, durationMs, detail = {}) {
    records.phases.push({
      name: String(name || ""),
      durationMs: roundMs(durationMs),
      ...sanitizeDetail(detail)
    });
    publish();
  }

  function recordScope(record) {
    records.scopes.push({
      scope: String(record.scope || ""),
      source: String(record.source || ""),
      status: String(record.status || "loaded"),
      payloadBytes: sanitizeNumber(record.payloadBytes),
      loadMs: roundMs(record.loadMs),
      parseMs: roundMs(record.parseMs),
      normalizeMs: roundMs(record.normalizeMs),
      rawEntries: sanitizeNumber(record.rawEntries),
      normalizedEntries: sanitizeNumber(record.normalizedEntries),
      error: sanitizeError(record.error)
    });
    publish();
  }

  function recordQuery(record) {
    records.queries.push({
      queryLength: sanitizeNumber(record.queryLength),
      entryCount: sanitizeNumber(record.entryCount),
      matchCount: sanitizeNumber(record.matchCount),
      visibleCount: sanitizeNumber(record.visibleCount),
      evaluateMs: roundMs(record.evaluateMs),
      sortMs: roundMs(record.sortMs),
      renderMs: roundMs(record.renderMs),
      totalMs: roundMs(record.totalMs)
    });
    records.queries = records.queries.slice(-8);
    publish();
  }

  function publish() {
    const snapshot = getSnapshot();
    if (report) {
      report.textContent = formatReport(snapshot);
    }
    if (summary) {
      summary.textContent = formatSummary(snapshot);
    }
    if (mode === "console") {
      console.info("search performance", snapshot);
    }
  }

  function getSnapshot() {
    return {
      enabled: true,
      mode,
      elapsedMs: roundMs(now() - startedAt),
      phases: records.phases.slice(),
      scopes: records.scopes.slice(),
      queries: records.queries.slice()
    };
  }

  publish();

  return {
    enabled,
    mode,
    getSnapshot,
    markPhase: recordPhase,
    recordScope,
    recordQuery,
    timer: createTimer
  };
}

export function estimatePayloadBytes(text) {
  const value = String(text || "");
  if (typeof TextEncoder !== "undefined") {
    return new TextEncoder().encode(value).length;
  }
  return value.length;
}

function createDisabledInstrumentation() {
  return {
    enabled: false,
    mode: "",
    getSnapshot: () => ({ enabled: false, mode: "", elapsedMs: 0, phases: [], scopes: [], queries: [] }),
    markPhase: () => {},
    recordScope: () => {},
    recordQuery: () => {},
    timer: () => ({ end: () => 0 })
  };
}

function createTimer() {
  const start = now();
  return {
    end: () => roundMs(now() - start)
  };
}

function resolveInstrumentationMode(location) {
  const params = new URLSearchParams(location && location.search ? location.search : "");
  const flag = firstNonEmpty([
    params.get("searchPerf"),
    params.get("search_performance"),
    params.get("perf")
  ]);
  if (flag && ENABLED_VALUES.has(flag.toLowerCase())) {
    return CONSOLE_VALUES.has(flag.toLowerCase()) ? "console" : "panel";
  }
  if (params.get("debug") === "search-performance") {
    return "panel";
  }

  try {
    const storage = typeof window !== "undefined" ? window.localStorage : null;
    const stored = storage ? String(storage.getItem(STORAGE_KEY) || "").trim().toLowerCase() : "";
    if (ENABLED_VALUES.has(stored)) {
      return CONSOLE_VALUES.has(stored) ? "console" : "panel";
    }
  } catch (_error) {
    // Local storage can be unavailable in private browsing or restricted embeds.
  }
  return "";
}

function firstNonEmpty(values) {
  for (const value of values) {
    const text = String(value || "").trim();
    if (text) return text;
  }
  return "";
}

function formatSummary(snapshot) {
  const loadedScopes = snapshot.scopes.filter((scope) => scope.status === "loaded");
  const failedScopes = snapshot.scopes.filter((scope) => scope.status === "failed");
  const latestQuery = snapshot.queries[snapshot.queries.length - 1];
  const scopeText = `${loadedScopes.length} scope${loadedScopes.length === 1 ? "" : "s"} loaded`;
  const failureText = failedScopes.length ? `, ${failedScopes.length} failed` : "";
  const queryText = latestQuery ? `, last query ${formatMs(latestQuery.totalMs)}` : "";
  return `Search performance: ${scopeText}${failureText}${queryText}`;
}

function formatReport(snapshot) {
  const lines = [
    "Search performance",
    `mode: ${snapshot.mode}`,
    `elapsed: ${formatMs(snapshot.elapsedMs)}`
  ];

  if (snapshot.phases.length) {
    lines.push("", "phases:");
    snapshot.phases.forEach((phase) => {
      lines.push(`- ${phase.name}: ${formatMs(phase.durationMs)}`);
    });
  }

  if (snapshot.scopes.length) {
    lines.push("", "scopes:");
    snapshot.scopes.forEach((scope) => {
      const pieces = [
        `${scope.scope || "unknown"} (${scope.source || "unknown"})`,
        scope.status,
        `${scope.normalizedEntries || 0}/${scope.rawEntries || 0} entries`,
        `${scope.payloadBytes || 0} bytes`,
        `load ${formatMs(scope.loadMs)}`,
        `parse ${formatMs(scope.parseMs)}`,
        `normalize ${formatMs(scope.normalizeMs)}`
      ];
      if (scope.error) pieces.push(`error ${scope.error}`);
      lines.push(`- ${pieces.join(", ")}`);
    });
  }

  if (snapshot.queries.length) {
    lines.push("", "recent queries:");
    snapshot.queries.forEach((query) => {
      lines.push(
        `- len ${query.queryLength || 0}: ${query.matchCount || 0}/${query.entryCount || 0} matches, ` +
        `${query.visibleCount || 0} visible, total ${formatMs(query.totalMs)} ` +
        `(eval ${formatMs(query.evaluateMs)}, sort ${formatMs(query.sortMs)}, render ${formatMs(query.renderMs)})`
      );
    });
  }

  return lines.join("\n");
}

function sanitizeDetail(detail) {
  const safe = {};
  if (!detail || typeof detail !== "object") return safe;
  for (const [key, value] of Object.entries(detail)) {
    if (typeof value === "number") {
      safe[key] = sanitizeNumber(value);
    } else if (typeof value === "boolean") {
      safe[key] = value;
    } else if (typeof value === "string") {
      safe[key] = value.slice(0, 80);
    }
  }
  return safe;
}

function sanitizeError(error) {
  if (!error) return "";
  if (error instanceof Error) return String(error.message || error.name || "error").slice(0, 120);
  return String(error).slice(0, 120);
}

function sanitizeNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.round(number)) : 0;
}

function roundMs(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) return 0;
  return Math.round(number * 10) / 10;
}

function formatMs(value) {
  return `${roundMs(value).toFixed(1)}ms`;
}

function now() {
  return typeof performance !== "undefined" && typeof performance.now === "function"
    ? performance.now()
    : Date.now();
}
