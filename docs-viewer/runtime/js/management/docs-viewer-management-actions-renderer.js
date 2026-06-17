var MANAGEMENT_ACTION_MENU_ITEMS = [
  {
    id: "docsViewerManageNewButton",
    action: "new",
    emoji: "📄",
    label: "New"
  },
  {
    id: "docsViewerManageImportButton",
    action: "import",
    emoji: "📥",
    label: "Import"
  },
  {
    id: "docsViewerManageDeleteButton",
    action: "delete",
    emoji: "🗑️",
    label: "Delete"
  },
  {
    id: "docsViewerManageNewScopeButton",
    action: "new-scope",
    emoji: "🗂️",
    label: "New Scope",
    hidden: true
  },
  {
    id: "docsViewerManageDeleteScopeButton",
    action: "delete-scope",
    emoji: "🗑️",
    label: "Delete Scope",
    hidden: true
  },
  {
    id: "docsViewerManagePublishButton",
    action: "publish-docs",
    emoji: "🌍",
    label: "Publish",
    hidden: true
  },
  {
    id: "docsViewerManageSettingsButton",
    action: "settings",
    emoji: "⚙️",
    label: "Settings"
  },
  {
    id: "docsViewerManageRebuildButton",
    action: "rebuild-docs",
    emoji: "🔄",
    label: "Rebuild docs"
  }
];

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderActionMenuItem(item) {
  var hidden = item.hidden ? " hidden" : "";
  var action = item.action ? ' data-docs-viewer-action="' + escapeHtml(item.action) + '"' : "";
  return [
    '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="' + escapeHtml(item.id) + '"' + action + hidden + ">",
    '          <span class="docsViewer__actionMenuEmoji" aria-hidden="true">' + escapeHtml(item.emoji || "") + "</span>",
    '          <span class="docsViewer__actionMenuLabel">' + escapeHtml(item.label) + "</span>",
    "        </button>"
  ].join("");
}

function renderScopeSelect() {
  return [
    '    <label class="docsViewer__scopeField" for="docsViewerScopeSelect" aria-label="Docs scope">',
    '      <select class="docsViewer__scopeSelectNative visually-hidden" id="docsViewerScopeSelect" tabindex="-1" aria-hidden="true"></select>',
    '      <div class="docsViewer__scopeSelectMenu" data-docs-viewer-scope-select-menu>',
    '        <button class="docsViewer__scopeSelectButton" type="button" id="docsViewerScopeSelectButton" aria-haspopup="listbox" aria-expanded="false" aria-controls="docsViewerScopeSelectList" aria-label="Docs scope">',
    '          <span class="docsViewer__scopeSelectEmoji" aria-hidden="true"></span>',
    '          <span class="docsViewer__scopeSelectText" data-docs-viewer-scope-select-label></span>',
    '        </button>',
    '        <div class="docsViewer__scopeSelectSurface" id="docsViewerScopeSelectList" role="listbox" hidden></div>',
    '      </div>',
    '    </label>'
  ].join("");
}

var MANAGEMENT_ACTIONS_MARKUP = [
  '<div class="docsViewer__manageRow" id="docsViewerManageRow" hidden>',
  '  <div class="docsViewer__manageActions" role="toolbar" aria-label="Management actions">',
  '    <div class="docsViewer__actionsMenuHost">',
  '      <button class="docsViewer__actionButton" type="button" id="docsViewerManageActionsButton" aria-haspopup="menu" aria-expanded="false" aria-controls="docsViewerManageActionsMenu">Actions</button>',
  '      <div class="docsViewer__actionsMenu" id="docsViewerManageActionsMenu" role="menu" hidden>',
  MANAGEMENT_ACTION_MENU_ITEMS.map(renderActionMenuItem).join(""),
  '      </div>',
  '    </div>',
  '    <button class="docsViewer__actionButton" type="button" id="docsViewerManageViewableButton">Show</button>',
  '    <label class="docsViewer__draftToggle">',
  '      <input class="docsViewer__draftInput" id="docsViewerDraftToggle" type="checkbox">',
  '      <span class="docsViewer__draftLabel">non-viewable</span>',
  '    </label>',
  renderScopeSelect(),
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
