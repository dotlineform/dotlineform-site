import {
  escapeHtml
} from "../../shared/docs-viewer-render.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function renderMeta(target) {
  var meta = Array.isArray(target.meta) ? target.meta.map(cleanString).filter(Boolean) : [];
  if (!meta.length) return "";
  return '<span class="docsViewerSemanticPicker__rowMeta">' + meta.map(escapeHtml).join(" · ") + "</span>";
}

function targetKey(target) {
  return cleanString(target.kind) + ":" + cleanString(target.id);
}

function rowMarkup(target, index, activeIndex) {
  var id = "docsViewerSemanticTargetOption-" + index;
  var active = index === activeIndex;
  return (
    '<button type="button" class="docsViewerSemanticPicker__row' + (active ? " is-active" : "") + '" ' +
      'id="' + id + '" role="option" aria-selected="' + (active ? "true" : "false") + '" data-target-index="' + index + '">' +
      '<span class="docsViewerSemanticPicker__rowMain">' +
        '<span class="docsViewerSemanticPicker__rowTitle">' + escapeHtml(target.title) + "</span>" +
        '<span class="docsViewerSemanticPicker__rowKind">' + escapeHtml(target.kind) + "</span>" +
        '<span class="docsViewerSemanticPicker__rowId">' + escapeHtml(target.id) + "</span>" +
      "</span>" +
      renderMeta(target) +
    "</button>"
  );
}

export function createSemanticTargetPickerList(root, options = {}) {
  var settings = options || {};
  var records = [];
  var activeIndex = -1;
  var onSelect = typeof settings.onSelect === "function" ? settings.onSelect : function () {};

  function render() {
    if (!root) return;
    root.innerHTML = records.map(function (target, index) {
      return rowMarkup(target, index, activeIndex);
    }).join("");
  }

  function setActiveIndex(index) {
    if (!records.length) {
      activeIndex = -1;
    } else {
      activeIndex = Math.max(0, Math.min(index, records.length - 1));
    }
    render();
  }

  function setTargets(nextRecords) {
    records = Array.isArray(nextRecords) ? nextRecords.slice() : [];
    activeIndex = records.length ? 0 : -1;
    render();
  }

  function selectIndex(index) {
    var record = records[index];
    if (!record) return false;
    onSelect(record);
    return true;
  }

  function handleKeydown(event) {
    if (!records.length) return false;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex(activeIndex + 1);
      return true;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex(activeIndex - 1);
      return true;
    }
    if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      return selectIndex(activeIndex);
    }
    return false;
  }

  function handleClick(event) {
    var button = event.target && event.target.closest ? event.target.closest("[data-target-index]") : null;
    if (!button || !root || !root.contains(button)) return;
    selectIndex(Number(button.getAttribute("data-target-index")));
  }

  if (root) root.addEventListener("click", handleClick);

  return {
    destroy: function () {
      if (root) root.removeEventListener("click", handleClick);
      records = [];
      if (root) root.replaceChildren();
    },
    handleKeydown: handleKeydown,
    selectedTarget: function () { return records[activeIndex] || null; },
    setActiveIndex: setActiveIndex,
    setTargets: setTargets,
    targetKey: targetKey
  };
}
