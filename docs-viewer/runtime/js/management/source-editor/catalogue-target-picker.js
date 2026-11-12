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

function rowMarkup(target, index, activeIndex, settings) {
  var id = "docsViewerCatalogueTargetOption-" + index;
  var active = index === activeIndex;
  var presentation = presentationFor(target, settings);
  var idTitleLayout = settings.layout === "id-title";
  var thumbnailColumn = idTitleLayout && typeof settings.thumbnailSrc === "function";
  var thumbnailSrc = thumbnailColumn ? settings.thumbnailSrc(target) : "";
  var thumbnail = thumbnailSrc
    ? '<img class="docsViewerCatalogueTargetPicker__rowThumb" src="' + escapeHtml(thumbnailSrc) +
      '" width="48" height="48" alt="" loading="lazy" decoding="async">'
    : '<span aria-hidden="true"></span>';
  var main = idTitleLayout
    ? (thumbnailColumn ? thumbnail : "") +
      '<span class="docsViewerCatalogueTargetPicker__rowId">' + escapeHtml(presentation.id) + "</span>" +
      '<span class="docsViewerCatalogueTargetPicker__rowTitle">' + escapeHtml(presentation.title) + "</span>"
    : '<span class="docsViewerCatalogueTargetPicker__rowTitle">' + escapeHtml(presentation.title) + "</span>" +
      '<span class="docsViewerCatalogueTargetPicker__rowKind">' + escapeHtml(presentation.kind) + "</span>" +
      '<span class="docsViewerCatalogueTargetPicker__rowId">' + escapeHtml(presentation.id) + "</span>";
  return (
    '<div class="docsViewerCatalogueTargetPicker__row' + (active ? " is-active" : "") + '" ' +
      'id="' + id + '" role="option" aria-selected="false" data-target-index="' + index + '">' +
      '<span class="docsViewerCatalogueTargetPicker__rowMain' +
        (idTitleLayout ? " docsViewerCatalogueTargetPicker__rowMain--idTitle" : "") +
        (thumbnailColumn ? " docsViewerCatalogueTargetPicker__rowMain--thumbnail" : "") + '">' +
        main +
      "</span>" +
      (idTitleLayout ? "" : renderMeta(presentation)) +
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
    var nextIndex = records.length ? Math.max(0, Math.min(index, records.length - 1)) : -1;
    if (nextIndex !== activeIndex) {
      root?.children[activeIndex]?.classList.remove("is-active");
      activeIndex = nextIndex;
      root?.children[activeIndex]?.classList.add("is-active");
    }
    notifyActiveChange();
    revealActive();
  }

  function setTargets(nextRecords) {
    records = Array.isArray(nextRecords) ? nextRecords.slice() : [];
    activeIndex = records.length ? 0 : -1;
    selectedIndex = -1;
    if (root) {
      root.innerHTML = records.map(function (target, index) {
        return rowMarkup(target, index, activeIndex, settings);
      }).join("");
      root.scrollTop = 0;
    }
    notifyActiveChange();
  }

  function selectIndex(index) {
    var record = records[index];
    if (!record) return false;
    var previous = root?.children[selectedIndex];
    previous?.classList.remove("is-selected");
    previous?.setAttribute("aria-selected", "false");
    selectedIndex = index;
    var selected = root?.children[index];
    selected?.classList.add("is-selected");
    selected?.setAttribute("aria-selected", "true");
    setActiveIndex(index);
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

  function hideFailedThumbnail(event) {
    if (event.target.classList.contains("docsViewerCatalogueTargetPicker__rowThumb")) {
      event.target.style.visibility = "hidden";
    }
  }

  if (root) {
    root.addEventListener("click", handleClick);
    if (settings.thumbnailSrc) root.addEventListener("error", hideFailedThumbnail, true);
  }

  return {
    destroy: function () {
      if (root) {
        root.removeEventListener("click", handleClick);
        if (settings.thumbnailSrc) root.removeEventListener("error", hideFailedThumbnail, true);
        root.replaceChildren();
      }
      records = [];
      activeIndex = -1;
      selectedIndex = -1;
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
