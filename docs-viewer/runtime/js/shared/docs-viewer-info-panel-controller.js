import {
  createDocsViewerInfoPanelHost
} from "./docs-viewer-info-panel-host.js";
/** Own detached reader capture in the shared shell; Close or Source entry releases it. */
export function createDocsViewerInfoPanelController(options) {
  var settings = options || {};
  var refs = settings.refs || {};
  var panelView = settings.panelView || null;
  var capture = null;
  var host = createDocsViewerInfoPanelHost({
    refs: refs,
    registry: settings.registry,
    project: function (projection) {
      settings.projectInfoPanel(Object.assign({}, projection || {}, {
        titleHref: capture ? settings.documentHref(capture.target) : ""
      }));
      if (panelView && typeof settings.projectViewState === "function") {
        panelView.viewState = settings.projectViewState();
      }
    }
  });

  function close() {
    capture = null;
    return host.close();
  }

  /** Retain one detached reader capture until replacement, Close or Source entry. */
  function pinRelatedLinks(nextCapture) {
    if (capture && host.isOpen() && capture.target.collection === nextCapture.target.collection
        && capture.target.doc_id === nextCapture.target.doc_id) return;
    capture = nextCapture;
    host.open("related-links", { capture: capture, panelTitle: capture.title });
  }

  function closeIfOpen() {
    if (!host.isOpen()) return false;
    close();
    return true;
  }

  function bind() {
    if (refs.closeButton) {
      refs.closeButton.addEventListener("click", function () {
        close();
      });
    }
  }

  return {
    bind: bind,
    closeIfOpen: closeIfOpen,
    pinRelatedLinks: pinRelatedLinks
  };
}
