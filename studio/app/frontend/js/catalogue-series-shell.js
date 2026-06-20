import {
  readCatalogueEditorMediaAttrs,
  renderMediaAttrs
} from "./catalogue-editor-shell-media.js";

export function renderCatalogueSeriesShell(config) {
  const mediaAttrs = renderMediaAttrs(readCatalogueEditorMediaAttrs(config), [
    "worksPrimaryBase",
    "thumbWorksBase",
    "primaryDisplayWidth",
    "primaryFullWidth",
    "primarySuffix",
    "thumbSizes",
    "thumbSuffix",
    "assetFormat"
  ]);
  return `<div
          class="studioPage catalogueWorkPage"
          id="catalogueSeriesRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
          ${mediaAttrs}
        >
          <section class="studioUi__panel studioUi__panel--editor">
            <div class="studioUi__inputRow studioUi__inputRow--editor">
              <div class="studioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueSeriesSearch">Find series by title</label>
                <div class="sharedSearchList__control catalogueWorkPage__searchControl" id="catalogueSeriesPopup">
                  <input type="text" class="studioUi__input" id="catalogueSeriesSearch" placeholder="find series by title" autocomplete="off">
                  <span id="catalogueSeriesPopupList" hidden></span>
                </div>
              </div>
              <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueSeriesOpen">Open</button>
              <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueSeriesNew">New</button>
              <p class="studioUi__status catalogueEditorMessage" id="catalogueSeriesStatus" aria-live="polite"></p>
            </div>
          </section>

          <div class="studioUi__grid catalogueWorkPage__grid">
            <section class="studioUi__panel studioUi__panel--editor">
              <div class="studioUi__headingRow">
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueSeriesSave">Save</button>
                  <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueSeriesPublication">Publish</button>
                  <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueSeriesDelete">Delete</button>
                </div>
              </div>
              <div class="studioForm__fields catalogueWorkForm__fields" id="catalogueSeriesFields"></div>
            </section>
            <aside class="studioUi__panel catalogueWorkSummary" id="catalogueSeriesSidePanel"></aside>
          </div>

          <section class="studioUi__panel catalogueSeriesMembers">
            <div class="studioUi__headingRow">
              <h2 class="studioUi__heading" id="catalogueSeriesMembersHeading">member works</h2>
              <div class="catalogueWorkDetails__rowActions catalogueSeriesMembers__actions" id="catalogueSeriesMembersActions" aria-label="Member work actions"></div>
            </div>
            <p class="studioForm__meta" id="catalogueSeriesMembersMeta"></p>
            <div class="catalogueSeriesMembers__results" id="catalogueSeriesMembersResults"></div>
          </section>
        </div>
        <p class="studioUi__status" id="catalogueSeriesLoading">loading catalogue series editor...</p>
        <p class="studioUi__empty" id="catalogueSeriesEmpty" hidden></p>`;
}
