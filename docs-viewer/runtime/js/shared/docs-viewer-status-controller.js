export function createDocsViewerStatusController(options) {
  var settings = options || {};
  var root = settings.root || null;
  var status = settings.status || null;
  var state = settings.state || {};

  function setStatus(message, isError) {
    if (!status) return;
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function syncBusyState() {
    var busy = Number(state.pendingBusyCount || 0) > 0;
    if (!root) return;
    root.classList.toggle("is-busy", busy);
    root.setAttribute("aria-busy", busy ? "true" : "false");
    if (root.dataset) root.dataset.docsViewerBusy = busy ? "true" : "false";
  }

  function startBusy() {
    state.pendingBusyCount = Number(state.pendingBusyCount || 0) + 1;
    syncBusyState();
    var stopped = false;
    return function stopBusy() {
      if (stopped) return;
      stopped = true;
      state.pendingBusyCount = Math.max(0, Number(state.pendingBusyCount || 0) - 1);
      syncBusyState();
    };
  }

  return {
    setStatus: setStatus,
    startBusy: startBusy
  };
}
