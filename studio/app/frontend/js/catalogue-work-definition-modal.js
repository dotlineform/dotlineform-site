import { catalogueSavedActionError } from "./catalogue-output-result.js";
import { activateStudioModalFrame, renderStudioModalFrame } from "./studio-modal.js";

/** Edit one shared definition; deletion replaces the form with an explicit confirmation. */
export async function openWorkDefinitionModal(state, {
  kind, id = "", title = "", deleteMessage = "", deleteBlocked = "",
  save, remove, restoreFocus, onBusyChange
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
      <p class="studioForm__meta" data-role="delete-reason" hidden></p>
      <p class="studioModal__label" data-role="delete-confirmation" hidden></p>
    `,
    includeStatus: true,
    actions: [
      { role: "modal-primary", label: "OK", primary: true },
      { role: "modal-cancel", label: "Cancel" },
      ...(id ? [{ role: "definition-delete", label: "Delete", disabled: Boolean(deleteBlocked) }] : [])
    ]
  });
  const input = host.querySelector("#catalogueDefinitionTitle");
  const primary = host.querySelector('[data-role="modal-primary"]');
  const cancel = host.querySelector('button[data-role="modal-cancel"]');
  const deleteButton = host.querySelector('[data-role="definition-delete"]');
  const reason = host.querySelector('[data-role="delete-reason"]');
  const dialog = host.querySelector('[role="dialog"]');
  input.value = title;
  reason.textContent = deleteBlocked;
  reason.hidden = !deleteBlocked;

  function syncControls() {
    input.disabled = saving;
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
        response = confirmingDelete ? await remove() : await save(input.value.trim());
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
  deleteButton?.addEventListener("click", () => {
    if (saving || deleteBlocked) return;
    confirmingDelete = true;
    host.querySelector('[data-role="definition-field"]').hidden = true;
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
  });
  input.addEventListener("keydown", event => {
    if (event.key !== "Enter" || confirmingDelete) return;
    event.preventDefault();
    void controller.submit();
  });
  input.addEventListener("input", syncControls);
  syncControls();
  state.activeModalController = controller;
  return controller.promise.finally(() => {
    if (state.activeModalController === controller) state.activeModalController = null;
  });
}
