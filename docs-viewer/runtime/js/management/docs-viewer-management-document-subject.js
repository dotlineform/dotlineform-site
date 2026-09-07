export const AUTHORING_SUBJECT_FIELDS = Object.freeze([
  "folder_path",
  "work_id",
  "series_id",
  "detail_uid"
]);

const SUBJECT_FIELD_BY_KIND = Object.freeze({
  folder: "folder_path",
  work: "work_id",
  series: "series_id",
  detail: "detail_uid"
});

/** Decode the exact Studio composite identifier without a record lookup. */
export function parseDocsViewerDetailUid(value) {
  var match = typeof value === "string" && value.length === 9
    ? /^([0-9]{5})-([0-9]{3})$/.exec(value)
    : null;
  return match ? Object.freeze({ workId: match[1], detailId: match[2] }) : null;
}

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
  var hasEvidence = Object.prototype.hasOwnProperty.call(subject, "evidence");
  if (
    !["fields,key,kind,state", "evidence,fields,key,kind,state"].includes(keys)
    || !Array.isArray(subject.fields)
    || subject.fields.some(function (field) {
      return !AUTHORING_SUBJECT_FIELDS.includes(field);
    })
    || new Set(subject.fields).size !== subject.fields.length
    || (
      hasEvidence
      && (
        !subject.evidence
        || typeof subject.evidence !== "object"
        || Array.isArray(subject.evidence)
      )
    )
  ) {
    invalidSubject(message);
  }

  var state = cleanString(subject.state);
  var kind = cleanString(subject.kind);
  var key = typeof subject.key === "string" ? subject.key : "";
  var fields = subject.fields.slice();
  var validField = SUBJECT_FIELD_BY_KIND[kind];
  var evidenceKeys = hasEvidence ? Object.keys(subject.evidence).sort() : [];
  var fieldKeys = fields.slice().sort();
  var valid = (
    state === "valid"
    && Boolean(validField)
    && Boolean(key)
    && key === key.trim()
    && (kind !== "detail" || Boolean(parseDocsViewerDetailUid(key)))
    && fields.length === 1
    && fields[0] === validField
    && !hasEvidence
  );
  var none = (
    state === "none"
    && kind === "none"
    && !key
    && !fields.length
    && !hasEvidence
  );
  var malformed = (
    state === "malformed"
    && Boolean(validField)
    && !key
    && fields.length === 1
    && fields[0] === validField
    && hasEvidence
    && evidenceKeys.length === 1
    && evidenceKeys[0] === validField
  );
  var conflicting = (
    state === "conflicting"
    && kind === "conflict"
    && !key
    && fields.length > 1
    && hasEvidence
    && evidenceKeys.join(",") === fieldKeys.join(",")
  );
  if (!valid && !none && !malformed && !conflicting) {
    invalidSubject(message);
  }
  var normalized = {
    state: state,
    kind: kind,
    key: key,
    fields: Object.freeze(fields)
  };
  if (hasEvidence) {
    normalized.evidence = Object.freeze(Object.assign({}, subject.evidence));
  }
  return Object.freeze(normalized);
}
