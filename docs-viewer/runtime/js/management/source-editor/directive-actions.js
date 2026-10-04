import { createDocsViewerToolbarIcon } from "../../shared/docs-viewer-toolbar-icon.js";
import { DOCS_VIEWER_ACTION_IDS as ACTION_IDS } from "../docs-viewer-action-definitions.js";
import { openCatalogueMediaModal } from "./catalogue-media-modal.js";
import { openDocumentLinkModal } from "./document-link-contribution.js";

export const DIRECTIVE_ACTIONS_CONTROL_ID = "source-directives";

const ICON_DIRECTIVE_SOURCE = "[[icon:refresh-cw]]";
const LINKS_DIRECTIVE_SOURCE = "[[links|related links]]";

const SOURCE_ACTIONS = [
  { actionId: ACTION_IDS.SOURCE_ADD_IMAGE, artwork: "docsViewer__icon--image", label: "Add image" },
  { actionId: ACTION_IDS.SOURCE_ADD_CATALOGUE_IMAGE, artwork: "docsViewer__icon--book-image", label: "Add Catalogue image" },
  { actionId: ACTION_IDS.SOURCE_ADD_FILE, artwork: "docsViewer__icon--paperclip", label: "Add file" },
  { actionId: ACTION_IDS.SOURCE_ADD_MEDIA_VIEW_LINK, artwork: "docsViewer__icon--image-plus", label: "Add Media View link" },
  { actionId: ACTION_IDS.SOURCE_INSERT_DOC_LINK, artwork: "docsViewer__icon--file-plus-corner", label: "Insert doc link" },
  { actionId: ACTION_IDS.OPEN_VSCODE, artwork: "docsViewer__icon--file-code-corner", label: "Open in VS Code" }
];

export const DIRECTIVE_ACTIONS = Object.freeze([
  Object.freeze({
    artwork: "docsViewer__icon--table",
    id: "table-detail",
    label: "Table detail",
    source: "<!-- dotlineform:table-detail -->"
  }),
  Object.freeze({
    artwork: "docsViewer__icon--waypoints",
    id: "insert-related-links",
    label: "Insert related links",
    source: LINKS_DIRECTIVE_SOURCE,
    placeholder: Object.freeze({ start: "[[links|".length, end: LINKS_DIRECTIVE_SOURCE.length - 2 })
  }),
  Object.freeze({
    artwork: "docsViewer__icon--image",
    id: "insert-icon",
    label: "Insert icon",
    source: ICON_DIRECTIVE_SOURCE,
    inline: true,
    placeholder: Object.freeze({ start: "[[icon:".length, end: ICON_DIRECTIVE_SOURCE.length - 2 })
  })
]);

var controllers = new WeakMap();

function directiveById(directiveId) {
  return DIRECTIVE_ACTIONS.find(function (directive) {
    return directive.id === directiveId;
  }) || null;
}

function validCapturedRange(source, snapshot, capture) {
  if (!capture || typeof capture !== "object") return null;
  var start = Number(capture.start);
  var end = Number(capture.end);
  var revision = Number(capture.revision);
  if (
    !Number.isInteger(start)
    || !Number.isInteger(end)
    || !Number.isInteger(revision)
    || start < 0
    || end < start
    || end > source.length
    || revision !== Number(snapshot.revision)
    || source.slice(start, end) !== String(capture.text || "")
  ) return null;
  return { start: start, end: end };
}

function trailingNewlines(source, insertionPoint) {
  if (/^\n+$/.test(source.slice(insertionPoint))) return "";
  if (insertionPoint === source.length) return "\n";
  var count = 0;
  while (count < 2 && source.charAt(insertionPoint + count) === "\n") count += 1;
  return "\n".repeat(2 - count);
}

export function createDirectiveInsertionPlan(options = {}) {
  var snapshot = options.snapshot || {};
  var capture = options.capture;
  var source = String(snapshot.value == null ? "" : snapshot.value);
  var range = validCapturedRange(source, snapshot, capture);
  var directive = directiveById(String(options.directiveId || ""));
  if (!range || !directive) return null;

  var leading = !directive.inline && range.start > 0 && source.charAt(range.start - 1) !== "\n" ? "\n" : "";
  var trailing = directive.inline ? "" : trailingNewlines(source, range.start);
  var insertedText = leading + directive.source + trailing;
  var selectionStart = directive.placeholder
    ? range.start + leading.length + directive.placeholder.start
    : range.start + insertedText.length;
  var selectionEnd = directive.placeholder
    ? range.start + leading.length + directive.placeholder.end
    : selectionStart;
  return {
    insertedText: insertedText,
    replacement: insertedText + String(capture.text || ""),
    selection: { start: selectionStart, end: selectionEnd }
  };
}

function closeMenu(controller, options = {}) {
  if (!controller) return;
  controller.capture = null;
  controller.adapter = null;
  controller.menu.hidden = true;
  controller.button.setAttribute("aria-expanded", "false");
  if (options.focusButton && controller.button.isConnected) controller.button.focus();
}

function disposeController(controller) {
  if (!controller || controller.disposed) return;
  controller.disposed = true;
  controller.document.removeEventListener("click", controller.onDocumentClick);
  controller.document.removeEventListener("keydown", controller.onDocumentKeydown);
  if (controller.observer) controller.observer.disconnect();
  controllers.delete(controller.root);
}

function createController(root, button, menu) {
  var document = root.ownerDocument;
  var controller = {
    adapter: null,
    button: button,
    capture: null,
    disposed: false,
    document: document,
    menu: menu,
    observer: null,
    root: root
  };
  controller.onDocumentClick = function (event) {
    if (!controller.menu.hidden && !controller.root.contains(event.target)) closeMenu(controller);
  };
  controller.onDocumentKeydown = function (event) {
    if (controller.menu.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeMenu(controller, { focusButton: true });
      return;
    }
    if (!controller.menu.contains(event.target)) return;
    if (event.key === "Tab") { closeMenu(controller); return; }
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    var items = enabledMenuItems(controller);
    if (!items.length) return;
    var index = items.indexOf(event.target.closest('[role="menuitem"]'));
    var next = event.key === "Home" ? 0 : event.key === "End" ? items.length - 1
      : (index + (event.key === "ArrowUp" ? -1 : 1) + items.length) % items.length;
    items[next].focus({ preventScroll: true });
  };
  document.addEventListener("click", controller.onDocumentClick);
  document.addEventListener("keydown", controller.onDocumentKeydown);
  var Observer = document.defaultView ? document.defaultView.MutationObserver : null;
  if (Observer) {
    controller.observer = new Observer(function () {
      if (!root.isConnected) disposeController(controller);
    });
    controller.observer.observe(document.documentElement, { childList: true, subtree: true });
  }
  controllers.set(root, controller);
  return controller;
}

function menuItem(document, directive) {
  var item = document.createElement("button");
  item.className = "docsViewer__actionMenuItem";
  item.type = "button";
  item.setAttribute("role", "menuitem");
  if (directive.actionId) item.dataset.docsViewerAction = directive.actionId;
  else item.dataset.docsViewerDirectiveAction = directive.id;
  item.title = directive.label;
  var icon = createDocsViewerToolbarIcon(document, directive.artwork);
  var label = document.createElement("span");
  label.className = "docsViewer__actionMenuLabel";
  label.textContent = directive.label;
  item.append(icon, label);
  return item;
}

export function directiveActionsControlDefinition() {
  return {
    id: DIRECTIVE_ACTIONS_CONTROL_ID,
    label: "Directives",
    ownerType: "view",
    ownerViewId: "rendered-document",
    modeIds: ["markdown-source"],
    surfaceId: "main-view",
    appKinds: ["manage"],
    features: ["source-editing"],
    renderer: "source-directives"
  };
}

export function directiveActionsControlRenderer(context) {
  var root = context.existingRoot;
  if (!root || !root.querySelector("#docsViewerManageSourceDirectivesButton")) {
    root = context.document.createElement("div");
    root.className = "docsViewer__actionsMenuHost docsViewerDirectiveActions";
    var button = context.document.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.id = "docsViewerManageSourceDirectivesButton";
    button.type = "button";
    button.appendChild(createDocsViewerToolbarIcon(context.document, "docsViewer__icon--puzzle"));
    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", "docsViewerManageSourceDirectivesMenu");
    var menu = context.document.createElement("div");
    menu.className = "docsViewer__actionsMenu docsViewerDirectiveActions__menu";
    menu.id = "docsViewerManageSourceDirectivesMenu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    SOURCE_ACTIONS.forEach(function (action) {
      menu.appendChild(menuItem(context.document, action));
    });
    var separator = context.document.createElement("div");
    separator.className = "docsViewer__actionMenuSeparator";
    separator.setAttribute("role", "separator");
    menu.appendChild(separator);
    DIRECTIVE_ACTIONS.forEach(function (directive) {
      menu.appendChild(menuItem(context.document, directive));
    });
    root.append(button, menu);
  }
  var controller = controllers.get(root) || createController(
    root,
    root.querySelector("#docsViewerManageSourceDirectivesButton"),
    root.querySelector("#docsViewerManageSourceDirectivesMenu")
  );
  controller.menu.querySelectorAll('[role="menuitem"]').forEach(function (item) {
    item.disabled = Boolean(context.control.state.disabled || context.control.state.hidden);
  });
  if (context.control.state.disabled || context.control.state.hidden) closeMenu(controller);
  return { root: root, interactive: controller.button };
}

function activeAdapter(context) {
  var services = context.sourceEditorServices || {};
  return typeof services.getActiveSourceEditorContextAdapter === "function"
    ? services.getActiveSourceEditorContextAdapter()
    : null;
}

function focusEditor(adapter) {
  if (adapter && typeof adapter.focus === "function") adapter.focus();
}

function enabledMenuItems(controller) {
  return Array.from(controller.menu.querySelectorAll('[role="menuitem"]')).filter(function (item) {
    return !item.disabled;
  });
}

function runSourceAction(context, controller, actionId) {
  var adapter = controller.adapter;
  var capture = controller.capture;
  closeMenu(controller);
  if (!adapter || !capture || adapter !== activeAdapter(context) || !adapter.isCurrent()) return false;
  Promise.resolve().then(function () {
    if (actionId === ACTION_IDS.SOURCE_ADD_IMAGE || actionId === ACTION_IDS.SOURCE_ADD_FILE) {
      return adapter.addSourceMedia(actionId === ACTION_IDS.SOURCE_ADD_FILE ? "file" : "image", capture);
    }
    if (actionId === ACTION_IDS.SOURCE_ADD_CATALOGUE_IMAGE || actionId === ACTION_IDS.SOURCE_ADD_MEDIA_VIEW_LINK) {
      return openCatalogueMediaModal({
        presentation: actionId === ACTION_IDS.SOURCE_ADD_CATALOGUE_IMAGE ? "image" : "media",
        adapter: adapter, capture: capture, root: context.root
      });
    }
    if (actionId === ACTION_IDS.SOURCE_INSERT_DOC_LINK) {
      return openDocumentLinkModal({
        adapter: adapter, capture: capture, root: context.root,
        isCurrent: function () { return activeAdapter(context) === adapter && adapter.isCurrent(); }
      });
    }
    if (actionId === ACTION_IDS.OPEN_VSCODE) return context.openSourceInVsCode(adapter.getDocumentTarget());
  }).catch(function (error) {
    context.setStatus(error.message || "The Source action failed.", true);
    focusEditor(adapter);
  });
  return true;
}

function insertDirective(context, controller, directiveId) {
  var adapter = controller.adapter;
  var capture = controller.capture;
  closeMenu(controller);
  if (
    !adapter
    || !capture
    || adapter !== activeAdapter(context)
    || typeof adapter.getBufferSnapshot !== "function"
    || typeof adapter.replaceCapturedRange !== "function"
  ) {
    focusEditor(adapter);
    return false;
  }
  var plan = createDirectiveInsertionPlan({
    capture: capture,
    directiveId: directiveId,
    snapshot: adapter.getBufferSnapshot()
  });
  if (!plan || !adapter.replaceCapturedRange(capture, plan.replacement, "end")) {
    focusEditor(adapter);
    return false;
  }
  var nextSnapshot = adapter.getBufferSnapshot();
  var finalSelection = {
    start: plan.selection.start,
    end: plan.selection.end,
    text: String(nextSnapshot.value || "").slice(plan.selection.start, plan.selection.end),
    revision: nextSnapshot.revision
  };
  if (
    typeof adapter.selectCapturedRange !== "function"
    || !adapter.selectCapturedRange(finalSelection)
  ) focusEditor(adapter);
  return true;
}

export function createDirectiveActionsMainViewControlHandlers() {
  return {
    [DIRECTIVE_ACTIONS_CONTROL_ID]: function (context) {
      var detail = context.detail || {};
      if (detail.eventType !== "click") return false;
      var controller = controllers.get(detail.target);
      if (!controller || controller.button.disabled) return false;
      if (detail.actionId) {
        if (!SOURCE_ACTIONS.some(function (action) { return action.actionId === detail.actionId; })
          || detail.actionTarget?.disabled) return false;
        return runSourceAction(context, controller, detail.actionId);
      }
      var action = detail.event && detail.event.target.closest(
        "[data-docs-viewer-directive-action]"
      );
      if (action && controller.root.contains(action)) {
        if (action.disabled) return false;
        return insertDirective(context, controller, action.dataset.docsViewerDirectiveAction);
      }
      if (!controller.menu.hidden) {
        closeMenu(controller);
        return true;
      }
      var adapter = activeAdapter(context);
      if (!adapter || typeof adapter.captureSelection !== "function") return false;
      controller.adapter = adapter;
      controller.capture = adapter.captureSelection();
      controller.menu.hidden = false;
      controller.button.setAttribute("aria-expanded", "true");
      enabledMenuItems(controller)[0]?.focus({ preventScroll: true });
      return true;
    }
  };
}
