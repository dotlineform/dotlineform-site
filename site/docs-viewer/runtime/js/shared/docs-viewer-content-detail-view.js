export const CONTENT_DETAIL_BACK_CONTROL_ID = "content-detail-back";
export const CONTENT_DETAIL_LABEL_CONTROL_ID = "content-detail-label";

function hideContentDetailControls(context) {
  if (!context || !context.mainView) return;
  context.mainView.projectControlState(CONTENT_DETAIL_BACK_CONTROL_ID, { hidden: true });
  context.mainView.projectControlState(CONTENT_DETAIL_LABEL_CONTROL_ID, { hidden: true });
}

function showContentDetailControls(context, label) {
  context.mainView.projectControlState(CONTENT_DETAIL_BACK_CONTROL_ID, {
    hidden: false,
    label: "Back to document"
  });
  context.mainView.projectControlState(CONTENT_DETAIL_LABEL_CONTROL_ID, {
    hidden: false,
    label: label
  });
}

/** Create the public-safe hosted lifecycle for one exact static presentation. */
export function createDocsViewerContentDetailView(options) {
  var settings = options || {};
  var tableDetailAdapter = settings.tableDetailAdapter || null;
  var active = null;

  function release(context, restoreDocumentContext) {
    if (!active) {
      hideContentDetailControls(context);
      return;
    }
    var current = active;
    active = null;
    current.presentation.release();
    if (current.mount && current.mount.dataset) {
      delete current.mount.dataset.docsContentDetailActive;
    }
    hideContentDetailControls(context);
    if (!restoreDocumentContext) return;
    if (current.window && typeof current.window.scrollTo === "function") {
      current.window.scrollTo({ left: current.scrollX, top: current.scrollY, behavior: "auto" });
    }
    if (current.presentation.invocationControl && current.presentation.invocationControl.isConnected) {
      current.presentation.invocationControl.focus({ preventScroll: true });
    }
  }

  function mount(context) {
    if (!tableDetailAdapter || typeof tableDetailAdapter.mountPresentation !== "function") {
      throw new Error("Content Detail View requires a table adapter.");
    }
    var mount = context.mount;
    if (!mount || !mount.ownerDocument) {
      throw new Error("Content Detail View requires the current document mount.");
    }
    var documentRef = mount.ownerDocument;
    var windowRef = documentRef.defaultView;
    var presentation = tableDetailAdapter.mountPresentation({
      content: mount,
      document: documentRef,
      targetContext: context.targetContext
    });
    active = {
      mount: mount,
      presentation: presentation,
      scrollX: windowRef ? windowRef.scrollX : 0,
      scrollY: windowRef ? windowRef.scrollY : 0,
      window: windowRef
    };
    mount.dataset.docsContentDetailActive = "true";
    mount.appendChild(presentation.root);
    if (typeof presentation.activate === "function") {
      presentation.activate({
        projectControlState: context.mainView.projectControlState,
        showWarning: context.mainView.showWarning
      });
    }
    showContentDetailControls(context, presentation.label);
    presentation.focusTarget.focus({ preventScroll: true });
  }

  return {
    beforeLeave: function () { return true; },
    mount: mount,
    update: function (context) {
      release(context, false);
      mount(context);
    },
    unmount: function (context) {
      release(context, context.requestReason === "back");
    },
    dispose: function (context) {
      release(context, false);
    }
  };
}

/** Add the public/Manage Content Detail definitions to one entrypoint contribution. */
export function withDocsViewerContentDetailDefinitions(definitions, options) {
  var source = definitions || {};
  var settings = options || {};
  return {
    views: (source.views || []).concat([{
      id: "content-detail",
      label: "Content detail",
      panel: "main",
      appKinds: ["public", "manage"],
      mainLayoutState: "expanded-main",
      load: function () {
        return createDocsViewerContentDetailView({
          tableDetailAdapter: settings.tableDetailAdapter
        });
      }
    }]),
    modes: (source.modes || []).slice(),
    controls: (source.controls || []).concat([
      {
        id: CONTENT_DETAIL_BACK_CONTROL_ID,
        label: "Back to document",
        ownerType: "view",
        ownerViewId: "content-detail",
        surfaceId: "main-view",
        appKinds: ["public", "manage"],
        renderer: "content-detail-back"
      },
      {
        id: CONTENT_DETAIL_LABEL_CONTROL_ID,
        label: "Content detail",
        ownerType: "view",
        ownerViewId: "content-detail",
        surfaceId: "main-view",
        appKinds: ["public", "manage"],
        renderer: "content-detail-label"
      }
    ])
  };
}
