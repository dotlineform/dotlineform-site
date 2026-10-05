import { catalogueSavedActionError } from "./catalogue-save-result.js";
import { activateStudioModalFrame, renderStudioModalFrame } from "./studio-modal.js";

/** Edit one shared definition; deletion replaces the form with an explicit confirmation. */
export async function openWorkDefinitionModal(state, {
  kind, id = "", title = "", deleteMessage = "", deleteBlocked = "",
  checkbox = null, save, remove, restoreFocus, onBusyChange,
  deleteOnly = false, cancelLabel = "Cancel"
}) {
  const host = state.modalHost;
  let saving = false;
  let confirmingDelete = false;
  host.innerHTML = renderStudioModalFrame({
    hidden: false, title: `${id ? "Edit" : "New"} ${kind}`,
    titleId: "catalogueDefinitionHeading", titleRole: "definition-heading",
    modalRole: "studio-modal", backdropRole: "modal-cancel", size: "compact",
    bodyHtml: `
      <label class="studioForm__field" data-role="definition-field" for="catalogueDefinitionTitle">
        <span class="studioForm__label">title</span>
        <input class="studioUi__input" id="catalogueDefinitionTitle" type="text" autocomplete="off">
      </label>
      ${checkbox ? `<div class="catalogueDefinition__relation" data-role="definition-checkbox-field">
        <label class="catalogueDefinition__checkboxRow" for="catalogueDefinitionCheckbox">
          <input id="catalogueDefinitionCheckbox" type="checkbox" aria-describedby="catalogueDefinitionSeriesContext">
          <span data-role="definition-checkbox-label"></span>
        </label>
        <p class="studioForm__meta" id="catalogueDefinitionSeriesContext" data-role="definition-checkbox-context"></p>
      </div>` : ""}
      <p class="studioForm__meta" data-role="delete-reason" hidden></p>
      <p class="studioModal__label" data-role="delete-confirmation" hidden></p>
    `,
    includeStatus: true,
    actions: [
      { role: "modal-primary", label: "OK", primary: true },
      { role: "modal-cancel", label: cancelLabel },
      ...(id ? [{ role: "definition-delete", label: "Delete", disabled: Boolean(deleteBlocked) }] : [])
    ]
  });
  const input = host.querySelector("#catalogueDefinitionTitle");
  const checkboxInput = host.querySelector("#catalogueDefinitionCheckbox");
  const primary = host.querySelector('[data-role="modal-primary"]');
  const cancel = host.querySelector('button[data-role="modal-cancel"]');
  const deleteButton = host.querySelector('[data-role="definition-delete"]');
  const reason = host.querySelector('[data-role="delete-reason"]');
  const dialog = host.querySelector('[role="dialog"]');
  input.value = title;
  if (checkboxInput) {
    checkboxInput.checked = Boolean(checkbox.checked);
    host.querySelector('[data-role="definition-checkbox-label"]').textContent = checkbox.label;
    host.querySelector('[data-role="definition-checkbox-context"]').textContent = checkbox.context;
  }
  reason.textContent = deleteBlocked;
  reason.hidden = !deleteBlocked;

  function syncControls() {
    input.disabled = saving;
    if (checkboxInput) checkboxInput.disabled = saving || checkbox.disabled;
    primary.disabled = saving || (!confirmingDelete && !input.value.trim());
    cancel.disabled = saving;
    if (deleteButton) deleteButton.disabled = saving || Boolean(deleteBlocked);
    dialog.setAttribute("aria-busy", String(saving));
  }

  const controller = activateStudioModalFrame(host, {
    restoreFocus, focusSelector: "#catalogueDefinitionTitle", selectInitialFocus: true, submitOnEnter: false,
    canCancel: () => !saving,
    async onSubmit(api) {
      if (saving || primary.disabled) return false;
      saving = true;
      syncControls();
      api.setStatus("", "");
      let response = null;
      try {
        onBusyChange?.(true);
        response = confirmingDelete ? await remove() : await save(input.value.trim(), checkboxInput?.checked);
        return { response };
      } catch (error) {
        api.setStatus("error", catalogueSavedActionError(response, error) || error.message);
        return false;
      } finally {
        saving = false;
        onBusyChange?.(false);
        syncControls();
      }
    }
  });
  function showDeleteConfirmation() {
    if (saving || deleteBlocked) return;
    confirmingDelete = true;
    host.querySelector('[data-role="definition-field"]').hidden = true;
    const checkboxField = host.querySelector('[data-role="definition-checkbox-field"]');
    if (checkboxField) checkboxField.hidden = true;
    const confirmation = host.querySelector('[data-role="delete-confirmation"]');
    confirmation.textContent = deleteMessage;
    confirmation.hidden = false;
    host.querySelector('[data-role="definition-heading"]').textContent = `Delete ${kind}?`;
    reason.hidden = true;
    deleteButton.hidden = true;
    primary.textContent = "Delete";
    primary.classList.remove("studioUi__button--defaultAction");
    cancel.classList.add("studioUi__button--defaultAction");
    controller.api.setStatus("", "");
    syncControls();
    cancel.focus();
  }
  deleteButton?.addEventListener("click", showDeleteConfirmation);
  input.addEventListener("keydown", event => {
    if (event.key !== "Enter" || confirmingDelete) return;
    event.preventDefault();
    void controller.submit();
  });
  input.addEventListener("input", syncControls);
  syncControls();
  state.activeModalController = controller;
  if (deleteOnly) showDeleteConfirmation();
  return controller.promise.finally(() => {
    if (state.activeModalController === controller) state.activeModalController = null;
  });
}
