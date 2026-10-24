import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { bindSearchList } from "/shared/frontend/js/search-list.js";
import { createStudioIcon } from "./studio-icon.js";

function disabled(state) {
  return state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
}

function matches(state) {
  const query = state.galleryPicker.searchInput.value.trim().toLowerCase();
  if (!query) return [];
  const selected = new Set(state.draft.gallery_ids || []);
  return Array.from(state.galleriesById.entries())
    .filter(([id, record]) => !selected.has(id) && (id.includes(query) || record.title.toLowerCase().includes(query)))
    .sort(([idA, a], [idB, b]) => a.title.localeCompare(b.title, undefined, { numeric: true, sensitivity: "base" }) || idA.localeCompare(idB));
}

function node(tag, className, text = "") {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

/** Render exact canonical Gallery selections; titles are lookup labels only. */
export function renderWorkGalleryPicker(state) {
  const picker = state.galleryPicker;
  if (!picker) return;
  picker.chipsNode.replaceChildren();
  const ids = state.draft.gallery_ids || [];
  for (const id of ids) {
    const title = state.galleriesById.get(id)?.title || "—";
    const chip = node("span", "studioUi__chip catalogueWorkSeriesPicker__chip");
    const edit = node("button", "catalogueWorkSeriesPicker__edit", title);
    edit.type = "button";
    edit.dataset.editGalleryId = id;
    edit.setAttribute("aria-label", `Edit Gallery ${title}`);
    const remove = node("button", "studioUi__chipRemove");
    remove.append(createStudioIcon(document, "x"));
    remove.type = "button";
    remove.dataset.removeGalleryId = id;
    remove.setAttribute("aria-label", `Remove ${title}`);
    remove.title = `Remove ${title}`;
    chip.append(edit, remove);
    picker.chipsNode.append(chip);
  }
  if (!ids.length) picker.chipsNode.append(node("span", "studioForm__meta", "No galleries selected."));
  picker.searchInput.value = "";
  picker.searchController.close();
  setWorkGalleryPickerAvailability(state);
}

/** Share the Work busy state in single, new and bulk editing. */
export function setWorkGalleryPickerAvailability(state) {
  const picker = state.galleryPicker;
  if (!picker) return;
  const busy = disabled(state);
  picker.searchInput.disabled = busy;
  picker.wrapper.querySelectorAll("button").forEach(button => { button.disabled = busy; });
  if (busy) picker.searchController.close();
}

/** Mount the Work-owned multiple Gallery picker using the existing Series picker styles. */
export function createWorkGalleryPicker(field, fieldsNode, state, options) {
  const wrapper = node("div", "studioForm__field catalogueWorkForm__field catalogueWorkForm__field--topAligned");
  const label = node("label", "studioForm__label", field.label);
  label.htmlFor = "catalogueWorkGallerySearch";
  const control = node("div", "catalogueWorkSeriesPicker__control");
  const chipsNode = node("div", "catalogueWorkSeriesPicker__chips");
  const searchWrap = node("div", "sharedSearchList__control");
  const searchInput = node("input", "studioUi__input catalogueWorkSeriesPicker__search");
  searchInput.id = label.htmlFor;
  searchInput.type = "text";
  searchInput.autocomplete = "off";
  searchInput.placeholder = "find galleries by title or id";
  const popupNode = node("div", "sharedSearchList__popup");
  popupNode.dataset.navigation = "pointer";
  popupNode.hidden = true;
  searchWrap.append(searchInput, popupNode);
  mountSearchField(searchInput);
  const searchRow = node("div", "catalogueWorkSeriesPicker__searchRow");
  const newButton = node("button", "studioUi__iconButton");
  newButton.append(createStudioIcon(document, "file"));
  newButton.title = "New Gallery";
  newButton.type = "button";
  newButton.setAttribute("aria-label", "New Gallery");
  newButton.addEventListener("click", () => {
    if (!disabled(state)) void options.onEditDefinition("Gallery", "", searchInput);
  });
  searchRow.append(searchWrap, newButton);
  control.append(chipsNode, searchRow);
  wrapper.append(label, control);
  fieldsNode.append(wrapper);
  state.galleryPicker = { wrapper, chipsNode, searchInput, popupNode, searchController: null };

  function changeSelection(ids) {
    if (disabled(state)) return;
    state.draft.gallery_ids = ids.slice().sort();
    if (state.mode === "bulk") state.bulkTouchedFields.add("gallery_ids");
    renderWorkGalleryPicker(state);
    options.onStateChange?.();
  }

  function add(id) {
    if (!state.galleriesById.has(id) || state.draft.gallery_ids.includes(id)) return;
    changeSelection([...state.draft.gallery_ids, id]);
  }

  const searchController = bindSearchList(searchInput, popupNode, {
    id: "catalogueWorkGallerySearchList",
    freeEntry: true,
    shouldOpen: () => !disabled(state) && searchInput.value.trim().length > 0,
    loadOptions: () => matches(state),
    filterOptions: items => items,
    getOptionValue: ([, record]) => record.title,
    renderOption: ([, record]) => node("span", "catalogueGallerySearch__title", record.title).outerHTML,
    noResultsText: "No matching galleries.",
    onCommit: ([id]) => {
      add(id);
      searchInput.focus();
    }
  });
  state.galleryPicker.searchController = searchController;
  searchInput.addEventListener("keydown", event => {
    // Preserve direct Enter selection; the shared list handles a navigated result.
    if (event.key !== "Enter" || event.defaultPrevented || disabled(state)) return;
    event.preventDefault();
    if (!searchInput.value.trim()) return;
    const first = searchController.matches[0];
    if (first) add(first[0]);
  });
  chipsNode.addEventListener("click", event => {
    const edit = event.target.closest("[data-edit-gallery-id]");
    if (edit && !disabled(state)) {
      void options.onEditDefinition("Gallery", edit.dataset.editGalleryId, searchInput);
      return;
    }
    const button = event.target.closest("[data-remove-gallery-id]");
    if (!button || disabled(state)) return;
    changeSelection(state.draft.gallery_ids.filter(id => id !== button.dataset.removeGalleryId));
    searchInput.focus();
  });
  renderWorkGalleryPicker(state);
}
