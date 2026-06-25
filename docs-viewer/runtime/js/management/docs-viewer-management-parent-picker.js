import {
  renderMetadataParentPopupMarkup
} from "./docs-viewer-management-render.js";

var PARENT_PICKER_TEXT = {
  rootOption: "Root",
  noMatches: "No matching parent docs."
};

function parentOptions(callbacks, doc) {
  return typeof callbacks.metadataParentOptions === "function" ? callbacks.metadataParentOptions(doc) : [];
}

function parentOptionTitle(state, option) {
  if (!option || !option.value) return PARENT_PICKER_TEXT.rootOption;
  return String(option.label || "").replace(/^(-\s*)+/, "");
}

function parentOptionDisplay(state, option) {
  return parentOptionTitle(state, option);
}

function parentMatchRank(state, option, query) {
  var display = parentOptionDisplay(state, option).toLowerCase();
  var title = parentOptionTitle(state, option).toLowerCase();
  var value = String(option && option.value || "").toLowerCase();
  if (value === query) return 0;
  if (title === query || display === query) return 1;
  if (value.startsWith(query)) return 2;
  if (title.startsWith(query) || display.startsWith(query)) return 3;
  if (value.includes(query)) return 4;
  if (title.includes(query) || display.includes(query)) return 5;
  return null;
}

export function createDocsViewerMetadataParentPicker(options = {}) {
  var refs = options.refs || {};
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var optionRecords = [];
  var activeIndex = -1;

  function hidePopup() {
    optionRecords = [];
    activeIndex = -1;
    if (refs.metadataParentPopup) {
      refs.metadataParentPopup.hidden = true;
      refs.metadataParentPopup.innerHTML = "";
    }
    if (refs.metadataParentInput) {
      refs.metadataParentInput.setAttribute("aria-expanded", "false");
      refs.metadataParentInput.removeAttribute("aria-activedescendant");
    }
  }

  function setActiveIndex(index) {
    if (!refs.metadataParentPopup || !refs.metadataParentInput) return;
    activeIndex = index;
    refs.metadataParentPopup.querySelectorAll("[data-parent-index]").forEach(function (button) {
      var active = Number(button.getAttribute("data-parent-index")) === activeIndex;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
      if (active) {
        refs.metadataParentInput.setAttribute("aria-activedescendant", button.id);
      }
    });
    if (activeIndex < 0) {
      refs.metadataParentInput.removeAttribute("aria-activedescendant");
    }
  }

  function matches(doc, query) {
    var normalizedQuery = String(query || "").trim().toLowerCase();
    if (!normalizedQuery) return [];
    return parentOptions(callbacks, doc).map(function (option, index) {
      return {
        index: index,
        option: option,
        rank: parentMatchRank(state, option, normalizedQuery)
      };
    }).filter(function (match) {
      return match.rank !== null;
    }).sort(function (left, right) {
      if (left.rank !== right.rank) return left.rank - right.rank;
      return left.index - right.index;
    }).slice(0, 14).map(function (match) {
      return match.option;
    });
  }

  function renderPopup(doc) {
    if (!refs.metadataParentInput || !refs.metadataParentPopup) return;
    var records = matches(doc, refs.metadataParentInput.value);
    optionRecords = records;
    if (!String(refs.metadataParentInput.value || "").trim()) {
      hidePopup();
      return;
    }
    if (!records.length) {
      refs.metadataParentPopup.innerHTML = renderMetadataParentPopupMarkup(records, {
        emptyText: PARENT_PICKER_TEXT.noMatches
      });
      refs.metadataParentPopup.hidden = false;
      refs.metadataParentInput.setAttribute("aria-expanded", "true");
      activeIndex = -1;
      refs.metadataParentInput.removeAttribute("aria-activedescendant");
      return;
    }
    refs.metadataParentPopup.innerHTML = renderMetadataParentPopupMarkup(records, {
      optionTitle: function (option) {
        return parentOptionTitle(state, option);
      }
    });
    refs.metadataParentPopup.hidden = false;
    refs.metadataParentInput.setAttribute("aria-expanded", "true");
    setActiveIndex(0);
  }

  function selectOption(index) {
    var option = optionRecords[index];
    if (!option || !refs.metadataParentInput) return;
    refs.metadataParentInput.value = parentOptionDisplay(state, option);
    hidePopup();
    refs.metadataParentInput.focus();
  }

  function renderOptions(doc) {
    if (!refs.metadataParentInput) return;
    var currentParentId = String(doc && doc.parent_id || "").trim();
    var records = parentOptions(callbacks, doc);
    var currentOption = records.find(function (option) {
      return option.value === currentParentId;
    }) || records[0];
    refs.metadataParentInput.value = parentOptionDisplay(state, currentOption);
    hidePopup();
  }

  function resolveParentId(doc) {
    if (!refs.metadataParentInput) return "";
    var inputValue = String(refs.metadataParentInput.value || "").trim();
    var rootLabel = PARENT_PICKER_TEXT.rootOption;
    if (!inputValue || inputValue.toLowerCase() === rootLabel.toLowerCase()) return "";
    var records = parentOptions(callbacks, doc);
    var exactDocId = records.find(function (option) {
      return option.value && option.value === inputValue;
    });
    if (exactDocId) return exactDocId.value;
    var exactTitle = records.filter(function (option) {
      return option.value && option.label.replace(/^(-\s*)+/, "") === inputValue;
    });
    if (exactTitle.length === 1) return exactTitle[0].value;
    return null;
  }

  function dismissSuggestions() {
    if (!refs.metadataParentInput) return;
    refs.metadataParentInput.blur();
    refs.metadataParentInput.value = "";
    hidePopup();
  }

  function moveActive(delta) {
    if (!optionRecords.length) return;
    var nextIndex = activeIndex + delta;
    if (delta > 0) nextIndex = Math.min(nextIndex, optionRecords.length - 1);
    if (delta < 0) nextIndex = Math.max(nextIndex, 0);
    setActiveIndex(nextIndex);
  }

  function handleInputKeydown(event, doc) {
    if (!refs.metadataParentPopup || refs.metadataParentPopup.hidden) {
      if (event.key === "ArrowDown" && doc) renderPopup(doc);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(-1);
      return;
    }
    if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      selectOption(activeIndex);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      hidePopup();
    }
  }

  return {
    dismissSuggestions: dismissSuggestions,
    handleInputKeydown: handleInputKeydown,
    hidePopup: hidePopup,
    renderOptions: renderOptions,
    renderPopup: renderPopup,
    resolveParentId: resolveParentId,
    selectOption: selectOption
  };
}
