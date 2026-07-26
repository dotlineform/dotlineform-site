import {
  escapeHtml
} from "../../shared/docs-viewer-render.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function valueFrom(settings, key, target) {
  var accessor = settings && typeof settings[key] === "function" ? settings[key] : null;
  return accessor ? accessor(target) : target && target[key];
}

function presentationFor(target, settings) {
  return {
    id: cleanString(valueFrom(settings, "id", target)),
    kind: cleanString(valueFrom(settings, "kind", target)),
    meta: Array.isArray(valueFrom(settings, "meta", target))
      ? valueFrom(settings, "meta", target).map(cleanString).filter(Boolean)
      : [],
    title: cleanString(valueFrom(settings, "title", target))
  };
}

function renderMeta(presentation) {
  var meta = presentation.meta;
  if (!meta.length) return "";
  return '<span class="docsViewerCatalogueTargetPicker__rowMeta">' + meta.map(escapeHtml).join(" · ") + "</span>";
}

function targetKey(target, settings) {
  var presentation = presentationFor(target, settings);
  return presentation.kind + ":" + presentation.id;
}

function rowMarkup(target, index, activeIndex, selectedIndex, settings) {
  var id = "docsViewerCatalogueTargetOption-" + index;
  var active = index === activeIndex;
  var selected = index === selectedIndex;
  var presentation = presentationFor(target, settings);
  return (
    '<div class="docsViewerCatalogueTargetPicker__row' + (active ? " is-active" : "") + (selected ? " is-selected" : "") + '" ' +
      'id="' + id + '" role="option" aria-selected="' + (selected ? "true" : "false") + '" data-target-index="' + index + '">' +
      '<span class="docsViewerCatalogueTargetPicker__rowMain">' +
        '<span class="docsViewerCatalogueTargetPicker__rowTitle">' + escapeHtml(presentation.title) + "</span>" +
        '<span class="docsViewerCatalogueTargetPicker__rowKind">' + escapeHtml(presentation.kind) + "</span>" +
        '<span class="docsViewerCatalogueTargetPicker__rowId">' + escapeHtml(presentation.id) + "</span>" +
      "</span>" +
      renderMeta(presentation) +
    "</div>"
  );
}

export function createCatalogueTargetPickerList(root, options = {}) {
  var settings = options || {};
  var records = [];
  var activeIndex = -1;
  var selectedIndex = -1;
  var onSelect = typeof settings.onSelect === "function" ? settings.onSelect : function () {};
  var onActiveChange = typeof settings.onActiveChange === "function"
    ? settings.onActiveChange
    : function () {};

  function render() {
    if (!root) return;
    root.innerHTML = records.map(function (target, index) {
      return rowMarkup(target, index, activeIndex, selectedIndex, settings);
    }).join("");
  }

  function activeOptionId() {
    return activeIndex >= 0 ? "docsViewerCatalogueTargetOption-" + activeIndex : "";
  }

  function notifyActiveChange() {
    onActiveChange(records[activeIndex] || null, activeOptionId());
  }

  function revealActive() {
    if (!root || activeIndex < 0) return;
    var active = root.querySelector('[data-target-index="' + activeIndex + '"]');
    if (active && typeof active.scrollIntoView === "function") {
      active.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  function setActiveIndex(index) {
    if (!records.length) {
      activeIndex = -1;
    } else {
      activeIndex = Math.max(0, Math.min(index, records.length - 1));
    }
    render();
    notifyActiveChange();
    revealActive();
  }

  function setTargets(nextRecords) {
    records = Array.isArray(nextRecords) ? nextRecords.slice() : [];
    activeIndex = records.length ? 0 : -1;
    selectedIndex = -1;
    render();
    if (root) root.scrollTop = 0;
    notifyActiveChange();
  }

  function selectIndex(index) {
    var record = records[index];
    if (!record) return false;
    activeIndex = index;
    selectedIndex = index;
    render();
    notifyActiveChange();
    revealActive();
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
      activeIndex = -1;
      selectedIndex = -1;
      if (root) root.replaceChildren();
      notifyActiveChange();
    },
    activeOptionId: activeOptionId,
    handleKeydown: handleKeydown,
    selectedTarget: function () { return records[selectedIndex] || null; },
    setActiveIndex: setActiveIndex,
    setTargets: setTargets,
    selectTarget: function (target) {
      var key = targetKey(target, settings);
      return selectIndex(records.findIndex(function (record) {
        return targetKey(record, settings) === key;
      }));
    },
    targetKey: function (target) { return targetKey(target, settings); }
  };
}
