export const FILE_PICKER_DEFAULT_CONFIG = Object.freeze({
  search: Object.freeze({
    maxFolderResults: 12,
    openFolderSearchOnFocus: false
  }),
  subfolders: Object.freeze({
    parentFallbackLabel: "folder",
    prefix: "⨽"
  }),
  text: Object.freeze({
    modalTitle: "select file",
    cancelButton: "cancel",
    confirmButton: "ok",
    folderLabel: "folder",
    subfolderLabel: "subfolders",
    filesLabel: "files",
    noFolderMatch: "No matching folders.",
    foldersFailed: "Folders could not be loaded.",
    filesFailed: "Files could not be loaded.",
    fileNotFound: "file not found",
    folderRequired: "Select a folder.",
    fileRequired: "Select a file."
  })
});

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function mergeConfig(base, overrides) {
  if (!isPlainObject(overrides)) return { ...base };
  const merged = { ...base };
  Object.entries(overrides).forEach(([key, value]) => {
    if (isPlainObject(value) && isPlainObject(base[key])) {
      merged[key] = mergeConfig(base[key], value);
      return;
    }
    if (value !== undefined) merged[key] = value;
  });
  return merged;
}

export function createFilePickerConfig(overrides = {}) {
  return mergeConfig(FILE_PICKER_DEFAULT_CONFIG, overrides);
}

export function filePickerText(config, key, tokens = null) {
  const text = isPlainObject(config && config.text) ? config.text : FILE_PICKER_DEFAULT_CONFIG.text;
  const fallback = FILE_PICKER_DEFAULT_CONFIG.text[key] || "";
  const value = text[key] == null ? fallback : String(text[key]);
  if (!tokens) return value;
  return Object.entries(tokens).reduce((result, [token, tokenValue]) => {
    return result.replace(new RegExp(`\\{${token}\\}`, "g"), tokenValue == null ? "" : String(tokenValue));
  }, value);
}
