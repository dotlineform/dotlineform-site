export const CONTENT_DETAIL_BACK_CONTROL_ID = "content-detail-back";
export const CONTENT_DETAIL_LABEL_CONTROL_ID = "content-detail-label";
export const CONTENT_DETAIL_OPEN_NEW_TAB_CONTROL_ID = "content-detail-open-new-tab";

function hideContentDetailControls(context) {
  if (!context || !context.mainView) return;
  context.mainView.projectControlState(CONTENT_DETAIL_BACK_CONTROL_ID, { hidden: true });
  context.mainView.projectControlState(CONTENT_DETAIL_LABEL_CONTROL_ID, { hidden: true });
  context.mainView.projectControlState(CONTENT_DETAIL_OPEN_NEW_TAB_CONTROL_ID, {
    hidden: true,
    href: ""
  });
}

function projectNewTabTarget(context, target) {
  var href = String(target || "").trim();
  context.mainView.projectControlState(CONTENT_DETAIL_OPEN_NEW_TAB_CONTROL_ID, {
    hidden: !href,
    href: href,
    label: "Open in new tab"
  });
}

function showContentDetailControls(context, presentation) {
  context.mainView.projectControlState(CONTENT_DETAIL_BACK_CONTROL_ID, {
    hidden: false,
    label: "Back to document"
  });
  context.mainView.projectControlState(CONTENT_DETAIL_LABEL_CONTROL_ID, {
    hidden: false,
    label: presentation.label
  });
  projectNewTabTarget(context, presentation.newTabTarget);
}

/** Create the public-safe hosted lifecycle for one exact static presentation. */
export function createDocsViewerContentDetailView(options) {
  var settings = options || {};
  var tableDetailAdapter = settings.tableDetailAdapter || null;
  var diagramDetailAdapter = settings.diagramDetailAdapter || null;
  var active = null;

  function presentationAdapter(targetContext) {
    var kind = String(targetContext && targetContext.kind || "").trim();
    if (kind === "table") return tableDetailAdapter;
    if (kind === "diagram") return diagramDetailAdapter;
    return null;
  }

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
    var adapter = presentationAdapter(context.targetContext);
    if (!adapter || typeof adapter.mountPresentation !== "function") {
      throw new Error("Content Detail View requires a supported exact target adapter.");
    }
    var mount = context.mount;
    if (!mount || !mount.ownerDocument) {
      throw new Error("Content Detail View requires the current document mount.");
    }
    var documentRef = mount.ownerDocument;
    var windowRef = documentRef.defaultView;
    var presentation = adapter.mountPresentation({
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
    showContentDetailControls(context, presentation);
    if (typeof presentation.activate === "function") {
      presentation.activate({
        projectNewTabTarget: function (target) {
          projectNewTabTarget(context, target);
        },
        projectControlState: context.mainView.projectControlState,
        showWarning: context.mainView.showWarning
      });
    }
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
          diagramDetailAdapter: settings.diagramDetailAdapter,
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
      },
      {
        id: CONTENT_DETAIL_OPEN_NEW_TAB_CONTROL_ID,
        label: "Open in new tab",
        ownerType: "view",
        ownerViewId: "content-detail",
        surfaceId: "main-view",
        appKinds: ["public", "manage"],
        renderer: "content-detail-open-new-tab"
      }
    ])
  };
}
