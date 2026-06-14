import {
  activateStudioModalFrame,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  normalizeText
} from "./catalogue-work-fields.js";
import {
  bindSearchList
} from "/shared/frontend/js/search-list.js";

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

function projectMediaState(state) {
  if (!state.projectMediaPicker) {
    state.projectMediaPicker = {
      folders: [],
      folderLoadPromise: null
    };
  }
  return state.projectMediaPicker;
}

async function loadProjectFolders(state, options = {}) {
  const picker = projectMediaState(state);
  if (picker.folderLoadPromise) return picker.folderLoadPromise;
  if (Array.isArray(picker.folders) && picker.folders.length) return picker.folders;
  if (!options || typeof options.loadProjectFolders !== "function") return [];
  picker.folderLoadPromise = options.loadProjectFolders("")
    .then((payload) => {
      const records = Array.isArray(payload && payload.project_folders) ? payload.project_folders : [];
      picker.folders = records
        .map((record) => normalizeText(record && record.project_folder))
        .filter(Boolean);
      return picker.folders;
    })
    .finally(() => {
      picker.folderLoadPromise = null;
    });
  return picker.folderLoadPromise;
}

function projectFolderMatches(folders, query) {
  const q = normalizeText(query).toLowerCase();
  if (!q) return folders.slice(0, 12);
  return folders
    .filter((folder) => folder.toLowerCase().startsWith(q))
    .slice(0, 12);
}

function setDraftField(state, fieldKey, value, options = {}) {
  if (!state.draft) state.draft = {};
  state.draft[fieldKey] = normalizeText(value);
  const node = state.fieldNodes && state.fieldNodes.get ? state.fieldNodes.get(fieldKey) : null;
  if (node && "value" in node) node.value = state.draft[fieldKey];
  if (state.mode === "bulk" && state.bulkTouchedFields) state.bulkTouchedFields.add(fieldKey);
  if (typeof options.onFieldInput === "function") {
    options.onFieldInput(fieldKey);
  } else if (typeof options.onStateChange === "function") {
    options.onStateChange();
  }
}

function applyProjectMediaSelection(state, selection, options = {}) {
  setDraftField(state, "project_folder", selection.project_folder, options);
  setDraftField(state, "project_subfolder", selection.project_subfolder || "", options);
  setDraftField(state, "project_filename", selection.project_filename || selection.filename || "", options);
}

async function chooseProjectFolder(state, projectFolder, options = {}) {
  const picker = projectMediaState(state);
  const folder = normalizeText(projectFolder);
  if (!folder) return;
  setDraftField(state, "project_folder", folder, options);
  setDraftField(state, "project_subfolder", "", options);
  setDraftField(state, "project_filename", "", options);
  if (picker.popupNode) picker.popupNode.hidden = true;
  if (state.mode === "bulk" || options.autoOpenFileModal === false) return;
  const result = await openProjectMediaFileModal(state, {
    ...options,
    projectFolder: folder,
    projectSubfolder: ""
  });
  if (result && result.confirmed) {
    applyProjectMediaSelection(state, result.selection, options);
  }
}

export function bindProjectFolderSearch(state, inputNode, popupNode, options = {}) {
  const picker = projectMediaState(state);
  picker.inputNode = inputNode;
  picker.popupNode = popupNode;
  if (!inputNode || !popupNode) return;
  picker.folderSearchController = bindSearchList(inputNode, popupNode, {
    id: "catalogueProjectFolderPopup",
    maxOptions: 12,
    classNames: {
      option: "catalogueProjectMediaPicker__folderOption"
    },
    loadOptions: () => loadProjectFolders(state, options),
    filterOptions: projectFolderMatches,
    getOptionValue: (folder) => folder,
    renderOption: (folder) => `<span class="sharedSearchList__optionText catalogueProjectMediaPicker__folderText">${escapeHtml(folder)}</span>`,
    renderNoResults: () => `<p class="sharedSearchList__empty tagStudioForm__meta">${escapeHtml(pickerText(options, "project_folder_no_match", "No matching project folders."))}</p>`,
    renderError: (error) => `<p class="sharedSearchList__empty tagStudioForm__meta">${escapeHtml(normalizeText(error && error.message) || pickerText(options, "project_folder_load_failed", "Project folders could not be loaded."))}</p>`,
    onCommit: (folder) => chooseProjectFolder(state, folder, options).catch((error) => {
      console.warn("catalogue_project_media_picker: failed to choose project folder", error);
    })
  });
}

function renderFileModalBody(options = {}) {
  return `
    <div class="catalogueProjectMediaPicker">
      <label class="tagStudioForm__field catalogueProjectMediaPicker__filterField" for="catalogueProjectMediaFilter">
        <span class="tagStudioForm__label">${escapeHtml(pickerText(options, "project_media_filter_label", "filter"))}</span>
        <input class="tagStudio__input" id="catalogueProjectMediaFilter" data-role="project-media-filter" type="text" autocomplete="off" spellcheck="false">
      </label>
      <label class="tagStudioForm__field catalogueProjectMediaPicker__subfolderField" for="catalogueProjectMediaSubfolder">
        <span class="tagStudioForm__label">${escapeHtml(pickerText(options, "project_media_subfolder_label", "subfolder"))}</span>
        <select class="tagStudio__input" id="catalogueProjectMediaSubfolder" data-role="project-media-subfolder"></select>
      </label>
      <div class="catalogueProjectMediaPicker__files" data-role="project-media-files"></div>
    </div>
  `;
}

function renderSubfolderOptions(selectNode, subfolders, selectedSubfolder, options = {}) {
  const selected = normalizeText(selectedSubfolder);
  const records = Array.isArray(subfolders) ? subfolders : [];
  selectNode.innerHTML = [
    `<option value="">${escapeHtml(pickerText(options, "project_media_no_subfolder", "project folder"))}</option>`,
    ...records.map((record) => {
      const value = normalizeText(record && record.project_subfolder);
      const selectedAttr = value === selected ? " selected" : "";
      return `<option value="${escapeHtml(value)}"${selectedAttr}>${escapeHtml(value)}</option>`;
    })
  ].join("");
  selectNode.hidden = records.length === 0;
  const field = selectNode.closest(".catalogueProjectMediaPicker__subfolderField");
  if (field) field.hidden = records.length === 0;
}

function renderFileRows(filesNode, files, selected, options = {}) {
  const records = Array.isArray(files) ? files : [];
  const selectedFile = normalizeText(selected);
  if (!records.length) {
    filesNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(pickerText(options, "project_media_files_empty", "No image files found."))}</p>`;
    return;
  }
  filesNode.innerHTML = records.map((record) => {
    const filename = normalizeText(record && record.filename);
    const selectedAttr = filename === selectedFile ? " aria-pressed=\"true\"" : "";
    return `
      <button type="button" class="tagStudioSuggest__workButton catalogueProjectMediaPicker__fileOption" data-project-file="${escapeHtml(filename)}"${selectedAttr}>
        <span class="tagStudioSuggest__workTitle">${escapeHtml(filename)}</span>
      </button>
    `;
  }).join("");
}

export async function openProjectMediaFileModal(state, options = {}) {
  const projectFolder = normalizeText(options.projectFolder || state.draft && state.draft.project_folder);
  if (!projectFolder) return null;
  const host = state.modalHost;
  if (!host || typeof options.loadProjectFiles !== "function") return null;
  host.innerHTML = renderStudioModalFrame({
    hidden: false,
    modalRole: "studio-modal",
    backdropRole: "modal-cancel",
    title: pickerText(options, "project_media_modal_title", "Choose image"),
    meta: projectFolder,
    size: "wide",
    bodyHtml: renderFileModalBody(options),
    statusHtml: '<p class="tagStudioForm__status tagStudioModal__status" data-role="modal-status" hidden></p>',
    actions: [
      { role: "modal-cancel", label: pickerText(options, "entry_modal_cancel_button", "Cancel") },
      { role: "modal-primary", label: pickerText(options, "project_media_select_button", "Select"), primary: true, disabled: true }
    ]
  });

  let selectedFilename = "";
  let selectedSubfolder = normalizeText(options.projectSubfolder || state.draft && state.draft.project_subfolder);
  const filterNode = host.querySelector('[data-role="project-media-filter"]');
  const subfolderNode = host.querySelector('[data-role="project-media-subfolder"]');
  const filesNode = host.querySelector('[data-role="project-media-files"]');
  const primaryNode = host.querySelector('[data-role="modal-primary"]');
  const controller = activateStudioModalFrame(host, {
    focusSelector: '[data-role="project-media-filter"]',
    submitOnEnter: false,
    async onSubmit(api) {
      if (!selectedFilename) {
        api.setStatus("error", pickerText(options, "project_media_select_required", "Select an image file."));
        return false;
      }
      return {
        selection: {
          project_folder: projectFolder,
          project_subfolder: selectedSubfolder,
          project_filename: selectedFilename
        }
      };
    }
  });

  async function loadFiles() {
    try {
      if (primaryNode) primaryNode.disabled = true;
      const payload = await options.loadProjectFiles({
        projectFolder,
        projectSubfolder: selectedSubfolder,
        query: filterNode ? filterNode.value : ""
      });
      if (subfolderNode) {
        renderSubfolderOptions(subfolderNode, payload.subfolders, selectedSubfolder, options);
      }
      renderFileRows(filesNode, payload.files, selectedFilename, options);
      if (!selectedSubfolder && Array.isArray(payload.files) && payload.files.length === 0 && Array.isArray(payload.subfolders) && payload.subfolders.length === 1 && !normalizeText(filterNode && filterNode.value)) {
        selectedSubfolder = normalizeText(payload.subfolders[0] && payload.subfolders[0].project_subfolder);
        await loadFiles();
        return;
      }
      if (primaryNode) primaryNode.disabled = !selectedFilename;
    } catch (error) {
      filesNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(normalizeText(error && error.message) || pickerText(options, "project_media_files_failed", "Image files could not be loaded."))}</p>`;
    }
  }

  if (filterNode) {
    filterNode.addEventListener("input", () => {
      selectedFilename = "";
      loadFiles();
    });
    filterNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      const first = filesNode.querySelector("[data-project-file]");
      if (!first) return;
      event.preventDefault();
      first.click();
    });
  }
  if (subfolderNode) {
    subfolderNode.addEventListener("change", () => {
      selectedSubfolder = normalizeText(subfolderNode.value);
      selectedFilename = "";
      loadFiles();
    });
  }
  if (filesNode) {
    filesNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-project-file]") : null;
      if (!button) return;
      selectedFilename = normalizeText(button.getAttribute("data-project-file"));
      renderFileRows(filesNode, Array.from(filesNode.querySelectorAll("[data-project-file]")).map((node) => ({
        filename: node.getAttribute("data-project-file")
      })), selectedFilename, options);
      if (primaryNode) primaryNode.disabled = !selectedFilename;
    });
    filesNode.addEventListener("dblclick", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-project-file]") : null;
      if (!button) return;
      selectedFilename = normalizeText(button.getAttribute("data-project-file"));
      controller.submit();
    });
  }

  await loadFiles();
  return controller.promise;
}

export async function openProjectMediaPickerForCurrentDraft(state, options = {}) {
  const result = await openProjectMediaFileModal(state, options);
  if (result && result.confirmed) {
    applyProjectMediaSelection(state, result.selection, options);
  }
  return result;
}
