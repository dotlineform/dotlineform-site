import MarkdownIt from "../vendor/markdown-it/markdown-it.mjs";
import { escapeHtml, openDocsViewerManagementModal } from "../docs-viewer-management-modal-shell.js";
import { sourceBodyStart } from "./source-buffer.js";

const markdown = new MarkdownIt("commonmark").enable("table");
const tableCheckboxes = [
  { name: "shadeFirstColumn", flag: "shade-first-column", label: "Shade first column" },
  { name: "smallText", flag: "small-text", label: "Small text" },
  { name: "horizontalRules", flag: "horizontal-rules", label: "Horizontal rules only" },
  { name: "firstRowIsHeader", flag: "no-header", label: "First row is a header", defaultChecked: true }
];
const flagsPattern = tableCheckboxes.map(option => option.flag).join("|");
const optionsComment = new RegExp(`^<!-- dotlineform:table(?= [a-z])(?: widths="([^"\\n]*)")?((?: (?:${flagsPattern}))*) -->$`);
const detailComment = /^<!-- dotlineform:table-detail(?: title="([^"\n]*)")? -->$/;

/** Resolve the selected standalone table and the exact range occupied by its options in the unsaved buffer. */
export function tableOptionsAtSelection(source, selection) {
  const bodyStart = sourceBodyStart(source);
  if (selection.start < bodyStart) return null;

  const body = source.slice(bodyStart);
  const blocks = [];
  markdown.block.parse(body, markdown, {}, blocks);
  const offsets = [bodyStart];
  for (let newline = body.indexOf("\n"); newline >= 0; newline = body.indexOf("\n", newline + 1)) {
    offsets.push(bodyStart + newline + 1);
  }
  offsets.push(source.length);

  for (const [index, table] of blocks.entries()) {
    if (table.type !== "table_open" || table.level !== 0) continue;
    const headerStart = offsets[table.map[0]];
    const end = offsets[table.map[1]];
    const lastCaret = source[end - 1] === "\n" ? end - 1 : end;
    if (selection.start > lastCaret || selection.end > end) continue;

    let start = headerStart;
    let widths = null;
    const flags = new Set();
    let encodedTitle = null;
    for (let previous = index - 1; previous >= 0; previous--) {
      const comment = blocks[previous];
      if (comment.type !== "html_block" || comment.level !== table.level) break;
      const from = offsets[comment.map[0]];
      const to = offsets[comment.map[1]];
      if (source.slice(to, start).trim()) break;
      const line = source.slice(from, to).replace(/\n$/, "");
      const options = optionsComment.exec(line);
      if (options) {
        widths = options[1] ?? widths;
        for (const flag of options[2].trim().split(" ").filter(Boolean)) flags.add(flag);
      } else {
        const detail = detailComment.exec(line);
        if (!detail) break;
        encodedTitle = detail[1] ?? "";
      }
      start = from;
    }
    if (selection.start < start) return null;

    let columns = 0;
    for (let cell = index + 1; blocks[cell].type !== "thead_close"; cell++) {
      if (blocks[cell].type === "th_open") columns++;
    }
    const checkboxes = Object.fromEntries(tableCheckboxes.map(({ name, flag, defaultChecked = false }) =>
      [name, flags.has(flag) !== defaultChecked]));
    return {
      columns, widths, ...checkboxes, encodedTitle,
      capture: { start, end: headerStart, revision: selection.revision, text: source.slice(start, headerStart) }
    };
  }
  return null;
}

/** Apply edits to the attached comments only. Save owns persistence and rendering. */
export function openTableOptionsModal(root, adapter, selection) {
  const snapshot = adapter.getBufferSnapshot();
  if (snapshot.revision !== selection.revision) {
    adapter.setStatus("The Source buffer changed. Choose Table options again.", true);
    adapter.focus();
    return;
  }
  const table = tableOptionsAtSelection(snapshot.value, selection);
  if (!table) {
    adapter.setStatus("Place the caret in a Markdown table or select one table, then choose Table options.", true);
    adapter.focus();
    return;
  }
  adapter.setStatus("", false);
  let fields, widths, detail, title, originalTitle;
  return openDocsViewerManagementModal({
    root,
    title: "Table options",
    size: "compact",
    restoreFocus: adapter,
    focusSelector: '[name="widths"]',
    bodyHtml: `<label class="docsViewer__field">
        <span class="docsViewer__fieldLabel">Relative widths</span>
        <input class="docsViewer__fieldInput" type="text" name="widths" aria-describedby="docsViewerTableWidthsHint" autocomplete="off" spellcheck="false">
      </label>
      <p class="docsViewer__modalNote muted small" id="docsViewerTableWidthsHint">Enter one weight per column (${table.columns}), separated by spaces. Leave blank for automatic widths.</p>
      ${tableCheckboxes.map(({ name, label }) => `<label class="docsViewer__field docsViewer__field--checkbox">
        <input class="docsViewer__checkboxInput" type="checkbox" name="${name}"><span class="docsViewer__fieldLabel">${label}</span>
      </label>`).join("")}
      <label class="docsViewer__field docsViewer__field--checkbox">
        <input class="docsViewer__checkboxInput" type="checkbox" name="detail"><span class="docsViewer__fieldLabel">Enable detail view</span>
      </label>
      <label class="docsViewer__field">
        <span class="docsViewer__fieldLabel">Table title</span>
        <input class="docsViewer__fieldInput" type="text" name="title" placeholder="Table" autocomplete="off">
      </label>`,
    actions: [{ role: "modal-primary", label: "Apply" }, { role: "modal-cancel", label: "Cancel" }],
    onOpen(api) {
      fields = api.host.querySelector("form").elements;
      widths = fields.namedItem("widths");
      detail = fields.namedItem("detail");
      title = fields.namedItem("title");
      widths.value = (table.widths ?? "").replaceAll(":", " ");
      for (const { name } of tableCheckboxes) fields.namedItem(name).checked = table[name];
      detail.checked = table.encodedTitle !== null;
      title.disabled = !detail.checked;
      // Decode authored HTML entities as text, including quotes in existing titles.
      const decoder = root.ownerDocument.createElement("textarea");
      decoder.innerHTML = (table.encodedTitle ?? "").replaceAll("<", "&lt;");
      title.value = decoder.value;
      originalTitle = title.value;
      detail.addEventListener("change", () => { title.disabled = !detail.checked; });
    },
    onSubmit(api) {
      const input = widths.value.trim();
      const weights = input ? input.split(/\s+/) : [];
      if (weights.length && (weights.length !== table.columns || weights.some(weight => !/^0*[1-9][0-9]*$/.test(weight)))) {
        api.setStatus(`Enter one positive whole number for each of the ${table.columns} columns, or leave Relative widths blank.`);
        widths.focus();
        return false;
      }
      const ratio = weights.length ? weights.join(":") : null;
      let encodedTitle = null;
      if (detail.checked) {
        encodedTitle = title.value === originalTitle ? table.encodedTitle ?? "" : escapeHtml(title.value.trim());
      }
      if (ratio === table.widths && encodedTitle === table.encodedTitle
        && tableCheckboxes.every(({ name }) => fields.namedItem(name).checked === table[name])) return;
      const comments = [];
      const options = [];
      if (ratio) options.push(`widths="${ratio}"`);
      for (const { name, flag, defaultChecked = false } of tableCheckboxes) {
        if (fields.namedItem(name).checked !== defaultChecked) options.push(flag);
      }
      if (options.length) comments.push(`<!-- dotlineform:table ${options.join(" ")} -->\n`);
      if (encodedTitle !== null) {
        comments.push(encodedTitle ? `<!-- dotlineform:table-detail title="${encodedTitle}" -->\n` : "<!-- dotlineform:table-detail -->\n");
      }
      if (!adapter.replaceCapturedRange(table.capture, comments.join(""), "preserve")) {
        api.setStatus("The Source buffer changed. Close this dialog and try again.");
        return false;
      }
    }
  });
}
