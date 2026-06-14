import { displayValue } from "./catalogue-editor-records.js";
import {
  catalogueReadinessItem
} from "./catalogue-editor-readiness.js";
import {
  buildPublicSeriesUrl
} from "./catalogue-public-links.js";
import {
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_READONLY_FIELDS as READONLY_FIELDS,
  dedupeSeriesIds,
  normalizeSeriesId,
  normalizeText,
  parseSeriesIds,
  seriesIdsToText
} from "./catalogue-work-fields.js";
import {
  bindProjectFolderSearch,
  openProjectMediaPickerForCurrentDraft
} from "./catalogue-project-media-picker.js";

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formText(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((text, [token, value]) => {
    return text.replace(new RegExp(`\\{${token}\\}`, "g"), value);
  }, fallback);
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

function draftHasChanges(state, options) {
  if (options && typeof options.draftHasChanges === "function") {
    return Boolean(options.draftHasChanges(state));
  }
  return false;
}

function stagedProseFileName(state) {
  const item = catalogueReadinessItem(state.buildPreview, "work_prose");
  if (normalizeText(item && item.status) !== "ready") return "";
  const sourcePath = normalizeText(item && item.source_path);
  if (sourcePath) {
    const parts = sourcePath.split("/");
    return normalizeText(parts[parts.length - 1]);
  }
  const workId = normalizeText(state.currentWorkId);
  return workId ? `${workId}.md` : "";
}

function stagedProseImportDisabled(state, options) {
  const item = catalogueReadinessItem(state.buildPreview, "work_prose");
  return (
    !state.currentRecord ||
    !state.currentWorkId ||
    !state.serverAvailable ||
    state.isSaving ||
    state.isBuilding ||
    state.isDeleting ||
    draftHasChanges(state, options) ||
    normalizeText(item && item.status) !== "ready"
  );
}

function seriesDisplayTitle(state, seriesId) {
  const record = state.seriesById.get(seriesId);
  return normalizeText(record && record.title) || seriesId;
}

function formatSeriesChoice(state, seriesId) {
  const title = seriesDisplayTitle(state, seriesId);
  return title === seriesId ? seriesId : `${title} (${seriesId})`;
}

function publicSeriesHref(state, seriesId) {
  try {
    return buildPublicSeriesUrl(state.config, seriesId);
  } catch (_error) {
    return "";
  }
}

function seriesSearchMatches(state, queryText) {
  const query = normalizeText(queryText).toLowerCase();
  const selected = new Set(parseSeriesIds(state.draft && state.draft.series_ids));
  if (!query) return [];
  return Array.from(state.seriesById.entries())
    .filter(([seriesId, record]) => {
      if (selected.has(seriesId)) return false;
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

function setSeriesDraftIds(state, seriesIds, options) {
  state.draft.series_ids = seriesIdsToText(dedupeSeriesIds(seriesIds.map((item) => normalizeSeriesId(item)).filter(Boolean)));
  const node = state.fieldNodes.get("series_ids");
  if (node) node.value = state.draft.series_ids;
  if (state.seriesPicker && state.seriesPicker.bulkInput) {
    state.seriesPicker.bulkInput.value = state.draft.series_ids;
  }
  if (state.mode === "bulk") {
    state.bulkTouchedFields.add("series_ids");
  }
  renderSeriesPicker(state, options);
  notifyStateChange(options);
}

function addSeriesDraftId(state, seriesId, options) {
  const normalizedId = normalizeSeriesId(seriesId);
  if (!normalizedId) return;
  const seriesIds = parseSeriesIds(state.draft.series_ids);
  if (!seriesIds.includes(normalizedId)) seriesIds.push(normalizedId);
  setSeriesDraftIds(state, seriesIds, options);
}

function removeSeriesDraftId(state, seriesId, options) {
  const normalizedId = normalizeSeriesId(seriesId);
  if (!normalizedId) return;
  setSeriesDraftIds(state, parseSeriesIds(state.draft.series_ids).filter((item) => item !== normalizedId), options);
}

function renderSeriesPickerMatches(state, options) {
  if (!state.seriesPicker) return;
  const matches = seriesSearchMatches(state, state.seriesPicker.searchInput.value);
  if (!matches.length) {
    state.seriesPicker.popupNode.hidden = true;
    state.seriesPicker.popupNode.innerHTML = "";
    return;
  }
  state.seriesPicker.popupNode.innerHTML = matches.map(([seriesId]) => `
    <button type="button" class="tagStudioSuggest__workButton catalogueWorkSeriesPicker__option" data-series-id="${escapeHtml(seriesId)}">
      <span class="tagStudioSuggest__workTitle">${escapeHtml(seriesDisplayTitle(state, seriesId))}</span>
      <span class="tagStudioSuggest__workMeta">${escapeHtml(seriesId)}</span>
    </button>
  `).join("");
  state.seriesPicker.popupNode.hidden = false;
}

function renderSeriesPicker(state, options = {}) {
  if (!state.seriesPicker) return;
  const seriesIds = parseSeriesIds(state.draft && state.draft.series_ids);
  state.seriesPicker.hiddenInput.value = seriesIdsToText(seriesIds);
  state.seriesPicker.chipsNode.innerHTML = seriesIds.length
    ? seriesIds.map((seriesId) => {
      const title = seriesDisplayTitle(state, seriesId);
      const href = publicSeriesHref(state, seriesId);
      const labelHtml = `
        <span class="tagStudio__chipText">${escapeHtml(title)}</span>
        <span class="catalogueWorkSeriesPicker__chipId">${escapeHtml(seriesId)}</span>
      `;
      return `
      <span class="tagStudio__chip catalogueWorkSeriesPicker__chip">
        ${href
          ? `<a class="catalogueWorkSeriesPicker__chipLink" href="${escapeHtml(href)}" target="_blank" rel="noopener">${labelHtml}</a>`
          : labelHtml}
        <button type="button" class="tagStudio__chipRemove" data-remove-series-id="${escapeHtml(seriesId)}" aria-label="${escapeHtml(`Remove ${formatSeriesChoice(state, seriesId)}`)}">×</button>
      </span>
    `;
    }).join("")
    : `<span class="tagStudioForm__meta">${escapeHtml(formText(options, "series_picker_empty", "No series selected."))}</span>`;
}

function renderField(field, fieldsNode, state, options) {
  if (field.key === "series_ids") {
    renderSeriesField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "project_folder") {
    renderProjectFolderField(field, fieldsNode, state, options);
    return;
  }
  if (field.key === "project_filename") {
    renderProjectFilenameField(field, fieldsNode, state, options);
    return;
  }

  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (field.type === "textarea") wrapper.classList.add("tagStudioForm__field--topAligned", "catalogueWorkForm__field--topAligned");
  if (!field.readonly) wrapper.htmlFor = `catalogueWorkField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  } else if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.className = "tagStudio__input tagStudioForm__descriptionInput";
    input.rows = 4;
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "tagStudio__input";
    field.options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
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
    help.className = "tagStudioForm__meta catalogueWorkForm__fieldMeta";
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

function renderProjectFolderField(field, fieldsNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field catalogueProjectMediaPicker__folderField";

  const label = document.createElement("label");
  label.className = "tagStudioForm__label";
  label.htmlFor = `catalogueWorkField-${field.key}`;
  label.textContent = field.label;
  wrapper.appendChild(label);

  const control = document.createElement("div");
  control.className = "sharedSearchList__control catalogueProjectMediaPicker__folderControl";

  const input = document.createElement("input");
  input.className = "tagStudio__input";
  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  input.type = "text";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.placeholder = formText(options, "project_folder_picker_placeholder", "find project folder");
  control.appendChild(input);

  const popupNode = document.createElement("div");
  popupNode.className = "catalogueProjectMediaPicker__folderPopup";
  popupNode.hidden = true;
  control.appendChild(popupNode);
  wrapper.appendChild(control);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  bindProjectFolderSearch(state, input, popupNode, {
    ...options,
    autoOpenFileModal: true
  });

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderProjectFilenameField(field, fieldsNode, state, options) {
  const wrapper = document.createElement("label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field catalogueProjectMediaPicker__filenameField";
  wrapper.htmlFor = `catalogueWorkField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const control = document.createElement("div");
  control.className = "catalogueProjectMediaPicker__filenameControl";

  const input = document.createElement("input");
  input.className = "tagStudio__input";
  input.id = `catalogueWorkField-${field.key}`;
  input.dataset.field = field.key;
  input.type = "text";
  input.autocomplete = "off";
  control.appendChild(input);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "tagStudio__button tagStudio__button--defaultWidth";
  button.dataset.projectMediaChoose = "work";
  button.textContent = formText(options, "project_media_choose_button", "Choose image...");
  control.appendChild(button);
  wrapper.appendChild(control);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  input.addEventListener("input", () => notifyFieldInput(options, field.key));
  input.addEventListener("change", () => notifyFieldInput(options, field.key));
  button.addEventListener("click", () => {
    openProjectMediaPickerForCurrentDraft(state, options).catch((error) => {
      console.warn("catalogue_work_form: failed to open project image picker", error);
    });
  });

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
  state.projectMediaChooseButton = button;
}

function renderStagedProseField(fieldsNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field catalogueWorkStagedProse";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = formText(options, "staged_prose_label", "staged prose");
  wrapper.appendChild(label);

  const control = document.createElement("div");
  control.className = "catalogueWorkStagedProse__control";

  const value = document.createElement("span");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  value.dataset.stagedProseValue = "work";
  control.appendChild(value);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "tagStudio__button tagStudio__button--defaultWidth";
  button.dataset.proseImport = "work";
  button.textContent = formText(options, "prose_import_button", "Import");
  control.appendChild(button);

  wrapper.appendChild(control);
  fieldsNode.appendChild(wrapper);
  state.stagedProseNode = value;
  state.stagedProseButton = button;
  updateStagedProseField(state, options);
}

function renderSeriesField(field, fieldsNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field catalogueWorkForm__field--topAligned catalogueWorkSeriesPicker";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.id = `catalogueWorkField-${field.key}`;
  hiddenInput.dataset.field = field.key;
  wrapper.appendChild(hiddenInput);

  const pickerNode = document.createElement("div");
  pickerNode.className = "catalogueWorkSeriesPicker__control";

  const chipsNode = document.createElement("div");
  chipsNode.className = "catalogueWorkSeriesPicker__chips";
  pickerNode.appendChild(chipsNode);

  const searchWrap = document.createElement("div");
  searchWrap.className = "catalogueWorkSeriesPicker__searchWrap";
  const searchInput = document.createElement("input");
  searchInput.className = "tagStudio__input catalogueWorkSeriesPicker__search";
  searchInput.type = "text";
  searchInput.autocomplete = "off";
  searchInput.placeholder = formText(options, "series_picker_placeholder", "find series by title");
  searchInput.setAttribute("aria-label", formText(options, "series_picker_label", "Find series by title"));
  const popupNode = document.createElement("div");
  popupNode.className = "tagStudio__popupInner catalogueWorkSeriesPicker__popup";
  popupNode.hidden = true;
  searchWrap.appendChild(searchInput);
  searchWrap.appendChild(popupNode);
  pickerNode.appendChild(searchWrap);

  const bulkInput = document.createElement("input");
  bulkInput.className = "tagStudio__input catalogueWorkSeriesPicker__bulkInput";
  bulkInput.type = "text";
  bulkInput.autocomplete = "off";
  bulkInput.placeholder = "+009, -010";
  pickerNode.appendChild(bulkInput);

  wrapper.appendChild(pickerNode);

  if (field.description) {
    const help = document.createElement("span");
    help.className = "tagStudioForm__meta catalogueWorkForm__fieldMeta";
    help.textContent = field.description;
    wrapper.appendChild(help);
  }

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  searchInput.addEventListener("input", () => renderSeriesPickerMatches(state, options));
  searchInput.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const matches = seriesSearchMatches(state, searchInput.value);
    if (!matches.length) return;
    event.preventDefault();
    addSeriesDraftId(state, matches[0][0], options);
    searchInput.value = "";
    popupNode.hidden = true;
  });
  popupNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-series-id]") : null;
    if (!button) return;
    addSeriesDraftId(state, button.getAttribute("data-series-id"), options);
    searchInput.value = "";
    popupNode.hidden = true;
    searchInput.focus();
  });
  chipsNode.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("[data-remove-series-id]") : null;
    if (!button) return;
    removeSeriesDraftId(state, button.getAttribute("data-remove-series-id"), options);
  });
  bulkInput.addEventListener("input", () => {
    state.draft.series_ids = bulkInput.value;
    hiddenInput.value = bulkInput.value;
    if (state.mode === "bulk") state.bulkTouchedFields.add("series_ids");
    notifyStateChange(options);
  });

  fieldsNode.appendChild(wrapper);
  state.seriesPicker = { wrapper, pickerNode, chipsNode, searchWrap, searchInput, popupNode, bulkInput, hiddenInput };
  state.fieldNodes.set(field.key, hiddenInput);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, readonlyNode, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  value.dataset.readonlyField = field.key;
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

export function renderWorkEditorFields(state, elements, options = {}) {
  EDITABLE_FIELDS.forEach((field) => renderField(field, elements.fieldsNode, state, options));
  renderStagedProseField(elements.fieldsNode, state, options);
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, elements.readonlyNode, state));
}

export function applyWorkFormText(state, options = {}) {
  if (state.seriesPicker) {
    state.seriesPicker.searchInput.placeholder = formText(options, "series_picker_placeholder", "find series by title");
    state.seriesPicker.searchInput.setAttribute("aria-label", formText(options, "series_picker_label", "Find series by title"));
  }
  if (state.stagedProseButton) {
    state.stagedProseButton.textContent = formText(options, "prose_import_button", "Import");
  }
  if (state.projectMediaChooseButton) {
    state.projectMediaChooseButton.textContent = formText(options, "project_media_choose_button", "Choose image...");
  }
}

export function updateStagedProseField(state, options = {}) {
  if (state.stagedProseNode) {
    state.stagedProseNode.textContent = stagedProseFileName(state);
  }
  if (state.stagedProseButton) {
    state.stagedProseButton.disabled = stagedProseImportDisabled(state, options);
  }
}

export function setFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = displayValue(text);
  }
}

export function getFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

export function applyDraftToInputs(state, options = {}) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    if (field.key === "series_ids") {
      node.value = normalizeText(state.draft[field.key]);
      if (state.seriesPicker && state.seriesPicker.bulkInput) {
        state.seriesPicker.bulkInput.value = normalizeText(state.draft[field.key]);
      }
      renderSeriesPicker(state, options);
      return;
    }
    setFieldNodeValue(node, normalizeText(state.draft[field.key]));
  });
}

export function applyReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    node.textContent = displayValue(state.currentRecord ? state.currentRecord[field.key] : "");
  });
}

export function clearReadonlyFields(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "—";
  });
}

export function setModeFieldAvailability(state) {
  const statusNode = state.fieldNodes.get("status");
  if (statusNode) {
    if ("disabled" in statusNode) statusNode.disabled = false;
    if ("readOnly" in statusNode) statusNode.readOnly = true;
  }
  const publishedDateNode = state.fieldNodes.get("published_date");
  if (publishedDateNode) {
    publishedDateNode.disabled = state.mode === "new";
  }
  if (state.seriesPicker) {
    const isBulk = state.mode === "bulk";
    state.seriesPicker.pickerNode.hidden = false;
    state.seriesPicker.chipsNode.hidden = isBulk;
    state.seriesPicker.searchWrap.hidden = isBulk;
    state.seriesPicker.bulkInput.hidden = !isBulk;
    state.seriesPicker.searchInput.disabled = isBulk || state.isSaving || state.isBuilding || state.isDeleting;
    state.seriesPicker.bulkInput.disabled = !isBulk || state.isSaving || state.isBuilding || state.isDeleting;
    if (isBulk) {
      state.seriesPicker.popupNode.hidden = true;
    }
  }
  if (state.projectMediaChooseButton) {
    state.projectMediaChooseButton.disabled = state.mode === "bulk" || state.isSaving || state.isBuilding || state.isDeleting;
  }
}

export function updateFieldMessages(state, errors, options = {}) {
  EDITABLE_FIELDS.forEach((field) => {
    const messageNode = state.fieldStatusNodes.get(field.key);
    if (!messageNode) return;
    let message = errors.get(field.key) || "";
    if (!message && state.mode === "bulk" && state.bulkMixedFields.has(field.key) && !state.bulkTouchedFields.has(field.key)) {
      message = field.key === "series_ids"
        ? formText(options, "bulk_field_mixed_series", "Mixed values across selection. Leave untouched to preserve, use plain ids to replace, or +id/-id to add or remove.")
        : formText(options, "bulk_field_mixed", "Mixed values across selection. Leave untouched to preserve per-record values.");
    }
    messageNode.textContent = message;
    messageNode.hidden = !message;
  });
}
