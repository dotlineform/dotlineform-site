const CUSTOMISATION_ID = "analysis_tags";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeFilterValue(value) {
  return cleanString(value).normalize("NFKC").replace(/\s+/g, " ").toLowerCase();
}

function normalizedGroups(data) {
  var values = data && Array.isArray(data.groups) ? data.groups : [];
  var seen = new Set();
  return values.map(normalizeFilterValue).filter(function (value) {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function groupFilter(groups) {
  return {
    id: "group",
    initialValue: "",
    matches: function (context) {
      var value = normalizeFilterValue(context && context.value);
      var documentRecord = context && context.document;
      var customisation = documentRecord && documentRecord.customisation;
      return !value || normalizeFilterValue(customisation && customisation.group) === value;
    },
    render: function (context) {
      var settings = context || {};
      var host = settings.host;
      if (!host || typeof settings.setValue !== "function") return;
      var activeValue = normalizeFilterValue(settings.value);
      host.setAttribute("role", "group");
      host.setAttribute("aria-label", "Filter Tags by group");
      ["", ...groups].forEach(function (group) {
        var button = host.ownerDocument.createElement("button");
        button.className = "docsViewerReport__filter";
        button.type = "button";
        button.dataset.docsSubscopeGroup = group;
        button.textContent = group || "all";
        button.setAttribute("aria-pressed", group === activeValue ? "true" : "false");
        button.addEventListener("click", function () {
          settings.setValue(group);
        });
        host.appendChild(button);
      });
    }
  };
}

export function createDocsViewerManagementSubscopeAnalysisTags(options = {}) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== CUSTOMISATION_ID) {
    throw new Error("Analysis/Tags customisation identity did not match its registry entry.");
  }
  return {
    id: CUSTOMISATION_ID,
    createFilters: function (context) {
      var groups = normalizedGroups(context && context.data);
      if (!groups.length) {
        throw new Error("Analysis/Tags customisation requires manifest groups.");
      }
      return [groupFilter(groups)];
    }
  };
}
