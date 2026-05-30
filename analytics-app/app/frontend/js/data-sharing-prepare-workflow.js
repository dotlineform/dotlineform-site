import { buildAnalyticsActivityContext } from "./analytics-activity-context.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function safeCapability(capabilityInfo) {
  return capabilityInfo && typeof capabilityInfo.capability === "object"
    ? capabilityInfo.capability
    : {};
}

export function prepareSelectionModel(capabilityInfo) {
  return normalizeText(safeCapability(capabilityInfo).selection_model) || "documents";
}

export function usesPrepareDocumentSelection(capabilityInfo) {
  return prepareSelectionModel(capabilityInfo) === "documents";
}

export function prepareProfilesForCapability(capabilityInfo) {
  const profiles = Array.isArray(safeCapability(capabilityInfo).sharing_profiles)
    ? safeCapability(capabilityInfo).sharing_profiles
    : [];
  return profiles.filter((profile) => profile && profile.enabled !== false);
}

export function enabledPrepareConfigsForScope(payload, scope) {
  const configs = Array.isArray(payload && payload.configs) ? payload.configs : [];
  return configs.filter((config) => {
    if (!config || config.enabled === false) return false;
    const scopes = Array.isArray(config.scopes) ? config.scopes : [];
    return scopes.includes(scope);
  });
}

export function selectedPrepareConfig(configs, configId) {
  const id = normalizeText(configId);
  const options = Array.isArray(configs) ? configs : [];
  return options.find((config) => normalizeText(config && config.id) === id) || null;
}

export function supportedFormatsForPrepareConfig(config) {
  const target = config && typeof config.target === "object" ? config.target : {};
  const configured = Array.isArray(target.supported_formats)
    ? target.supported_formats.map(normalizeText).filter(Boolean)
    : [];
  const fallback = normalizeText(target.format);
  const formats = configured.length ? configured : [fallback].filter(Boolean);
  return formats.filter((format, index) => formats.indexOf(format) === index);
}

export function defaultFormatForPrepareConfig(config, allowedFormats = []) {
  const formats = supportedFormatsForPrepareConfig(config)
    .filter((format) => !allowedFormats.length || allowedFormats.includes(format));
  const target = config && typeof config.target === "object" ? config.target : {};
  const preferred = normalizeText(target.format);
  return formats.includes(preferred) ? preferred : formats[0] || "";
}

export function prepareConfigSelection(config) {
  return config && typeof config.selection === "object" ? config.selection : {};
}

export function prepareSelectsAllMatching(config, usesDocumentSelection) {
  return Boolean(usesDocumentSelection) && normalizeText(prepareConfigSelection(config).mode) === "all_matching";
}

export function buildPrepareActivityContext({ scope, configId } = {}) {
  const safeScope = normalizeText(scope);
  const safeConfigId = normalizeText(configId);
  return buildAnalyticsActivityContext({
    pageId: "data-sharing-prepare",
    actionId: "prepare-share-package",
    route: "/analytics/data-sharing/prepare/?mode=manage",
    controlId: "dataSharingPrepareRun",
    controlSelector: "#dataSharingPrepareRun",
    recordIdField: "export_id",
    recordId: `${safeScope}:${safeConfigId}`
  });
}

export function buildPreparePackageRequest({
  scope,
  config,
  targetFormat,
  selectedIds,
  usesDocumentSelection,
  missingSummaryOnlyAvailable,
  missingSummaryOnly
} = {}) {
  const configId = normalizeText(config && config.id);
  const selectAll = prepareSelectsAllMatching(config, usesDocumentSelection);
  const docIds = selectAll ? [] : Array.from(selectedIds || []);
  return {
    data_domain: normalizeText(scope),
    config_id: configId,
    target_format: normalizeText(targetFormat),
    doc_ids: docIds,
    select_all: selectAll,
    missing_summary_only: usesDocumentSelection && missingSummaryOnlyAvailable
      ? Boolean(missingSummaryOnly)
      : null,
    activity_context: buildPrepareActivityContext({ scope, configId })
  };
}
