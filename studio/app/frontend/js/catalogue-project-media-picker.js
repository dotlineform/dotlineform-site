import {
  activateStudioModalFrame,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  normalizeText
} from "./catalogue-work-fields.js";
import {
  createFilePicker,
  createFilePickerConfig,
  filePickerText
} from "/shared/frontend/js/file-picker.js";

function projectMediaState(state) {
  if (!state.projectMediaPicker) {
    state.projectMediaPicker = {
      folders: [],
      folderLoadPromise: null,
      mediaSourceId: ""
    };
  }
  return state.projectMediaPicker;
}

function selectedMediaSourceId(state, options = {}) {
  if (typeof options.getMediaSourceId === "function") {
    return normalizeText(options.getMediaSourceId());
  }
  return normalizeText(options.mediaSourceId || (state.draft && state.draft.media_source_id));
}

export function resetProjectMediaFolders(state) {
  const picker = projectMediaState(state);
  picker.folders = [];
  picker.folderLoadPromise = null;
  picker.mediaSourceId = "";
}

async function loadProjectFolders(state, options = {}) {
  const picker = projectMediaState(state);
  const mediaSourceId = selectedMediaSourceId(state, options);
  if (picker.mediaSourceId !== mediaSourceId) {
    picker.folders = [];
    picker.folderLoadPromise = null;
    picker.mediaSourceId = mediaSourceId;
  }
  if (picker.folderLoadPromise) return picker.folderLoadPromise;
  if (Array.isArray(picker.folders) && picker.folders.length) return picker.folders;
  if (!options || typeof options.loadProjectFolders !== "function") return [];
  const loadPromise = options.loadProjectFolders(mediaSourceId, "")
    .then((payload) => {
      const records = Array.isArray(payload && payload.project_folders) ? payload.project_folders : [];
      const folders = records
        .map(record => record.project_folder)
        .filter(Boolean);
      if (picker.mediaSourceId === mediaSourceId) picker.folders = folders;
      return folders;
    })
    .finally(() => {
      if (picker.folderLoadPromise === loadPromise) picker.folderLoadPromise = null;
    });
  picker.folderLoadPromise = loadPromise;
  return loadPromise;
}

function setDraftField(state, fieldKey, value, options = {}) {
  if (!state.draft) state.draft = {};
  state.draft[fieldKey] = fieldKey.startsWith("project_") ? value || "" : normalizeText(value);
  const node = state.fieldNodes && state.fieldNodes.get ? state.fieldNodes.get(fieldKey) : null;
  if (node && "value" in node) node.value = state.draft[fieldKey];
  if (node && node.dataset && node.dataset.displayTarget) {
    const displayNode = node.ownerDocument.getElementById(node.dataset.displayTarget);
    if (displayNode) displayNode.textContent = state.draft[fieldKey] || "—";
  }
  if (state.mode === "bulk" && state.bulkTouchedFields) state.bulkTouchedFields.add(fieldKey);
  if (typeof options.onFieldInput === "function") {
    options.onFieldInput(fieldKey);
  } else if (typeof options.onStateChange === "function") {
    options.onStateChange();
  }
}

function applyProjectMediaSelection(state, selection, options = {}) {
  state.pendingWorkBatch = null;
  state.regenerateImage = true;
  if (state.mode === "new" && !state.draft.work_id) {
    state.draft.work_id = state.nextSuggestedWorkId;
    state.searchNode.value = state.draft.work_id;
  }
  setDraftField(state, "project_folder", selection.project_folder, options);
  setDraftField(state, "project_subfolder", selection.project_subfolder, options);
  setDraftField(state, "project_filename", selection.project_filename, options);
}

function renderPickerBody() {
  return '<div data-role="catalogue-project-media-picker"></div>';
}

function createProjectMediaPickerConfig(overrides = {}) {
  return createFilePickerConfig({
    ...overrides,
    search: {
      ...(overrides && overrides.search ? overrides.search : {}),
      openFolderSearchOnFocus: true
    }
  });
}

/** Return confined source identities and, in folder mode, all loaded filenames. */
export async function openProjectMediaModal(state, options = {}) {
  const host = state.modalHost;
  if (!host || typeof options.loadProjectFiles !== "function" || typeof options.loadProjectFolders !== "function") return null;
  const pickerConfig = createProjectMediaPickerConfig(options.filePickerConfig);
  const mediaSourceId = selectedMediaSourceId(state, options);
  const folderMode = options.selectionMode === "folder";
  host.innerHTML = renderStudioModalFrame({
    hidden: false,
    modalRole: "studio-modal",
    backdropRole: "modal-cancel",
    title: filePickerText(pickerConfig, folderMode ? "folderModalTitle" : "modalTitle"),
    size: "wide",
    bodyHtml: renderPickerBody(),
    statusHtml: '<p class="studioForm__status studioModal__status" data-role="modal-status" hidden></p>',
    actions: [
      { role: "modal-cancel", label: filePickerText(pickerConfig, "cancelButton") },
      { role: "modal-primary", label: filePickerText(pickerConfig, "confirmButton"), primary: true, disabled: true }
    ]
  });

  let modalController = null;
  const pickerRoot = host.querySelector('[data-role="catalogue-project-media-picker"]');
  const primaryNode = host.querySelector('[data-role="modal-primary"]');
  const pickerController = createFilePicker(pickerRoot, {
    id: "catalogueProjectMediaFilePicker",
    scope: mediaSourceId,
    primaryNode,
    config: pickerConfig,
    selectionMode: folderMode ? "folder" : "single",
    requireSubfolder: folderMode,
    initialSelection: {
      folder: state.draft && state.draft.project_folder,
      subfolder: state.draft && state.draft.project_subfolder,
      filename: state.draft && state.draft.project_filename
    },
    loadFolders: () => loadProjectFolders(state, options),
    loadFiles: async request => {
      const payload = await options.loadProjectFiles({
        mediaSourceId,
        projectFolder: request.folder,
        projectSubfolder: request.subfolder,
        query: ""
      });
      return {
        subfolders: payload.subfolders.map(record => ({ subfolder: record.project_subfolder })),
        files: payload.files
      };
    },
    onSubmit: () => {
      if (modalController) modalController.submit();
    }
  });

  modalController = activateStudioModalFrame(host, {
    focusSelector: '[role="dialog"]',
    submitOnEnter: false,
    async onSubmit(api) {
      await pickerController.ready;
      const result = pickerController.submit();
      if (result && result.ok === false) {
        if ("status" in result) api.setStatus(result.statusKind || "error", result.status || "");
        return false;
      }
      const selection = result.selection || {};
      return {
        selection: {
          media_source_id: selection.scope,
          project_folder: selection.folder,
          project_subfolder: selection.subfolder || "",
          project_filename: selection.filename,
          filenames: selection.filenames
        }
      };
    }
  });
  pickerController.ready.then(() => {
    if (host.querySelector('[data-role="studio-modal"]')) pickerController.focusPreferred();
  });

  const result = await modalController.promise;
  pickerController.destroy();
  return result;
}

export async function openProjectMediaPickerForCurrentDraft(state, options = {}) {
  const result = await openProjectMediaModal(state, options);
  if (result && result.confirmed) {
    applyProjectMediaSelection(state, result.selection, options);
  }
  return result;
}

/** Confirm an unsaved batch; Save alone persists it and completes local media. */
export async function openProjectMediaFolderForCurrentDraft(state, options = {}) {
  if (state.mode !== "new") return null;
  const result = await openProjectMediaModal(state, { ...options, selectionMode: "folder" });
  if (!result?.confirmed) return result;
  const selection = result.selection;
  state.pendingWorkBatch = {
    media_source_id: selection.media_source_id,
    project_folder: selection.project_folder,
    project_subfolder: selection.project_subfolder,
    filenames: selection.filenames.slice()
  };
  state.regenerateImage = false;
  state.draft.work_id = "";
  state.searchNode.value = "";
  setDraftField(state, "title", "", options);
  setDraftField(state, "project_folder", selection.project_folder, options);
  setDraftField(state, "project_subfolder", selection.project_subfolder, options);
  setDraftField(state, "project_filename", "", options);
  return result;
}
