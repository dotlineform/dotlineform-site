import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";

var ACTION_IDS = DOCS_VIEWER_ACTION_IDS;

var MANAGEMENT_ACTION_MENU_ITEMS = [
  {
    id: "docsViewerManageNewButton",
    actionId: ACTION_IDS.NEW,
    emoji: "📄",
    label: "New"
  },
  {
    id: "docsViewerManageImportButton",
    actionId: ACTION_IDS.IMPORT,
    emoji: "📥",
    label: "Import"
  },
  {
    id: "docsViewerManagePreparePackageLink",
    href: "/docs/packages/prepare/",
    emoji: "📦",
    label: "Prepare package"
  },
  {
    id: "docsViewerManageReturnedPackagesLink",
    href: "/docs/packages/returned/",
    emoji: "📥",
    label: "Returned packages"
  },
  {
    id: "docsViewerManageDeleteButton",
    actionId: ACTION_IDS.DELETE,
    emoji: "🗑️",
    label: "Delete"
  },
  {
    id: "docsViewerManageNewScopeButton",
    actionId: ACTION_IDS.NEW_SCOPE,
    emoji: "🗂️",
    label: "New scope",
    hidden: true
  },
  {
    id: "docsViewerManageRenameScopeButton",
    actionId: ACTION_IDS.RENAME_SCOPE,
    emoji: "🏷️",
    label: "Rename scope",
    hidden: true
  },
  {
    id: "docsViewerManageDeleteScopeButton",
    actionId: ACTION_IDS.DELETE_SCOPE,
    emoji: "🗑️",
    label: "Delete scope",
    hidden: true
  },
  {
    id: "docsViewerManageNewSubScopeButton",
    actionId: ACTION_IDS.NEW_SUB_SCOPE,
    emoji: "📁",
    label: "New sub-scope",
    hidden: true
  },
  {
    id: "docsViewerManageDeleteSubScopeButton",
    actionId: ACTION_IDS.DELETE_SUB_SCOPE,
    emoji: "🗑️",
    label: "Delete sub-scope",
    hidden: true
  },
  {
    id: "docsViewerManagePublishButton",
    actionId: ACTION_IDS.PUBLISH_DOCS,
    emoji: "🌍",
    label: "Publish"
  },
  {
    id: "docsViewerManageExportButton",
    actionId: ACTION_IDS.EXPORT_DOCS,
    emoji: "⬇️",
    label: "Export",
    hidden: true
  },
  {
    id: "docsViewerManageSettingsButton",
    actionId: ACTION_IDS.SETTINGS,
    emoji: "⚙️",
    label: "Settings"
  },
  {
    id: "docsViewerManageRebuildButton",
    actionId: ACTION_IDS.REBUILD_DOCS,
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
  var action = item.actionId ? ' data-docs-viewer-action="' + escapeHtml(item.actionId) + '"' : "";
  var label = escapeHtml(item.label);
  if (item.href) {
    return [
      '        <a class="docsViewer__actionMenuItem" role="menuitem" id="' + escapeHtml(item.id) + '" href="' + escapeHtml(item.href) + '" data-docs-viewer-scope-href="' + escapeHtml(item.href) + '" target="_blank" rel="noopener noreferrer" aria-label="' + label + '" title="' + label + '"' + hidden + '>',
      '          <span class="docsViewer__actionMenuEmoji" aria-hidden="true">' + escapeHtml(item.emoji || "") + "</span>",
      '          <span class="docsViewer__actionMenuLabel">' + label + "</span>",
      "        </a>"
    ].join("");
  }
  return [
    '        <button class="docsViewer__actionMenuItem" role="menuitem" type="button" id="' + escapeHtml(item.id) + '"' + action + ' aria-label="' + label + '" title="' + label + '"' + hidden + ">",
    '          <span class="docsViewer__actionMenuEmoji" aria-hidden="true">' + escapeHtml(item.emoji || "") + "</span>",
    '          <span class="docsViewer__actionMenuLabel">' + label + "</span>",
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

function elementFromMarkup(documentRef, markup) {
  var template = documentRef.createElement("template");
  template.innerHTML = markup;
  return template.content.firstElementChild;
}

function renderActionButton(context, options) {
  var settings = options || {};
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = settings.className || "docsViewer__actionButton";
    button.id = settings.id || "";
    button.type = "button";
  }
  button.textContent = "";
  if (settings.iconOnly) {
    var icon = context.document.createElement("span");
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = settings.text || "";
    button.appendChild(icon);
  } else {
    button.textContent = settings.text || context.control.label;
  }
  return button;
}

function renderManagementActionsMenu(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerManageActionsButton")) {
    root = elementFromMarkup(context.document, [
      '<div class="docsViewer__actionsMenuHost">',
      '  <button class="docsViewer__actionButton" type="button" id="docsViewerManageActionsButton" aria-haspopup="menu" aria-expanded="false" aria-controls="docsViewerManageActionsMenu">Actions</button>',
      '  <div class="docsViewer__actionsMenu" id="docsViewerManageActionsMenu" role="menu" hidden>',
      MANAGEMENT_ACTION_MENU_ITEMS.map(renderActionMenuItem).join(""),
      "  </div>",
      "</div>"
    ].join(""));
  }
  return { root: root, interactive: root.querySelector("#docsViewerManageActionsButton") };
}

function renderDraftToggle(context) {
  var root = context.existingRoot;
  var input = root ? root.querySelector("#docsViewerDraftToggle") : null;
  if (!root || !input) {
    root = elementFromMarkup(context.document, [
      '<label class="docsViewer__draftToggle">',
      '  <input class="docsViewer__draftInput" id="docsViewerDraftToggle" type="checkbox" aria-label="Show non-viewable docs">',
      '  <span class="docsViewer__draftLabel">Show non-viewable</span>',
      "</label>"
    ].join(""));
    input = root.querySelector("#docsViewerDraftToggle");
  }
  input.checked = Boolean(context.control.state && context.control.state.pressed);
  return { root: root, interactive: input };
}

function renderScopeControl(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerScopeSelect")) {
    root = elementFromMarkup(context.document, renderScopeSelect().trim());
  }
  return { root: root, interactive: root.querySelector("#docsViewerScopeSelect") };
}

function renderThemeToggle(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = elementFromMarkup(context.document, [
      '<button class="docsViewer__themeToggle" type="button" data-docs-viewer-theme-toggle>',
      '  <svg class="docsViewer__themeIcon" data-docs-viewer-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">',
      '    <circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="M4.93 4.93l1.41 1.41"></path><path d="M17.66 17.66l1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="M4.93 19.07l1.41-1.41"></path><path d="M17.66 6.34l1.41-1.41"></path>',
      "  </svg>",
      '  <svg class="docsViewer__themeIcon" data-docs-viewer-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden><path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path></svg>',
      "</button>"
    ].join(""));
  }
  var dark = Boolean(context.control.state && context.control.state.pressed);
  button.querySelectorAll("[data-docs-viewer-theme-icon]").forEach(function (icon) {
    icon.hidden = icon.dataset.docsViewerThemeIcon !== (dark ? "dark" : "light");
  });
  return button;
}

export function createDocsViewerManagementAppControlRenderers() {
  return {
    "manage-toolbar-import": function (context) {
      return renderActionButton(context, {
        className: "docsViewer__actionButton docsViewer__actionButton--iconOnly",
        id: "docsViewerManageToolbarImportButton",
        iconOnly: true,
        text: "📥"
      });
    },
    "manage-actions-menu": renderManagementActionsMenu,
    "manage-toolbar-publish": function (context) {
      return renderActionButton(context, { id: "docsViewerManageToolbarPublishButton", text: "Publish" });
    },
    "manage-show": function (context) {
      return renderActionButton(context, { id: "docsViewerManageViewableButton", text: "Show" });
    },
    "manage-show-non-viewable": renderDraftToggle,
    "manage-scope-select": renderScopeControl,
    "manage-theme-toggle": renderThemeToggle
  };
}
