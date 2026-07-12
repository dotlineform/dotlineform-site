var DOCS_HTML_IMPORT_TEXT = {
  allFilesOption: "< all >",
  attachmentMediaResultType: "attachment",
  cancelOverwriteButton: "Cancel",
  collisionBody: "This import matches an existing doc target. Confirm overwrite to replace the current source while keeping the same doc identity and filename.",
  collisionHeading: "Overwrite warning",
  confirmOverwriteButton: "Confirm overwrite",
  fileLabel: "staged file",
  fileRequired: "Select a staged file first.",
  filenameConflictBody: "A source file named {doc_id}.md already exists. Edit the doc_id to choose a new filename.",
  filenameConflictCancelButton: "Cancel",
  filenameConflictCancelled: "Import cancelled.",
  filenameConflictHeading: "File already exists",
  filenameConflictOkButton: "OK",
  filenameConflictReplaceAllButton: "Replace all",
  filenameConflictReplaceButton: "Replace",
  imageMediaResultType: "image, {format} <= {max_width}px",
  importAllSuccess: "Imported {count} staged files.",
  importButton: "Import",
  importCancelledPartial: "Import cancelled after {count} of {total} files.",
  importFailed: "Import failed.",
  includePromptMetaLabel: "Include obvious prompt/meta blocks",
  interactiveAssetCollisionBody: "This import includes an interactive HTML companion that matches an existing asset. Confirm overwrite to replace that asset.",
  interactiveAssetOverwriteRequired: "Interactive asset overwrite required: {path}. Review the warning and confirm if you want to replace it.",
  idleStatus: "Select a staged source file and import it into a configured docs scope.",
  loadFilesFailed: "Failed to load staged import files.",
  noFiles: "No supported staged import files found in the shared import drop-zone.",
  overwriteCancelled: "Overwrite cancelled.",
  overwriteRequired: "Overwrite required: {doc_id} ({title}). Review the warning and confirm if you want to replace it.",
  replacementDocIdLabel: "doc_id",
  replacementDocIdRequired: "Enter a doc_id first.",
  resultMarkdownCounts: "{chars} chars, {links} links, {images} images",
  resultMarkdownPackageCounts: "{chars} chars, {links} links, {images} images, {attachments} attachments",
  resultOpenSourceFailed: "Failed to open source doc.",
  resultSummaryCounts: "{links} links, {images} images, {svg} SVG, {details} details blocks",
  resultTitle: "Imported",
  resultTitleAll: "Imported {count} files",
  runningStatus: "Converting and validating staged source...",
  runningStatusAll: "Importing {index} of {total}: {filename}",
  scopeLabel: "publish into",
  scriptFileResultType: "script file",
  warningsHeading: "Warnings"
};

export function formatImportText(template, tokens = {}) {
  var text = String(template || "");
  Object.keys(tokens).forEach(function (key) {
    text = text.replace(new RegExp("\\{" + key + "\\}", "g"), tokens[key]);
  });
  return text;
}

export function importText(key, tokens = {}) {
  return formatImportText(DOCS_HTML_IMPORT_TEXT[key], tokens);
}
