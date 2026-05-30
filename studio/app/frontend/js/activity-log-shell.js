export function renderActivityLogShell() {
  return `<div
          class="tagStudioPage buildActivityPage studioActivityPage"
          id="studioActivityRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <div class="tagStudio__panel buildActivityPage__panel">
            <p class="buildActivityPage__meta" id="studioActivityMeta"></p>
            <div id="studioActivityList"></div>
          </div>
        </div>

        <p class="buildActivityPage__status" id="studioActivityStatus">loading Studio activity...</p>
        <p class="buildActivityPage__empty" id="studioActivityEmpty" hidden>No Studio activity yet.</p>`;
}
