export const AUTHORING_SUBJECT_FIELDS = Object.freeze([
  "folder_path",
  "work_id",
  "series_id"
]);

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function invalidSubject(message) {
  throw new Error(message || "Authoring subject metadata is invalid.");
}

export function normalizeDocsViewerAuthoringSubject(value, options = {}) {
  var message = cleanString(options.errorMessage) || "Authoring subject metadata is invalid.";
  var subject = value;
  if (!subject || typeof subject !== "object" || Array.isArray(subject)) {
    invalidSubject(message);
  }
  var keys = Object.keys(subject).sort().join(",");
  var kind = cleanString(subject.kind);
  var key = subject.key;
  if (
    keys !== "key,kind"
    || !["none", "folder", "work", "series"].includes(kind)
    || typeof key !== "string"
    || key !== key.trim()
    || (kind === "none" ? key !== "" : !key)
  ) {
    invalidSubject(message);
  }
  return Object.freeze({ kind: kind, key: key });
}
