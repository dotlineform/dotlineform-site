import {
  SERIES_EDITABLE_FIELDS as EDITABLE_FIELDS,
  normalizeText
} from "./catalogue-series-fields.js";

function formText(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((text, [token, value]) => {
    return text.replace(new RegExp(`\\{${token}\\}`, "g"), value == null ? "" : String(value));
  }, fallback);
}

function notifyFieldInput(options, fieldKey) {
  if (options && typeof options.onFieldInput === "function") {
    options.onFieldInput(fieldKey);
  }
}

export function refreshSeriesTypeOptions(state) {
  const node = state.fieldNodes.get("series_type");
  if (!node || node.tagName !== "SELECT") return;
  const current = normalizeText(node.value || state.draft.series_type).toLowerCase();
  node.innerHTML = "";
  const options = state.seriesTypeOptions.slice();
  if (current && !options.includes(current)) options.push(current);
  options.forEach((optionValue) => {
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = optionValue || "(blank)";
    node.appendChild(option);
  });
  if (current) node.value = current;
}

function renderField(field, fieldsNode, state, options) {
  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "studioForm__field catalogueWorkForm__field";
  if (field.type === "textarea") wrapper.classList.add("studioForm__field--topAligned", "catalogueWorkForm__field--topAligned");
  if (!field.readonly) wrapper.htmlFor = `catalogueSeriesField-${field.key}`;

  const label = document.createElement("span");
  label.className = "studioForm__label";
  label.dataset.fieldLabel = field.key;
  label.textContent = formText(options, `field_label_${field.key}`, field.label);
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "studioUi__input studioUi__input--readonlyDisplay";
  } else if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.className = "studioUi__input studioForm__descriptionInput";
    input.rows = 4;
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "studioUi__input";
    const optionsList = field.key === "series_type" ? state.seriesTypeOptions : field.options;
    optionsList.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "studioUi__input";
    input.type = field.type === "date" ? "date" : "text";
    if (field.type === "number") {
      input.inputMode = field.step && String(field.step).includes(".") ? "decimal" : "numeric";
    }
  }

  input.id = `catalogueSeriesField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  if (!field.readonly) {
    input.addEventListener("input", () => notifyFieldInput(options, field.key));
    input.addEventListener("change", () => notifyFieldInput(options, field.key));
  }
  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

export function renderSeriesEditorFields(fieldsNode, state, options = {}) {
  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state, options));
}

export function setSeriesFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = text || "-";
  }
}

export function getSeriesFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

export function applySeriesDraftToInputs(state) {
  refreshSeriesTypeOptions(state);
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    setSeriesFieldNodeValue(node, normalizeText(state.draft[field.key]));
  });
}

export function setSeriesModeFieldAvailability(state) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    let disabled = state.isSaving || state.isBuilding || state.isDeleting;
    if (state.mode === "new" && (field.key === "status" || field.key === "published_date" || field.key === "primary_work_id")) {
      disabled = true;
    }
    if ("disabled" in node) node.disabled = disabled;
    if (field.readonly) {
      if ("disabled" in node) node.disabled = false;
      if ("readOnly" in node) node.readOnly = true;
    }
  });
}

export function updateSeriesFieldMessages(state, errors) {
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldStatusNodes.get(field.key);
    if (!node) return;
    const message = errors.get(field.key) || "";
    node.textContent = message;
    node.hidden = !message;
  });
}
