import { getStudioText } from "./studio-config.js";
import { openNoticeModal } from "./studio-modal.js";

export function clearDataSharingPrepareResultModal(state) {
  if (state && state.modalHost) state.modalHost.innerHTML = "";
}

export function showDataSharingPrepareResultModal(state, payload, failed = false) {
  if (!state) return Promise.resolve();
  const files = outputFiles(payload);
  const fileText = files.join("\n");
  const fileLabel = getStudioText(state.config, "data_sharing_prepare.result_files_label", "files created");
  const emptyFiles = getStudioText(state.config, "data_sharing_prepare.result_files_empty", "No files created.");
  const formatLabel = getStudioText(state.config, "data_sharing_prepare.result_format_label", "format");
  const targetFormat = normalizeText(payload?.target_format).toUpperCase();
  const bodyHtml = `
    <dl class="dataSharingPrepareModal__details">
      <div class="dataSharingPrepareModal__countRow" data-detail-key="format">
        <dt>${escapeHtml(formatLabel)}</dt>
        <dd>${escapeHtml(targetFormat || "n/a")}</dd>
      </div>
    </dl>
    <dl class="dataSharingPrepareModal__counts">
      ${countRows(state, payload?.counts, payload)}
    </dl>
    <label class="dataSharingPrepareModal__files">
      <span>${escapeHtml(fileLabel)}</span>
      <textarea class="tagStudio__input dataSharingPrepareModal__fileList" readonly rows="${Math.max(1, files.length)}">${escapeHtml(fileText || emptyFiles)}</textarea>
    </label>
    ${issueList(state, payload?.warnings, payload?.errors)}
  `;
  return openNoticeModal({
    root: state.root,
    restoreFocus: state.runButton,
    titleId: "dataSharingPrepareResultModalTitle",
    title: failed
      ? getStudioText(state.config, "data_sharing_prepare.result_title_failed", "Package preparation failed")
      : getStudioText(state.config, "data_sharing_prepare.result_title", "Package result"),
    bodyHtml,
    closeLabel: getStudioText(state.config, "data_sharing_prepare.result_close", "Close")
  });
}

function countRows(state, counts, payload) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const unit = normalizeText(payload?.count_unit) || "document";
  const rows = [
    ["selected", "data_sharing_prepare.count_selected", "selected", Number(safeCounts.selected || 0)],
    ["exported", "data_sharing_prepare.count_exported", "packaged", Number(safeCounts.exported || 0)],
    ["skipped", "data_sharing_prepare.count_skipped", "skipped", Number(safeCounts.skipped || 0)],
    ["failed", "data_sharing_prepare.count_failed", "failed", Number(safeCounts.failed || 0)],
    ["truncated", "data_sharing_prepare.count_truncated", "truncated", Number(safeCounts.truncated || 0)]
  ];
  return rows.map(([key, textKey, fallback, count]) => `
    <div class="dataSharingPrepareModal__countRow" data-count-key="${escapeHtml(key)}">
      <dt>${escapeHtml(getStudioText(state.config, textKey, fallback))}</dt>
      <dd>${escapeHtml(countLabel(count, unit))}</dd>
    </div>
  `).join("");
}

function issueList(state, warnings, errors) {
  const errorItems = Array.isArray(errors) ? errors.map(normalizeText).filter(Boolean) : [];
  const warningItems = Array.isArray(warnings) ? warnings.map(normalizeText).filter(Boolean) : [];
  const items = [...errorItems, ...warningItems];
  if (!items.length) return "";
  const heading = getStudioText(
    state.config,
    errorItems.length ? "data_sharing_prepare.issues_heading" : "data_sharing_prepare.warnings_heading",
    errorItems.length ? "Issues" : "Warnings"
  );
  return `
    <div class="dataSharingPrepareModal__issues">
      <h4>${escapeHtml(heading)}</h4>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function outputFiles(payload) {
  const files = [];
  const outputFiles = Array.isArray(payload?.output_files) ? payload.output_files : [];
  outputFiles.forEach((file) => {
    const filename = basename(file);
    if (filename) files.push(filename);
  });
  const outputFile = basename(payload?.output_file);
  if (outputFile && !files.includes(outputFile)) files.push(outputFile);
  return files;
}

function basename(path) {
  const value = normalizeText(path);
  if (!value) return "";
  const parts = value.split(/[\\/]+/).filter(Boolean);
  return parts[parts.length - 1] || value;
}

function countLabel(count, unit = "document") {
  const safeCount = Number(count || 0);
  const normalizedUnit = normalizeText(unit) || "document";
  if (normalizedUnit === "record") return safeCount === 1 ? "1 record" : `${safeCount} records`;
  if (normalizedUnit === "file") return safeCount === 1 ? "1 file" : `${safeCount} files`;
  return safeCount === 1 ? "1 document" : `${safeCount} documents`;
}

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
