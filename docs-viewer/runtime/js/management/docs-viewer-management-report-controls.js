function cleanString(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
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
  var hidden = Boolean(options.hidden);
  var disabled = Boolean(options.disabled);
  var editTarget = options.actionContext && options.actionContext.documentTarget;
  var sourceTarget = sourceMode ? options.sourceTarget : editTarget;

  return {
    editDocument: control({
      hidden: hidden || sourceMode,
      disabled: disabled || sourceMode || !editTarget,
      label: "Edit document"
    }, editTarget),
    openVsCode: control({
      hidden: hidden,
      disabled: disabled || !sourceTarget,
      label: "Open in VS Code"
    }, sourceTarget),
    returnToDoc: control({
      hidden: hidden || !sourceMode,
      disabled: disabled || !sourceMode,
      label: "Return to doc"
    }, null)
  };
}
