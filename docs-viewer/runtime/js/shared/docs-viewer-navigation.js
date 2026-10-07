/**
 * Retain the current browser entry and one consumable caller. View owners release
 * everything outside that pair; older native browser destinations reload by URL.
 */
export function createDocsViewerNavigation(options) {
  var window = options.window;
  var session = window.crypto.randomUUID();
  var records = new Map();
  window.history.scrollRestoration = "manual";
  var active = null;
  var restoringCancelledEntry = false;
  var busy = false;

  function owned(state) {
    return state && state.session === session && records.has(state.entryId);
  }

  function project() {
    options.onNavigationChange();
  }

  function retainPair() {
    records.forEach(function (_, id) {
      if (id !== active.entryId && id !== active.callerId) records.delete(id);
    });
    options.retain(Array.from(records.values()).filter(Boolean));
  }

  async function capture() {
    if (!active) return;
    var id = active.entryId;
    var record = await options.capture();
    if (records.has(id)) records.set(id, record);
  }

  function entry(position, callerId) {
    return { session: session, entryId: window.crypto.randomUUID(), position: position, callerId: callerId || "" };
  }

  async function open(destination, settings = {}) {
    if (busy) return null;
    busy = true;
    try {
      if (!await options.confirm()) return null;
      await options.prepare();
      await capture();
      var replace = settings.replace === true;
      var previous = active;
      active = replace && previous ? previous : entry(previous ? previous.position + 1 : 0, previous && previous.entryId);
      window.history[replace ? "replaceState" : "pushState"](active, "", destination.url);
      records.set(active.entryId, null);
      retainPair();
      var result = await options.open(destination);
      await capture();
      return result;
    } catch (error) {
      await capture();
      options.reportError(error);
      return null;
    } finally {
      busy = false;
      if (active) retainPair();
      project();
    }
  }

  async function initialize(destination) {
    active = entry(0, "");
    window.history.replaceState(active, "", destination.url);
    records.set(active.entryId, null);
    await options.prepare();
    var result = await options.open(destination);
    await capture();
    retainPair();
    project();
    return result;
  }

  async function popstate(event) {
    if (restoringCancelledEntry) {
      restoringCancelledEntry = false;
      project();
      return;
    }
    var destination = event.state;
    if (!destination || destination.session !== session) {
      await capture();
      window.location.reload();
      return;
    }
    if (busy) {
      restoringCancelledEntry = true;
      window.history.go(active.position - destination.position);
      return;
    }
    busy = true;
    try {
      if (!await options.confirm()) {
        restoringCancelledEntry = true;
        window.history.go(active.position - destination.position);
        return;
      }
      await options.prepare();
      await capture();
      if (!owned(destination)) {
        window.location.reload();
        return;
      }
      active = Object.assign({}, destination, { callerId: "" });
      window.history.replaceState(active, "", window.location.href);
      await options.restore(records.get(active.entryId));
      await capture();
    } catch (error) {
      options.reportError(error);
    } finally {
      busy = false;
      retainPair();
      project();
    }
  }

  return {
    initialize: initialize,
    open: open,
    back: function () { if (!busy && active && active.callerId && records.has(active.callerId)) window.history.back(); },
    hasCaller: function () { return Boolean(active && active.callerId && records.has(active.callerId)); },
    bind: function () { window.addEventListener("popstate", popstate); },
    replaceUrl: function (url) { if (active) window.history.replaceState(active, "", url); },
    update: function () { return busy ? Promise.resolve() : capture(); }
  };
}
