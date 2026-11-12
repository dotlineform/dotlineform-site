import { createRecordList } from "/shared/frontend/js/record-list.js";
import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { bindSearchList } from "/shared/frontend/js/search-list.js";
import { openAddGalleryWorksModal } from "./catalogue-add-gallery-works-modal.js";
import { confirmCatalogueActionModal } from "./catalogue-editor-action-modals.js";
import { buildWorkThumbPreview } from "./catalogue-media-preview.js";
import { syncWorkSeriesUrl, workBulkEditingPaused } from "./catalogue-work-route-state.js";

const browseCollator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getBrowseMatches(seriesById, galleriesById, rawQuery) {
  const query = rawQuery.trim().toLowerCase();
  if (!query) return [];
  const matches = [];
  for (const [kind, definitions] of [["series", seriesById], ["gallery", galleriesById]]) {
    for (const [id, { title }] of definitions) {
      if (id.includes(query) || title.toLowerCase().includes(query)) matches.push({ kind, id, title });
    }
  }
  return matches.sort((a, b) => browseCollator.compare(a.id, b.id));
}

/** Browse saved Series and Gallery members using the route's loaded projections.
 * Browsing and Series creation preserve the current Work draft and assignment.
 */
export function createWorkSeriesBrowser(state, elements, options) {
  const { seriesBrowseSearch: search, seriesBrowsePopup: popup, seriesBrowseMembers: members,
    seriesBrowseStatus: status, seriesBrowseCount: count, seriesBrowseEdit: edit,
    browseNew: newButton, galleryAddWorks: addWorksButton, editorPane, summaryPanelNode } = elements;
  let browseTarget = null;
  let list = null;
  let visibleIds = new Set();
  let renderedMembersKey = "";
  let opening = false;
  let definitionOpen = false;
  let addingWorks = false;
  let currentRecord = null;
  let bulkRecords = null;
  let currentWorkId = "";
  let mode = "";

  function getSelectedSeriesId() {
    return browseTarget?.kind === "series" ? browseTarget.id : "";
  }

  function setBrowseTarget(target) {
    if (browseTarget?.kind === target?.kind && browseTarget?.id === target?.id) return;
    browseTarget = target;
    syncWorkSeriesUrl(getSelectedSeriesId());
    const kind = browseTarget?.kind ?? "series";
    if (state.browseKind !== kind) {
      state.browseKind = kind;
      options.onBrowseKindChange();
    }
  }

  function busy() {
    return opening || definitionOpen || addingWorks || state.isEditingDefinition || state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
  }

  function browsedDefinition() {
    if (!browseTarget) return null;
    const definitions = browseTarget.kind === "gallery" ? state.galleriesById : state.seriesById;
    return definitions.get(browseTarget.id);
  }

  function showGallerySearchIcon(show) {
    searchField.classList.toggle("catalogueWorkBrowseSearch--gallery", show);
    if (show) search.setAttribute("aria-description", "Showing Gallery members");
    else search.removeAttribute("aria-description");
  }

  function restoreSearch() {
    const definition = browsedDefinition();
    search.value = definition?.title ?? "";
    showGallerySearchIcon(browseTarget?.kind === "gallery" && Boolean(definition));
    searchController.close();
  }

  function syncAvailability() {
    const unavailable = busy();
    const browsingGallery = browseTarget?.kind === "gallery";
    search.disabled = unavailable;
    edit.disabled = unavailable || !getSelectedSeriesId();
    newButton.disabled = unavailable;
    addWorksButton.hidden = !browsingGallery;
    addWorksButton.disabled = unavailable || !browsingGallery;
    members.inert = unavailable;
    members.setAttribute("aria-busy", String(opening));
    editorPane.inert = opening || definitionOpen || addingWorks || state.isEditingDefinition;
    summaryPanelNode.inert = editorPane.inert;
    if (unavailable) restoreSearch();
  }

  function renderMembers() {
    const browsingGallery = browseTarget?.kind === "gallery";
    const memberWorks = browseTarget ? Array.from(state.workSearchById.values()).filter(record => browsingGallery
      ? record.gallery_ids.includes(browseTarget.id)
      : record.series_id === browseTarget.id) : [];
    const records = memberWorks
      .sort((a, b) => browseCollator.compare(a.title, b.title))
      .map(record => {
        const preview = buildWorkThumbPreview(state.mediaConfig, record.work_id, {
          mediaVersion: record.media_version, imageStaged: record.image_staged
        });
        return {
          workId: record.work_id, title: record.title,
          titleTooltip: `${record.title}\nYear: ${record.year}\nYear display: ${record.year_display}`,
          association: browsingGallery ? state.seriesById.get(record.series_id).title
            : record.gallery_ids.map(id => state.galleriesById.get(id).title).join(", "),
          thumbSrc: preview.src, thumbSrcset: preview.srcset, thumbSizes: "48px",
          thumbWidth: 48, thumbHeight: 48, thumbAlt: "", thumbFallback: "No preview"
        };
      });
    const membersKey = JSON.stringify([browseTarget, records.map(({ association: _association, ...record }) => record)]);
    if (list && membersKey === renderedMembersKey) {
      const updates = records.filter((record, index) => record.association !== list.options.records[index].association)
        .map(record => ({ id: record.workId, values: { association: record.association } }));
      if (updates.length) list.updateCells(updates);
      list.setSelection(visibleSelection());
      return;
    }
    const scrollTop = members.scrollTop;
    list?.destroy();
    visibleIds = new Set(records.map(record => record.workId));
    count.textContent = browseTarget ? `${records.length} ${records.length === 1 ? "work" : "works"}` : "";
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
        { key: "title", label: "title", formatText: value => value, tooltipKey: "titleTooltip", width: "minmax(0, 1fr)", truncate: true },
        { key: "association", label: browsingGallery ? "series" : "galleries", formatText: value => value, width: "minmax(0, 1fr)", truncate: false }
      ],
      showHeader: false,
      emptyText: browseTarget ? `No works currently belong to this ${browseTarget.kind}.` : "Find a series or gallery to see its works.",
      selectionMode: "multiple",
      initialSelection: visibleSelection(),
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

  function visibleSelection() {
    return workBulkEditingPaused(state) ? [] : selectedWorkIds().filter(id => visibleIds.has(id));
  }

  async function openMembers(workIds) {
    if (busy() || (!workBulkEditingPaused(state)
      && workIds.slice().sort().join(",") === selectedWorkIds().slice().sort().join(","))) return;
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
      list.setSelection(visibleSelection());
      syncAvailability();
      const selectedRow = members.querySelector('[data-record-list-row="true"][tabindex="0"]');
      (selectedRow || search).focus({ preventScroll: true });
    }
  }

  function selectTarget(kind, id) {
    if (busy()) return;
    setBrowseTarget({ kind, id });
    status.textContent = "";
    delete status.dataset.state;
    restoreSearch();
    syncAvailability();
    renderMembers();
    members.scrollTop = 0;
  }

  async function changeDefinition(create = false) {
    const seriesId = getSelectedSeriesId();
    if (busy() || (!create && !seriesId)) return;
    definitionOpen = true;
    syncAvailability();
    try {
      const result = create
        ? await options.onCreateDefinition(browseTarget?.kind === "gallery" ? "Gallery" : "Series", newButton)
        : await options.onEditDefinition("Series", seriesId, edit);
      if (!result?.confirmed) return;
      if (result.response.created) {
        setBrowseTarget(result.kind === "Gallery"
          ? { kind: "gallery", id: result.response.gallery_id }
          : { kind: "series", id: result.response.series_id });
      } else if (result.response.deleted) setBrowseTarget(null);
      status.textContent = "";
      delete status.dataset.state;
      restoreSearch();
      renderMembers();
      if (result.response.created) members.scrollTop = 0;
    } catch (error) {
      status.textContent = error.message;
      status.dataset.state = "error";
    } finally {
      definitionOpen = false;
      syncAvailability();
      (create ? newButton : edit.disabled ? search : edit).focus({ preventScroll: true });
    }
  }

  async function addGalleryWorks() {
    if (busy() || browseTarget?.kind !== "gallery") return;
    if (options.draftHasChanges()) {
      status.textContent = "Save or discard the unsaved Work changes before adding Works.";
      status.dataset.state = "warn";
      return;
    }
    const { id: galleryId } = browseTarget;
    const { title: galleryTitle } = browsedDefinition();
    status.textContent = "";
    delete status.dataset.state;
    addingWorks = true;
    syncAvailability();
    try {
      const result = await openAddGalleryWorksModal(state, {
        galleryId, galleryTitle, restoreFocus: addWorksButton, save: options.addWorksToGallery
      });
      if (result.confirmed) {
        status.textContent = result.message;
        status.dataset.state = result.tone;
      }
    } catch (error) {
      status.textContent = `Could not open Add works. ${error.message}`;
      status.dataset.state = "error";
    } finally {
      addingWorks = false;
      syncAvailability();
      addWorksButton.focus({ preventScroll: true });
    }
  }

  const { root: searchField } = mountSearchField(search);
  const searchController = bindSearchList(search, popup, {
    id: "catalogueWorkSeriesBrowseList",
    openOnFocus: false,
    shouldOpen: () => !busy(),
    loadOptions: query => getBrowseMatches(state.seriesById, state.galleriesById, query),
    filterOptions: records => records,
    getOptionValue: option => option.title,
    renderOption: ({ kind, title }) => `
      <span class="catalogueWorkBrowseSearch__result">
        ${kind === "gallery" ? `
          <span class="studioUi__icon studioUi__icon--small studioUi__icon--images" aria-hidden="true"></span>
          <span class="visually-hidden">Gallery</span>
        ` : ""}
        <span class="catalogueSeriesSearch__title">${escapeHtml(title)}</span>
      </span>
    `,
    onCommit: ({ kind, id }) => selectTarget(kind, id),
    onCancel: restoreSearch,
    onTransientInput: () => showGallerySearchIcon(false),
    noResultsText: "No matching series or galleries."
  });
  search.addEventListener("blur", restoreSearch);
  popup.addEventListener("mousedown", event => {
    if (event.button === 0 && event.target.closest("[data-search-list-index]")) event.preventDefault();
  });
  edit.addEventListener("click", () => { void changeDefinition(); });
  newButton.addEventListener("click", () => { void changeDefinition(true); });
  addWorksButton.addEventListener("click", () => { void addGalleryWorks(); });

  function sync({ recordsChanged = false } = {}) {
    syncAvailability();
    if (!recordsChanged && currentRecord === state.currentRecord && bulkRecords === state.bulkRecords
      && currentWorkId === state.currentWorkId && mode === state.mode) return;
    currentRecord = state.currentRecord;
    bulkRecords = state.bulkRecords;
    currentWorkId = state.currentWorkId;
    mode = state.mode;
    const initialSeriesId = currentRecord?.series_id || (mode === "new" ? state.draft.series_id
      : state.bulkRecords.values().next().value?.series_id);
    if (!browseTarget && initialSeriesId && state.seriesById.has(initialSeriesId)) {
      setBrowseTarget({ kind: "series", id: initialSeriesId });
      restoreSearch();
    }
    if (!opening) renderMembers();
    syncAvailability();
  }

  sync();
  return {
    sync,
    /** Select a known Series for browsing without opening a Work or changing its draft. */
    selectSeries: id => selectTarget("series", id),
    /** Return the displayed Series independently of the loaded Work or draft. */
    getSelectedSeriesId,
    refresh() {
      if (browseTarget && !browsedDefinition()) {
        setBrowseTarget(null);
        status.textContent = "";
        delete status.dataset.state;
      }
      restoreSearch();
      renderMembers();
      syncAvailability();
    },
    preserveScrollAnchor: change => list ? list.preserveScrollAnchor(change) : change()
  };
}
