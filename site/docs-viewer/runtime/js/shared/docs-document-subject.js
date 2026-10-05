export const AUTHORING_SUBJECT_FIELDS = Object.freeze([
  "folder_path",
  "work_id"
]);

function hasSourceBoundaryWhitespace(value) {
  // Match Python str.strip(): U+0085 is whitespace; U+FEFF is not.
  return [value.charCodeAt(0), value.charCodeAt(value.length - 1)].some((code) =>
    code >= 0x09 && code <= 0x0d || code >= 0x1c && code <= 0x20
    || code >= 0x2000 && code <= 0x200a
    || [0x85, 0xa0, 0x1680, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000].includes(code));
}

/**
 * Classify a record's optional scalar Subject without registry or filesystem reads.
 * Omission means None for management data; public Context omission may instead
 * select an authored thumbnail. Present invalid values and retired objects fail.
 * @param {Object} record Generated row, committed metadata or source-context response.
 * @param {Object} [options]
 * @param {boolean} [options.folderSupported=false] Exact owner's Folder capability.
 * @param {string} [options.errorMessage] Caller-owned boundary failure message.
 * @returns {{kind: string, key: string}} Ephemeral typed input for a consumer.
 */
export function classifyDocsDocumentSubject(record, options = {}) {
  const message = options.errorMessage || "Document subject metadata is invalid.";
  if (!record || typeof record !== "object" || Array.isArray(record) || Object.hasOwn(record, "authoring_subject")) {
    throw new Error(message);
  }
  if (!Object.hasOwn(record, "subject")) return Object.freeze({ kind: "none", key: "" });
  const value = record.subject;
  if (typeof value !== "string" || !value || hasSourceBoundaryWhitespace(value)) throw new Error(message);
  if (/^[0-9]{5}$/.test(value)) return Object.freeze({ kind: "work", key: value });
  if (options.folderSupported !== true || value.startsWith("/") || value.includes("\\")
    || Array.from(value).some((character) => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127)
    || /^[A-Za-z][A-Za-z0-9+.-]*:/.test(value) || value.toLowerCase().includes("dlf-local:")
    || value.split("/").some((part) => !part || part === "." || part === "..")) {
    throw new Error(message);
  }
  return Object.freeze({ kind: "folder", key: value });
}
