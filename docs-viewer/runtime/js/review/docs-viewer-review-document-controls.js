import {
  renderDocsViewerManagementDocumentActions
} from "../management/docs-viewer-management-document-actions-renderer.js";

export function createDocsViewerReviewDocumentControls() {
  var refs = null;
  var boundRoot = null;
  var routeModeApplied = false;
  var lastSettings = null;

  function projectUrl(windowRef, sourceActive) {
    var url = new URL(windowRef.location.href);
    if (sourceActive) url.searchParams.set("view", "source");
    else url.searchParams.delete("view");
    windowRef.history.replaceState(windowRef.history.state, "", url.pathname + url.search + url.hash);
  }

  function render(options) {
    var settings = options || {};
    lastSettings = settings;
    var root = settings.root;
    var viewRegistry = settings.viewRegistry;
    var activeViewState = settings.activeViewState || {};
    var windowRef = settings.window || window;
    if (!refs) {
      refs = renderDocsViewerManagementDocumentActions({
        document: settings.document,
        root: root,
        viewRegistry: viewRegistry
      });
    }
    if (!refs) return;
    var sourceControl = viewRegistry.resolveControl("markdown-source", activeViewState);
    var saveControl = viewRegistry.resolveControl("save-markdown-source", activeViewState);
    if (refs.sourceButton) {
      refs.sourceButton.hidden = !sourceControl.available;
      refs.sourceButton.disabled = !sourceControl.available;
      refs.sourceButton.classList.toggle("is-active", activeViewState.activeModeId === "markdown-source");
    }
    if (refs.sourceSaveButton) {
      refs.sourceSaveButton.hidden = !(saveControl.available && saveControl.active);
      refs.sourceSaveButton.disabled = !(saveControl.available && saveControl.active);
    }

    if (boundRoot !== root) {
      boundRoot = root;
      root.addEventListener("click", function (event) {
        var button = event.target.closest("[data-docs-viewer-action]");
        if (!button || button.disabled) return;
        if (button.dataset.docsViewerAction === "markdown-source") {
          var nextMode = button.classList.contains("is-active") ? "rendered-document" : "markdown-source";
          routeModeApplied = true;
          settings.requestDocumentMode(nextMode, { warn: false });
          projectUrl(windowRef, nextMode === "markdown-source");
        }
        if (button.dataset.docsViewerAction === "markdown-save") {
          root.dispatchEvent(new CustomEvent("docs-viewer-source-editor-save", { bubbles: true }));
        }
      });
    }

    if (routeModeApplied) {
      projectUrl(windowRef, activeViewState.activeModeId === "markdown-source");
    }
  }

  function applyRequestedMode() {
    if (!lastSettings) return;
    var sourceRequested = new URLSearchParams(lastSettings.window.location.search).get("view") === "source";
    routeModeApplied = true;
    if (sourceRequested && lastSettings.activeViewState.activeModeId !== "markdown-source") {
      lastSettings.requestDocumentMode("markdown-source", { warn: false });
    }
  }

  return {
    applyRequestedMode: applyRequestedMode,
    render: render
  };
}
