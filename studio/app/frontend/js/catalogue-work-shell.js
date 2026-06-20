import {
  readCatalogueEditorMediaAttrs,
  renderMediaAttrs
} from "./catalogue-editor-shell-media.js";

export function renderCatalogueWorkShell(config) {
  const mediaAttrs = renderMediaAttrs(readCatalogueEditorMediaAttrs(config), [
    "worksPrimaryBase",
    "stagedWorksPrimaryBase",
    "thumbWorksBase",
    "thumbWorkDetailsBase",
    "primaryDisplayWidth",
    "primaryFullWidth",
    "primarySuffix",
    "thumbSizes",
    "thumbSuffix",
    "assetFormat"
  ]);
  return `<div
          class="studioPage catalogueWorkPage"
          id="catalogueWorkRoot"
          hidden
          data-studio-route="catalogue-work"
          data-studio-ready="false"
          data-studio-busy="false"
          ${mediaAttrs}
        >
          <section class="studioUi__panel studioUi__panel--editor">
            <div class="studioUi__inputRow studioUi__inputRow--editor">
              <div class="studioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueWorkSearch">Find work by id</label>
                <div class="sharedSearchList__control catalogueWorkPage__searchControl" id="catalogueWorkPopup">
                  <input type="text" class="studioUi__input" id="catalogueWorkSearch" placeholder="find work by id" autocomplete="off">
                  <span id="catalogueWorkPopupList" hidden></span>
                </div>
              </div>
              <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueWorkOpen">Open</button>
              <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueWorkNew">New</button>
              <p class="studioUi__status catalogueEditorMessage catalogueWorkPage__message" id="catalogueWorkStatus" aria-live="polite"></p>
            </div>
          </section>

          <div class="studioUi__grid catalogueWorkPage__grid">
            <section class="studioUi__panel studioUi__panel--editor">
              <div class="studioUi__headingRow">
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueWorkSave">Save</button>
                  <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueWorkPublication">Publish</button>
                  <button type="button" class="studioUi__button studioUi__button--defaultWidth" id="catalogueWorkDelete">Delete</button>
                </div>
              </div>
              <p class="studioForm__meta" id="catalogueWorkMeta"></p>
              <div class="studioForm__fields catalogueWorkForm__fields" id="catalogueWorkFields"></div>
            </section>

            <aside class="studioUi__panel catalogueWorkSummary">
              <div id="catalogueWorkPreview"></div>
              <div class="catalogueWorkResources" id="catalogueWorkResourcesPanel">
                <div class="studioUi__headingRow catalogueWorkResources__actionRow">
                  <span class="studioForm__label">links</span>
                  <div class="catalogueWorkDetails__rowActions" id="catalogueWorkResourcesActions" aria-label="Resource actions"></div>
                </div>
                <p class="studioForm__meta" id="catalogueWorkResourcesMeta"></p>
                <div class="catalogueWorkDetails__results" id="catalogueWorkResourcesResults"></div>
              </div>
              <div class="studioForm__fields" id="catalogueWorkReadonly"></div>
              <p class="studioForm__impact" id="catalogueWorkRuntimeState"></p>
              <p class="studioForm__impact" id="catalogueWorkBuildImpact"></p>
              <div class="studioForm__fields" id="catalogueWorkSummary"></div>
              <div class="studioForm__fields" id="catalogueWorkReadiness"></div>
            </aside>
          </div>

          <section class="studioUi__panel catalogueWorkDetailBrowser" id="catalogueWorkDetailBrowserPanel" aria-label="Browse details">
            <div class="studioUi__headingRow catalogueWorkDetailBrowser__actionRow">
              <div class="studioForm__searchWrap catalogueWorkDetailBrowser__searchWrap">
                <label class="visually-hidden" for="catalogueWorkDetailBrowserSearch">Find detail by row id</label>
                <input type="text" class="studioUi__input catalogueWorkDetailBrowser__searchInput" id="catalogueWorkDetailBrowserSearch" placeholder="find detail id" autocomplete="off" inputmode="numeric">
                <button type="button" class="catalogueWorkDetailBrowser__searchClear" id="catalogueWorkDetailBrowserSearchClear" aria-label="Clear detail search" title="Clear detail search" hidden>×</button>
              </div>
            </div>
            <div class="catalogueWorkDetailBrowser__layout">
              <section class="catalogueWorkDetailBrowser__pane" aria-label="Detail sections">
                <div class="catalogueWorkDetailBrowser__paneActionRow">
                  <div class="catalogueWorkDetails__rowActions catalogueWorkDetailBrowser__sectionActions" id="catalogueWorkDetailBrowserSectionActions" aria-label="Section actions"></div>
                </div>
                <div class="catalogueWorkDetailBrowser__sectionList" id="catalogueWorkDetailBrowserSections"></div>
              </section>
              <section class="catalogueWorkDetailBrowser__pane" aria-label="Details in selected section">
                <div class="catalogueWorkDetailBrowser__paneActionRow">
                  <div class="catalogueWorkDetails__rowActions catalogueWorkDetailBrowser__actions" id="catalogueWorkDetailBrowserActions" aria-label="Detail actions"></div>
                </div>
                <div class="catalogueWorkDetailBrowser__imageList" id="catalogueWorkDetailBrowserImages"></div>
              </section>
            </div>
          </section>

        </div>
        <p class="studioUi__status" id="catalogueWorkLoading">loading catalogue work editor...</p>
        <p class="studioUi__empty" id="catalogueWorkEmpty" hidden></p>`;
}
