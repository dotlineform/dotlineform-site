import {
  bindSearchList
} from "/shared/frontend/js/search-list.js";

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

function pickerText(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((text, [token, value]) => {
    return text.replace(new RegExp(`\\{${token}\\}`, "g"), value == null ? "" : String(value));
  }, fallback);
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

function renderBody(id, options = {}) {
  const folderLabel = pickerText(options, "file_picker_folder_label", "folder");
  const subfolderLabel = pickerText(options, "file_picker_subfolder_label", "subfolders");
  const fileLabel = pickerText(options, "file_picker_files_label", "files");
  return `
    <div class="sharedFilePicker" data-role="file-picker">
      <label class="sharedFilePicker__folderField" for="${escapeHtml(id)}-folder">
        <span class="sharedFilePicker__label">${escapeHtml(folderLabel)}</span>
        <span class="sharedSearchList__control sharedFilePicker__folderControl">
          <input class="sharedFilePicker__folderInput" id="${escapeHtml(id)}-folder" data-role="file-picker-folder-input" type="text" autocomplete="off" spellcheck="false">
          <span class="sharedFilePicker__folderPopup" data-role="file-picker-folder-popup" hidden></span>
        </span>
      </label>
      <p class="sharedFilePicker__status" data-role="file-picker-status" hidden></p>
      <div class="sharedFilePicker__listboxes">
        <label class="sharedFilePicker__listboxField" for="${escapeHtml(id)}-subfolders">
          <span class="sharedFilePicker__label">${escapeHtml(subfolderLabel)}</span>
          <select class="sharedFilePicker__listbox" id="${escapeHtml(id)}-subfolders" data-role="file-picker-subfolder-list" size="12" aria-label="${escapeHtml(subfolderLabel)}" disabled></select>
        </label>
        <label class="sharedFilePicker__listboxField" for="${escapeHtml(id)}-files">
          <span class="sharedFilePicker__label sharedFilePicker__labelSpacer" aria-hidden="true"></span>
          <select class="sharedFilePicker__listbox" id="${escapeHtml(id)}-files" data-role="file-picker-file-list" size="12" aria-label="${escapeHtml(fileLabel)}" disabled></select>
        </label>
      </div>
    </div>
  `;
}

function renderSelectOptions(selectNode, values, selectedValue) {
  const selected = normalizeText(selectedValue);
  selectNode.innerHTML = values.map((value) => {
    const selectedAttr = value === selected ? " selected" : "";
    return `<option value="${escapeHtml(value)}"${selectedAttr}>${escapeHtml(value)}</option>`;
  }).join("");
  if (!selected || !values.includes(selected)) selectNode.selectedIndex = -1;
}

function selectedListboxValue(selectNode) {
  return selectNode && selectNode.selectedIndex >= 0 ? normalizeText(selectNode.value) : "";
}

function moveListboxSelection(selectNode, direction) {
  if (!selectNode || !selectNode.options.length) return false;
  const currentIndex = selectNode.selectedIndex;
  const nextIndex = currentIndex < 0
    ? (direction > 0 ? 0 : selectNode.options.length - 1)
    : Math.max(0, Math.min(selectNode.options.length - 1, currentIndex + direction));
  if (nextIndex === currentIndex) return false;
  selectNode.selectedIndex = nextIndex;
  if (selectNode.options[nextIndex] && typeof selectNode.options[nextIndex].scrollIntoView === "function") {
    selectNode.options[nextIndex].scrollIntoView({ block: "nearest" });
  }
  selectNode.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

function bindListboxWheel(selectNode) {
  if (!selectNode) return;
  selectNode.addEventListener("wheel", (event) => {
    if (!event.deltaY) return;
    event.preventDefault();
    event.stopPropagation();
    moveListboxSelection(selectNode, event.deltaY > 0 ? 1 : -1);
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
  rootNode.innerHTML = renderBody(id, options);

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
    if (subfolderNode) subfolderNode.disabled = Boolean(disabled);
    if (fileNode) fileNode.disabled = Boolean(disabled);
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
      renderSelectOptions(subfolderNode, [], "");
      renderSelectOptions(fileNode, [], "");
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
        setStatus("warning", pickerText(options, "file_picker_file_not_found", "file not found"));
      } else if (!loadOptions.keepStatus) {
        setStatus("", "");
      }

      renderSelectOptions(subfolderNode, state.subfolders, selected.subfolder);
      renderSelectOptions(fileNode, state.files, selected.filename);
      setListboxesDisabled(false);
      setPrimaryDisabled(primaryNode, !selected.filename);
    } catch (error) {
      state.files = [];
      renderSelectOptions(fileNode, [], "");
      if (fileNode) fileNode.disabled = true;
      if (subfolderNode) subfolderNode.disabled = false;
      setPrimaryDisabled(primaryNode, true);
      setStatus("error", normalizeText(error && error.message) || pickerText(options, "file_picker_files_failed", "Files could not be loaded."));
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
    maxOptions: 12,
    classNames: {
      option: "sharedFilePicker__folderOption"
    },
    loadOptions: loadFolders,
    filterOptions: prefixMatches,
    getOptionValue: (folder) => folder,
    renderOption: (folder) => `<span class="sharedSearchList__optionText">${escapeHtml(folder)}</span>`,
    renderNoResults: () => `<p class="sharedSearchList__empty">${escapeHtml(pickerText(options, "file_picker_no_folder_match", "No matching folders."))}</p>`,
    renderError: (error) => `<p class="sharedSearchList__empty">${escapeHtml(normalizeText(error && error.message) || pickerText(options, "file_picker_folders_failed", "Folders could not be loaded."))}</p>`,
    onTransientInput: ({ value }) => {
      setPrimaryDisabled(primaryNode, normalizeText(value) !== selected.folder || !selected.filename);
    },
    onCancel: () => {
      setPrimaryDisabled(primaryNode, !selected.filename);
    },
    onCommit: (folder) => selectFolder(folder, { autoSelectFirst: true }).catch((error) => {
      setStatus("error", normalizeText(error && error.message) || pickerText(options, "file_picker_files_failed", "Files could not be loaded."));
    })
  });

  if (subfolderNode) {
    subfolderNode.addEventListener("change", () => {
      selected.subfolder = selectedListboxValue(subfolderNode);
      selected.filename = "";
      loadFilesForSelection({ autoSelectFirst: true }).catch((error) => {
        setStatus("error", normalizeText(error && error.message) || pickerText(options, "file_picker_files_failed", "Files could not be loaded."));
      });
    });
    bindListboxWheel(subfolderNode);
  }

  if (fileNode) {
    fileNode.addEventListener("change", () => {
      selected.filename = selectedListboxValue(fileNode);
      setPrimaryDisabled(primaryNode, !selected.filename);
    });
    fileNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || !selected.filename || typeof options.onSubmit !== "function") return;
      event.preventDefault();
      options.onSubmit();
    });
    fileNode.addEventListener("dblclick", () => {
      selected.filename = selectedListboxValue(fileNode);
      if (selected.filename && typeof options.onSubmit === "function") options.onSubmit();
    });
    bindListboxWheel(fileNode);
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
      setStatus("warning", pickerText(options, "file_picker_file_not_found", "file not found"));
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
        renderSelectOptions(subfolderNode, state.subfolders, "");
        setPrimaryDisabled(primaryNode, true);
        setStatus("warning", pickerText(options, "file_picker_file_not_found", "file not found"));
      }
    }
  }

  function submit() {
    const folderText = normalizeText(folderInput && folderInput.value);
    if (!selected.folder || folderText !== selected.folder) {
      return {
        ok: false,
        statusKind: "error",
        status: pickerText(options, "file_picker_folder_required", "Select a folder.")
      };
    }
    if (!selected.filename) {
      return {
        ok: false,
        statusKind: "error",
        status: pickerText(options, "file_picker_file_required", "Select a file.")
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
    setStatus("error", normalizeText(error && error.message) || pickerText(options, "file_picker_folders_failed", "Folders could not be loaded."));
  });

  return {
    ready,
    submit,
    focus() {
      if (folderInput) folderInput.focus();
    },
    destroy() {
      if (searchController && typeof searchController.destroy === "function") searchController.destroy();
    },
    getSelection() {
      return { ...selected };
    }
  };
}
