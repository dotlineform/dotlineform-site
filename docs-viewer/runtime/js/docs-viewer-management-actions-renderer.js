var MANAGEMENT_ACTIONS_MARKUP = [
  '<div class="docsViewer__manageRow" id="docsViewerManageRow" hidden>',
  '  <div class="docsViewer__manageActions">',
  '    <button class="docsViewer__indexViewToggle" type="button" id="docsViewerIndexViewToggle" aria-label="Tree index view" title="Tree index view" hidden>📁</button>',
  '    <div class="docsViewer__actionsMenuHost">',
  '      <button class="docsViewer__actionButton" type="button" id="docsViewerManageActionsButton" aria-haspopup="menu" aria-expanded="false" aria-controls="docsViewerManageActionsMenu">Actions</button>',
  '      <div class="docsViewer__actionsMenu" id="docsViewerManageActionsMenu" role="menu" hidden>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageRebuildButton">Rebuild docs</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageSettingsButton">Settings</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageNewScopeButton" hidden>New scope</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageDeleteScopeButton" hidden>Delete scope</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageImportButton">Import</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageNewButton">New</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageEditButton">Edit</button>',
  '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="docsViewerManageDeleteButton">Delete</button>',
  '      </div>',
  '    </div>',
  '    <button class="docsViewer__actionButton" type="button" id="docsViewerManageViewableButton">Show</button>',
  '    <label class="docsViewer__draftToggle">',
  '      <input class="docsViewer__draftInput" id="docsViewerDraftToggle" type="checkbox">',
  '      <span class="docsViewer__draftLabel">hidden</span>',
  '    </label>',
  '  </div>',
  '  <button class="docsViewer__themeToggle" type="button" data-docs-viewer-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">',
  '    <svg class="docsViewer__themeIcon" data-docs-viewer-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">',
  '      <circle cx="12" cy="12" r="4"></circle>',
  '      <path d="M12 2v2"></path>',
  '      <path d="M12 20v2"></path>',
  '      <path d="M4.93 4.93l1.41 1.41"></path>',
  '      <path d="M17.66 17.66l1.41 1.41"></path>',
  '      <path d="M2 12h2"></path>',
  '      <path d="M20 12h2"></path>',
  '      <path d="M4.93 19.07l1.41-1.41"></path>',
  '      <path d="M17.66 6.34l1.41-1.41"></path>',
  '    </svg>',
  '    <svg class="docsViewer__themeIcon" data-docs-viewer-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>',
  '      <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>',
  '    </svg>',
  '  </button>',
  '</div>'
].join("");

export function renderDocsViewerManagementActions(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var mount = settings.mount;
  if (!mount) return null;

  mount.replaceChildren();

  var template = documentRef.createElement("template");
  template.innerHTML = MANAGEMENT_ACTIONS_MARKUP;
  var row = template.content.firstElementChild;
  if (!row) return null;

  mount.appendChild(row);
  return row;
}
