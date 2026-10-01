let searchFieldId = 0;

/**
 * Wrap a caller-owned search input with a focus icon and a query-clear button.
 * The input keeps its identity, labels and listeners. Clearing emits its ordinary
 * bubbling input event; the caller still owns filtering, selection and persistence.
 * Call once after placing the input in its host. No document-level listeners remain.
 * @param {HTMLInputElement} input Existing search or autocomplete input.
 * @param {{clearLabel?: string}} [options] Accessible name for the clear button.
 * @returns {{root: HTMLSpanElement, clearButton: HTMLButtonElement}} Mounted controls.
 */
export function mountSearchField(input, options = {}) {
  const documentRef = input.ownerDocument;
  if (!input.id) input.id = `sharedSearchField-${++searchFieldId}`;
  if (!input.placeholder) input.placeholder = "search";
  input.classList.add("sharedSearchField__input");

  const root = documentRef.createElement("span");
  root.className = "sharedSearchField";
  const icon = documentRef.createElement("span");
  icon.className = "sharedSearchField__icon";
  icon.setAttribute("aria-hidden", "true");
  const text = documentRef.createElement("span");
  text.className = "sharedSearchField__text";
  const clearButton = documentRef.createElement("button");
  clearButton.className = "sharedSearchField__clear";
  clearButton.type = "button";
  clearButton.setAttribute("aria-label", options.clearLabel || "Clear search");
  const clearIcon = documentRef.createElement("span");
  clearIcon.className = "sharedSearchField__clearIcon";
  clearIcon.setAttribute("aria-hidden", "true");
  clearButton.append(clearIcon);

  input.replaceWith(root);
  text.append(input, clearButton);
  root.append(icon, text);
  icon.addEventListener("pointerdown", event => {
    if (event.button !== 0 || input.disabled) return;
    event.preventDefault();
    input.focus();
  });
  icon.addEventListener("click", () => { if (!input.disabled) input.focus(); });
  clearButton.addEventListener("pointerdown", event => {
    // Preserve autocomplete queries that the owner otherwise restores on blur.
    if (event.button === 0) event.preventDefault();
  });
  clearButton.addEventListener("click", () => {
    if (input.disabled || input.readOnly) return;
    input.value = "";
    input.focus();
    input.dispatchEvent(new documentRef.defaultView.Event("input", { bubbles: true }));
  });
  return { root, clearButton };
}
