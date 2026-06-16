import {
  bindSearchList
} from "/shared/frontend/js/search-list.js";
import {
  createFilePickerConfig,
  filePickerText
} from "/shared/frontend/js/file-picker-config.js";

export {
  FILE_PICKER_DEFAULT_CONFIG,
  createFilePickerConfig,
  filePickerText
} from "/shared/frontend/js/file-picker-config.js";

let pickerId = 0;

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function optionValue(record, keys) {
  if (record && typeof record === "object") {
    for (const key of keys) {
      const value = normalizeText(record[key]);
      if (value) return value;
    }
  }
  return normalizeText(record);
}

function folderValue(record) {
  return optionValue(record, ["folder", "project_folder", "value"]);
}

function subfolderValue(record) {
  return optionValue(record, ["subfolder", "project_subfolder", "value"]);
}

function fileValue(record) {
  return optionValue(record, ["filename", "file", "value"]);
}

function fileStem(filename) {
  const value = normalizeText(filename);
  const dotIndex = value.lastIndexOf(".");
  return dotIndex > 0 ? value.slice(0, dotIndex) : value;
}

function normalizeList(records, valueForRecord) {
  const seen = new Set();
  const values = [];
  (Array.isArray(records) ? records : []).forEach((record) => {
    const value = valueForRecord(record);
    const key = value.toLowerCase();
    if (!value || seen.has(key)) return;
    seen.add(key);
    values.push(value);
  });
  return values;
}

function renderBody(id, config) {
  const folderLabel = filePickerText(config, "folderLabel");
  const subfolderLabel = filePickerText(config, "subfolderLabel");
  const fileLabel = filePickerText(config, "filesLabel");
  return `
    <div class="sharedFilePicker" data-role="file-picker">
      <div class="sharedFilePicker__folderField">
        <span class="sharedSearchList__control sharedFilePicker__folderControl">
          <input class="sharedFilePicker__folderInput" id="${escapeHtml(id)}-folder" data-role="file-picker-folder-input" type="text" autocomplete="off" spellcheck="false" aria-label="${escapeHtml(folderLabel)}">
          <span class="sharedFilePicker__folderPopup" data-role="file-picker-folder-popup" hidden></span>
        </span>
      </div>
      <p class="sharedFilePicker__status" data-role="file-picker-status" hidden></p>
      <div class="sharedFilePicker__listboxes">
        <div class="sharedFilePicker__listboxField">
          <div class="sharedFilePicker__listbox" id="${escapeHtml(id)}-subfolders" data-role="file-picker-subfolder-list" role="listbox" tabindex="-1" aria-disabled="true" aria-label="${escapeHtml(subfolderLabel)}"></div>
        </div>
        <div class="sharedFilePicker__listboxField">
          <div class="sharedFilePicker__fileToolbar" data-role="file-picker-file-toolbar" hidden>
            <button class="sharedFilePicker__toolbarButton" type="button" data-role="file-picker-select-all">${escapeHtml(filePickerText(config, "selectAllButton"))}</button>
            <button class="sharedFilePicker__toolbarButton" type="button" data-role="file-picker-deselect-all">${escapeHtml(filePickerText(config, "deselectAllButton"))}</button>
            <span class="sharedFilePicker__selectionCount" data-role="file-picker-selection-count"></span>
          </div>
          <div class="sharedFilePicker__listbox" id="${escapeHtml(id)}-files" data-role="file-picker-file-list" role="listbox" tabindex="-1" aria-disabled="true" aria-label="${escapeHtml(fileLabel)}"></div>
        </div>
      </div>
    </div>
  `;
}

function listboxOptionId(listboxNode, index) {
  return `${listboxNode.id}-option-${index}`;
}

function listboxItem(item) {
  if (item && typeof item === "object") {
    const value = normalizeText(item.value);
    return {
      className: normalizeText(item.className),
      disabled: Boolean(item.disabled),
      label: normalizeText(item.label) || value,
      title: normalizeText(item.title),
      value
    };
  }
  const value = normalizeText(item);
  return { className: "", disabled: false, label: value, title: "", value };
}

function renderListboxOptions(listboxNode, options, selectedValue, renderOptions = {}) {
  if (!listboxNode) return;
  const items = (Array.isArray(options) ? options : []).map(listboxItem);
  const multipleSelected = renderOptions.multipleSelected instanceof Set ? renderOptions.multipleSelected : null;
  const selected = multipleSelected ? "" : normalizeText(selectedValue);
  const selectedIndex = multipleSelected
    ? items.findIndex((item) => !item.disabled)
    : items.findIndex((item) => item.value === selected && !item.disabled);
  const activeIndex = selectedIndex >= 0 ? selectedIndex : -1;
  listboxNode.filePickerItems = items;
  listboxNode.filePickerValues = items.map((item) => item.value);
  listboxNode.dataset.selectedValue = selectedIndex >= 0 && !multipleSelected ? selected : "";
  listboxNode.dataset.activeIndex = String(activeIndex);
  listboxNode.innerHTML = items.map((item, index) => {
    const optionId = listboxOptionId(listboxNode, index);
    const selectedOption = multipleSelected ? multipleSelected.has(item.value) : index === selectedIndex;
    const selectedAttr = selectedOption ? "true" : "false";
    const className = ["sharedFilePicker__option", item.className].filter(Boolean).join(" ");
    const disabledAttr = item.disabled ? ' aria-disabled="true"' : "";
    const titleAttr = item.title ? ` title="${escapeHtml(item.title)}"` : "";
    const checkboxHtml = multipleSelected
      ? `<span class="sharedFilePicker__optionCheck" aria-hidden="true">${selectedOption ? "✓" : ""}</span>`
      : "";
    return `<div class="${escapeHtml(className)}" id="${escapeHtml(optionId)}" data-listbox-option-index="${index}" data-listbox-option-value="${escapeHtml(item.value)}" role="option" aria-selected="${selectedAttr}"${disabledAttr}${titleAttr}>${checkboxHtml}<span class="sharedFilePicker__optionText">${escapeHtml(item.label)}</span></div>`;
  }).join("");
  if (activeIndex >= 0) {
    listboxNode.setAttribute("aria-activedescendant", listboxOptionId(listboxNode, activeIndex));
  } else {
    listboxNode.removeAttribute("aria-activedescendant");
  }
}

function selectedListboxValue(listboxNode) {
  return normalizeText(listboxNode && listboxNode.dataset.selectedValue);
}

function listboxItemAt(listboxNode, index) {
  const items = Array.isArray(listboxNode && listboxNode.filePickerItems) ? listboxNode.filePickerItems : [];
  return index >= 0 && index < items.length ? items[index] : null;
}

function listboxItemDisabled(listboxNode, index) {
  const item = listboxItemAt(listboxNode, index);
  return Boolean(item && item.disabled);
}

function setListboxActive(listboxNode, index) {
  const values = Array.isArray(listboxNode && listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
  if (!listboxNode || !values.length || index < 0 || index >= values.length || listboxItemDisabled(listboxNode, index)) return false;
  listboxNode.dataset.activeIndex = String(index);
  listboxNode.setAttribute("aria-activedescendant", listboxOptionId(listboxNode, index));
  const activeNode = listboxNode.querySelector(`[data-listbox-option-index="${index}"]`);
  if (activeNode && typeof activeNode.scrollIntoView === "function") {
    activeNode.scrollIntoView({ block: "nearest" });
  }
  return true;
}

function setListboxSelection(listboxNode, index) {
  const values = Array.isArray(listboxNode && listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
  if (!listboxNode || !values.length || index < 0 || index >= values.length || listboxItemDisabled(listboxNode, index)) return false;
  const value = values[index];
  listboxNode.dataset.selectedValue = value;
  setListboxActive(listboxNode, index);
  listboxNode.querySelectorAll("[data-listbox-option-index]").forEach((optionNode) => {
    optionNode.setAttribute("aria-selected", optionNode.getAttribute("data-listbox-option-index") === String(index) ? "true" : "false");
  });
  listboxNode.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

function nextEnabledIndex(listboxNode, startIndex, direction) {
  const values = Array.isArray(listboxNode && listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
  if (!listboxNode || !values.length) return -1;
  let nextIndex = Math.max(0, Math.min(values.length - 1, startIndex));
  while (nextIndex >= 0 && nextIndex < values.length) {
    if (!listboxItemDisabled(listboxNode, nextIndex)) return nextIndex;
    nextIndex += direction;
  }
  return -1;
}

function moveListboxSelection(listboxNode, direction, options = {}) {
  const values = Array.isArray(listboxNode && listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
  if (!listboxNode || !values.length) return false;
  const currentIndex = Number(listboxNode.dataset.activeIndex);
  const candidateIndex = currentIndex < 0
    ? (direction > 0 ? 0 : values.length - 1)
    : Math.max(0, Math.min(values.length - 1, currentIndex + direction));
  const nextIndex = nextEnabledIndex(listboxNode, candidateIndex, direction > 0 ? 1 : -1);
  if (nextIndex < 0) return false;
  if (nextIndex === currentIndex) return false;
  if (options.activeOnly) return setListboxActive(listboxNode, nextIndex);
  return setListboxSelection(listboxNode, nextIndex);
}

function setListboxDisabled(listboxNode, disabled) {
  if (!listboxNode) return;
  listboxNode.setAttribute("aria-disabled", disabled ? "true" : "false");
  listboxNode.tabIndex = disabled ? -1 : 0;
}

function disabledValueSet(values) {
  if (values instanceof Set) {
    return new Set([...values].map((value) => normalizeText(value).toLowerCase()).filter(Boolean));
  }
  if (Array.isArray(values)) {
    return new Set(values.map((value) => normalizeText(value).toLowerCase()).filter(Boolean));
  }
  return new Set();
}

function subfolderListOptions(folder, subfolders, config, disabledSubfolders = new Set()) {
  const parentFolder = normalizeText(folder);
  const subfolderConfig = config && config.subfolders ? config.subfolders : {};
  const prefix = normalizeText(subfolderConfig.prefix) || "⨽";
  const disabledTitle = filePickerText(config, "subfolderUnavailable");
  const records = [
    {
      className: "sharedFilePicker__option--parent",
      label: parentFolder || normalizeText(subfolderConfig.parentFallbackLabel) || filePickerText(config, "folderLabel"),
      value: ""
    }
  ];
  (Array.isArray(subfolders) ? subfolders : []).forEach((subfolder) => {
    const disabled = disabledSubfolders.has(normalizeText(subfolder).toLowerCase());
    records.push({
      className: "sharedFilePicker__option--subfolder",
      disabled,
      label: `${prefix} ${subfolder}`,
      title: disabled ? disabledTitle : "",
      value: subfolder
    });
  });
  return records;
}

function bindListbox(listboxNode, options = {}) {
  if (!listboxNode) return;
  listboxNode.addEventListener("click", (event) => {
    const optionNode = event.target && event.target.closest ? event.target.closest("[data-listbox-option-index]") : null;
    if (!optionNode || !listboxNode.contains(optionNode)) return;
    const index = Number(optionNode.getAttribute("data-listbox-option-index"));
    if (!Number.isInteger(index) || listboxItemDisabled(listboxNode, index)) return;
    if (options.selectionMode === "multiple") {
      setListboxActive(listboxNode, index);
      if (typeof options.onToggle === "function") options.onToggle(index);
      return;
    }
    setListboxSelection(listboxNode, index);
  });
  listboxNode.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveListboxSelection(listboxNode, 1, { activeOnly: options.selectionMode === "multiple" });
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveListboxSelection(listboxNode, -1, { activeOnly: options.selectionMode === "multiple" });
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      if (options.selectionMode === "multiple") setListboxActive(listboxNode, nextEnabledIndex(listboxNode, 0, 1));
      else setListboxSelection(listboxNode, nextEnabledIndex(listboxNode, 0, 1));
      return;
    }
    if (event.key === "End") {
      const values = Array.isArray(listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
      event.preventDefault();
      if (options.selectionMode === "multiple") setListboxActive(listboxNode, nextEnabledIndex(listboxNode, values.length - 1, -1));
      else setListboxSelection(listboxNode, nextEnabledIndex(listboxNode, values.length - 1, -1));
      return;
    }
    if (event.key === " " && options.selectionMode === "multiple") {
      event.preventDefault();
      const activeIndex = Number(listboxNode.dataset.activeIndex);
      if (Number.isInteger(activeIndex) && typeof options.onToggle === "function") options.onToggle(activeIndex);
      return;
    }
    if (event.key === "Enter" && typeof options.onEnter === "function") {
      event.preventDefault();
      options.onEnter();
    }
  });
  listboxNode.addEventListener("wheel", (event) => {
    if (!event.deltaY) return;
    event.preventDefault();
    event.stopPropagation();
    moveListboxSelection(listboxNode, event.deltaY > 0 ? 1 : -1, { activeOnly: options.selectionMode === "multiple" });
  }, { passive: false });
}

function prefixMatches(options, query) {
  const q = normalizeText(query).toLowerCase();
  if (!q) return options.slice(0, 12);
  return options.filter((value) => value.toLowerCase().startsWith(q)).slice(0, 12);
}

function setPrimaryDisabled(primaryNode, disabled) {
  if (primaryNode) primaryNode.disabled = Boolean(disabled);
}

export function createFilePicker(rootNode, options = {}) {
  if (!rootNode) {
    throw new Error("createFilePicker requires a root node");
  }
  const id = normalizeText(options.id) || `sharedFilePicker-${++pickerId}`;
  const config = createFilePickerConfig(options.config);
  const multipleFiles = options.selectionMode === "multiple";
  const fileOptions = options.files && typeof options.files === "object" ? options.files : {};
  const selectAllEnabled = multipleFiles && fileOptions.selectAll !== false;
  const defaultFileSelection = normalizeText(fileOptions.defaultSelection || (multipleFiles ? "all" : "first"));
  const disabledSubfolders = disabledValueSet(options.disabledSubfolders);
  rootNode.innerHTML = renderBody(id, config);

  const initial = options.initialSelection || {};
  const selected = {
    scope: normalizeText(initial.scope || options.scope),
    folder: normalizeText(initial.folder || initial.project_folder),
    subfolder: normalizeText(initial.subfolder || initial.project_subfolder),
    filename: normalizeText(initial.filename || initial.project_filename),
    filenames: new Set(Array.isArray(initial.filenames) ? initial.filenames.map(normalizeText).filter(Boolean) : [])
  };
  const state = {
    folders: [],
    subfolders: [],
    files: []
  };

  const folderInput = rootNode.querySelector('[data-role="file-picker-folder-input"]');
  const folderPopup = rootNode.querySelector('[data-role="file-picker-folder-popup"]');
  const statusNode = rootNode.querySelector('[data-role="file-picker-status"]');
  const subfolderNode = rootNode.querySelector('[data-role="file-picker-subfolder-list"]');
  const fileNode = rootNode.querySelector('[data-role="file-picker-file-list"]');
  const fileToolbarNode = rootNode.querySelector('[data-role="file-picker-file-toolbar"]');
  const selectAllNode = rootNode.querySelector('[data-role="file-picker-select-all"]');
  const deselectAllNode = rootNode.querySelector('[data-role="file-picker-deselect-all"]');
  const selectionCountNode = rootNode.querySelector('[data-role="file-picker-selection-count"]');
  const primaryNode = options.primaryNode || null;

  function setStatus(kind, message) {
    const text = normalizeText(message);
    if (!statusNode) return;
    statusNode.textContent = text;
    statusNode.hidden = !text;
    if (kind) statusNode.dataset.state = kind;
    if (!text) statusNode.removeAttribute("data-state");
  }

  function setListboxesDisabled(disabled) {
    setListboxDisabled(subfolderNode, Boolean(disabled));
    setListboxDisabled(fileNode, Boolean(disabled));
  }

  function selectedFileCount() {
    return multipleFiles ? selected.filenames.size : (selected.filename ? 1 : 0);
  }

  function setPrimaryForFileSelection() {
    setPrimaryDisabled(primaryNode, selectedFileCount() <= 0);
  }

  function updateFileSelectionToolbar() {
    if (!fileToolbarNode) return;
    fileToolbarNode.hidden = !selectAllEnabled || !state.files.length;
    if (selectionCountNode) {
      selectionCountNode.textContent = filePickerText(config, "selectedFilesCount", {
        count: String(selected.filenames.size)
      });
    }
    if (selectAllNode) selectAllNode.disabled = !state.files.length || selected.filenames.size === state.files.length;
    if (deselectAllNode) deselectAllNode.disabled = !selected.filenames.size;
  }

  function renderFileList() {
    if (multipleFiles) {
      renderListboxOptions(fileNode, state.files, "", { multipleSelected: selected.filenames });
      updateFileSelectionToolbar();
      setPrimaryForFileSelection();
      return;
    }
    renderListboxOptions(fileNode, state.files, selected.filename);
    setPrimaryForFileSelection();
  }

  function resetFileSelectionForLoadedFiles(loadOptions = {}) {
    if (!multipleFiles) {
      const requestedFilename = normalizeText(loadOptions.filename);
      if (requestedFilename && state.files.includes(requestedFilename)) {
        selected.filename = requestedFilename;
      } else if (loadOptions.autoSelectFirst) {
        selected.filename = state.files[0] || "";
      } else {
        selected.filename = "";
      }
      return Boolean(requestedFilename && !selected.filename);
    }

    const requestedFilenames = Array.isArray(loadOptions.filenames) ? loadOptions.filenames.map(normalizeText).filter(Boolean) : [];
    selected.filenames.clear();
    requestedFilenames.forEach((filename) => {
      if (state.files.includes(filename)) selected.filenames.add(filename);
    });
    if (!requestedFilenames.length && defaultFileSelection === "all") {
      state.files.forEach((filename) => selected.filenames.add(filename));
    }
    return requestedFilenames.some((filename) => !selected.filenames.has(filename));
  }

  function toggleFileSelection(index) {
    if (!multipleFiles) return;
    const filename = state.files[index];
    if (!filename) return;
    if (selected.filenames.has(filename)) selected.filenames.delete(filename);
    else selected.filenames.add(filename);
    renderFileList();
  }

  function selectAllFiles() {
    if (!multipleFiles) return;
    state.files.forEach((filename) => selected.filenames.add(filename));
    renderFileList();
  }

  function deselectAllFiles() {
    if (!multipleFiles) return;
    selected.filenames.clear();
    renderFileList();
  }

  async function loadFolders() {
    if (state.folders.length) return state.folders;
    if (typeof options.loadFolders !== "function") return [];
    const payload = await options.loadFolders({
      scope: selected.scope,
      query: ""
    });
    const records = Array.isArray(payload) ? payload : payload && (payload.folders || payload.project_folders);
    state.folders = normalizeList(records, folderValue);
    return state.folders;
  }

  async function loadFilesForSelection(loadOptions = {}) {
    const folder = normalizeText(selected.folder);
    if (!folder || typeof options.loadFiles !== "function") {
      state.subfolders = [];
      state.files = [];
      renderListboxOptions(subfolderNode, [], "");
      renderListboxOptions(fileNode, [], "");
      setListboxesDisabled(true);
      setPrimaryDisabled(primaryNode, true);
      return;
    }

    setPrimaryDisabled(primaryNode, true);
    setListboxesDisabled(true);
    try {
      const payload = await options.loadFiles({
        scope: selected.scope,
        folder,
        subfolder: selected.subfolder,
        query: ""
      });
      state.subfolders = normalizeList(payload && payload.subfolders, subfolderValue);
      state.files = normalizeList(payload && payload.files, fileValue);

      const missingRequestedFile = resetFileSelectionForLoadedFiles(loadOptions);
      if (missingRequestedFile) {
        setStatus("warning", filePickerText(config, "fileNotFound"));
      } else if (!loadOptions.keepStatus) {
        setStatus("", "");
      }

      renderListboxOptions(subfolderNode, subfolderListOptions(folder, state.subfolders, config, disabledSubfolders), selected.subfolder);
      renderFileList();
      setListboxesDisabled(false);
      setPrimaryForFileSelection();
    } catch (error) {
      state.files = [];
      selected.filename = "";
      selected.filenames.clear();
      renderFileList();
      setListboxDisabled(fileNode, true);
      setListboxDisabled(subfolderNode, false);
      setPrimaryDisabled(primaryNode, true);
      setStatus("error", normalizeText(error && error.message) || filePickerText(config, "filesFailed"));
    }
  }

  async function selectFolder(folder, loadOptions = {}) {
    selected.folder = normalizeText(folder);
    selected.subfolder = "";
    selected.filename = "";
    selected.filenames.clear();
    if (folderInput) folderInput.value = selected.folder;
    await loadFilesForSelection({ autoSelectFirst: loadOptions.autoSelectFirst !== false });
    if (loadOptions.focusFiles !== false && fileNode && !fileNode.disabled) {
      fileNode.focus();
    }
  }

  const searchController = bindSearchList(folderInput, folderPopup, {
    id: `${id}-folder-popup`,
    maxOptions: config.search.maxFolderResults,
    openOnFocus: config.search.openFolderSearchOnFocus,
    classNames: {
      option: "sharedFilePicker__folderOption"
    },
    loadOptions: loadFolders,
    filterOptions: prefixMatches,
    getOptionValue: (folder) => folder,
    renderOption: (folder) => `<span class="sharedSearchList__optionText">${escapeHtml(folder)}</span>`,
    renderNoResults: () => `<p class="sharedSearchList__empty">${escapeHtml(filePickerText(config, "noFolderMatch"))}</p>`,
    renderError: (error) => `<p class="sharedSearchList__empty">${escapeHtml(normalizeText(error && error.message) || filePickerText(config, "foldersFailed"))}</p>`,
    onTransientInput: ({ value }) => {
      setPrimaryDisabled(primaryNode, normalizeText(value) !== selected.folder || selectedFileCount() <= 0);
    },
    onCancel: () => {
      setPrimaryForFileSelection();
    },
    onCommit: (folder) => selectFolder(folder, { autoSelectFirst: true }).catch((error) => {
      setStatus("error", normalizeText(error && error.message) || filePickerText(config, "filesFailed"));
    })
  });

  if (subfolderNode) {
    subfolderNode.addEventListener("change", () => {
      selected.subfolder = selectedListboxValue(subfolderNode);
      selected.filename = "";
      selected.filenames.clear();
      loadFilesForSelection({ autoSelectFirst: true }).catch((error) => {
        setStatus("error", normalizeText(error && error.message) || filePickerText(config, "filesFailed"));
      });
    });
    bindListbox(subfolderNode);
  }

  if (fileNode) {
    fileNode.addEventListener("change", () => {
      selected.filename = selectedListboxValue(fileNode);
      setPrimaryForFileSelection();
    });
    fileNode.addEventListener("dblclick", () => {
      selected.filename = selectedListboxValue(fileNode);
      if (selectedFileCount() > 0 && typeof options.onSubmit === "function") options.onSubmit();
    });
    bindListbox(fileNode, {
      selectionMode: multipleFiles ? "multiple" : "single",
      onToggle: toggleFileSelection,
      onEnter() {
        if (selectedFileCount() > 0 && typeof options.onSubmit === "function") options.onSubmit();
      }
    });
  }

  if (selectAllNode) selectAllNode.addEventListener("click", selectAllFiles);
  if (deselectAllNode) deselectAllNode.addEventListener("click", deselectAllFiles);

  async function initialize() {
    setPrimaryDisabled(primaryNode, true);
    setListboxesDisabled(true);
    if (folderInput) folderInput.value = selected.folder;
    const folders = await loadFolders();
    if (!selected.folder) return;
    if (!folders.includes(selected.folder)) {
      selected.folder = "";
      selected.subfolder = "";
      selected.filename = "";
      if (folderInput) folderInput.value = "";
      setStatus("warning", filePickerText(config, "fileNotFound"));
      return;
    }

    const requestedSubfolder = selected.subfolder;
    const requestedFilename = selected.filename;
    const requestedFilenames = [...selected.filenames];
    selected.subfolder = "";
    selected.filename = "";
    selected.filenames.clear();
    await loadFilesForSelection({
      filename: requestedSubfolder ? "" : requestedFilename,
      filenames: requestedSubfolder ? [] : requestedFilenames,
      keepStatus: true
    });

    if (requestedSubfolder) {
      if (state.subfolders.includes(requestedSubfolder)) {
        selected.subfolder = requestedSubfolder;
        await loadFilesForSelection({ filename: requestedFilename, filenames: requestedFilenames });
      } else {
        selected.subfolder = "";
        selected.filename = "";
        selected.filenames.clear();
        renderListboxOptions(subfolderNode, subfolderListOptions(selected.folder, state.subfolders, config, disabledSubfolders), "");
        setPrimaryDisabled(primaryNode, true);
        setStatus("warning", filePickerText(config, "fileNotFound"));
      }
    }
  }

  function submit() {
    const folderText = normalizeText(folderInput && folderInput.value);
    if (!selected.folder || folderText !== selected.folder) {
      return {
        ok: false,
        statusKind: "error",
        status: filePickerText(config, "folderRequired")
      };
    }
    if (selectedFileCount() <= 0) {
      return {
        ok: false,
        statusKind: "error",
        status: filePickerText(config, "fileRequired")
      };
    }
    return {
      selection: {
        scope: selected.scope,
        folder: selected.folder,
        subfolder: selected.subfolder,
        filename: selected.filename,
        filenames: multipleFiles ? [...selected.filenames] : (selected.filename ? [selected.filename] : []),
        file_titles: multipleFiles ? [...selected.filenames].map((filename) => ({
          filename,
          title: fileStem(filename)
        })) : []
      }
    };
  }

  const ready = initialize().catch((error) => {
    setStatus("error", normalizeText(error && error.message) || filePickerText(config, "foldersFailed"));
  });

  return {
    ready,
    submit,
    focus() {
      if (folderInput) folderInput.focus();
    },
    focusPreferred() {
      if (selected.folder && selected.filename && fileNode && fileNode.getAttribute("aria-disabled") !== "true") {
        fileNode.focus();
        return;
      }
      if (folderInput) {
        folderInput.focus();
        if (typeof folderInput.select === "function") folderInput.select();
      }
    },
    destroy() {
      if (searchController && typeof searchController.destroy === "function") searchController.destroy();
    },
    getSelection() {
      return {
        ...selected,
        filenames: [...selected.filenames]
      };
    }
  };
}
