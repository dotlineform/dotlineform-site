
import { mountSearchField } from "/shared/frontend/js/search-field.js";
import {
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId
} from "./catalogue-work-fields.js";
import {
  bindSearchList
} from "/shared/frontend/js/search-list.js";

const SEARCH_LIMIT = 20;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalizeSearchText(value) {
  return normalizeText(value).toLowerCase().replace(/\s+/g, " ");
}

function workSearchOptions(state) {
  return Array.from(state.workSearchById.entries()).map(([workId, record]) => ({ workId, record }));
}

function singleWorkId(value) {
  const text = normalizeText(value);
  return /^\d{1,5}$/.test(text) ? normalizeWorkId(text) : "";
}

function workIdPrefixMatches(workId, rawQuery) {
  const queryId = singleWorkId(rawQuery);
  if (!queryId) return false;
  const query = queryId.replace(/^0+/, "") || "0";
  const normalizedWorkId = normalizeText(workId).replace(/^0+/, "") || "0";
  return normalizedWorkId.startsWith(query);
}

function titleMatches(record, rawQuery) {
  const query = normalizeSearchText(rawQuery);
  if (!query || !/[a-z]/i.test(query)) return false;
  return normalizeSearchText(record && record.title).includes(query);
}

export function setWorkSelectionPopupVisibility(state, visible) {
  if (state.popupListNode) state.popupListNode.hidden = !visible;
  else if (state.popupNode) state.popupNode.hidden = !visible;
}

export function getWorkSearchMatches(state, rawQuery) {
  const normalizedQuery = normalizeText(rawQuery);
  if (!normalizedQuery) return [];
  const matches = [];
  for (const [workId, record] of state.workSearchById.entries()) {
    if (/[a-z]/i.test(normalizedQuery) ? titleMatches(record, normalizedQuery) : workIdPrefixMatches(workId, normalizedQuery)) {
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
    state.popupListNode.innerHTML = `<p class="sharedSearchList__empty">${escapeHtml(message)}</p>`;
    setWorkSelectionPopupVisibility(state, true);
    return;
  }

  const rows = matches.map(({ workId, record }) => `
    <button type="button" class="sharedSearchList__option catalogueWorkSearch__option" data-work-id="${escapeHtml(workId)}">
      <span class="catalogueWorkSearch__id">${escapeHtml(workId)}</span>
      <span class="catalogueWorkSearch__title">${escapeHtml(record.title)}</span>
    </button>
  `);
  state.popupListNode.innerHTML = rows.join("");
  setWorkSelectionPopupVisibility(state, true);
}

/** Open a nonempty exact selection from one displayed Series; search/URL entry opens one Work. */
export async function openSelectedWorks(state, workIds, context) {
  if (workIds.length === 1) {
    await openWorkById(state, workIds[0], context);
    return;
  }

  setWorkSelectionPopupVisibility(state, false);
  const lookups = await Promise.all(workIds.map((workId) => context.loadWorkLookupRecord(workId)));
  const recordsById = new Map();
  const recordHashes = new Map();
  for (let index = 0; index < workIds.length; index += 1) {
    const workId = workIds[index];
    const lookup = lookups[index];
    const record = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
    if (!record) {
      throw new Error(`work source missing record for ${workId}`);
    }
    recordsById.set(workId, record);
    recordHashes.set(workId, normalizeText(lookup.record_hash));
  }
  context.setLoadedBulkWorks(workIds, recordsById, recordHashes);
}

export async function openWorkById(state, requestedWorkId, context) {
  const workId = singleWorkId(requestedWorkId);
  if (!workId) {
    renderWorkSearchMatches(state, []);
    return;
  }
  const searchRecord = state.workSearchById.get(workId);
  if (!searchRecord) {
    const matches = getWorkSearchMatches(state, requestedWorkId);
    if (matches.length) {
      renderWorkSearchMatches(state, matches);
    } else {
      renderWorkSearchMatches(state, [], `Unknown work id: ${workId}.`);
    }
    return;
  }

  state.searchNode.value = workId;
  setWorkSelectionPopupVisibility(state, false);
  const lookup = await context.loadWorkLookupRecord(workId);
  const record = lookup && lookup.work && typeof lookup.work === "object" ? lookup.work : null;
  if (!record) {
    throw new Error(`work source missing record for ${workId}`);
  }
  context.setLoadedWorkRecord(workId, record, {
    recordHash: normalizeText(lookup.record_hash)
  });
}

/** Bind Work lookup; the explicit × also releases an unsaved New Work draft. */
export function bindWorkSelectionControls(state, context) {
  const { clearButton } = mountSearchField(state.searchNode);
  state.workSearchClearButton = clearButton;
  clearButton.addEventListener("click", () => {
    if (state.mode !== "new" || state.searchNode.disabled) return;
    context.setEmptySearchMode();
  });
  const searchController = bindSearchList(state.searchNode, state.popupListNode, {
    id: "catalogueWorkSearchList",
    maxOptions: SEARCH_LIMIT,
    shouldOpen: ({ value }) => state.mode !== "new" && normalizeText(value),
    loadOptions: () => workSearchOptions(state),
    filterOptions: (options, rawQuery) => {
      const query = normalizeText(rawQuery);
      if (!query) return [];
      const hasLetters = /[a-z]/i.test(query);
      const matches = options.filter(({ workId, record }) => (
        hasLetters ? titleMatches(record, query) : workIdPrefixMatches(workId, query)
      ));
      return matches.sort((a, b) => a.workId.localeCompare(b.workId, undefined, { numeric: true, sensitivity: "base" }));
    },
    getOptionValue: (option) => option.workId,
    renderOption: ({ workId, record }) => `
      <span class="catalogueWorkSearch__id">${escapeHtml(workId)}</span>
      <span class="catalogueWorkSearch__title">${escapeHtml(record.title)}</span>
    `,
    renderNoResults: () => '<p class="sharedSearchList__empty">No matching work ids.</p>',
    classNames: {
      option: "catalogueWorkSearch__option"
    },
    onTransientInput: ({ value }) => {
      if (state.mode !== "new") return;
      state.draft.work_id = normalizeWorkId(value);
      context.updateEditorState();
    },
    onCommit: (option) => openWorkById(state, option.workId, context)
  });
  state.workSearchController = searchController;

  state.searchNode.addEventListener("keydown", (event) => {
    if (event.defaultPrevented) return;
    if (event.key !== "Enter") return;
    event.preventDefault();
    if (state.mode === "new") {
      context.saveCurrentWork().catch((error) => {
        console.warn("catalogue_work_editor: unexpected create failure", error);
      });
      return;
    }
    openWorkById(state, state.searchNode.value, context).catch((error) => {
      console.warn("catalogue_work_editor: failed to open requested work", error);
    });
  });

  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-work-id]") : null;
    if (!button) return;
    openWorkById(state, button.getAttribute("data-work-id"), context).catch((error) => {
      console.warn("catalogue_work_editor: failed to open selected work", error);
    });
  });

  document.addEventListener("click", (event) => {
    if (event.target === state.searchNode || state.popupNode.contains(event.target) || state.popupListNode.contains(event.target)) return;
    setWorkSelectionPopupVisibility(state, false);
  });
}

/** Apply Work, new-Work or Series-only entry using the already loaded editor lookups. */
export async function applyInitialWorkRouteSelection(state, context) {
  const params = new URLSearchParams(window.location.search);
  const requestedMode = normalizeText(params.get("mode")).toLowerCase();
  const requestedWorkValue = normalizeText(params.get("work"));
  const requestedSeriesRaw = normalizeText(params.get("series"));
  const requestedSeriesId = normalizeSeriesId(requestedSeriesRaw);
  if (requestedWorkValue) {
    try {
      await openWorkById(state, requestedWorkValue, context);
    } catch (error) {
      console.warn("catalogue_work_editor: failed to open requested work", error);
      context.setEmptySearchMode({ keepSearchValue: true });
      context.setTextWithState(
        state.statusNode,
        `Failed to load the requested work. ${normalizeText(error && error.message)}`.trim(),
        "error"
      );
    }
  } else {
    const hasSeriesParam = Boolean(requestedSeriesRaw);
    const seriesIsValid = Boolean(requestedSeriesId && state.seriesById.has(requestedSeriesId));
    if (requestedMode === "new") {
      context.setNewWorkMode({ seriesId: seriesIsValid ? requestedSeriesId : "" });
    } else {
      context.setEmptySearchMode();
      if (seriesIsValid) context.selectSeries(requestedSeriesId);
    }
    if (hasSeriesParam && !seriesIsValid) {
      context.setTextWithState(
        state.statusNode,
        requestedSeriesId
          ? `Unknown series id: ${requestedSeriesId}.`
          : "Invalid series id.",
        "error"
      );
    }
  }
}
