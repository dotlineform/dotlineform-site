import { createRecordList } from "/shared/frontend/js/record-list.js";
import { bindSearchList } from "/shared/frontend/js/search-list.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import { buildWorkThumbPreview } from "./catalogue-media-preview.js";
import { getSeriesSearchMatches } from "./catalogue-series-records.js";
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
    seriesBrowseDelete: remove, editorPane, summaryPanelNode } = elements;
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
    summaryPanelNode.inert = editorPane.inert;
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
          galleries: record.gallery_ids.map(id => state.galleriesById.get(id)?.title || id).join(", "),
          thumbSrc: preview.src, thumbSrcset: preview.srcset, thumbSizes: "48px",
          thumbWidth: 48, thumbHeight: 48, thumbAlt: "", thumbFallback: "No preview"
        };
      });
    const visibleIds = new Set(records.map(record => record.workId));
    const selectedIds = selectedWorkIds().filter(id => visibleIds.has(id));
    const membersKey = JSON.stringify([seriesId, records.map(({ galleries: _galleries, ...record }) => record)]);
    if (list && membersKey === renderedMembersKey) {
      const updates = records.filter((record, index) => record.galleries !== list.options.records[index].galleries)
        .map(record => ({ id: record.workId, values: { galleries: record.galleries } }));
      if (updates.length) list.updateCells(updates);
      list.setSelection(selectedIds);
      return;
    }
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
        { key: "title", label: "title", width: "minmax(0, 1fr)", truncate: true },
        { key: "galleries", label: "galleries", width: "minmax(0, 1fr)", truncate: false }
      ],
      showHeader: false,
      emptyText: seriesId ? "No works currently belong to this series." : "Find a series to see its works.",
      selectionMode: "multiple",
      initialSelection: selectedIds,
      getRecordId: record => record.workId,
      onSelectionChange: ({ selections }) => {
        void openMembers(selections.map(selection => selection.id));
      }
    });
    renderedMembersKey = membersKey;
    members.scrollTop = scrollTop;
  }

  function selectedWorkIds() {
    return state.mode === "bulk" ? state.bulkWorkIds : state.currentWorkId ? [state.currentWorkId] : [];
  }

  async function openMembers(workIds) {
    if (busy() || workIds.slice().sort().join(",") === selectedWorkIds().slice().sort().join(",")) return;
    const previousSearch = state.searchNode.value;
    opening = true;
    syncAvailability();
    try {
      if (state.mode !== "bulk" && options.draftHasChanges()) {
        const confirmed = await confirmCatalogueActionModal(state, {
          title: "Discard unsaved Work changes?",
          message: "Change the Work selection and discard the current unsaved changes?",
          primaryLabel: "Discard and open", cancelLabel: "Cancel", defaultAction: "cancel",
          restoreFocus: search
        });
        if (!confirmed) return;
      }
      status.textContent = "";
      delete status.dataset.state;
      if (workIds.length) await options.openWorks(workIds);
      else options.clearWork();
    } catch (error) {
      state.searchNode.value = previousSearch;
      status.textContent = `Could not change the Work selection. ${error.message}`;
      status.dataset.state = "error";
    } finally {
      opening = false;
      renderMembers();
      syncAvailability();
      const selectedRow = members.querySelector('[data-record-list-row="true"][tabindex="0"]');
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
    loadOptions: query => getSeriesSearchMatches(state.seriesById, query),
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
    const bulkSeriesIds = new Set([...state.bulkRecords.values()].map(record => record.series_id));
    const initialSeriesId = currentRecord?.series_id || (mode === "new" ? state.draft.series_id
      : bulkSeriesIds.size === 1 ? [...bulkSeriesIds][0] : "");
    if (!seriesId && initialSeriesId && state.seriesById.has(initialSeriesId)) {
      seriesId = initialSeriesId;
      restoreSearch();
    }
    if (!opening) renderMembers();
    syncAvailability();
  }

  sync();
  return { sync, preserveScrollAnchor: change => list ? list.preserveScrollAnchor(change) : change() };
}
