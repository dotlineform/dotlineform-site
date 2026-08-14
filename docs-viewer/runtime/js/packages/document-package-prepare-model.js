import {
  packageText,
  profileForId
} from "./document-package-view.js";

function normalizeIds(values) {
  const seen = new Set();
  return (Array.isArray(values) ? values : []).map(packageText).filter((value) => {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function documentId(record) {
  return packageText(record && (record.doc_id || record.id));
}

export function documentPackageProfile(profiles, profileId) {
  return profileForId(profiles, profileId) || (Array.isArray(profiles) ? profiles[0] : null) || null;
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

export function documentPackageProfileRequiresDescendants(profile) {
  return packageText(profile && profile.record_shape) === "document_tree";
}

export function documentPackageProfileIncludesDescendants(profile) {
  if (documentPackageProfileRequiresDescendants(profile)) return true;
  const selection = profile && typeof profile.selection === "object" ? profile.selection : {};
  return selection.include_descendants !== false;
}

export function documentPackageDescendantIds(documents, docId) {
  const childrenByParent = new Map();
  (Array.isArray(documents) ? documents : []).forEach((record) => {
    const parentId = packageText(record && record.parent_id);
    const childId = documentId(record);
    if (!parentId || !childId) return;
    if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, []);
    childrenByParent.get(parentId).push(childId);
  });
  const descendants = [];
  const pending = [...(childrenByParent.get(packageText(docId)) || [])];
  const seen = new Set();
  while (pending.length) {
    const childId = pending.shift();
    if (!childId || seen.has(childId)) continue;
    seen.add(childId);
    descendants.push(childId);
    pending.push(...(childrenByParent.get(childId) || []));
  }
  return descendants;
}

export function documentPackageSelectionEligibility(documents, checkedDocIds) {
  const checked = normalizeIds(checkedDocIds);
  const selectable = new Set(
    (Array.isArray(documents) ? documents : [])
      .filter((record) => record && record.selectable !== false)
      .map(documentId)
      .filter(Boolean)
  );
  return {
    eligibleDocIds: checked.filter((docId) => selectable.has(docId)),
    ineligibleDocIds: checked.filter((docId) => !selectable.has(docId))
  };
}

export function expandDocumentPackageSelection(documents, checkedDocIds, includeDescendants) {
  const eligibility = documentPackageSelectionEligibility(documents, checkedDocIds);
  const allowed = new Set(
    (Array.isArray(documents) ? documents : [])
      .filter((record) => record && record.selectable !== false)
      .map(documentId)
      .filter(Boolean)
  );
  const expanded = [];
  const seen = new Set();
  eligibility.eligibleDocIds.forEach((docId) => {
    const affected = includeDescendants
      ? [docId, ...documentPackageDescendantIds(documents, docId)]
      : [docId];
    affected.forEach((affectedId) => {
      if (!allowed.has(affectedId) || seen.has(affectedId)) return;
      seen.add(affectedId);
      expanded.push(affectedId);
    });
  });
  return expanded;
}

export function projectDocumentPackageSelection(options = {}) {
  const profile = options.profile || null;
  const selection = profile && typeof profile.selection === "object" ? profile.selection : {};
  const documents = Array.isArray(options.documents) ? options.documents : [];
  const documentsById = new Map(
    documents.map((record) => [documentId(record), record]).filter(([docId]) => Boolean(docId))
  );
  const includeDescendants = options.flatCollection === true
    ? false
    : documentPackageProfileRequiresDescendants(profile)
      ? true
      : options.includeDescendants === true;
  const supportsMissingSummaryOnly = selection.supports_missing_summary_only === true;
  const missingSummaryOnly = supportsMissingSummaryOnly
    ? Object.prototype.hasOwnProperty.call(options, "missingSummaryOnly")
      ? options.missingSummaryOnly === true
      : selection.default_missing_summary_only === true
    : false;
  const supportsIncludeNonPublishable = selection.supports_include_non_publishable === true;
  const defaultIncludeNonPublishable = selection.include_non_publishable !== false;
  const includeNonPublishable = supportsIncludeNonPublishable
    ? Object.prototype.hasOwnProperty.call(options, "includeNonPublishable")
      ? options.includeNonPublishable !== false
      : defaultIncludeNonPublishable
    : defaultIncludeNonPublishable;

  const expandedDocIds = expandDocumentPackageSelection(
    documents,
    options.checkedDocIds,
    includeDescendants
  );
  const afterPublishability = expandedDocIds.filter((docId) => {
    const record = documentsById.get(docId);
    return includeNonPublishable || !record || record.publishable !== false;
  });
  const excludedNonPublishableCount = expandedDocIds.length - afterPublishability.length;
  const afterSummary = afterPublishability.filter((docId) => {
    const record = documentsById.get(docId);
    return !missingSummaryOnly || !packageText(record && record.summary);
  });
  const excludedWithSummaryCount = afterPublishability.length - afterSummary.length;
  const rawMaxDocuments = profile && profile.limits && profile.limits.max_documents;
  const maxDocuments = Number.isInteger(rawMaxDocuments) && rawMaxDocuments > 0
    ? rawMaxDocuments
    : null;
  const docIds = maxDocuments === null ? afterSummary : afterSummary.slice(0, maxDocuments);
  const excludedByLimitCount = afterSummary.length - docIds.length;
  const includedNonPublishableCount = docIds.filter((docId) => {
    const record = documentsById.get(docId);
    return record && record.publishable === false;
  }).length;

  return {
    docIds,
    includeDescendants,
    missingSummaryOnly,
    includeNonPublishable,
    supportsMissingSummaryOnly,
    supportsIncludeNonPublishable,
    total: docIds.length,
    excludedNonPublishableCount,
    excludedWithSummaryCount,
    excludedByLimitCount,
    includedNonPublishableCount
  };
}

export function documentPackageProfileLabel(profile) {
  const label = packageText(profile && profile.label) || packageText(profile && profile.profile_id);
  return profile && profile.supports_return_import === false
    ? `${label} (export only)`
    : label;
}

export function createDocumentPackagePrepareRequest(options = {}) {
  const scope = packageText(options.scope).toLowerCase();
  const subScope = packageText(options.subScope).toLowerCase();
  const profile = options.profile || null;
  const effectiveDocIds = normalizeIds(options.effectiveDocIds);
  if (!scope) throw new Error("A Docs Viewer scope is required.");
  if (!profile || !packageText(profile.profile_id)) throw new Error("A document-package profile is required.");
  if (!effectiveDocIds.length) throw new Error("No documents remain for package preparation.");

  const eligibility = documentPackageSelectionEligibility(options.documents, effectiveDocIds);
  if (eligibility.ineligibleDocIds.length) {
    throw new Error(
      "Target documents are unavailable for package preparation: " + eligibility.ineligibleDocIds.join(", ")
    );
  }

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

  const request = {
    scope,
    profile_id: packageText(profile.profile_id),
    doc_ids: effectiveDocIds,
    select_all: false,
    missing_summary_only: options.missingSummaryOnly === true,
    include_non_publishable: options.includeNonPublishable !== false,
    target_format: requestedTargetFormat,
    content_format: requestedContentFormat,
    dry_run: false
  };
  if (subScope) request.sub_scope = subScope;
  return request;
}
