import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { bindSearchList } from "/shared/frontend/js/search-list.js";
import { matchingWorkMediumSuggestions } from "./catalogue-work-medium-data.js";

function escapeHtml(value) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/** Mount an ordinary Medium draft field with optional saved-value suggestions. */
export function renderWorkMediumField(field, fieldsNode, state, options) {
  const document = fieldsNode.ownerDocument;
  const wrapper = document.createElement("div");
  wrapper.className = "studioForm__field catalogueWorkForm__field";
  const label = document.createElement("label");
  label.className = "studioForm__label";
  label.textContent = field.label;
  label.htmlFor = `catalogueWorkField-${field.key}`;
  const control = document.createElement("div");
  control.className = "sharedSearchList__control";
  const input = document.createElement("input");
  input.type = "text";
  input.className = "studioUi__input";
  input.id = label.htmlFor;
  input.dataset.field = field.key;
  input.autocomplete = "off";
  const popup = document.createElement("div");
  control.append(input, popup);
  const searchField = mountSearchField(input, { clearLabel: "Clear medium" });
  searchField.clearButton.tabIndex = -1;
  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.append(label, control, message);
  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
  input.addEventListener("click", () => input.select());
  const notifyInput = () => options.onFieldInput(field.key);
  input.addEventListener("input", notifyInput);
  input.addEventListener("change", notifyInput);
  state.mediumSearch = bindSearchList(input, popup, {
    id: "catalogueWorkMediumSuggestions",
    freeEntry: true,
    openOnFocus: false,
    shouldOpen: () => !input.disabled && !input.readOnly && input.value.trim().length >= 2,
    loadOptions: () => state.mediumOptions,
    filterOptions: matchingWorkMediumSuggestions,
    // Every matching saved value fits in the existing scrollable popup.
    maxOptions: Number.MAX_SAFE_INTEGER,
    getOptionValue: suggestion => suggestion.value,
    renderOption: suggestion => `<span class="sharedSearchList__optionText">${escapeHtml(suggestion.value)}</span>`,
    noResultsText: "No matching saved medium. You can keep your own text.",
    onCommit: notifyInput
  });
}
