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
  const includeDescendants = documentPackageProfileRequiresDescendants(profile)
    ? true
    : options.includeDescendants === true;
  const supportsMissingSummaryOnly = selection.supports_missing_summary_only === true;
  const missingSummaryOnly = supportsMissingSummaryOnly
    ? Object.prototype.hasOwnProperty.call(options, "missingSummaryOnly")
      ? options.missingSummaryOnly === true
      : selection.default_missing_summary_only === true
    : false;
  const supportsIncludeNonViewable = selection.supports_include_non_viewable === true;
  const defaultIncludeNonViewable = selection.include_non_viewable !== false;
  const includeNonViewable = supportsIncludeNonViewable
    ? Object.prototype.hasOwnProperty.call(options, "includeNonViewable")
      ? options.includeNonViewable !== false
      : defaultIncludeNonViewable
    : defaultIncludeNonViewable;

  const expandedDocIds = expandDocumentPackageSelection(
    documents,
    options.checkedDocIds,
    includeDescendants
  );
  const afterViewability = expandedDocIds.filter((docId) => {
    const record = documentsById.get(docId);
    return includeNonViewable || !record || record.viewable !== false;
  });
  const excludedNonViewableCount = expandedDocIds.length - afterViewability.length;
  const afterSummary = afterViewability.filter((docId) => {
    const record = documentsById.get(docId);
    return !missingSummaryOnly || !packageText(record && record.summary);
  });
  const excludedWithSummaryCount = afterViewability.length - afterSummary.length;
  const rawMaxDocuments = profile && profile.limits && profile.limits.max_documents;
  const maxDocuments = Number.isInteger(rawMaxDocuments) && rawMaxDocuments > 0
    ? rawMaxDocuments
    : null;
  const docIds = maxDocuments === null ? afterSummary : afterSummary.slice(0, maxDocuments);
  const excludedByLimitCount = afterSummary.length - docIds.length;
  const includedNonViewableCount = docIds.filter((docId) => {
    const record = documentsById.get(docId);
    return record && record.viewable === false;
  }).length;

  return {
    docIds,
    includeDescendants,
    missingSummaryOnly,
    includeNonViewable,
    supportsMissingSummaryOnly,
    supportsIncludeNonViewable,
    total: docIds.length,
    excludedNonViewableCount,
    excludedWithSummaryCount,
    excludedByLimitCount,
    includedNonViewableCount
  };
}

export function documentPackageExternalContext(profile) {
  const context = profile && typeof profile.external_context === "object" ? profile.external_context : {};
  const descriptions = context && typeof context.field_descriptions === "object"
    ? context.field_descriptions
    : {};
  const fieldDescriptions = {};
  (Array.isArray(profile && profile.document_fields) ? profile.document_fields : []).forEach((field) => {
    const outputPath = packageText(field && field.output_path);
    if (outputPath) fieldDescriptions[outputPath] = packageText(descriptions[outputPath]);
  });
  return {
    task: packageText(context.task),
    response_guidance: packageText(context.response_guidance),
    field_descriptions: fieldDescriptions
  };
}

export function documentPackageExternalContextMissingValues(profile, externalContext) {
  const context = externalContext && typeof externalContext === "object" ? externalContext : {};
  const descriptions = context.field_descriptions && typeof context.field_descriptions === "object"
    ? context.field_descriptions
    : {};
  const missing = [];
  if (!packageText(context.task)) missing.push("task");
  if (!packageText(context.response_guidance)) missing.push("response guidance");
  (Array.isArray(profile && profile.document_fields) ? profile.document_fields : []).forEach((field) => {
    const outputPath = packageText(field && field.output_path);
    if (outputPath && !packageText(descriptions[outputPath])) missing.push(outputPath);
  });
  return missing;
}

export function documentPackageExternalContextChanged(profile, externalContext) {
  return JSON.stringify(documentPackageExternalContext(profile)) !== JSON.stringify(externalContext || {});
}

export function documentPackageProfileLabel(profile) {
  const label = packageText(profile && profile.label) || packageText(profile && profile.profile_id);
  return profile && profile.supports_return_import === false
    ? `${label} (export only)`
    : label;
}

export function createDocumentPackagePrepareRequest(options = {}) {
  const scope = packageText(options.scope).toLowerCase();
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

  return {
    scope,
    profile_id: packageText(profile.profile_id),
    doc_ids: effectiveDocIds,
    select_all: false,
    missing_summary_only: options.missingSummaryOnly === true,
    include_non_viewable: options.includeNonViewable !== false,
    target_format: requestedTargetFormat,
    content_format: requestedContentFormat,
    dry_run: false,
    activity_context: options.activityContext && typeof options.activityContext === "object"
      ? { ...options.activityContext }
      : {}
  };
}
