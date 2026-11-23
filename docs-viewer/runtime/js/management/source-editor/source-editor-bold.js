export const SOURCE_BOLD_CONTROL_ID = "source-toggle-bold";

export async function handleSourceBoldControl(context) {
  const { detail } = context;
  if (detail.eventType !== "click" || detail.target.disabled || detail.target.hidden) return;
  const adapter = context.sourceEditorServices?.getActiveSourceEditorContextAdapter?.();
  if (!adapter?.isCurrent()) return;
  const capture = adapter.captureSelection();
  if (capture.start === capture.end) return;
  const { value } = adapter.getBufferSnapshot();

  try {
    const { toggleBoldInSelection } = await import("./source-bold-selection.js");
    if (!adapter.isCurrent()) return;
    const replacement = toggleBoldInSelection(value, capture);
    if (replacement === null) {
      adapter.setStatus("Select a complete bold span or text within one Markdown paragraph or table cell.", true);
      adapter.focus();
      return;
    }
    if (adapter.replaceCapturedRange(capture, replacement, "select")) adapter.setStatus("", false);
  } catch (error) {
    if (adapter.isCurrent()) {
      adapter.setStatus(error.message || "Bold formatting could not be changed.", true);
      adapter.focus();
    }
  }
}
