import { computeRecordHash } from "./catalogue-editor-records.js";
import {
  normalizeDetailId,
  normalizeDetailUid,
  normalizeText,
  normalizeWorkId
} from "./catalogue-work-detail-fields.js";

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
  const section = normalizeText(record && record.section_title);
  if (title && section) return `${title} · ${section}`;
  return title || section || "—";
}

export function parseWorkDetailSelection(rawValue) {
  const rawText = normalizeText(rawValue);
  if (!rawText) return [];
  const tokens = rawText.split(",").map((item) => normalizeText(item)).filter(Boolean);
  const detailUids = [];
  const seen = new Set();
  tokens.forEach((token) => {
    const rangeMatch = token.match(/^(\d{5})-(\d{3})-(\d{3})$/);
    if (rangeMatch) {
      const workId = normalizeWorkId(rangeMatch[1]);
      const start = Number(rangeMatch[2]);
      const end = Number(rangeMatch[3]);
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) {
        throw new Error(`Invalid detail range: ${token}`);
      }
      for (let value = start; value <= end; value += 1) {
        const detailUid = `${workId}-${String(value).padStart(3, "0")}`;
        if (seen.has(detailUid)) continue;
        seen.add(detailUid);
        detailUids.push(detailUid);
      }
      return;
    }
    const detailUid = normalizeDetailUid(token);
    if (!detailUid) {
      throw new Error(`Invalid detail id: ${token}`);
    }
    if (seen.has(detailUid)) return;
    seen.add(detailUid);
    detailUids.push(detailUid);
  });
  return detailUids;
}

export function isWorkDetailBulkQuery(rawValue) {
  try {
    return parseWorkDetailSelection(rawValue).length > 1;
  } catch (_error) {
    return false;
  }
}

export function setWorkDetailSelectionPopupVisibility(state, visible) {
  state.popupNode.hidden = !visible;
}

export function getWorkDetailSearchMatches(state, rawQuery) {
  const query = normalizeText(rawQuery).toLowerCase();
  const normalizedUid = normalizeDetailUid(rawQuery);
  const normalizedDetailId = normalizeDetailId(rawQuery);
  if (!query && !normalizedUid && !normalizedDetailId) return [];
  const matches = [];
  for (const [detailUid, record] of state.detailSearchByUid.entries()) {
    const detailId = normalizeText(record && record.detail_id);
    const title = normalizeText(record && record.title).toLowerCase();
    if (
      (normalizedUid && detailUid.startsWith(normalizedUid)) ||
      (normalizedDetailId && detailId.startsWith(normalizedDetailId)) ||
      detailUid.toLowerCase().startsWith(query) ||
      title.includes(query)
    ) {
      matches.push({ detailUid, record });
    }
  }
  matches.sort((a, b) => a.detailUid.localeCompare(b.detailUid, undefined, { numeric: true, sensitivity: "base" }));
  return matches.slice(0, SEARCH_LIMIT);
}

export function renderWorkDetailSearchMatches(state, matches, message = "") {
  if (!matches.length && !message) {
    state.popupListNode.innerHTML = "";
    setWorkDetailSelectionPopupVisibility(state, false);
    return;
  }

  if (!matches.length) {
    state.popupListNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(message)}</p>`;
    setWorkDetailSelectionPopupVisibility(state, true);
    return;
  }

  const rows = matches.map(({ detailUid, record }) => `
    <button type="button" class="tagStudioSuggest__workButton" data-detail-uid="${escapeHtml(detailUid)}">
      <span class="tagStudioSuggest__workId">${escapeHtml(detailUid)}</span>
      <span class="tagStudioSuggest__workTitle">${escapeHtml(buildRecordSummary(record))}</span>
    </button>
  `);
  state.popupListNode.innerHTML = `<div class="tagStudioSuggest__workRows">${rows.join("")}</div>`;
  setWorkDetailSelectionPopupVisibility(state, true);
}

export function renderWorkDetailSearchSuggestions(state, context, rawQuery) {
  if (!normalizeText(rawQuery)) {
    renderWorkDetailSearchMatches(state, [], "");
    return;
  }
  if (isWorkDetailBulkQuery(rawQuery)) {
    renderWorkDetailSearchMatches(state, [], "");
    return;
  }
  const matches = getWorkDetailSearchMatches(state, rawQuery);
  if (!matches.length) {
    renderWorkDetailSearchMatches(state, [], text(context, "search_no_match", "No matching detail ids."));
    return;
  }
  renderWorkDetailSearchMatches(state, matches);
}

export async function openWorkDetailSelection(state, requestedValue, context) {
  let detailUids;
  try {
    detailUids = parseWorkDetailSelection(requestedValue);
  } catch (error) {
    renderWorkDetailSearchMatches(state, [], normalizeText(error && error.message) || text(context, "search_empty", "Enter a detail id."));
    return;
  }

  if (!detailUids.length) {
    renderWorkDetailSearchMatches(state, [], text(context, "search_empty", "Enter a detail id."));
    return;
  }
  if (detailUids.length === 1) {
    await openWorkDetailByUid(state, detailUids[0], context);
    return;
  }

  const unknown = detailUids.find((detailUid) => !state.detailSearchByUid.has(detailUid));
  if (unknown) {
    renderWorkDetailSearchMatches(state, [], text(context, "unknown_detail_error", "Unknown detail id: {detail_uid}.", { detail_uid: unknown }));
    return;
  }

  state.searchNode.value = detailUids.join(", ");
  setWorkDetailSelectionPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookups = await Promise.all(detailUids.map((detailUid) => context.loadDetailLookupRecord(detailUid)));
  const recordsById = new Map();
  const recordHashes = new Map();
  for (let index = 0; index < detailUids.length; index += 1) {
    const detailUid = detailUids[index];
    const lookup = lookups[index];
    const record = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : null;
    if (!record) {
      throw new Error(`detail lookup missing record for ${detailUid}`);
    }
    recordsById.set(detailUid, record);
    recordHashes.set(detailUid, normalizeText(lookup.record_hash) || await computeRecordHash(record));
  }
  context.setLoadedBulkDetails(detailUids, recordsById, recordHashes);
}

export async function openWorkDetailByUid(state, requestedDetailUid, context) {
  const detailUid = normalizeDetailUid(requestedDetailUid);
  if (!detailUid) {
    renderWorkDetailSearchMatches(state, [], text(context, "search_empty", "Enter a detail id."));
    return;
  }

  const searchRecord = state.detailSearchByUid.get(detailUid);
  if (!searchRecord) {
    const matches = getWorkDetailSearchMatches(state, requestedDetailUid);
    if (matches.length) renderWorkDetailSearchMatches(state, matches);
    else renderWorkDetailSearchMatches(state, [], text(context, "unknown_detail_error", "Unknown detail id: {detail_uid}.", { detail_uid: detailUid }));
    return;
  }

  state.searchNode.value = detailUid;
  setWorkDetailSelectionPopupVisibility(state, false);
  state.rebuildPending = false;
  const lookup = await context.loadDetailLookupRecord(detailUid);
  const record = lookup && lookup.work_detail && typeof lookup.work_detail === "object" ? lookup.work_detail : null;
  if (!record) {
    throw new Error(`detail lookup missing record for ${detailUid}`);
  }
  context.setLoadedRecord(detailUid, record, {
    recordHash: normalizeText(lookup.record_hash) || await computeRecordHash(record),
    lookup
  });
}

export function bindWorkDetailSelectionControls(state, context) {
  state.searchNode.addEventListener("input", () => {
    renderWorkDetailSearchSuggestions(state, context, state.searchNode.value);
  });

  state.searchNode.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    openWorkDetailSelection(state, state.searchNode.value, context).catch((error) => {
      console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
    });
  });

  state.popupListNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-detail-uid]") : null;
    if (!button) return;
    openWorkDetailByUid(state, button.getAttribute("data-detail-uid"), context).catch((error) => {
      console.warn("catalogue_work_detail_editor: failed to open selected detail", error);
    });
  });

  state.openButton.addEventListener("click", () => {
    openWorkDetailSelection(state, state.searchNode.value, context).catch((error) => {
      console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
    });
  });

  document.addEventListener("click", (event) => {
    if (event.target === state.searchNode || state.popupNode.contains(event.target)) return;
    setWorkDetailSelectionPopupVisibility(state, false);
  });
}

export async function applyInitialWorkDetailRouteSelection(state, context) {
  const params = new URLSearchParams(window.location.search);
  const requestedMode = normalizeText(params.get("mode")).toLowerCase();
  const requestedWorkValue = normalizeText(params.get("work"));
  const requestedDetailValue = normalizeText(params.get("detail"));
  if (requestedMode === "new") {
    context.setNewDetailMode(requestedWorkValue);
  } else if (requestedDetailValue) {
    await openWorkDetailSelection(state, requestedDetailValue, context).catch((error) => {
      console.warn("catalogue_work_detail_editor: failed to open requested detail selection", error);
      context.setTextWithState(
        state.statusNode,
        `${text(context, "load_requested_detail_failed", "Failed to load the requested detail.")} ${normalizeText(error && error.message)}`.trim(),
        "error"
      );
    });
  } else {
    context.setTextWithState(state.contextNode, text(context, "missing_detail_param", "Search for a work detail by detail id."));
    context.updateEditorState();
  }
}
