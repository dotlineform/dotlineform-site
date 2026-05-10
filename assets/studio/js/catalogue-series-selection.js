import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  normalizeSeriesId,
  normalizeText
} from "./catalogue-series-fields.js";

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

function buildRecordSummary(record) {
  const title = normalizeText(record && record.title);
  return title || "—";
}

function buildSearchToken(value) {
  const normalized = normalizeText(value);
  if (!normalized) return "";
  return normalized.toLowerCase();
}

export function setSeriesSelectionPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

export function getSeriesSearchMatches(state, rawQuery) {
  const query = buildSearchToken(rawQuery);
  if (!query) return [];
  const matches = [];
  for (const [seriesId, record] of state.seriesById.entries()) {
    const title = normalizeText(record && record.title).toLowerCase();
    if (seriesId.includes(query) || title.includes(query)) {
      matches.push({ seriesId, record });
    }
  }
  matches.sort((a, b) => a.seriesId.localeCompare(b.seriesId, undefined, { numeric: true, sensitivity: "base" }));
  return matches.slice(0, SEARCH_LIMIT);
}

export function renderSeriesSearchMatches(state, matches, message = "") {
  if (!matches.length && !message) {
    state.popupListNode.innerHTML = "";
    setSeriesSelectionPopupVisibility(state, false);
    return;
  }
  if (!matches.length) {
    state.popupListNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(message)}</p>`;
    setSeriesSelectionPopupVisibility(state, true);
    return;
  }
  const rows = matches.map(({ seriesId, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-series-id="${escapeHtml(seriesId)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(seriesId)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setSeriesSelectionPopupVisibility(state, true);
}

export function renderSeriesSearchSuggestions(state, context, rawQuery) {
  if (!normalizeText(rawQuery)) {
    renderSeriesSearchMatches(state, [], "");
    return;
  }
  const matches = getSeriesSearchMatches(state, rawQuery);
  if (!matches.length) {
    renderSeriesSearchMatches(state, [], text(context, "search_no_match", "No matching series records."));
    return;
  }
  renderSeriesSearchMatches(state, matches);
}

export async function openSeriesById(state, requestedSeriesId, context) {
  const seriesId = normalizeSeriesId(requestedSeriesId);
  if (!seriesId) {
    renderSeriesSearchMatches(state, [], text(context, "search_empty", "Enter a series title or id."));
    return;
  }
  const searchRecord = state.seriesById.get(seriesId);
  if (!searchRecord) {
    const matches = getSeriesSearchMatches(state, requestedSeriesId);
    if (matches.length) renderSeriesSearchMatches(state, matches);
    else renderSeriesSearchMatches(state, [], text(context, "unknown_series_error", "Unknown series id: {series_id}.", { series_id: seriesId }));
    return;
  }
  state.searchNode.value = `${seriesId} ${normalizeText(searchRecord.title)}`.trim();
  setSeriesSelectionPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookup = await context.loadSeriesLookupRecord(seriesId);
  const record = lookup && lookup.series && typeof lookup.series === "object" ? lookup.series : null;
  if (!record) {
    throw new Error(`series lookup missing record for ${seriesId}`);
  }
  context.setLoadedSeries(seriesId, record, {
    recordHash: normalizeText(lookup.record_hash) || normalizeText(searchRecord.record_hash) || await computeRecordHash(record),
    lookup
  });
  await context.refreshBuildPreview();
}

export function openFirstSeriesSearchMatch(state, context) {
  const matches = getSeriesSearchMatches(state, state.searchNode.value);
  if (matches[0]) {
    openSeriesById(state, matches[0].seriesId, context).catch((error) => {
      console.warn("catalogue_series_editor: failed to open requested series", error);
    });
  }
}

export function bindSeriesSelectionControls(state, context) {
  state.searchNode.addEventListener("input", () => {
    if (state.mode === "new") {
      state.draft.series_id = normalizeSeriesId(state.searchNode.value);
      setSeriesSelectionPopupVisibility(state, false);
      context.updateEditorState();
      return;
    }
    renderSeriesSearchSuggestions(state, context, state.searchNode.value);
  });

  state.searchNode.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    if (state.mode === "new") {
      context.saveCurrentSeries().catch((error) => {
        console.warn("catalogue_series_editor: unexpected create failure", error);
      });
      return;
    }
    openFirstSeriesSearchMatch(state, context);
  });

  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-series-id]") : null;
    if (!button) return;
    openSeriesById(state, button.getAttribute("data-series-id"), context).catch((error) => {
      console.warn("catalogue_series_editor: failed to open selected series", error);
    });
  });

  state.openButton.addEventListener("click", () => {
    if (state.mode === "new") {
      context.setEmptySearchMode({ keepSearchValue: true });
    }
    openFirstSeriesSearchMatch(state, context);
  });

  document.addEventListener("click", (event) => {
    if (event.target === state.searchNode || state.popupNode.contains(event.target)) return;
    setSeriesSelectionPopupVisibility(state, false);
  });
}

export async function applyInitialSeriesRouteSelection(state, context) {
  const params = new URLSearchParams(window.location.search);
  const requestedSeriesId = normalizeSeriesId(params.get("series"));
  const requestedMode = normalizeText(params.get("mode")).toLowerCase();
  if (requestedMode === "new") {
    context.setNewSeriesMode({ seriesId: requestedSeriesId });
  } else if (requestedSeriesId) {
    await openSeriesById(state, requestedSeriesId, context).catch((error) => {
      console.warn("catalogue_series_editor: failed to open requested series", error);
      context.setTextWithState(
        state.statusNode,
        `${text(context, "load_requested_series_failed", "Failed to load the requested series.")} ${normalizeText(error && error.message)}`.trim(),
        "error"
      );
    });
  } else {
    context.setEmptySearchMode();
  }
}
