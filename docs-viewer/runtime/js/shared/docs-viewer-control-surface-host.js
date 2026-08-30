var DELEGATED_EVENT_TYPES = ["click", "change", "input"];

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function rendererFor(renderers, rendererId) {
  if (renderers instanceof Map) return renderers.get(rendererId) || null;
  if (!renderers || typeof renderers !== "object") return null;
  return typeof renderers[rendererId] === "function" ? renderers[rendererId] : null;
}

function renderedParts(result) {
  if (result && result.nodeType === 1) return { root: result, interactive: result };
  var root = result && result.root && result.root.nodeType === 1 ? result.root : null;
  var interactive = result && result.interactive && result.interactive.nodeType === 1
    ? result.interactive
    : root;
  return { root: root, interactive: interactive };
}

function setBooleanAttribute(element, name, value) {
  if (!element) return;
  element.setAttribute(name, value ? "true" : "false");
}

function applyControlState(parts, control) {
  var root = parts.root;
  var interactive = parts.interactive;
  var state = control.state || {};
  root.hidden = Boolean(state.hidden);
  if (Object.prototype.hasOwnProperty.call(state, "disabled") && interactive && "disabled" in interactive) {
    interactive.disabled = Boolean(state.disabled);
  }
  if (Object.prototype.hasOwnProperty.call(state, "pressed")) {
    setBooleanAttribute(interactive, "aria-pressed", state.pressed);
  }
  if (Object.prototype.hasOwnProperty.call(state, "expanded")) {
    setBooleanAttribute(interactive, "aria-expanded", state.expanded);
  }
  if (Object.prototype.hasOwnProperty.call(state, "busy")) {
    setBooleanAttribute(root, "aria-busy", state.busy);
  }
  if (Object.prototype.hasOwnProperty.call(state, "active")) {
    root.dataset.docsViewerControlActive = state.active ? "true" : "false";
  } else {
    delete root.dataset.docsViewerControlActive;
  }
  var label = Object.prototype.hasOwnProperty.call(state, "label") ? state.label : control.label;
  if (label && interactive) {
    interactive.setAttribute("aria-label", label);
    interactive.title = label;
  }
  if (Object.prototype.hasOwnProperty.call(state, "count")) {
    root.dataset.docsViewerControlCount = String(state.count);
    var countMount = root.querySelector("[data-docs-viewer-control-count]");
    if (countMount) countMount.textContent = String(state.count);
  }
}

function applyControlIdentity(parts, control, surfaceId) {
  parts.root.dataset.docsViewerControl = control.id;
  parts.root.dataset.docsViewerControlSurface = surfaceId;
  if (control.actionId) parts.root.dataset.docsViewerAction = control.actionId;
  if (parts.interactive && parts.interactive !== parts.root) {
    parts.interactive.setAttribute("data-docs-viewer-control-interactive", "");
  }
}

export function createDocsViewerControlSurfaceHost(options) {
  var settings = options || {};
  var mount = settings.mount || null;
  var registry = settings.registry || null;
  var renderers = settings.renderers || {};
  var surfaceId = cleanString(settings.surfaceId);
  var bound = false;

  if (!registry || typeof registry.projectControls !== "function") {
    throw new Error("Docs Viewer control surface host requires a control registry.");
  }
  if (!surfaceId) throw new Error("Docs Viewer control surface host requires a surface id.");

  function handleEvent(event) {
    if (!mount || typeof settings.onDispatch !== "function") return;
    var target = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-docs-viewer-control]")
      : null;
    if (!target || !mount.contains(target)) return;
    var actionTarget = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-docs-viewer-action]")
      : null;
    if (actionTarget && !target.contains(actionTarget)) actionTarget = null;
    settings.onDispatch({
      actionId: cleanString(actionTarget ? actionTarget.dataset.docsViewerAction : target.dataset.docsViewerAction),
      controlId: cleanString(target.dataset.docsViewerControl),
      event: event,
      eventType: event.type,
      surfaceId: surfaceId,
      target: target,
      actionTarget: actionTarget
    });
  }

  function bind() {
    if (!mount || bound) return;
    DELEGATED_EVENT_TYPES.forEach(function (eventType) {
      mount.addEventListener(eventType, handleEvent);
    });
    bound = true;
  }

  function render(state) {
    if (!mount) return [];
    var activeState = state || {};
    var controls = registry.projectControls({
      activeModeId: activeState.activeModeId,
      activeViewId: activeState.activeViewId,
      controlStateById: activeState.controlStateById,
      surfaceId: surfaceId
    });
    var roots = controls.map(function (control) {
      var renderer = rendererFor(renderers, control.renderer);
      if (!renderer) {
        throw new Error("Docs Viewer control " + control.id + " has no renderer contribution: " + control.renderer);
      }
      var existingRoot = Array.from(mount.children).find(function (child) {
        return child.dataset && child.dataset.docsViewerControl === control.id;
      }) || null;
      var parts = renderedParts(renderer({
        control: control,
        document: mount.ownerDocument,
        existingRoot: existingRoot,
        mount: mount,
        surfaceId: surfaceId
      }));
      if (!parts.root) throw new Error("Docs Viewer control renderer returned no element: " + control.renderer);
      applyControlIdentity(parts, control, surfaceId);
      applyControlState(parts, control);
      return parts.root;
    });
    var currentRoots = Array.from(mount.children);
    var orderChanged = currentRoots.length !== roots.length || roots.some(function (root, index) {
      return currentRoots[index] !== root;
    });
    if (orderChanged) mount.replaceChildren.apply(mount, roots);
    mount.hidden = roots.every(function (root) { return root.hidden; });
    bind();
    return controls;
  }

  function dispose() {
    if (!mount || !bound) return;
    DELEGATED_EVENT_TYPES.forEach(function (eventType) {
      mount.removeEventListener(eventType, handleEvent);
    });
    bound = false;
  }

  return {
    bind: bind,
    dispose: dispose,
    render: render,
    surfaceId: function () { return surfaceId; }
  };
}
