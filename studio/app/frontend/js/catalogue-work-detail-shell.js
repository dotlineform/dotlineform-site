import {
  readCatalogueEditorMediaAttrs,
  renderMediaAttrs
} from "./catalogue-editor-shell-media.js";

export function renderCatalogueWorkDetailShell(config) {
  const mediaAttrs = renderMediaAttrs(readCatalogueEditorMediaAttrs(config), [
    "thumbWorkDetailsBase",
    "thumbSizes",
    "thumbSuffix",
    "assetFormat"
  ]);
  return `<div
          class="tagStudioPage catalogueWorkPage"
          id="catalogueWorkDetailRoot"
          hidden
          ${mediaAttrs}
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueWorkDetailSearchGlobal">Find detail by id</label>
                <input type="text" class="tagStudio__input" id="catalogueWorkDetailSearchGlobal" placeholder="find detail by id" autocomplete="off">
                <div class="tagStudio__popup" id="catalogueWorkDetailPopup" hidden>
                  <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueWorkDetailPopupList"></div>
                </div>
              </div>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailOpen">Open</button>
            </div>
            <p class="tagStudio__contextHint" id="catalogueWorkDetailContext"></p>
            <p class="tagStudio__status" id="catalogueWorkDetailStatus"></p>
            <p class="tagStudio__saveWarning" id="catalogueWorkDetailWarning"></p>
            <p class="tagStudio__saveResult" id="catalogueWorkDetailResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading">work detail metadata</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailSave">Save</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailPublication">Publish</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailDelete">Delete</button>
                </div>
              </div>
              <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkDetailFields"></div>
            </section>
            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading">current record</h2>
              <div id="catalogueWorkDetailPreview"></div>
              <div class="tagStudioForm__fields" id="catalogueWorkDetailReadonly"></div>
              <p class="tagStudioForm__impact" id="catalogueWorkDetailRuntimeState"></p>
              <p class="tagStudioForm__impact" id="catalogueWorkDetailBuildImpact"></p>
              <div class="tagStudioForm__fields" id="catalogueWorkDetailSummary"></div>
              <div class="tagStudioForm__fields" id="catalogueWorkDetailReadiness"></div>
            </aside>
          </div>
        </div>
        <p class="tagStudio__status" id="catalogueWorkDetailLoading">loading catalogue work detail editor...</p>
        <p class="tagStudio__empty" id="catalogueWorkDetailEmpty" hidden></p>`;
}
