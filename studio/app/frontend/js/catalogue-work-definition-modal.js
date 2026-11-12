import { catalogueSavedActionError } from "./catalogue-save-result.js";
import { activateStudioModalFrame, renderStudioModalFrame } from "./studio-modal.js";

function titleComparisonKey(value) {
  return String(value ?? "").trim().replace(/\s+/g, " ").toLowerCase();
}

/** Create or edit a shared definition; deletion has its own confirmation. */
export async function openWorkDefinitionModal(state, {
  kind, id = "", title = "", deleteMessage = "", deleteBlocked = "",
  checkbox = null, save, remove, restoreFocus, onBusyChange,
  deleteOnly = false, cancelLabel = "Cancel", chooseKind = false
}) {
  const host = state.modalHost;
  let saving = false;
  let confirmingDelete = false;
  host.innerHTML = renderStudioModalFrame({
    hidden: false, title: chooseKind ? "New Series or Gallery" : `${id ? "Edit" : "New"} ${kind}`,
    titleId: "catalogueDefinitionHeading", titleRole: "definition-heading",
    modalRole: "studio-modal", backdropRole: "modal-cancel", size: "compact",
    bodyHtml: `
      ${chooseKind ? `<fieldset class="catalogueDefinition__kind">
        <legend class="studioForm__label">Type</legend>
        <label><input type="radio" name="catalogue-definition-kind" value="Series"${kind === "Series" ? " checked" : ""}> Series</label>
        <label><input type="radio" name="catalogue-definition-kind" value="Gallery"${kind === "Gallery" ? " checked" : ""}> Gallery</label>
      </fieldset>` : ""}
      <label class="studioForm__field" data-role="definition-field" for="catalogueDefinitionTitle">
        <span class="studioForm__label">title</span>
        <input class="studioUi__input" id="catalogueDefinitionTitle" type="text" autocomplete="off" aria-describedby="catalogueDefinitionTitleWarning">
      </label>
      <p class="studioForm__status studioUi__status" id="catalogueDefinitionTitleWarning" data-role="definition-title-warning" data-state="warn" aria-live="polite" hidden></p>
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
      ...(id && remove ? [{ role: "definition-delete", label: "Delete", disabled: Boolean(deleteBlocked) }] : [])
    ]
  });
  const input = host.querySelector("#catalogueDefinitionTitle");
  const titleWarning = host.querySelector('[data-role="definition-title-warning"]');
  const kindInputs = Array.from(host.querySelectorAll('[name="catalogue-definition-kind"]'));
  const selectedKind = () => kindInputs.find(option => option.checked)?.value ?? kind;
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

  function syncTitleWarning() {
    const key = titleComparisonKey(input.value);
    const activeKind = selectedKind();
    const definitions = activeKind === "Series" ? state.seriesById : state.galleriesById;
    let duplicateId = "";
    if (key && !confirmingDelete) {
      for (const [otherId, record] of definitions) {
        if (otherId !== id && titleComparisonKey(record.title) === key) {
          duplicateId = otherId;
          break;
        }
      }
    }
    titleWarning.textContent = duplicateId
      ? `Another ${activeKind} uses this title (${duplicateId}). You can still save.`
      : "";
    titleWarning.hidden = !duplicateId;
  }

  function syncControls() {
    input.disabled = saving;
    kindInputs.forEach(option => { option.disabled = saving; });
    if (checkboxInput) checkboxInput.disabled = saving || checkbox.disabled;
    primary.disabled = saving || (!confirmingDelete && !input.value.trim());
    cancel.disabled = saving;
    if (deleteButton) deleteButton.disabled = saving || Boolean(deleteBlocked);
    dialog.setAttribute("aria-busy", String(saving));
    syncTitleWarning();
  }

  const controller = activateStudioModalFrame(host, {
    restoreFocus,
    focusSelector: chooseKind ? '[name="catalogue-definition-kind"]:checked' : "#catalogueDefinitionTitle",
    selectInitialFocus: !chooseKind, submitOnEnter: false,
    canCancel: () => !saving,
    async onSubmit(api) {
      if (saving || primary.disabled) return false;
      const activeKind = selectedKind();
      saving = true;
      syncControls();
      api.setStatus("", "");
      let response = null;
      try {
        onBusyChange?.(true);
        response = confirmingDelete ? await remove() : await save({
          kind: activeKind, title: input.value.trim(), related: checkboxInput?.checked
        });
        return { kind: activeKind, response };
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
    if (!deleteButton || saving || deleteBlocked) return;
    confirmingDelete = true;
    host.querySelector('[data-role="definition-field"]').hidden = true;
    const checkboxField = host.querySelector('[data-role="definition-checkbox-field"]');
    if (checkboxField) checkboxField.hidden = true;
    const confirmation = host.querySelector('[data-role="delete-confirmation"]');
    confirmation.textContent = typeof deleteMessage === "function" ? deleteMessage() : deleteMessage;
    confirmation.hidden = false;
    host.querySelector('[data-role="definition-heading"]').textContent = `Delete ${kind}?`;
    reason.hidden = true;
    deleteButton.hidden = true;
    primary.textContent = deleteOnly ? `Delete ${kind}` : "Delete";
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
  kindInputs.forEach(option => option.addEventListener("change", syncTitleWarning));
  syncControls();
  state.activeModalController = controller;
  if (deleteOnly) showDeleteConfirmation();
  return controller.promise.finally(() => {
    if (state.activeModalController === controller) state.activeModalController = null;
  });
}
