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
      label: normalizeText(item.label) || value,
      value
    };
  }
  const value = normalizeText(item);
  return { className: "", label: value, value };
}

function renderListboxOptions(listboxNode, options, selectedValue) {
  if (!listboxNode) return;
  const items = (Array.isArray(options) ? options : []).map(listboxItem);
  const selected = normalizeText(selectedValue);
  const selectedIndex = items.findIndex((item) => item.value === selected);
  const activeIndex = selectedIndex >= 0 ? selectedIndex : -1;
  listboxNode.filePickerValues = items.map((item) => item.value);
  listboxNode.dataset.selectedValue = selectedIndex >= 0 ? selected : "";
  listboxNode.dataset.activeIndex = String(activeIndex);
  listboxNode.innerHTML = items.map((item, index) => {
    const optionId = listboxOptionId(listboxNode, index);
    const selectedAttr = index === selectedIndex ? "true" : "false";
    const className = ["sharedFilePicker__option", item.className].filter(Boolean).join(" ");
    return `<div class="${escapeHtml(className)}" id="${escapeHtml(optionId)}" data-listbox-option-index="${index}" data-listbox-option-value="${escapeHtml(item.value)}" role="option" aria-selected="${selectedAttr}">${escapeHtml(item.label)}</div>`;
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

function setListboxSelection(listboxNode, index) {
  const values = Array.isArray(listboxNode && listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
  if (!listboxNode || !values.length || index < 0 || index >= values.length) return false;
  const value = values[index];
  listboxNode.dataset.selectedValue = value;
  listboxNode.dataset.activeIndex = String(index);
  listboxNode.setAttribute("aria-activedescendant", listboxOptionId(listboxNode, index));
  listboxNode.querySelectorAll("[data-listbox-option-index]").forEach((optionNode) => {
    optionNode.setAttribute("aria-selected", optionNode.getAttribute("data-listbox-option-index") === String(index) ? "true" : "false");
  });
  const selectedNode = listboxNode.querySelector(`[data-listbox-option-index="${index}"]`);
  if (selectedNode && typeof selectedNode.scrollIntoView === "function") {
    selectedNode.scrollIntoView({ block: "nearest" });
  }
  listboxNode.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

function moveListboxSelection(listboxNode, direction) {
  const values = Array.isArray(listboxNode && listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
  if (!listboxNode || !values.length) return false;
  const currentIndex = Number(listboxNode.dataset.activeIndex);
  const nextIndex = currentIndex < 0
    ? (direction > 0 ? 0 : values.length - 1)
    : Math.max(0, Math.min(values.length - 1, currentIndex + direction));
  if (nextIndex === currentIndex) return false;
  return setListboxSelection(listboxNode, nextIndex);
}

function setListboxDisabled(listboxNode, disabled) {
  if (!listboxNode) return;
  listboxNode.setAttribute("aria-disabled", disabled ? "true" : "false");
  listboxNode.tabIndex = disabled ? -1 : 0;
}

function subfolderListOptions(folder, subfolders, config) {
  const parentFolder = normalizeText(folder);
  const subfolderConfig = config && config.subfolders ? config.subfolders : {};
  const prefix = normalizeText(subfolderConfig.prefix) || "⨽";
  const records = [
    {
      className: "sharedFilePicker__option--parent",
      label: parentFolder || normalizeText(subfolderConfig.parentFallbackLabel) || filePickerText(config, "folderLabel"),
      value: ""
    }
  ];
  (Array.isArray(subfolders) ? subfolders : []).forEach((subfolder) => {
    records.push({
      className: "sharedFilePicker__option--subfolder",
      label: `${prefix} ${subfolder}`,
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
    if (Number.isInteger(index)) setListboxSelection(listboxNode, index);
  });
  listboxNode.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveListboxSelection(listboxNode, 1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveListboxSelection(listboxNode, -1);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      setListboxSelection(listboxNode, 0);
      return;
    }
    if (event.key === "End") {
      const values = Array.isArray(listboxNode.filePickerValues) ? listboxNode.filePickerValues : [];
      event.preventDefault();
      setListboxSelection(listboxNode, values.length - 1);
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
    moveListboxSelection(listboxNode, event.deltaY > 0 ? 1 : -1);
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
  rootNode.innerHTML = renderBody(id, config);

  const initial = options.initialSelection || {};
  const selected = {
    scope: normalizeText(initial.scope || options.scope),
    folder: normalizeText(initial.folder || initial.project_folder),
    subfolder: normalizeText(initial.subfolder || initial.project_subfolder),
    filename: normalizeText(initial.filename || initial.project_filename)
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

      const requestedFilename = normalizeText(loadOptions.filename);
      if (requestedFilename && state.files.includes(requestedFilename)) {
        selected.filename = requestedFilename;
      } else if (loadOptions.autoSelectFirst) {
        selected.filename = state.files[0] || "";
      } else {
        selected.filename = "";
      }

      if (requestedFilename && !selected.filename) {
        setStatus("warning", filePickerText(config, "fileNotFound"));
      } else if (!loadOptions.keepStatus) {
        setStatus("", "");
      }

      renderListboxOptions(subfolderNode, subfolderListOptions(folder, state.subfolders, config), selected.subfolder);
      renderListboxOptions(fileNode, state.files, selected.filename);
      setListboxesDisabled(false);
      setPrimaryDisabled(primaryNode, !selected.filename);
    } catch (error) {
      state.files = [];
      renderListboxOptions(fileNode, [], "");
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
      setPrimaryDisabled(primaryNode, normalizeText(value) !== selected.folder || !selected.filename);
    },
    onCancel: () => {
      setPrimaryDisabled(primaryNode, !selected.filename);
    },
    onCommit: (folder) => selectFolder(folder, { autoSelectFirst: true }).catch((error) => {
      setStatus("error", normalizeText(error && error.message) || filePickerText(config, "filesFailed"));
    })
  });

  if (subfolderNode) {
    subfolderNode.addEventListener("change", () => {
      selected.subfolder = selectedListboxValue(subfolderNode);
      selected.filename = "";
      loadFilesForSelection({ autoSelectFirst: true }).catch((error) => {
        setStatus("error", normalizeText(error && error.message) || filePickerText(config, "filesFailed"));
      });
    });
    bindListbox(subfolderNode);
  }

  if (fileNode) {
    fileNode.addEventListener("change", () => {
      selected.filename = selectedListboxValue(fileNode);
      setPrimaryDisabled(primaryNode, !selected.filename);
    });
    fileNode.addEventListener("dblclick", () => {
      selected.filename = selectedListboxValue(fileNode);
      if (selected.filename && typeof options.onSubmit === "function") options.onSubmit();
    });
    bindListbox(fileNode, {
      onEnter() {
        if (selected.filename && typeof options.onSubmit === "function") options.onSubmit();
      }
    });
  }

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
    selected.subfolder = "";
    selected.filename = "";
    await loadFilesForSelection({
      filename: requestedSubfolder ? "" : requestedFilename,
      keepStatus: true
    });

    if (requestedSubfolder) {
      if (state.subfolders.includes(requestedSubfolder)) {
        selected.subfolder = requestedSubfolder;
        await loadFilesForSelection({ filename: requestedFilename });
      } else {
        selected.subfolder = "";
        selected.filename = "";
        renderListboxOptions(subfolderNode, subfolderListOptions(selected.folder, state.subfolders, config), "");
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
    if (!selected.filename) {
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
        filename: selected.filename
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
      return { ...selected };
    }
  };
}
