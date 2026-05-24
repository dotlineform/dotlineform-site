import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  buildWorkRecordSummary as buildRecordSummary
} from "./catalogue-work-sections.js";
import {
  normalizeText,
  normalizeWorkId
} from "./catalogue-work-fields.js";

const SEARCH_LIMIT = 20;

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function text(context, key, fallback, tokens = null) {
  if (context && typeof context.text === "function") {
    return context.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
}

function buildSearchToken(value) {
  const normalized = normalizeText(value);
  if (!normalized) return "";
  const digits = normalized.replace(/\D/g, "");
  return digits || normalized.toLowerCase();
}

function getSourceWorkRecord(state, workId, fallbackRecord = null) {
  const sourceRecord = state.sourceWorkRecordsById.get(workId);
  if (sourceRecord && typeof sourceRecord === "object") return sourceRecord;
  if (fallbackRecord && typeof fallbackRecord === "object") return fallbackRecord;
  return null;
}

export function parseWorkSelection(rawValue) {
  const normalized = normalizeText(rawValue);
  if (!normalized) return [];
  const tokens = normalized.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const workIds = [];
  const seen = new Set();
  tokens.forEach((token) => {
    const rangeMatch = token.match(/^(\d{1,5})\s*-\s*(\d{1,5})$/);
    if (rangeMatch) {
      const start = Number(normalizeWorkId(rangeMatch[1]));
      const end = Number(normalizeWorkId(rangeMatch[2]));
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) {
        throw new Error(`Invalid work id range: ${token}`);
      }
      for (let value = start; value <= end; value += 1) {
        const workId = String(value).padStart(5, "0");
        if (seen.has(workId)) continue;
        seen.add(workId);
        workIds.push(workId);
      }
      return;
    }
    const workId = normalizeWorkId(token);
    if (!workId) {
      throw new Error(`Invalid work id: ${token}`);
    }
    if (seen.has(workId)) return;
    seen.add(workId);
    workIds.push(workId);
  });
  return workIds;
}

export function isWorkBulkQuery(rawValue) {
  try {
    return parseWorkSelection(rawValue).length > 1;
  } catch (_error) {
    return false;
  }
}

export function setWorkSelectionPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

export function getWorkSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [workId, record] of state.workSearchById.entries()) {
    if (workId.includes(query)) {
      matches.push({ workId, record });
      continue;
    }
    if (normalizeWorkId(query) && workId === normalizeWorkId(query)) {
      matches.push({ workId, record });
    }
  }
  matches.sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
  return matches.slice(0, SEARCH_LIMIT);
}

export function renderWorkSearchMatches(state, matches, message = "") {
  if (!matches.length && !message) {
    state.popupListNode.innerHTML = "";
    setWorkSelectionPopupVisibility(state, false);
    return;
  }

  if (!matches.length) {
    state.popupListNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(message)}</p>`;
    setWorkSelectionPopupVisibility(state, true);
    return;
  }

  const rows = matches.map(({ workId, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-work-id="${escapeHtml(workId)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(workId)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setWorkSelectionPopupVisibility(state, true);
}

export function renderWorkSearchSuggestions(state, context, rawQuery) {
  if (!normalizeText(rawQuery)) {
    renderWorkSearchMatches(state, [], "");
    return;
  }
  if (isWorkBulkQuery(rawQuery)) {
    renderWorkSearchMatches(state, [], "");
    return;
  }
  const matches = getWorkSearchMatches(state, rawQuery);
  if (!matches.length) {
    renderWorkSearchMatches(state, [], text(context, "search_no_match", "No matching work ids."));
    return;
  }
  renderWorkSearchMatches(state, matches);
}

export async function openWorkSelection(state, requestedValue, context) {
  let workIds;
  try {
    workIds = parseWorkSelection(requestedValue);
  } catch (error) {
    renderWorkSearchMatches(state, [], normalizeText(error && error.message) || text(context, "search_empty", "Enter a work id."));
    return;
  }

  if (!workIds.length) {
    renderWorkSearchMatches(state, [], text(context, "search_empty", "Enter a work id."));
    return;
  }
  if (workIds.length === 1) {
    await openWorkById(state, workIds[0], context);
    return;
  }

  const unknown = workIds.find((workId) => !state.workSearchById.has(workId));
  if (unknown) {
    renderWorkSearchMatches(state, [], text(context, "unknown_work_error", "Unknown work id: {work_id}.", { work_id: unknown }));
    return;
  }

  state.searchNode.value = workIds.join(", ");
  state.detailSearchNode.value = "";
  setWorkSelectionPopupVisibility(state, false);
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  const lookups = await Promise.all(workIds.map((workId) => context.loadWorkLookupRecord(workId)));
  const recordsById = new Map();
  const recordHashes = new Map();
  for (let index = 0; index < workIds.length; index += 1) {
    const workId = workIds[index];
    const lookup = lookups[index];
    const fallbackRecord = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
    const record = getSourceWorkRecord(state, workId, fallbackRecord);
    if (!record) {
      throw new Error(`work source missing record for ${workId}`);
    }
    recordsById.set(workId, record);
    recordHashes.set(workId, await computeRecordHash(record));
  }
  context.setLoadedBulkWorks(workIds, recordsById, recordHashes);
  await context.refreshBuildPreview();
}

export async function openWorkById(state, requestedWorkId, context) {
  const workId = normalizeWorkId(requestedWorkId);
  if (!workId) {
    renderWorkSearchMatches(state, [], text(context, "search_empty", "Enter a work id."));
    return;
  }

  const searchRecord = state.workSearchById.get(workId);
  if (!searchRecord) {
    const matches = getWorkSearchMatches(state, requestedWorkId);
    if (matches.length) {
      renderWorkSearchMatches(state, matches);
    } else {
      renderWorkSearchMatches(state, [], text(context, "unknown_work_error", "Unknown work id: {work_id}.", { work_id: workId }));
    }
    return;
  }

  state.searchNode.value = workId;
  state.detailSearchNode.value = "";
  setWorkSelectionPopupVisibility(state, false);
  state.pendingBuildExtraSeriesIds = [];
  state.rebuildPending = false;
  const lookup = await context.loadWorkLookupRecord(workId);
  const fallbackRecord = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
  const record = getSourceWorkRecord(state, workId, fallbackRecord);
  if (!record) {
    throw new Error(`work source missing record for ${workId}`);
  }
  context.setLoadedWorkRecord(workId, record, {
    recordHash: await computeRecordHash(record),
    lookup
  });
  await context.refreshBuildPreview();
}

export function bindWorkSelectionControls(state, context) {
  state.searchNode.addEventListener("input", () => {
    const query = state.searchNode.value;
    if (state.mode === "new") {
      state.draft.work_id = normalizeWorkId(query);
      setWorkSelectionPopupVisibility(state, false);
      context.updateEditorState();
      return;
    }
    renderWorkSearchSuggestions(state, context, query);
  });

  state.searchNode.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    if (state.mode === "new") {
      context.saveCurrentWork().catch((error) => {
        console.warn("catalogue_work_editor: unexpected create failure", error);
      });
      return;
    }
    openWorkSelection(state, state.searchNode.value, context).catch((error) => {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
    });
  });

  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-work-id]") : null;
    if (!button) return;
    openWorkById(state, button.getAttribute("data-work-id"), context).catch((error) => {
      console.warn("catalogue_work_editor: failed to open selected work", error);
    });
  });

  state.openButton.addEventListener("click", () => {
    if (state.mode === "new") {
      context.setEmptySearchMode({ keepSearchValue: true });
    }
    openWorkSelection(state, state.searchNode.value, context).catch((error) => {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
    });
  });

  document.addEventListener("click", (event) => {
    if (event.target === state.searchNode || state.popupNode.contains(event.target)) return;
    setWorkSelectionPopupVisibility(state, false);
  });
}

export async function applyInitialWorkRouteSelection(state, context) {
  const params = new URLSearchParams(window.location.search);
  const requestedMode = normalizeText(params.get("mode")).toLowerCase();
  const requestedWorkValue = normalizeText(params.get("work"));
  if (requestedWorkValue) {
    try {
      await openWorkSelection(state, requestedWorkValue, context);
    } catch (error) {
      console.warn("catalogue_work_editor: failed to open requested work selection", error);
      context.setEmptySearchMode({ keepSearchValue: true });
      context.setTextWithState(
        state.statusNode,
        `${text(context, "load_requested_work_failed", "Failed to load the requested work.")} ${normalizeText(error && error.message)}`.trim(),
        "error"
      );
    }
  } else if (requestedMode === "new") {
    context.setNewWorkMode();
  } else {
    context.setEmptySearchMode();
  }
}
