function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function lifecycleFromLoaded(loaded, fallback) {
  if (loaded && typeof loaded === "object") return loaded;
  return fallback || {};
}

function callLifecycle(lifecycle, name, context) {
  if (!lifecycle || typeof lifecycle[name] !== "function") return Promise.resolve(null);
  return Promise.resolve(lifecycle[name](context));
}

export function createDocsViewerInfoPanelHost(options = {}) {
  const refs = options.refs || {};
  const registry = options.registry || null;
  const project = typeof options.project === "function" ? options.project : function () {};
  let activeViewId = "";
  let activeLifecycle = null;
  let mounted = false;
  let open = false;

  function viewOptions() {
    return (registry ? registry.listViews("info") : []).map(function (view) {
      return {
        id: view.id,
        label: view.label,
        available: Boolean(view.available),
        unavailableReason: view.unavailableReason || ""
      };
    });
  }

  function projectPanel(projection) {
    project(Object.assign({
      activeViewId: activeViewId,
      statusHidden: true,
      title: "info",
      visible: open
    }, projection || {}));
  }

  function unavailableStatus(reason) {
    if (reason === "access") return "This info view is not available on this route.";
    if (reason === "disabled") return "This info view is disabled.";
    return "This info view is unavailable.";
  }

  function unmountActive() {
    const lifecycle = activeLifecycle;
    activeLifecycle = null;
    mounted = false;
    if (refs.body) refs.body.replaceChildren();
    return callLifecycle(lifecycle, "unmount", { mount: refs.body });
  }

  function close() {
    open = false;
    return unmountActive().finally(function () {
      projectPanel({ visible: false, statusText: "", statusHidden: true, statusError: false });
    });
  }

  function loadLifecycle(view) {
    return Promise.resolve()
      .then(function () {
        return typeof view.load === "function" ? view.load() : null;
      })
      .then(function (loaded) {
        return lifecycleFromLoaded(loaded, view);
      });
  }

  function mountLifecycle(lifecycle, context) {
    activeLifecycle = lifecycle;
    mounted = true;
    return callLifecycle(lifecycle, "mount", Object.assign({ mount: refs.body }, context || {}));
  }

  function openView(viewId, context) {
    const nextViewId = cleanString(viewId);
    activeViewId = nextViewId;
    if (!registry || typeof registry.resolveView !== "function") {
      open = true;
      projectPanel({
        statusText: "Info views are unavailable.",
        statusHidden: false,
        statusError: true,
        visible: true
      });
      return Promise.resolve(false);
    }

    const resolved = registry.resolveView(nextViewId);
    open = true;
    if (!resolved.available || !resolved.view) {
      unmountActive();
      projectPanel({
        statusText: unavailableStatus(resolved.reason),
        statusHidden: false,
        statusError: true,
        visible: true
      });
      return Promise.resolve(false);
    }

    projectPanel({ statusText: "", statusHidden: true, statusError: false, visible: true });
    return unmountActive()
      .then(function () {
        return loadLifecycle(resolved.view);
      })
      .then(function (lifecycle) {
        return mountLifecycle(lifecycle, context).then(function () {
          return true;
        });
      })
      .catch(function (error) {
        console.warn("docs_viewer: info panel hosted view failed", error);
        activeLifecycle = null;
        mounted = false;
        if (refs.body) refs.body.replaceChildren();
        projectPanel({
          statusText: "Info view failed to load.",
          statusHidden: false,
          statusError: true,
          visible: true
        });
        return false;
      });
  }

  function update(context) {
    if (!open || !mounted || !activeLifecycle) return Promise.resolve(false);
    return callLifecycle(activeLifecycle, "update", Object.assign({ mount: refs.body }, context || {}))
      .then(function () {
        projectPanel({ statusText: "", statusHidden: true, statusError: false, visible: true });
        return true;
      })
      .catch(function (error) {
        console.warn("docs_viewer: info panel hosted view update failed", error);
        projectPanel({
          statusText: "Info view failed to update.",
          statusHidden: false,
          statusError: true,
          visible: true
        });
        return false;
      });
  }

  function dispose() {
    const lifecycle = activeLifecycle;
    activeLifecycle = null;
    mounted = false;
    open = false;
    if (refs.body) refs.body.replaceChildren();
    return callLifecycle(lifecycle, "dispose", { mount: refs.body });
  }

  return {
    activeViewId: function () { return activeViewId; },
    close: close,
    dispose: dispose,
    isOpen: function () { return open; },
    open: openView,
    update: update,
    viewOptions: viewOptions
  };
}
