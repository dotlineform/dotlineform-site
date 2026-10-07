const snapshots = new Map();

/**
 * Keep one JSON-safe browsing snapshot per configured collection report and tab.
 * Report owners supply controls; this owner supplies storage and reading position.
 * No document payloads, mounts or subscriptions survive through this snapshot.
 * Blocked session storage still permits restoration within the current page.
 * @param {Object} options Report identity and control callbacks.
 * @param {HTMLElement} options.root Mounted report whose ancestors own scroll.
 * @param {string} options.collectionId Configured collection identity.
 * @param {string} options.hostDocId Immutable ordinary report host identity.
 * @param {function(): boolean} options.isReady Whether current list controls are ready.
 * @param {function(): Object} options.captureControls JSON-safe control snapshot.
 * @param {function(Object): void} options.restoreControls Reconcile saved controls with current inventory.
 * @returns {Object} Capture/restore owner; dispose releases listeners and pending position restoration.
 */
export function createDocsCollectionReportState(options) {
  const root = options.root;
  const window = root.ownerDocument.defaultView;
  const key = "docs-viewer:collection-report:v1:" + window.location.pathname
    + ":" + options.collectionId + ":" + options.hostDocId;
  let frame = null;

  function visible() {
    return options.isReady() && root.isConnected
      && !root.closest('[hidden], [data-docs-content-detail-active], [data-document-display-mode="markdown-source"]');
  }

  function read() {
    if (snapshots.has(key)) return snapshots.get(key);
    try {
      const saved = JSON.parse(window.sessionStorage.getItem(key));
      if (saved && saved.controls && typeof saved.controls === "object"
        && !Array.isArray(saved.controls) && Array.isArray(saved.positions)) {
        snapshots.set(key, saved);
        return saved;
      }
    } catch (_error) {
      // Remembering report controls is optional when browser storage is unavailable.
    }
    return null;
  }

  function save() {
    if (!visible() || frame !== null) return read()?.controls || null;
    const positions = [];
    for (let node = root; node; node = node.parentElement) {
      positions.push({ top: node.scrollTop, left: node.scrollLeft });
    }
    try {
      const serialized = JSON.stringify({ controls: options.captureControls(), positions,
        x: window.scrollX, y: window.scrollY });
      snapshots.set(key, JSON.parse(serialized));
      try { window.sessionStorage.setItem(key, serialized); } catch (_error) {
        // The small in-page snapshot remains usable without session storage.
      }
    } catch (_error) {
      // An invalid contribution snapshot must not prevent document navigation.
    }
    return read()?.controls || null;
  }

  function restore() {
    const saved = read();
    if (saved && options.isReady()) options.restoreControls(saved.controls);
  }

  function restorePosition() {
    const saved = read();
    if (!saved || !visible() || window.location.hash) return;
    if (frame !== null) window.cancelAnimationFrame(frame);
    frame = window.requestAnimationFrame(function () {
      frame = null;
      if (!visible() || window.location.hash) return;
      let index = 0;
      for (let node = root; node; node = node.parentElement) {
        const position = saved.positions[index++];
        if (position && Number.isFinite(position.top) && Number.isFinite(position.left)) {
          node.scrollTop = position.top;
          node.scrollLeft = position.left;
        }
      }
      if (Number.isFinite(saved.x) && Number.isFinite(saved.y)) window.scrollTo(saved.x, saved.y);
    });
  }

  // Capture before a toolbar action can hide the rendered report (for example Source).
  window.addEventListener("click", save, true);
  window.addEventListener("pagehide", save);
  return {
    save, restore, restorePosition,
    dispose: function () {
      save();
      window.removeEventListener("click", save, true);
      window.removeEventListener("pagehide", save);
      if (frame !== null) window.cancelAnimationFrame(frame);
      frame = null;
    }
  };
}
