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

function renderFileModalBody(projectFolder, options = {}) {
  return `
    <div class="catalogueProjectMediaPicker">
      <p class="catalogueProjectMediaPicker__projectFolder">
        <span>${escapeHtml(pickerText(options, "project_media_project_folder_label", "project folder"))}</span>
        <strong>${escapeHtml(projectFolder)}</strong>
      </p>
      <div class="catalogueProjectMediaPicker__listboxes">
        <label class="catalogueProjectMediaPicker__listboxField" for="catalogueProjectMediaSubfolders">
          <span class="tagStudioForm__label">${escapeHtml(pickerText(options, "project_media_subfolder_label", "subfolders"))}</span>
          <select class="catalogueProjectMediaPicker__listbox" id="catalogueProjectMediaSubfolders" data-role="project-media-subfolder-list" size="12" aria-label="${escapeHtml(pickerText(options, "project_media_subfolder_label", "subfolders"))}"></select>
        </label>
        <label class="catalogueProjectMediaPicker__listboxField" for="catalogueProjectMediaFiles">
          <span class="tagStudioForm__label catalogueProjectMediaPicker__listboxLabelSpacer" aria-hidden="true"></span>
          <select class="catalogueProjectMediaPicker__listbox" id="catalogueProjectMediaFiles" data-role="project-media-file-list" size="12" aria-label="${escapeHtml(pickerText(options, "project_media_files_label", "files in folder/subfolder"))}"></select>
        </label>
      </div>
    </div>
  `;
}

function renderSubfolderOptions(selectNode, subfolders, selectedSubfolder) {
  const selected = normalizeText(selectedSubfolder);
  const records = Array.isArray(subfolders) ? subfolders : [];
  selectNode.innerHTML = records.map((record) => {
    const value = normalizeText(record && record.project_subfolder);
    const selectedAttr = value === selected ? " selected" : "";
    return `<option value="${escapeHtml(value)}"${selectedAttr}>${escapeHtml(value)}</option>`;
  }).join("");
  if (!selected) selectNode.selectedIndex = -1;
}

function renderFileOptions(selectNode, files, selected) {
  const records = Array.isArray(files) ? files : [];
  const selectedFile = normalizeText(selected);
  selectNode.innerHTML = records.map((record) => {
    const filename = normalizeText(record && record.filename);
    const selectedAttr = filename === selectedFile ? " selected" : "";
    return `<option value="${escapeHtml(filename)}"${selectedAttr}>${escapeHtml(filename)}</option>`;
  }).join("");
  if (!records.length) selectNode.selectedIndex = -1;
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

export async function openProjectMediaFileModal(state, options = {}) {
  const projectFolder = normalizeText(options.projectFolder || state.draft && state.draft.project_folder);
  if (!projectFolder) return null;
  const host = state.modalHost;
  if (!host || typeof options.loadProjectFiles !== "function") return null;
  host.innerHTML = renderStudioModalFrame({
    hidden: false,
    modalRole: "studio-modal",
    backdropRole: "modal-cancel",
    title: pickerText(options, "project_media_modal_title", "select file"),
    size: "wide",
    bodyHtml: renderFileModalBody(projectFolder, options),
    statusHtml: '<p class="tagStudioForm__status tagStudioModal__status" data-role="modal-status" hidden></p>',
    actions: [
      { role: "modal-cancel", label: pickerText(options, "entry_modal_cancel_button", "cancel") },
      { role: "modal-primary", label: pickerText(options, "project_media_select_button", "ok"), primary: true, disabled: true }
    ]
  });

  let selectedFilename = "";
  let selectedSubfolder = "";
  const subfolderNode = host.querySelector('[data-role="project-media-subfolder-list"]');
  const filesNode = host.querySelector('[data-role="project-media-file-list"]');
  const primaryNode = host.querySelector('[data-role="modal-primary"]');
  const controller = activateStudioModalFrame(host, {
    focusSelector: '[data-role="project-media-subfolder-list"]',
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
        query: ""
      });
      if (subfolderNode) {
        renderSubfolderOptions(subfolderNode, payload.subfolders, selectedSubfolder);
      }
      const fileRecords = Array.isArray(payload.files) ? payload.files : [];
      const draftFilename = normalizeText(state.draft && state.draft.project_filename);
      const fileNames = fileRecords.map((record) => normalizeText(record && record.filename)).filter(Boolean);
      if (!fileNames.includes(selectedFilename)) {
        selectedFilename = fileNames.includes(draftFilename) ? draftFilename : fileNames[0] || "";
      }
      renderFileOptions(filesNode, fileRecords, selectedFilename);
      if (primaryNode) primaryNode.disabled = !selectedFilename;
    } catch (error) {
      if (filesNode) {
        filesNode.innerHTML = "";
        filesNode.setAttribute("aria-label", normalizeText(error && error.message) || pickerText(options, "project_media_files_failed", "Image files could not be loaded."));
      }
    }
  }

  if (subfolderNode) {
    subfolderNode.addEventListener("change", () => {
      selectedSubfolder = selectedListboxValue(subfolderNode);
      selectedFilename = "";
      loadFiles();
    });
    bindListboxWheel(subfolderNode);
  }
  if (filesNode) {
    filesNode.addEventListener("change", () => {
      selectedFilename = selectedListboxValue(filesNode);
      if (primaryNode) primaryNode.disabled = !selectedFilename;
    });
    filesNode.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || !selectedFilename) return;
      event.preventDefault();
      controller.submit();
    });
    filesNode.addEventListener("dblclick", () => {
      selectedFilename = selectedListboxValue(filesNode);
      if (selectedFilename) controller.submit();
    });
    bindListboxWheel(filesNode);
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
