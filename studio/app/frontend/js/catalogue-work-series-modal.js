import { createCatalogueSeries, saveCatalogueSeries } from "./catalogue-editor-service-client.js";
import { catalogueSavedActionError } from "./catalogue-output-result.js";
import { suggestNextSeriesId } from "./catalogue-series-fields.js";
import { loadStudioServerReadJson } from "./studio-data.js";
import { activateStudioModalFrame, renderStudioModalFrame } from "./studio-modal.js";

/** Save one Series title independently of the Work draft; New stays local until OK. */
export async function openWorkSeriesTitleModal(state, { seriesId = "", restoreFocus } = {}) {
  let editingId = seriesId;
  let revision = "";
  let initialTitle = "";
  let saving = false;
  if (editingId) {
    const lookup = await loadStudioServerReadJson("catalogue_lookup_series_base", editingId, { cache: "no-store" });
    if (lookup.series?.series_id !== editingId || !lookup.record_hash || typeof lookup.series.title !== "string") {
      throw new Error("Series lookup is missing its record or revision.");
    }
    initialTitle = lookup.series.title;
    revision = lookup.record_hash;
  }

  const host = state.modalHost;
  host.innerHTML = renderStudioModalFrame({
    hidden: false,
    title: editingId ? "Edit Series" : "New Series",
    titleId: "catalogueSeriesTitleModalHeading",
    titleRole: "series-title-heading",
    modalRole: "studio-modal",
    backdropRole: "modal-cancel",
    size: "compact",
    bodyHtml: `
      <label class="studioForm__field" for="catalogueSeriesTitleInput">
        <span class="studioForm__label">title</span>
        <input class="studioUi__input" id="catalogueSeriesTitleInput" type="text" autocomplete="off">
      </label>
    `,
    includeStatus: true,
    actions: [
      { role: "modal-primary", label: "OK", primary: true },
      { role: "modal-cancel", label: "Cancel" },
      { role: "series-new", label: "New" }
    ]
  });
  const input = host.querySelector("#catalogueSeriesTitleInput");
  const primary = host.querySelector('[data-role="modal-primary"]');
  const cancel = host.querySelector('button[data-role="modal-cancel"]');
  const newButton = host.querySelector('[data-role="series-new"]');
  input.value = initialTitle;

  function syncControls() {
    input.disabled = saving;
    primary.disabled = saving || !input.value.trim();
    cancel.disabled = saving;
    newButton.disabled = saving || !editingId;
    host.querySelector('[role="dialog"]').setAttribute("aria-busy", String(saving));
  }

  const controller = activateStudioModalFrame(host, {
    restoreFocus,
    focusSelector: "#catalogueSeriesTitleInput",
    selectInitialFocus: true,
    canCancel: () => !saving,
    async onSubmit(api) {
      const title = input.value.trim();
      if (saving || !title) return false;
      saving = true;
      syncControls();
      api.setStatus("", "");
      let response = null;
      try {
        let targetId = editingId;
        if (!targetId) {
          const lookup = await loadStudioServerReadJson("catalogue_lookup_series_search", "", { cache: "no-store" });
          if (!Array.isArray(lookup.items)) throw new Error("Series search lookup is unavailable.");
          targetId = suggestNextSeriesId(lookup.items);
          response = await createCatalogueSeries({ series_id: targetId, record: { title } });
        } else {
          response = await saveCatalogueSeries({
            series_id: targetId, expected_record_hash: revision, record: { title }
          });
        }
        if (response.series_id !== targetId || response.record?.series_id !== targetId
          || typeof response.record.title !== "string" || !response.record_hash) {
          throw new Error("Series save response is missing its record or revision.");
        }
        return { seriesId: targetId, response };
      } catch (error) {
        api.setStatus("error", catalogueSavedActionError(response, error) || error.message);
        return false;
      } finally {
        saving = false;
        syncControls();
      }
    }
  });
  newButton.addEventListener("click", () => {
    if (saving) return;
    editingId = "";
    revision = "";
    input.value = "";
    host.querySelector('[data-role="series-title-heading"]').textContent = "New Series";
    controller.api.setStatus("", "");
    syncControls();
    input.focus();
  });
  input.addEventListener("input", syncControls);
  syncControls();
  state.activeModalController = controller;
  return controller.promise.finally(() => {
    if (state.activeModalController === controller) state.activeModalController = null;
  });
}
