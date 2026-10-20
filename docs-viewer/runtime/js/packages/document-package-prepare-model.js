import {
  packageText
} from "./document-package-view.js";

function normalizeIds(values) {
  const seen = new Set();
  return (Array.isArray(values) ? values : []).map(packageText).filter((value) => {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

export function documentPackageProfile(profiles, profileId) {
  return profiles.find((profile) => profile.profile_id === profileId) || null;
}

export function documentPackageTargetFormats(profile) {
  const formats = Array.isArray(profile && profile.supported_target_formats)
    ? normalizeIds(profile.supported_target_formats)
    : [];
  const fallback = packageText(profile && profile.target_format);
  return formats.length ? formats : [fallback].filter(Boolean);
}

export function documentPackageContentFormats(profile) {
  const formats = Array.isArray(profile && profile.supported_content_formats)
    ? normalizeIds(profile.supported_content_formats)
    : [];
  const fallback = packageText(profile && profile.content_format);
  return formats.length ? formats : [fallback].filter(Boolean);
}

export function projectDocumentPackageSelection(options = {}) {
  const profile = options.profile || null;
  const selection = profile && typeof profile.selection === "object" ? profile.selection : {};
  const documents = Array.isArray(options.documents) ? options.documents : [];
  const documentsById = new Map(
    documents.map((record) => [record.doc_id, record])
  );
  const supportsMissingSummaryOnly = selection.supports_missing_summary_only === true;
  const missingSummaryOnly = supportsMissingSummaryOnly
    ? Object.prototype.hasOwnProperty.call(options, "missingSummaryOnly")
      ? options.missingSummaryOnly === true
      : selection.default_missing_summary_only === true
    : false;
  const checkedDocIds = options.checkedDocIds;
  const afterSummary = checkedDocIds.filter((docId) => {
    const record = documentsById.get(docId);
    return !missingSummaryOnly || !packageText(record && record.summary);
  });
  const excludedWithSummaryCount = checkedDocIds.length - afterSummary.length;
  const rawMaxDocuments = profile && profile.limits && profile.limits.max_documents;
  const maxDocuments = Number.isInteger(rawMaxDocuments) && rawMaxDocuments > 0
    ? rawMaxDocuments
    : null;
  const docIds = maxDocuments === null ? afterSummary : afterSummary.slice(0, maxDocuments);
  const excludedByLimitCount = afterSummary.length - docIds.length;
  return {
    docIds,
    missingSummaryOnly,
    supportsMissingSummaryOnly,
    total: docIds.length,
    excludedWithSummaryCount,
    excludedByLimitCount,
  };
}

export function documentPackageProfileLabel(profile) {
  const label = packageText(profile && profile.label) || packageText(profile && profile.profile_id);
  return profile && profile.supports_return_import === false
    ? `${label} (export only)`
    : label;
}

export function createDocumentPackagePrepareRequest(options = {}) {
  const collection = packageText(options.collection).toLowerCase();
  const profile = options.profile || null;
  const effectiveDocIds = normalizeIds(options.effectiveDocIds);
  if (!profile || !packageText(profile.profile_id)) throw new Error("A document-package profile is required.");
  if (!effectiveDocIds.length) throw new Error("No documents remain for package preparation.");

  const targetFormats = documentPackageTargetFormats(profile);
  const requestedTargetFormat = packageText(options.targetFormat) || packageText(profile.target_format) || targetFormats[0];
  if (!targetFormats.includes(requestedTargetFormat)) {
    throw new Error("The selected package format is not supported by this profile.");
  }

  const contentFormats = documentPackageContentFormats(profile);
  const requestedContentFormat = packageText(options.contentFormat) || packageText(profile.content_format) || contentFormats[0] || "";
  if (requestedContentFormat && !contentFormats.includes(requestedContentFormat)) {
    throw new Error("The selected content format is not supported by this profile.");
  }

  return {
    collection,
    profile_id: packageText(profile.profile_id),
    doc_ids: effectiveDocIds,
    target_format: requestedTargetFormat,
    content_format: requestedContentFormat,
    dry_run: false
  };
}
