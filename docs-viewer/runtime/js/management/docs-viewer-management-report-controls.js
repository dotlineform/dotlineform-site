import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}

function optionalTarget(value) {
  if (!value) return null;
  return normalizeManagedDocumentTarget(value);
}

function control(state, target) {
  return {
    state: state,
    target: target || null
  };
}

export function projectDocsViewerReportControlState(options = {}) {
  var mode = cleanString(options.documentMode) || "rendered-document";
  var sourceMode = mode === "markdown-source";
  var reportState = cleanString(options.reportState);
  var reportActive = Boolean(options.reportActive);
  var hidden = Boolean(options.hidden);
  var disabled = Boolean(options.disabled);
  var ordinaryTarget = optionalTarget(options.ordinaryTarget);
  var parentTarget = optionalTarget(options.parentTarget);
  var subdocTarget = optionalTarget(options.subdocTarget);
  var validDetail = reportActive && reportState === "detail" && Boolean(subdocTarget);
  var listView = reportActive && reportState === "list";
  var editTarget = reportActive
    ? (validDetail ? subdocTarget : (listView ? parentTarget : null))
    : ordinaryTarget;
  var sourceTarget = reportActive ? parentTarget : ordinaryTarget;

  return {
    editMetadata: control({
      hidden: hidden || sourceMode,
      disabled: disabled || sourceMode || !editTarget,
      label: "Edit metadata"
    }, editTarget),
    openVsCode: control({
      hidden: hidden,
      disabled: disabled || (!sourceMode && !editTarget),
      label: "Open in VS Code"
    }, sourceMode ? null : editTarget),
    parentSource: control({
      hidden: hidden,
      disabled: disabled || sourceMode || !sourceTarget,
      label: reportActive ? "Parent Source" : "Source"
    }, sourceTarget),
    subdocSource: control({
      hidden: hidden || !reportActive,
      disabled: disabled || sourceMode || !validDetail,
      label: "Subdoc Source"
    }, validDetail ? subdocTarget : null),
    returnToDoc: control({
      hidden: hidden || !sourceMode,
      disabled: disabled || !sourceMode,
      label: "Return to doc"
    }, null)
  };
}
