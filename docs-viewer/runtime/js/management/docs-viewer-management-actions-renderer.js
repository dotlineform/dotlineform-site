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
    id: "docsViewerManageExportWorkspaceButton",
    actionId: ACTION_IDS.EXPORT_WORKSPACE,
    emoji: "⬇️",
    label: "Export"
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
    id: "docsViewerManageSettingsButton",
    actionId: ACTION_IDS.SETTINGS,
    emoji: "⚙️",
    label: "Settings"
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
  }
  button.className = settings.className || "docsViewer__actionButton";
  button.id = settings.id || "";
  button.type = "button";
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
    "manage-toolbar-rebuild": function (context) {
      return renderActionButton(context, {
        className: "docsViewer__actionButton docsViewer__actionButton--iconOnly",
        id: "docsViewerManageRebuildButton",
        iconOnly: true,
        text: "🔄"
      });
    },
    "manage-toolbar-publish": function (context) {
      return renderActionButton(context, {
        className: "docsViewer__actionButton docsViewer__actionButton--iconOnly",
        id: "docsViewerManageToolbarPublishButton",
        iconOnly: true,
        text: "🌍"
      });
    },
    "manage-toolbar-pre-publish": function (context) {
      return renderActionButton(context, {
        className: "docsViewer__actionButton",
        id: "docsViewerManagePrePublishButton",
        text: "Pre-publish"
      });
    },
    "manage-stage-select": function (context) {
      var root = context.existingRoot || context.document.createElement("div");
      root.className = "docsViewer__stageButtons";
      root.dataset.docsViewerStages = "true";
      root.setAttribute("role", "group");
      return root;
    }
  };
}
