export const DOCS_IMPORT_DEFAULT_SOURCE_DIRECTORY = "data-sharing/import-staging";
export const DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY = "dotlineform-docs-import-source-directory";

function text(value) {
  return String(value == null ? "" : value).trim();
}

export function createDocsImportSourceSelection(options = {}) {
  if (typeof options.loadDirectory !== "function" || typeof options.loadCandidates !== "function") {
    throw new Error("Docs Import source selection configuration is incomplete.");
  }
  let storage = options.storage || null;
  try {
    storage = storage || window.localStorage;
  } catch (_error) {
    storage = null;
  }
  const project = typeof options.onDirectoryChange === "function"
    ? options.onDirectoryChange
    : () => {};
  let current = "";

  function storageValue(action, value = "") {
    if (!storage) return "";
    try {
      if (action === "read") return text(storage.getItem(DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY));
      if (action === "write") storage.setItem(DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY, value);
      else storage.removeItem(DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY);
    } catch (_error) {
      return "";
    }
    return value;
  }

  async function loadDirectory({ directory } = {}) {
    const requested = text(directory);
    if (!requested) throw new Error("Import source folder is required.");
    return options.loadDirectory({ directory: requested });
  }

  async function validate(directory) {
    const requested = text(directory);
    const payload = await loadDirectory({ directory: requested });
    if (text(payload && payload.current_directory) !== requested || payload.current_selectable !== true) {
      throw new Error("Import source folder was not accepted.");
    }
    return requested;
  }

  async function refresh(directory) {
    current = directory;
    project({ directory });
    return options.loadCandidates({ directory });
  }

  async function initialize() {
    const remembered = storageValue("read");
    let accepted;
    try {
      accepted = await validate(remembered || DOCS_IMPORT_DEFAULT_SOURCE_DIRECTORY);
    } catch (error) {
      if (!remembered) throw error;
      storageValue("remove");
      accepted = await validate(DOCS_IMPORT_DEFAULT_SOURCE_DIRECTORY);
    }
    await refresh(accepted);
    return accepted;
  }

  async function acceptDirectory({ directory } = {}) {
    const accepted = await validate(directory);
    current = accepted;
    project({ directory: accepted });
    storageValue("write", accepted);
    await options.loadCandidates({ directory: accepted });
    return accepted;
  }

  function chooseFolder(restoreFocus) {
    if (!current || typeof options.openFolderPicker !== "function") {
      return Promise.resolve(false);
    }
    return Promise.resolve(options.openFolderPicker({
      initialDirectory: current,
      loadDirectory,
      onSubmit: acceptDirectory,
      restoreFocus: restoreFocus || null
    }));
  }

  async function useImportStaging(restoreFocus) {
    const accepted = await validate(DOCS_IMPORT_DEFAULT_SOURCE_DIRECTORY);
    await refresh(accepted);
    storageValue("remove");
    if (restoreFocus && typeof restoreFocus.focus === "function") {
      restoreFocus.focus({ preventScroll: true });
    }
    return accepted;
  }

  return Object.freeze({
    chooseFolder,
    getDirectory: () => current,
    initialize,
    refresh: () => current ? options.loadCandidates({ directory: current }) : initialize(),
    useImportStaging
  });
}
