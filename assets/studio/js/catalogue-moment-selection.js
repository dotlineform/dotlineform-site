import {
  normalizeMomentId,
  normalizeText
} from "./catalogue-moment-fields.js";

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

export function setMomentSelectionPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

export function getMomentSearchMatches(state, query) {
  const needle = normalizeText(query).toLowerCase();
  if (!needle) return [];
  return state.momentRows
    .filter((row) => row.search.includes(needle))
    .slice(0, SEARCH_LIMIT);
}

export function renderMomentSearchSuggestions(state, context, rawQuery) {
  const query = normalizeText(rawQuery);
  const rows = getMomentSearchMatches(state, query);
  if (!rows.length) {
    state.popupListNode.innerHTML = `<p class="tagStudio__popupEmpty">${escapeHtml(text(context, "search_no_match", "No matching moment records."))}</p>`;
    setMomentSelectionPopupVisibility(state, Boolean(query));
    return;
  }
  state.popupListNode.innerHTML = rows.map((row) => `
    <button type="button" class="tagStudio__popupItem" data-moment-id="${escapeHtml(row.moment_id)}">
      <span class="tagStudio__popupTitle">${escapeHtml(row.title || row.moment_id)}</span>
      <span class="tagStudio__popupMeta">${escapeHtml(row.moment_id)}</span>
    </button>
  `).join("");
  setMomentSelectionPopupVisibility(state, true);
}

export async function openMomentSelection(state, requestedValue, context) {
  const value = normalizeMomentId(requestedValue);
  if (!value) {
    context.setTextWithState(
      state.statusNode,
      text(context, "search_empty", "Enter a moment id or title."),
      "warning"
    );
    return;
  }
  const exact = state.moments.has(value) ? value : "";
  const match = exact || (getMomentSearchMatches(state, value)[0] || {}).moment_id || "";
  await context.openMoment(match || value);
}

export function bindMomentSelectionControls(state, context) {
  state.searchNode.addEventListener("input", () => {
    renderMomentSearchSuggestions(state, context, state.searchNode.value);
  });
  state.searchNode.addEventListener("focus", () => {
    renderMomentSearchSuggestions(state, context, state.searchNode.value);
  });
  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-moment-id]") : null;
    if (!button) return;
    state.searchNode.value = button.dataset.momentId || "";
    setMomentSelectionPopupVisibility(state, false);
    context.openMoment(state.searchNode.value).catch((error) => {
      console.warn("catalogue_moment_editor: open failed", error);
    });
  });
  state.openButton.addEventListener("click", () => {
    openMomentSelection(state, state.searchNode.value, context).catch((error) => {
      console.warn("catalogue_moment_editor: open failed", error);
    });
  });
}

export async function applyInitialMomentRouteSelection(state, context) {
  const initialMoment = normalizeMomentId(new URLSearchParams(window.location.search).get("moment"));
  const initialImportFile = context.currentImportFile();
  if (initialMoment) {
    state.searchNode.value = initialMoment;
    await context.openMoment(initialMoment, { skipUrl: true });
  } else if (initialImportFile) {
    state.emptyNode.hidden = true;
    context.enterImportMode(initialImportFile);
    await context.previewImport();
  } else {
    context.setEmptyMode();
  }
}
