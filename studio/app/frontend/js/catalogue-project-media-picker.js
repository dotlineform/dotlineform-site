import {
  activateStudioModalFrame,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  normalizeText
} from "./catalogue-work-fields.js";
import {
  createFilePicker
} from "/shared/frontend/js/file-picker.js";

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

function setDraftField(state, fieldKey, value, options = {}) {
  if (!state.draft) state.draft = {};
  state.draft[fieldKey] = normalizeText(value);
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
  setDraftField(state, "project_folder", selection.project_folder || selection.folder, options);
  setDraftField(state, "project_subfolder", selection.project_subfolder || selection.subfolder || "", options);
  setDraftField(state, "project_filename", selection.project_filename || selection.filename || "", options);
}

function renderPickerBody() {
  return '<div data-role="catalogue-project-media-picker"></div>';
}

export async function openProjectMediaFileModal(state, options = {}) {
  const host = state.modalHost;
  if (!host || typeof options.loadProjectFiles !== "function" || typeof options.loadProjectFolders !== "function") return null;
  host.innerHTML = renderStudioModalFrame({
    hidden: false,
    modalRole: "studio-modal",
    backdropRole: "modal-cancel",
    title: pickerText(options, "project_media_modal_title", "select file"),
    size: "wide",
    bodyHtml: renderPickerBody(),
    statusHtml: '<p class="tagStudioForm__status tagStudioModal__status" data-role="modal-status" hidden></p>',
    actions: [
      { role: "modal-cancel", label: pickerText(options, "entry_modal_cancel_button", "cancel") },
      { role: "modal-primary", label: pickerText(options, "project_media_select_button", "ok"), primary: true, disabled: true }
    ]
  });

  let modalController = null;
  const pickerRoot = host.querySelector('[data-role="catalogue-project-media-picker"]');
  const primaryNode = host.querySelector('[data-role="modal-primary"]');
  const pickerController = createFilePicker(pickerRoot, {
    id: "catalogueProjectMediaFilePicker",
    scope: "projects",
    primaryNode,
    initialSelection: {
      folder: state.draft && state.draft.project_folder,
      subfolder: state.draft && state.draft.project_subfolder,
      filename: state.draft && state.draft.project_filename
    },
    text: (key, fallback, tokens) => {
      const mappedKey = key.replace(/^file_picker_/, "project_media_");
      return pickerText(options, mappedKey, fallback, tokens);
    },
    loadFolders: () => loadProjectFolders(state, options),
    loadFiles: (request) => options.loadProjectFiles({
      projectFolder: request.folder,
      projectSubfolder: request.subfolder,
      query: request.query || ""
    }),
    onSubmit: () => {
      if (modalController) modalController.submit();
    }
  });

  modalController = activateStudioModalFrame(host, {
    focusSelector: '[data-role="file-picker-folder-input"]',
    selectInitialFocus: true,
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
          project_folder: selection.folder,
          project_subfolder: selection.subfolder || "",
          project_filename: selection.filename
        }
      };
    }
  });

  const result = await modalController.promise;
  pickerController.destroy();
  return result;
}

export async function openProjectMediaPickerForCurrentDraft(state, options = {}) {
  const result = await openProjectMediaFileModal(state, options);
  if (result && result.confirmed) {
    applyProjectMediaSelection(state, result.selection, options);
  }
  return result;
}
