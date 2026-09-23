import { createRecordList } from "/shared/frontend/js/record-list.js";
import { bindSearchList } from "/shared/frontend/js/search-list.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import { buildWorkThumbPreview } from "./catalogue-media-preview.js";
import { getSeriesSearchMatches } from "./catalogue-series-selection.js";
import { catalogueOutputError, catalogueSavedActionError } from "./catalogue-output-result.js";
import { openWorkSeriesTitleModal } from "./catalogue-work-series-modal.js";
import { deleteEmptyWorkSeries } from "./catalogue-work-series-actions.js";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Browse saved Series membership without changing the Work's editable assignment.
 * Uses the route's canonical search projections; only opening a Work reads its full record.
 */
export function createWorkSeriesBrowser(state, elements, options) {
  const { seriesBrowseSearch: search, seriesBrowsePopup: popup, seriesBrowseMembers: members,
    seriesBrowseStatus: status, seriesBrowseCount: count, seriesBrowseEdit: edit,
    seriesBrowseDelete: remove, editorPane } = elements;
  let seriesId = "";
  let list = null;
  let renderedMembersKey = "";
  let opening = false;
  let editingSeries = false;
  let deletingSeries = false;
  let currentRecord = null;
  let bulkRecords = null;
  let currentWorkId = "";
  let mode = "";

  function busy() {
    return opening || editingSeries || deletingSeries || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  }

  function canDeleteSeries() {
    return Boolean(seriesId && state.seriesById.has(seriesId))
      && !Array.from(state.workSearchById.values()).some(record => record.series_id === seriesId);
  }

  function seriesLabel(id) {
    const record = state.seriesById.get(id);
    return record ? `${record.title} (${id})` : "";
  }

  function restoreSearch() {
    search.value = seriesLabel(seriesId);
    searchController.close();
  }

  function syncAvailability() {
    search.disabled = busy();
    edit.disabled = busy();
    remove.disabled = busy() || !canDeleteSeries();
    members.inert = busy();
    members.setAttribute("aria-busy", String(opening));
    editorPane.inert = opening || editingSeries || deletingSeries;
    if (busy()) restoreSearch();
  }

  function renderMembers() {
    const records = Array.from(state.workSearchById.values())
      .filter(record => seriesId && record.series_id === seriesId)
      .sort((a, b) => a.work_id.localeCompare(b.work_id))
      .map(record => {
        const preview = buildWorkThumbPreview(state.mediaConfig, record.work_id);
        return {
          workId: record.work_id, title: record.title || "—",
          thumbSrc: preview.src, thumbSrcset: preview.srcset, thumbSizes: "48px",
          thumbWidth: 48, thumbHeight: 48, thumbAlt: "", thumbFallback: "No preview"
        };
      });
    const selectedId = state.mode === "single" && records.some(record => record.workId === state.currentWorkId)
      ? state.currentWorkId : "";
    const membersKey = JSON.stringify([seriesId, records]);
    // Opening a row should preserve its mounted thumbnails and the list's scroll position.
    if (list && membersKey === renderedMembersKey && (list.selection()?.id || "") === selectedId) return;
    const scrollTop = members.scrollTop;
    list?.destroy();
    count.textContent = seriesId ? `${records.length} ${records.length === 1 ? "work" : "works"}` : "";
    list = createRecordList(members, {
      id: "catalogueWorkSeriesMembers",
      records,
      columns: [
        {
          key: "thumbSrc", label: "thumbnail", width: "48px", type: "image",
          srcKey: "thumbSrc", srcsetKey: "thumbSrcset", sizesKey: "thumbSizes",
          widthKey: "thumbWidth", heightKey: "thumbHeight", altKey: "thumbAlt",
          fallbackTextKey: "thumbFallback", truncate: false
        },
        { key: "workId", label: "work", width: "minmax(3.5rem, 4.9rem)", truncate: false },
        { key: "title", label: "title", width: "minmax(0, 1fr)", truncate: true }
      ],
      showHeader: false,
      emptyText: seriesId ? "No works currently belong to this series." : "Find a series to see its works.",
      selectionMode: "single",
      initialSelection: selectedId,
      getRecordId: record => record.workId,
      onSelectionChange: ({ selection }) => {
        if (selection?.record) void openMember(selection.record.workId);
      }
    });
    renderedMembersKey = membersKey;
    members.scrollTop = scrollTop;
  }

  async function openMember(workId) {
    if (busy() || (state.mode === "single" && state.currentWorkId === workId)) return;
    const previousSearch = state.searchNode.value;
    opening = true;
    syncAvailability();
    try {
      if (options.draftHasChanges()) {
        const confirmed = await confirmCatalogueActionModal(state, {
          title: "Discard unsaved Work changes?",
          message: `Open Work ${workId} and discard the current unsaved changes?`,
          primaryLabel: "Discard and open", cancelLabel: "Cancel", defaultAction: "cancel",
          restoreFocus: search
        });
        if (!confirmed) return;
      }
      status.textContent = "";
      delete status.dataset.state;
      await options.openWork(workId);
    } catch (error) {
      state.searchNode.value = previousSearch;
      status.textContent = `Could not open Work ${workId}. ${error.message}`;
      status.dataset.state = "error";
    } finally {
      opening = false;
      renderMembers();
      syncAvailability();
      const selectedRow = members.querySelector('[data-record-list-row="true"][aria-selected="true"]');
      (selectedRow || search).focus({ preventScroll: true });
    }
  }

  function selectSeries(id) {
    if (busy() || !state.seriesById.has(id)) return;
    seriesId = id;
    status.textContent = "";
    delete status.dataset.state;
    restoreSearch();
    renderMembers();
    members.scrollTop = 0;
    syncAvailability();
  }

  async function editSeries() {
    if (busy()) return;
    editingSeries = true;
    syncAvailability();
    try {
      const result = await openWorkSeriesTitleModal(state, { seriesId, restoreFocus: edit });
      if (!result.confirmed) return;
      const { response } = result;
      state.seriesById.set(result.seriesId, { ...response.record, record_hash: response.record_hash });
      const changedSeries = seriesId !== result.seriesId;
      seriesId = result.seriesId;
      restoreSearch();
      renderMembers();
      if (changedSeries) members.scrollTop = 0;
      options.onSeriesChanged();
      status.textContent = catalogueOutputError(response);
      if (status.textContent) status.dataset.state = "error";
      else delete status.dataset.state;
    } catch (error) {
      status.textContent = error.message;
      status.dataset.state = "error";
    } finally {
      editingSeries = false;
      syncAvailability();
      edit.focus({ preventScroll: true });
    }
  }

  async function deleteSeries() {
    if (busy() || !canDeleteSeries()) return;
    deletingSeries = true;
    syncAvailability();
    let response = null;
    try {
      response = await deleteEmptyWorkSeries(state, { seriesId, restoreFocus: remove });
      if (!response) return;
      if (!response.deleted || response.kind !== "series" || response.id !== seriesId) {
        throw new Error("Delete response does not match the selected Series.");
      }
      state.seriesById.delete(seriesId);
      seriesId = "";
      restoreSearch();
      renderMembers();
      options.onSeriesChanged();
      status.textContent = catalogueOutputError(response);
      if (status.textContent) status.dataset.state = "error";
      else delete status.dataset.state;
    } catch (error) {
      status.textContent = catalogueSavedActionError(response, error) || error.message;
      status.dataset.state = "error";
    } finally {
      deletingSeries = false;
      syncAvailability();
      (remove.disabled ? search : remove).focus({ preventScroll: true });
    }
  }

  const searchController = bindSearchList(search, popup, {
    id: "catalogueWorkSeriesBrowseList",
    openOnFocus: false,
    shouldOpen: () => !busy(),
    loadOptions: query => getSeriesSearchMatches(state, query),
    filterOptions: records => records,
    getOptionValue: option => seriesLabel(option.seriesId),
    renderOption: ({ seriesId, record }) => `
      <span class="catalogueSeriesSearch__id">${escapeHtml(seriesId)}</span>
      <span class="catalogueSeriesSearch__title">${escapeHtml(record.title)}</span>
    `,
    classNames: { option: "catalogueSeriesSearch__option" },
    onCommit: option => selectSeries(option.seriesId),
    onCancel: restoreSearch,
    noResultsText: "No matching series."
  });
  search.addEventListener("blur", restoreSearch);
  popup.addEventListener("mousedown", event => {
    if (event.button === 0 && event.target.closest("[data-search-list-index]")) event.preventDefault();
  });
  edit.addEventListener("click", () => { void editSeries(); });
  remove.addEventListener("click", () => { void deleteSeries(); });

  function sync() {
    syncAvailability();
    if (currentRecord === state.currentRecord && bulkRecords === state.bulkRecords
      && currentWorkId === state.currentWorkId && mode === state.mode) return;
    currentRecord = state.currentRecord;
    bulkRecords = state.bulkRecords;
    currentWorkId = state.currentWorkId;
    mode = state.mode;
    const initialSeriesId = currentRecord?.series_id || (mode === "new" ? state.draft.series_id : "");
    if (!seriesId && initialSeriesId && state.seriesById.has(initialSeriesId)) {
      seriesId = initialSeriesId;
      restoreSearch();
    }
    if (!opening) renderMembers();
    syncAvailability();
  }

  sync();
  return { sync };
}
