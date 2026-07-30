import {
  normalizeManagedDocumentCollectionTarget
} from "../management/docs-viewer-management-document-target.js";

export const DOCS_IMPORT_CANDIDATE_ORDINARY = "ordinary_document";
export const DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE = "returned_package";
export const DOCS_IMPORT_CANDIDATE_EDITED_REVIEW_SOURCE = "edited_review_source";
export const DOCS_IMPORT_TARGET_ORDINARY_CONTEXT = "ordinary_context";
export const DOCS_IMPORT_TARGET_MANIFEST_COLLECTION = "manifest_collection";
export const DOCS_IMPORT_TARGET_NONE = "none";

const CANDIDATE_KINDS = new Set([
  DOCS_IMPORT_CANDIDATE_ORDINARY,
  DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE,
  DOCS_IMPORT_CANDIDATE_EDITED_REVIEW_SOURCE
]);
const TARGET_MODES = new Set([
  DOCS_IMPORT_TARGET_ORDINARY_CONTEXT,
  DOCS_IMPORT_TARGET_MANIFEST_COLLECTION,
  DOCS_IMPORT_TARGET_NONE
]);

function cleanText(value) {
  return String(value == null ? "" : value).trim();
}

function requiredBoolean(record, key) {
  if (record[key] !== true && record[key] !== false) {
    throw new Error(`Import candidate ${key} must be a boolean.`);
  }
  return record[key] === true;
}

function candidateDiagnostics(value) {
  if (!Array.isArray(value)) return Object.freeze([]);
  return Object.freeze(value.map((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      throw new Error("Import candidate diagnostics are invalid.");
    }
    const code = cleanText(item.code);
    const message = cleanText(item.message);
    if (!code || !message) {
      throw new Error("Import candidate diagnostics require code and message.");
    }
    return Object.freeze({ code, message });
  }));
}

function normalizeCandidate(record) {
  if (!record || typeof record !== "object" || Array.isArray(record)) {
    throw new Error("Import candidate must be an object.");
  }
  const filename = cleanText(record.filename);
  const candidateKind = cleanText(record.candidate_kind);
  const targetMode = cleanText(record.target_mode);
  const validationState = cleanText(record.validation_state);
  if (!filename) throw new Error("Import candidate filename is required.");
  if (!CANDIDATE_KINDS.has(candidateKind)) {
    throw new Error(`Import candidate ${filename} has an unsupported kind.`);
  }
  if (!TARGET_MODES.has(targetMode)) {
    throw new Error(`Import candidate ${filename} has an unsupported target mode.`);
  }
  if (validationState !== "ready" && validationState !== "blocked") {
    throw new Error(`Import candidate ${filename} has an unsupported validation state.`);
  }

  let target = null;
  if (record.target != null) {
    target = normalizeManagedDocumentCollectionTarget(record.target);
  }
  if (
    candidateKind === DOCS_IMPORT_CANDIDATE_ORDINARY
    && (targetMode !== DOCS_IMPORT_TARGET_ORDINARY_CONTEXT || target)
  ) {
    throw new Error(`Ordinary Import candidate ${filename} has an invalid target contract.`);
  }
  if (
    candidateKind !== DOCS_IMPORT_CANDIDATE_ORDINARY
    && targetMode === DOCS_IMPORT_TARGET_ORDINARY_CONTEXT
  ) {
    throw new Error(`Manifest Import candidate ${filename} cannot use display context.`);
  }

  const supportsDocsReview = requiredBoolean(record, "supports_docs_review");
  const supportsReturnImport = requiredBoolean(record, "supports_return_import");
  const docsReviewEnabled = requiredBoolean(record, "docs_review_enabled");
  const importEnabled = requiredBoolean(record, "import_enabled");
  if (
    candidateKind === DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE
    && supportsReturnImport
    && !supportsDocsReview
  ) {
    throw new Error(`Import candidate ${filename} has an invalid capability matrix.`);
  }
  if (
    docsReviewEnabled
    && (
      validationState !== "ready"
      ||
      candidateKind !== DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE
      || targetMode !== DOCS_IMPORT_TARGET_MANIFEST_COLLECTION
      || !target
      || !supportsDocsReview
    )
  ) {
    throw new Error(`Import candidate ${filename} has an invalid Docs Review action.`);
  }
  if (
    importEnabled
    && (
      validationState !== "ready"
      || (
        candidateKind !== DOCS_IMPORT_CANDIDATE_ORDINARY
        && (
          targetMode !== DOCS_IMPORT_TARGET_MANIFEST_COLLECTION
          || !target
          || !supportsReturnImport
        )
      )
    )
  ) {
    throw new Error(`Import candidate ${filename} has an invalid Import action.`);
  }
  if (
    validationState === "ready"
    && !docsReviewEnabled
    && !importEnabled
  ) {
    throw new Error(`Import candidate ${filename} is ready without an enabled action.`);
  }
  if (
    validationState === "blocked"
    && (docsReviewEnabled || importEnabled)
  ) {
    throw new Error(`Import candidate ${filename} is blocked with an enabled action.`);
  }

  return Object.freeze({
    raw: record,
    filename,
    displayName: cleanText(record.display_name),
    sourceFormat: cleanText(record.source_format),
    candidateKind,
    validationState,
    targetMode,
    target,
    targetLabel: cleanText(record.target_label),
    supportsDocsReview,
    supportsReturnImport,
    docsReviewEnabled,
    docsReviewDisabledReason: cleanText(record.docs_review_disabled_reason),
    importEnabled,
    importDisabledReason: cleanText(record.import_disabled_reason),
    disabledReason: cleanText(record.disabled_reason),
    diagnostics: candidateDiagnostics(record.diagnostics),
    documentCount: Number.isInteger(record.document_count)
      ? record.document_count
      : null
  });
}

export function docsImportCandidateInventory(payload) {
  if (!payload || !Array.isArray(payload.candidates)) {
    throw new Error("Docs Import candidate inventory is unavailable.");
  }
  const candidates = payload.candidates.map(normalizeCandidate);
  const filenames = new Set();
  candidates.forEach((candidate) => {
    if (filenames.has(candidate.filename)) {
      throw new Error(`Docs Import candidate identity is duplicated: ${candidate.filename}`);
    }
    filenames.add(candidate.filename);
  });
  return Object.freeze(candidates);
}

export function docsImportCandidateKindLabel(candidate) {
  const kind = candidate && candidate.candidateKind;
  if (kind === DOCS_IMPORT_CANDIDATE_RETURNED_PACKAGE) return "Returned package";
  if (kind === DOCS_IMPORT_CANDIDATE_EDITED_REVIEW_SOURCE) {
    return "Edited review-source folder";
  }
  if (kind === DOCS_IMPORT_CANDIDATE_ORDINARY) return "Ordinary document";
  return "Unavailable";
}

export function docsImportCandidateTarget(candidate, ordinaryDestination) {
  if (!candidate) return null;
  if (candidate.targetMode === DOCS_IMPORT_TARGET_ORDINARY_CONTEXT) {
    return ordinaryDestination
      ? normalizeManagedDocumentCollectionTarget(ordinaryDestination)
      : null;
  }
  if (candidate.targetMode === DOCS_IMPORT_TARGET_MANIFEST_COLLECTION) {
    return candidate.target
      ? normalizeManagedDocumentCollectionTarget(candidate.target)
      : null;
  }
  return null;
}

export function docsImportCollectionLabel(target) {
  if (!target) return "Unavailable";
  const normalized = normalizeManagedDocumentCollectionTarget(target);
  return normalized.sub_scope
    ? `${normalized.scope} / ${normalized.sub_scope}`
    : normalized.scope;
}

export function docsImportCandidateDestinationLabel(
  candidate,
  ordinaryDestination,
  ordinaryDestinationLabel = ""
) {
  const target = docsImportCandidateTarget(candidate, ordinaryDestination);
  if (!target) return "Unavailable";
  if (candidate.targetMode === DOCS_IMPORT_TARGET_ORDINARY_CONTEXT) {
    return cleanText(ordinaryDestinationLabel) || docsImportCollectionLabel(target);
  }
  return candidate.targetLabel || docsImportCollectionLabel(target);
}

export function docsImportCandidateDisabledMessage(candidate, action = "import") {
  if (!candidate) return "Select one staged source.";
  const reason = action === "review"
    ? candidate.docsReviewDisabledReason
    : candidate.importDisabledReason || candidate.disabledReason;
  const matchingDiagnostic = candidate.diagnostics.find((item) => item.code === reason);
  if (matchingDiagnostic) return matchingDiagnostic.message;
  if (action === "review") {
    if (candidate.candidateKind === DOCS_IMPORT_CANDIDATE_ORDINARY) {
      return "Ordinary sources do not open in Docs Review.";
    }
    if (candidate.candidateKind === DOCS_IMPORT_CANDIDATE_EDITED_REVIEW_SOURCE) {
      return "Edited review-source folders are already review outputs.";
    }
    return "Docs Review is not available for this returned package.";
  }
  return candidate.diagnostics[0] && candidate.diagnostics[0].message
    ? candidate.diagnostics[0].message
    : "Import is not available for this staged source.";
}
