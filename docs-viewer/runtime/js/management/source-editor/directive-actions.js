export const DIRECTIVE_ACTIONS_CONTROL_ID = "source-directives";

export const DIRECTIVE_ACTIONS = Object.freeze([
  Object.freeze({
    emoji: "⊞",
    id: "table-detail",
    label: "Table detail",
    source: "<!-- dotlineform:table-detail -->"
  }),
  Object.freeze({
    emoji: "📐",
    id: "table-publish-svg",
    label: "Table to SVG",
    source: "<!-- dotlineform:table-publish format=svg id=table-name -->",
    placeholder: Object.freeze({ start: 45, end: 55 })
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

  var leading = range.start > 0 && source.charAt(range.start - 1) !== "\n" ? "\n" : "";
  var trailing = trailingNewlines(source, range.start);
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
    if (event.key !== "Escape" || controller.menu.hidden) return;
    event.preventDefault();
    closeMenu(controller, { focusButton: true });
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
  item.setAttribute("data-docs-viewer-directive-action", directive.id);
  var emoji = document.createElement("span");
  emoji.className = "docsViewer__actionMenuEmoji";
  emoji.setAttribute("aria-hidden", "true");
  emoji.textContent = directive.emoji;
  var label = document.createElement("span");
  label.className = "docsViewer__actionMenuLabel";
  label.textContent = directive.label;
  item.append(emoji, label);
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
    button.className = "docsViewer__documentActionButton";
    button.id = "docsViewerManageSourceDirectivesButton";
    button.type = "button";
    button.textContent = "🧩";
    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", "docsViewerManageSourceDirectivesMenu");
    var menu = context.document.createElement("div");
    menu.className = "docsViewer__actionsMenu docsViewerDirectiveActions__menu";
    menu.id = "docsViewerManageSourceDirectivesMenu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
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

function insertDirective(context, controller, directiveId) {
  var adapter = activeAdapter(context);
  var capture = controller.capture;
  closeMenu(controller);
  if (
    !adapter
    || !capture
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
      var action = detail.event && detail.event.target.closest(
        "[data-docs-viewer-directive-action]"
      );
      if (action && controller.root.contains(action)) {
        return insertDirective(context, controller, action.dataset.docsViewerDirectiveAction);
      }
      if (!controller.menu.hidden) {
        closeMenu(controller);
        return true;
      }
      var adapter = activeAdapter(context);
      if (!adapter || typeof adapter.captureSelection !== "function") return false;
      controller.capture = adapter.captureSelection();
      controller.menu.hidden = false;
      controller.button.setAttribute("aria-expanded", "true");
      return true;
    }
  };
}
