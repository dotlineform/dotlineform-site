import { normalizeText } from "./catalogue-work-fields.js";

function disabled(state) {
  return state.isSaving || state.isBuilding || state.isDeleting || !state.serverAvailable;
}

function matches(state) {
  const query = state.galleryPicker.searchInput.value.trim().toLowerCase();
  if (!query) return [];
  const selected = new Set(state.draft.gallery_ids || []);
  return Array.from(state.galleriesById.entries())
    .filter(([id, record]) => !selected.has(id) && (id.includes(query) || record.title.toLowerCase().includes(query)))
    .sort(([idA, a], [idB, b]) => a.title.localeCompare(b.title, undefined, { numeric: true, sensitivity: "base" }) || idA.localeCompare(idB))
    .slice(0, 12);
}

function node(tag, className, text = "") {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

function renderMatches(state) {
  const picker = state.galleryPicker;
  picker.popupNode.replaceChildren();
  if (disabled(state)) {
    picker.popupNode.hidden = true;
    return;
  }
  for (const [id, record] of matches(state)) {
    const button = node("button", "studioSuggest__workButton catalogueWorkSeriesPicker__option");
    button.type = "button";
    button.dataset.galleryId = id;
    button.append(node("span", "studioSuggest__workTitle", record.title), node("span", "studioSuggest__workMeta", id));
    picker.popupNode.append(button);
  }
  picker.popupNode.hidden = !picker.popupNode.childElementCount;
}

/** Render exact canonical Gallery selections; titles are lookup labels only. */
export function renderWorkGalleryPicker(state) {
  const picker = state.galleryPicker;
  if (!picker) return;
  picker.chipsNode.replaceChildren();
  const ids = state.draft.gallery_ids || [];
  for (const id of ids) {
    const title = state.galleriesById.get(id)?.title || id;
    const chip = node("span", "studioUi__chip catalogueWorkSeriesPicker__chip");
    const remove = node("button", "studioUi__chipRemove", "×");
    remove.type = "button";
    remove.dataset.removeGalleryId = id;
    remove.setAttribute("aria-label", `Remove ${title} (${id})`);
    chip.append(node("span", "studioUi__chipText", title), node("span", "catalogueWorkSeriesPicker__chipId", id), remove);
    picker.chipsNode.append(chip);
  }
  if (!ids.length) picker.chipsNode.append(node("span", "studioForm__meta", "No galleries selected."));
  picker.searchInput.value = "";
  picker.popupNode.hidden = true;
  setWorkGalleryPickerAvailability(state);
}

/** Share the Work busy state in single, new and bulk editing. */
export function setWorkGalleryPickerAvailability(state) {
  const picker = state.galleryPicker;
  if (!picker) return;
  const busy = disabled(state);
  picker.searchInput.disabled = busy;
  picker.wrapper.querySelectorAll("button").forEach(button => { button.disabled = busy; });
  if (busy) picker.popupNode.hidden = true;
}

/** Mount the Work-owned multiple Gallery picker using the existing Series picker styles. */
export function createWorkGalleryPicker(field, fieldsNode, state, options) {
  const wrapper = node("div", "studioForm__field catalogueWorkForm__field catalogueWorkForm__field--topAligned");
  const label = node("label", "studioForm__label", field.label);
  label.htmlFor = "catalogueWorkGallerySearch";
  const control = node("div", "catalogueWorkSeriesPicker__control");
  const chipsNode = node("div", "catalogueWorkSeriesPicker__chips");
  const searchWrap = node("div", "catalogueWorkSeriesPicker__searchWrap");
  const searchInput = node("input", "studioUi__input catalogueWorkSeriesPicker__search");
  searchInput.id = label.htmlFor;
  searchInput.type = "text";
  searchInput.autocomplete = "off";
  searchInput.placeholder = "find galleries by title or id";
  const popupNode = node("div", "studioUi__popupInner catalogueWorkSeriesPicker__popup");
  popupNode.hidden = true;
  searchWrap.append(searchInput, popupNode);
  control.append(chipsNode, searchWrap);
  wrapper.append(label, control);
  fieldsNode.append(wrapper);
  state.galleryPicker = { wrapper, chipsNode, searchInput, popupNode };

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

  searchInput.addEventListener("input", () => renderMatches(state));
  searchInput.addEventListener("focus", () => renderMatches(state));
  searchInput.addEventListener("keydown", event => {
    if (event.key === "Escape") popupNode.hidden = true;
    if (event.key !== "Enter" || disabled(state)) return;
    event.preventDefault();
    const first = matches(state)[0];
    if (first) add(first[0]);
  });
  popupNode.addEventListener("mousedown", event => {
    // Keep input focus until click selects the result; WebKit can blur without focusing the button.
    if (event.button === 0 && event.target.closest("[data-gallery-id]")) event.preventDefault();
  });
  popupNode.addEventListener("click", event => {
    const button = event.target.closest("[data-gallery-id]");
    if (!button || disabled(state)) return;
    add(normalizeText(button.dataset.galleryId));
    searchInput.focus();
  });
  chipsNode.addEventListener("click", event => {
    const button = event.target.closest("[data-remove-gallery-id]");
    if (!button || disabled(state)) return;
    changeSelection(state.draft.gallery_ids.filter(id => id !== button.dataset.removeGalleryId));
    searchInput.focus();
  });
  wrapper.addEventListener("focusout", event => {
    if (!wrapper.contains(event.relatedTarget)) popupNode.hidden = true;
  });
  renderWorkGalleryPicker(state);
}
