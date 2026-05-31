export function renderStudioRiskShell() {
  return `<div
          class="tagStudioPage studioRiskPage"
          id="studioRiskRoot"
          hidden
          data-studio-route="studio-risk"
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <div class="tagStudio__panel studioRiskPage__panel">
            <p class="studioRiskPage__intro" id="studioRiskIntro"></p>
            <p class="tagStudio__status" id="studioRiskStatus"></p>
            <form class="studioRiskForm" id="studioRiskForm">
              <label class="studioRiskField">
                <span id="studioRiskAppLabel"></span>
                <select class="tagStudio__input" id="studioRiskApp" name="app"></select>
              </label>
              <label class="studioRiskField">
                <span id="studioRiskAreaLabel"></span>
                <input class="tagStudio__input" id="studioRiskArea" name="area" value="runtime" autocomplete="off">
              </label>
              <label class="studioRiskField">
                <span id="studioRiskRunIdLabel"></span>
                <input class="tagStudio__input" id="studioRiskRunId" name="run_id" autocomplete="off">
              </label>
              <label class="studioRiskCheck">
                <input type="checkbox" id="studioRiskDryRun" name="dry_run">
                <span id="studioRiskDryRunLabel"></span>
              </label>
              <label class="studioRiskCheck">
                <input type="checkbox" id="studioRiskRuntime" name="include_runtime">
                <span id="studioRiskRuntimeLabel"></span>
              </label>
              <label class="studioRiskCheck">
                <input type="checkbox" id="studioRiskLighthouse" name="include_lighthouse">
                <span id="studioRiskLighthouseLabel"></span>
              </label>
              <div class="studioRiskActions">
                <button
                  type="submit"
                  class="tagStudio__button tagStudio__button--defaultWidth"
                  id="studioRiskRun"
                ></button>
              </div>
            </form>
          </div>
          <section class="tagStudio__panel studioRiskPage__panel">
            <h3 id="studioRiskSummaryTitle"></h3>
            <div class="studioRiskSummary" id="studioRiskSummary"></div>
          </section>
          <section class="tagStudio__panel studioRiskPage__panel">
            <h3 id="studioRiskRunsTitle"></h3>
            <div class="studioRiskRuns" id="studioRiskRuns"></div>
          </section>
        </div>

        <p class="tagStudio__status" id="studioRiskBootStatus">loading Studio risk...</p>`;
}
