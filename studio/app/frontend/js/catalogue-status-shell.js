export function renderCatalogueStatusShell() {
  return `<div
          class="tagStudioPage catalogueStatusPage"
          id="catalogueStatusRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel">
            <div class="tagStudioFilters catalogueStatusPage__filters">
              <div class="tagStudio__key tagStudioFilters__key" id="catalogueStatusKey"></div>
              <label class="tagStudioFilters__searchWrap catalogueStatusPage__searchWrap">
                <span class="visually-hidden">Search catalogue draft rows</span>
                <input
                  type="text"
                  class="tagStudio__input tagStudioFilters__searchInput"
                  id="catalogueStatusSearch"
                  placeholder="search"
                  autocomplete="off"
                >
              </label>
            </div>

            <p class="tagStudio__status catalogueStatusPage__meta" id="catalogueStatusMeta"></p>
            <div id="catalogueStatusList"></div>
          </section>
        </div>

        <p class="tagStudio__status" id="catalogueStatusLoading">loading catalogue drafts...</p>
        <p class="tagStudio__empty" id="catalogueStatusEmpty" hidden>No draft catalogue source records.</p>`;
}
