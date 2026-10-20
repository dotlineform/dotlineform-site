import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createStudioIcon } from "./studio-icon.js";
import { createWorkGalleryPicker, renderWorkGalleryPicker, setWorkGalleryPickerAvailability } from "./catalogue-work-gallery-picker.js";
import { bindSearchList } from "/shared/frontend/js/search-list.js";
import { renderWorkMediumField } from "./catalogue-work-medium.js";
import { BULK_WORK_METADATA_FIELDS, WORK_EDITABLE_FIELDS as EDITABLE_FIELDS, WORK_FIELD_DEFINITIONS, WORK_READONLY_FIELDS as READONLY_FIELDS, isWorkFieldRequired, normalizeSeriesId, normalizeText } from "./catalogue-work-fields.js";
import {
  openProjectMediaPickerForCurrentDraft,
  openProjectMediaFolderForCurrentDraft,
  resetProjectMediaFolders
} from "./catalogue-project-media-picker.js";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function notifyFieldInput(options, fieldKey) {
  if (options && typeof options.onFieldInput === "function") {
    options.onFieldInput(fieldKey);
  }
}

function notifyStateChange(options) {
  if (options && typeof options.onStateChange === "function") {
    options.onStateChange();
  }
}

function mediaSourceConfig(state) {
  const config = state.workMediaSourceConfig && typeof state.workMediaSourceConfig === "object"
    ? state.workMediaSourceConfig
    : {};
  const sourceIds = Array.isArray(config.mediaSourceIds)
    ? config.mediaSourceIds.map(normalizeText).filter(Boolean)
    : [];
  const defaultSourceId = normalizeText(config.defaultMediaSourceId);
  return { sourceIds, defaultSourceId };
}

export function resolvedWorkMediaSourceId(state) {
  const config = mediaSourceConfig(state);
  const sourceId = state.draft.media_source_id;
  return sourceId === undefined || sourceId === null || sourceId === "" ? config.defaultSourceId : sourceId;
}

function mediaSourceLabel(sourceId) {
  return `${sourceId.slice(0, 1).toUpperCase()}${sourceId.slice(1)}`;
}

function updateMediaSourceButton(state) {
  const button = state.mediaSourceButton;
  if (!button) return;
  const config = mediaSourceConfig(state);
  const currentSourceId = resolvedWorkMediaSourceId(state);
  const currentIndex = config.sourceIds.indexOf(currentSourceId);
  const nextSourceId = currentIndex >= 0 && config.sourceIds.length > 1
    ? config.sourceIds[(currentIndex + 1) % config.sourceIds.length]
    : "";
  const currentLabel = mediaSourceLabel(currentSourceId);
  const nextLabel = mediaSourceLabel(nextSourceId);
  button.textContent = currentLabel;
  button.dataset.mediaSourceId = currentSourceId;
  button.setAttribute(
    "aria-label",
    nextSourceId
      ? `Media source: ${currentLabel}. Select ${nextLabel}.`
      : `Media source: ${currentLabel}.`
  );
}

export function applyWorkMediaSourceConfig(state, payload) {
  const sourceIds = Array.isArray(payload && payload.media_source_ids)
    ? payload.media_source_ids.map(normalizeText).filter(Boolean)
    : [];
  const defaultSourceId = normalizeText(payload && payload.default_media_source_id);
  if (!defaultSourceId || sourceIds.length !== 2 || !sourceIds.includes(defaultSourceId)) {
    throw new Error("Work media source configuration is invalid.");
  }
  state.workMediaSourceConfig = {
    defaultMediaSourceId: defaultSourceId,
    mediaSourceIds: sourceIds
  };
  updateMediaSourceButton(state);
}

function seriesDisplayTitle(state, seriesId) {
  const record = state.seriesById.get(seriesId);
  return normalizeText(record && record.title) || "—";
}

function seriesSearchMatches(state, queryText) {
  const query = normalizeText(queryText).toLowerCase();
  if (!query) return [];
  return Array.from(state.seriesById.entries())
    .filter(([seriesId, record]) => {
      const title = normalizeText(record && record.title).toLowerCase();
      return seriesId.includes(query) || title.includes(query);
    })
    .sort((a, b) => {
      const titleA = normalizeText(a[1] && a[1].title);
      const titleB = normalizeText(b[1] && b[1].title);
      return titleA.localeCompare(titleB, undefined, { numeric: true, sensitivity: "base" });
    })
    .slice(0, 12);
}

function setSeriesDraftId(state, seriesId, options) {
  state.draft.series_id = normalizeSeriesId(seriesId);
  const node = state.fieldNodes.get("series_id");
  if (node) node.value = state.draft.series_id;
  renderSeriesPicker(state);
  notifyStateChange(options);
}

/** Refresh the selected Series label without applying or resetting the Work draft. */
export function renderSeriesPicker(state) {
  if (!state.seriesPicker) return;
  const seriesId = state.draft.series_id;
  state.seriesPicker.hiddenInput.value = seriesId;
  state.seriesPicker.searchInput.value = seriesId ? seriesDisplayTitle(state, seriesId) : "";
  state.seriesPicker.searchController.close();
}

function renderField(field, fieldsNode, state, options) {
  if (field.key === "medium") {
    renderWorkMediumField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "gallery_ids") {
    createWorkGalleryPicker(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "series_id") {
    renderSeriesField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "media_source_id") {
    renderMediaSourceField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "project_folder") {
    renderProjectMediaDisplayField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "project_subfolder") {
    renderProjectMediaDisplayField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "project_filename") {
    renderProjectMediaDisplayField(field, fieldsNode, state, options);
    return;
  }

  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "studioForm__field catalogueWorkForm__field";
  if (!field.readonly) wrapper.htmlFor = `catalogueWorkField-${field.key}`;

  const label = document.createElement("span");
  label.className = "studioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "studioUi__input studioUi__input--readonlyDisplay";
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "studioUi__input";
    field.options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "studioUi__input";
    input.type = field.type === "date" ? "date" : "text";
    if (field.type === "number") {
      input.inputMode = field.step && String(field.step).includes(".") ? "decimal" : "numeric";
    }
  }

  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  if (field.description) {
    input.setAttribute("aria-describedby", `catalogueWorkFieldHelp-${field.key}`);
  }
  wrapper.appendChild(input);

  if (field.description) {
    const help = document.createElement("span");
    help.className = "studioForm__meta catalogueWorkForm__fieldMeta";
    help.id = `catalogueWorkFieldHelp-${field.key}`;
    help.textContent = field.description;
    wrapper.appendChild(help);
  }

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  if (!field.readonly) {
    input.addEventListener("input", () => notifyFieldInput(options, field.key));
    input.addEventListener("change", () => notifyFieldInput(options, field.key));
  }
  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderMediaSourceField(field, fieldsNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "studioForm__field catalogueWorkForm__field catalogueWorkMediaSource";

  const label = document.createElement("span");
  label.className = "studioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const input = document.createElement("input");
  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  input.type = "hidden";
  wrapper.appendChild(input);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "studioUi__button catalogueWorkMediaSource__button";
  button.addEventListener("click", () => {
    const config = mediaSourceConfig(state);
    const currentSourceId = resolvedWorkMediaSourceId(state);
    const currentIndex = config.sourceIds.indexOf(currentSourceId);
    if (currentIndex < 0 || config.sourceIds.length !== 2) return;
    const nextSourceId = config.sourceIds[(currentIndex + 1) % config.sourceIds.length];
    const storedSourceId = nextSourceId === config.defaultSourceId ? "" : nextSourceId;
    state.draft.media_source_id = storedSourceId;
    state.regenerateImage = false;
    if (state.pendingWorkBatch) {
      state.pendingWorkBatch = null;
      state.draft.work_id = state.nextSuggestedWorkId;
      state.searchNode.value = state.draft.work_id;
    }
    input.value = storedSourceId;
    ["project_folder", "project_subfolder", "project_filename"].forEach((fieldKey) => {
      state.draft[fieldKey] = "";
      const fieldNode = state.fieldNodes.get(fieldKey);
      if (fieldNode) setFieldNodeValue(fieldNode, "");
    });
    resetProjectMediaFolders(state);
    updateMediaSourceButton(state);
    notifyStateChange(options);
  });
  wrapper.appendChild(button);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
  state.mediaSourceWrapper = wrapper;
  state.mediaSourceButton = button;
  updateMediaSourceButton(state);
}

function renderProjectMediaDisplayField(field, fieldsNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "studioForm__field catalogueWorkForm__field catalogueProjectMediaPicker__displayField";

  const label = document.createElement("span");
  label.className = "studioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const control = document.createElement("div");
  control.className = "catalogueProjectMediaPicker__displayControl";

  const display = document.createElement("a");
  display.className = "studioUi__input studioUi__input--readonlyDisplay catalogueProjectMediaPicker__displayValue";
  display.id = `catalogueWorkFieldDisplay-${field.key}`;
  display.dataset.projectMediaDisplay = field.key;
  display.textContent = "—";
  display.addEventListener("click", event => {
    event.preventDefault();
    if (display.getAttribute("aria-disabled") === "true") return;
    options.onOpenSourceTarget(field.key);
  });
  control.appendChild(display);

  const input = document.createElement("input");
  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  input.dataset.displayTarget = display.id;
  input.type = "hidden";
  control.appendChild(input);

  if (field.key === "project_subfolder") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "studioUi__iconButton";
    button.append(createStudioIcon(document, "folder-open"));
    button.title = "Open subfolder";
    button.setAttribute("aria-label", "Open subfolder");
    button.addEventListener("click", event => {
      event.stopPropagation();
      openProjectMediaFolderForCurrentDraft(state, options).catch(error => {
        console.warn("catalogue_work_form: failed to open project folder picker", error);
      });
    });
    control.appendChild(button);
    state.projectMediaFolderButton = button;
  }

  if (field.key === "project_filename") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "studioUi__iconButton";
    button.dataset.projectMediaChoose = "work";
    button.append(createStudioIcon(document, "folder-open"));
    button.title = "Choose image...";
    button.setAttribute("aria-label", "Choose image...");
    button.addEventListener("click", (event) => {
      // The opener must not dismiss the folder list when cached folders load immediately.
      event.stopPropagation();
      openProjectMediaPickerForCurrentDraft(state, options).catch((error) => {
        console.warn("catalogue_work_form: failed to open project image picker", error);
      });
    });
    control.appendChild(button);
    state.projectMediaChooseButton = button;
  }

  wrapper.appendChild(control);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderSeriesField(field, fieldsNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "studioForm__field catalogueWorkForm__field catalogueWorkForm__field--topAligned catalogueWorkSeriesPicker";

  const label = document.createElement("span");
  label.className = "studioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.id = `catalogueWorkField-${field.key}`;
  hiddenInput.dataset.field = field.key;
  wrapper.appendChild(hiddenInput);

  const pickerNode = document.createElement("div");
  pickerNode.className = "catalogueWorkSeriesPicker__control";

  const searchWrap = document.createElement("div");
  searchWrap.className = "sharedSearchList__control";
  const searchInput = document.createElement("input");
  searchInput.className = "studioUi__input catalogueWorkSeriesPicker__search";
  searchInput.type = "text";
  searchInput.autocomplete = "off";
  searchInput.placeholder = "find series by title";
  searchInput.setAttribute("aria-label", "Find series by title");
  const popupNode = document.createElement("div");
  popupNode.hidden = true;
  searchWrap.appendChild(searchInput);
  mountSearchField(searchInput);
  searchWrap.appendChild(popupNode);
  pickerNode.append(searchWrap);

  wrapper.appendChild(pickerNode);

  if (field.description) {
    const help = document.createElement("span");
    help.className = "studioForm__meta catalogueWorkForm__fieldMeta";
    help.textContent = field.description;
    wrapper.appendChild(help);
  }

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  const searchController = bindSearchList(searchInput, popupNode, {
    id: "catalogueWorkSeriesSearchList",
    openOnFocus: false,
    shouldOpen: () => !searchInput.disabled,
    loadOptions: () => Array.from(state.seriesById.entries()),
    filterOptions: (_items, query) => seriesSearchMatches(state, query),
    getOptionValue: ([seriesId]) => seriesDisplayTitle(state, seriesId),
    renderOption: ([seriesId]) => `
      <span class="catalogueSeriesSearch__title">${escapeHtml(seriesDisplayTitle(state, seriesId))}</span>
    `,
    noResultsText: "No matching series.",
    onCommit: ([seriesId]) => {
      if (searchInput.disabled) return;
      setSeriesDraftId(state, seriesId, options);
      searchInput.focus();
    },
    onCancel: () => renderSeriesPicker(state)
  });
  searchInput.addEventListener("blur", () => renderSeriesPicker(state));
  popupNode.addEventListener("mousedown", event => {
    // Preserve the query and results until click commits the exact Series selection.
    if (event.button === 0 && event.target.closest("[data-search-list-index]")) event.preventDefault();
  });
  fieldsNode.appendChild(wrapper);
  state.seriesPicker = { wrapper, pickerNode, searchWrap, searchInput, popupNode, hiddenInput, searchController };
  state.fieldNodes.set(field.key, hiddenInput);
  state.fieldStatusNodes.set(field.key, message);
  renderSeriesPicker(state);
}

function renderReadonlyField(field, readonlyNode, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "studioForm__field";

  const label = document.createElement("span");
  label.className = "studioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "studioUi__input studioUi__input--readonlyDisplay";
  value.dataset.readonlyField = field.key;
  value.textContent = "";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

export function renderWorkEditorFields(state, elements, options = {}) {
  EDITABLE_FIELDS.forEach((field) => renderField(field, elements.fieldsNode, state, options));
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, elements.readonlyNode, state));
}

export function setFieldNodeValue(node, value) {
  const text = value ?? "";
  if (typeof text !== "string") throw new Error("Work control values must be text or absent.");
  if ("value" in node) {
    node.value = text;
    if (node.dataset && node.dataset.displayTarget) {
      const displayNode = node.ownerDocument.getElementById(node.dataset.displayTarget);
      if (displayNode) displayNode.textContent = text;
    }
  } else {
    node.textContent = text;
  }
}

export function getFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return node.textContent;
}

export function applyDraftToInputs(state) {
  state.mediumSearch?.close();
  renderWorkGalleryPicker(state);
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    if (field.key === "series_id") {
      node.value = state.draft[field.key];
      renderSeriesPicker(state);
      return;
    }
    setFieldNodeValue(node, state.draft[field.key]);
  });
  updateMediaSourceButton(state);
}

export function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    node.textContent = state.currentRecord?.[field.key] ?? "";
  });
}

export function clearReadonlyFields(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "";
  });
}

export function setModeFieldAvailability(state) {
  setWorkGalleryPickerAvailability(state);
  const isBulk = state.mode === "bulk";
  const busy = state.isSaving || state.isBuilding || state.isDeleting;
  state.fieldsNode.querySelectorAll("[data-project-media-display]").forEach(link => {
    const value = state.draft[link.dataset.projectMediaDisplay];
    const disabled = !value || isBulk || busy || state.isOpeningSource || !state.serverAvailable;
    link.setAttribute("aria-disabled", String(disabled));
    link.title = value ? (link.dataset.projectMediaDisplay === "project_filename" ? "Reveal original in Finder" : "Open folder in Finder") : "";
    if (disabled) link.removeAttribute("href");
    else link.href = "#";
  });
  state.fieldNodes.forEach((node, key) => {
    const field = WORK_FIELD_DEFINITIONS[key];
    const bulkEditable = BULK_WORK_METADATA_FIELDS.includes(field);
    const batchAssigned = Boolean(state.pendingWorkBatch) && key === "title";
    if ("readOnly" in node) node.readOnly = (isBulk && !bulkEditable) || batchAssigned;
    if ("disabled" in node) node.disabled = busy || (isBulk && node.tagName === "SELECT");
    const required = !batchAssigned && isWorkFieldRequired(field, state.mode, state.bulkTouchedFields);
    if ("placeholder" in node) {
      const mixed = isBulk && bulkEditable && state.bulkMixedFields.has(key) && !state.bulkTouchedFields.has(key);
      node.placeholder = batchAssigned ? "From filenames" : mixed ? "Mixed values" : "";
    }
    const label = node.closest(".catalogueWorkForm__field")?.querySelector(":scope > .studioForm__label");
    label?.classList.toggle("studioForm__label--required", required);
    const control = key === "series_id" ? state.seriesPicker.searchInput : node;
    if (required) control.setAttribute("aria-required", "true");
    else control.removeAttribute("aria-required");
  });
  if (state.fieldNodes.get("medium").disabled) state.mediumSearch?.close();
  const workIdRequired = !state.pendingWorkBatch && isWorkFieldRequired(WORK_FIELD_DEFINITIONS.work_id, state.mode);
  state.searchNode.readOnly = Boolean(state.pendingWorkBatch);
  if (state.mode === "new") state.searchNode.placeholder = state.pendingWorkBatch ? "Assigned on Save" : "new work id";
  for (const label of state.searchNode.labels) label.classList.toggle("studioForm__label--required", workIdRequired);
  if (workIdRequired) state.searchNode.setAttribute("aria-required", "true");
  else state.searchNode.removeAttribute("aria-required");
  if (state.seriesPicker) {
    state.seriesPicker.pickerNode.hidden = false;
    state.seriesPicker.searchWrap.hidden = false;
    state.seriesPicker.searchInput.disabled = isBulk || busy || !state.serverAvailable;
    if (state.seriesPicker.searchInput.disabled) {
      renderSeriesPicker(state);
    }
  }
  if (state.projectMediaChooseButton) {
    state.projectMediaChooseButton.disabled = state.mode === "bulk" || state.isSaving || state.isBuilding || state.isDeleting;
  }
  if (state.projectMediaFolderButton) {
    state.projectMediaFolderButton.hidden = state.mode !== "new";
    state.projectMediaFolderButton.disabled = busy || !state.serverAvailable;
  }
  if (state.mediaSourceButton) {
    state.mediaSourceButton.disabled = state.mode === "bulk"
      || state.isSaving
      || state.isBuilding
      || state.isDeleting
      || !state.serverAvailable;
  }
  if (state.mediaSourceWrapper) {
    state.mediaSourceWrapper.hidden = state.mode === "bulk";
  }
}

export function updateFieldMessages(state, errors, options = {}) {
  void errors;
  void options;
  EDITABLE_FIELDS.forEach((field) => {
    const messageNode = state.fieldStatusNodes.get(field.key);
    if (!messageNode) return;
    messageNode.textContent = "";
    messageNode.hidden = true;
  });
}
