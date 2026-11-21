import { openDocsViewerManagementModal } from "../docs-viewer-management-modal-shell.js";
import { sourceHeaderPairs } from "./source-buffer.js";

const DATE_TOKEN = "[[date]]";
const DATE_MARKUP = '<small class="muted">' + DATE_TOKEN + "</small>";

function insertionPointInDate(source, bodyStart, selection) {
  if (selection.start < bodyStart) return false;
  var from = Math.max(bodyStart, selection.start - DATE_MARKUP.length + 1);
  var nearby = source.slice(from, selection.start + DATE_MARKUP.length);
  var point = selection.start - from;
  return [DATE_MARKUP, DATE_TOKEN].some(function (markup) {
    var start = nearby.lastIndexOf(markup, point);
    return start >= 0 && point < start + markup.length
      && (start < point || selection.end > selection.start);
  });
}

function readDateField(field) {
  var raw = field?.raw || "";
  if (raw.startsWith('"')) return JSON.parse(raw);
  if (raw.startsWith("'") && raw.endsWith("'")) return raw.slice(1, -1).replace(/\\'/g, "'");
  return raw;
}

function suggestDisplayDate(label, date) {
  var shownDate = date.endsWith("-01-01") ? date.slice(0, 4) : date;
  return [label, shownDate].filter(Boolean).join(" ");
}

function normalizeCalendarDate(value) {
  var iso = value.trim();
  var slashDate = /^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/.exec(iso);
  if (slashDate) {
    var day = slashDate[1].padStart(2, "0");
    var month = slashDate[2].padStart(2, "0");
    var year = slashDate[3];
    if (year.length === 2) year = "20" + year;
    iso = year + "-" + month + "-" + day;
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso) || iso.startsWith("0000-")) return "";
  var date = new Date(iso + "T00:00:00Z");
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === iso ? iso : "";
}

export function handleSourceAddDateControl(context) {
  var detail = context.detail;
  if (detail.eventType !== "click" || detail.target.disabled || detail.target.hidden) return;
  var adapter = context.sourceEditorServices?.getActiveSourceEditorContextAdapter?.();
  if (!adapter?.isCurrent()) return;

  var capture = adapter.captureSelection();
  var source = adapter.getBufferSnapshot().value;
  var header = /^(---[ \t]*\n)([\s\S]*?)\n(---[ \t]*(?:\n|$))/.exec(source);
  if (!header) {
    adapter.setStatus("Add date requires a complete front matter block.", true);
    adapter.focus();
    return;
  }
  var bodyStart = header[0].length;
  var editing = insertionPointInDate(source, bodyStart, capture);
  var lines = header[2].split("\n");
  var pairs = sourceHeaderPairs(lines);
  var dateField = pairs.find(function (field) { return field.key === "date"; });
  var displayField = pairs.find(function (field) { return field.key === "date_display"; });
  var dateValue;
  var displayValue;
  try {
    dateValue = readDateField(dateField);
    displayValue = readDateField(displayField);
  } catch (_error) {
    adapter.setStatus("Correct the quoted date fields in front matter before using Add date.", true);
    adapter.focus();
    return;
  }

  return openDocsViewerManagementModal({
    root: context.root,
    title: editing ? "Edit date" : "Add date",
    size: "compact",
    submitOnEnter: !editing,
    restoreFocus: { focus: function () { adapter.focus(); } },
    focusSelector: "#docsViewerSourceDateLabel",
    bodyHtml:
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">Label</span>' +
        '<input class="docsViewer__fieldInput" id="docsViewerSourceDateLabel" type="text">' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">Date</span>' +
        '<input class="docsViewer__fieldInput" id="docsViewerSourceDate" type="text" spellcheck="false">' +
      '</label>' +
      '<label class="docsViewer__field">' +
        '<span class="docsViewer__fieldLabel">Display date</span>' +
        '<input class="docsViewer__fieldInput" id="docsViewerSourceDateDisplay" type="text">' +
      '</label>',
    actions: [
      { role: "modal-primary", label: editing ? "Update date" : "Insert date" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var label = api.host.querySelector("#docsViewerSourceDateLabel");
      var date = api.host.querySelector("#docsViewerSourceDate");
      var display = api.host.querySelector("#docsViewerSourceDateDisplay");
      var displayEdited = false;
      date.value = dateValue;
      display.value = displayValue;
      function suggest() {
        if (!displayEdited) {
          var iso = normalizeCalendarDate(date.value);
          display.value = iso ? suggestDisplayDate(label.value.trim(), iso) : "";
        }
      }
      label.addEventListener("input", suggest);
      date.addEventListener("input", suggest);
      display.addEventListener("input", function () { displayEdited = true; });
      if (!displayValue) suggest();
    },
    onSubmit: function (api) {
      var date = normalizeCalendarDate(api.host.querySelector("#docsViewerSourceDate").value);
      var display = api.host.querySelector("#docsViewerSourceDateDisplay").value.trim();
      if (!date) {
        api.setStatus("Enter a valid date, such as 2026-01-01 or 1/1/26.");
        return false;
      }

      var nextLines = lines.slice();
      var dateLine = "date: " + date;
      var displayLine = display ? "date_display: " + JSON.stringify(display) : "";
      if (dateField) nextLines[dateField.index] = dateLine;
      else nextLines.push(dateLine);
      if (displayField && displayLine) nextLines[displayField.index] = displayLine;
      else if (displayField) nextLines.splice(displayField.index, 1);
      else if (displayLine) nextLines.push(displayLine);

      var insertionPoint = Math.max(bodyStart, capture.start);
      var closing = header[3].endsWith("\n") ? header[3] : header[3] + "\n";
      var insertion = editing ? "" : "<br>" + DATE_MARKUP;
      if (!editing && insertionPoint === bodyStart) {
        var bodyNeedsBlankLine = bodyStart < source.length && source[bodyStart] !== "\n";
        insertion = "\n" + insertion + (bodyNeedsBlankLine ? "\n\n" : "\n");
      }
      var prefix = header[1] + nextLines.join("\n") + "\n" + closing + source.slice(bodyStart, insertionPoint);
      // Apply the fields and any insertion as one buffer edit.
      var range = { start: 0, end: insertionPoint, text: source.slice(0, insertionPoint), revision: capture.revision };
      if (!adapter.replaceCapturedSelection(range, prefix + insertion)) {
        api.setStatus("The Source buffer changed. Close this dialog and try again.");
        return false;
      }
      adapter.setStatus("", false);
      return { confirmed: true };
    }
  });
}
