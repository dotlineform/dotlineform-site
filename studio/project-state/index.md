---
layout: studio
title: "Project State"
permalink: /studio/project-state/
section: project-state
studio_page_doc: /docs/?scope=studio&doc=project-state-page
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="projectStateRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="projectStatePageHeading">project state</h2>
      <span class="tagStudio__saveMode" id="projectStateSaveMode"></span>
    </div>
    <p class="tagStudio__contextHint" id="projectStateContext"></p>
    <p class="tagStudio__status" id="projectStateStatus"></p>
    <p class="tagStudio__saveWarning" id="projectStateWarning"></p>
    <p class="tagStudio__saveResult" id="projectStateResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading" id="projectStateRunHeading">report</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="projectStateRunButton">Run</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields">
        <div class="tagStudioForm__field">
          <span class="tagStudioForm__label" id="projectStateOutputLabel">output</span>
          <span class="tagStudio__input tagStudio__input--readonlyDisplay" id="projectStateOutputPath">_docs_src/project-state.md</span>
        </div>
        <div class="tagStudioForm__field">
          <span class="tagStudioForm__label" id="projectStateSourceLabel">source</span>
          <span class="tagStudio__input tagStudio__input--readonlyDisplay" id="projectStateSourceRoot">$DOTLINEFORM_PROJECTS_BASE_DIR/projects</span>
        </div>
        <label class="catalogueWorkPage__updateToggle" for="projectStateIncludeSubfolders">
          <input type="checkbox" id="projectStateIncludeSubfolders">
          <span id="projectStateIncludeSubfoldersLabel">include sub-folders</span>
        </label>
      </div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading" id="projectStateSummaryHeading">summary</h2>
      <div class="tagStudioForm__fields" id="projectStateSummary"></div>
      <div class="catalogueWorkPage__actions">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="projectStateOpenButton">Open file</button>
      </div>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="projectStateLoading">loading project state…</p>
<p class="tagStudio__empty" id="projectStateEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/project-state.js' | relative_url }}"></script>
