import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

const MAIN_VIEW_MOUNT_SELECTOR = "[data-docs-viewer-main-view-mount]";

export function mainViewMount(root) {
  if (!root) return null;
  return root.querySelector(MAIN_VIEW_MOUNT_SELECTOR);
}

export function renderDocsViewerMainView(options = {}) {
  const documentRef = options.document || document;
  const mount = options.mount || null;
  const toolbarMount = options.toolbarMount || null;
  const controls = options.viewRegistry
    ? options.viewRegistry.listControls({ surfaceId: "main-view" }).filter(function (control) {
        return control.available;
      })
    : [];
  if (!mount) return findDocsViewerMainViewRefs({ document: documentRef, root: options.root });

  const main = documentRef.createElement("article");
  main.className = "docsViewer__main";
  main.setAttribute("aria-live", "polite");
  main.setAttribute("data-docs-viewer-panel", "main");

  const toolbar = controls.length ? documentRef.createElement("div") : null;
  if (toolbar) {
    toolbar.className = "docsViewer__mainViewToolbar";
    toolbar.id = "docsViewerMainViewToolbar";
    toolbar.hidden = true;
    toolbar.setAttribute("role", "toolbar");
    toolbar.setAttribute("aria-label", "Document controls");
  }

  const actions = documentRef.createElement("div");
  actions.className = "docsViewer__mainViewToolbarActions";
  actions.setAttribute("data-docs-viewer-control-surface-mount", "main-view");

  if (toolbar) {
    const back = documentRef.createElement("button");
    back.type = "button";
    back.className = "docsViewer__toolbarIconButton docsViewer__collectionBack";
    back.hidden = true;
    back.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--arrow-left"));
    const controlGroup = documentRef.createElement("div");
    controlGroup.className = "docsViewer__mainViewToolbarControlGroup";
    const collectionActions = documentRef.createElement("div");
    collectionActions.className = "docsViewer__collectionActionMount";
    controlGroup.append(actions, collectionActions);
    toolbar.append(back, controlGroup);
  }
  if (toolbarMount && toolbar) {
    toolbarMount.replaceChildren(toolbar);
  } else if (toolbarMount) {
    toolbarMount.replaceChildren();
  }

  const content = documentRef.createElement("div");
  content.className = "docsViewer__content content";
  content.id = "docsViewerContent";

  if (!toolbarMount && toolbar) {
    main.appendChild(toolbar);
  }
  main.appendChild(content);
  mount.replaceChildren(main);

  return findDocsViewerMainViewRefs({ document: documentRef, root: options.root || mount });
}

export function findDocsViewerMainViewRefs(options = {}) {
  const documentRef = options.document || document;
  const root = options.root || documentRef;
  return {
    main: root.querySelector(".docsViewer__main"),
    toolbar: root.querySelector("#docsViewerMainViewToolbar"),
    collectionBack: root.querySelector(".docsViewer__collectionBack"),
    collectionActions: root.querySelector(".docsViewer__collectionActionMount"),
    content: root.querySelector("#docsViewerContent")
  };
}

export function applyDocsViewerMainViewProjection(options = {}) {
  const refs = options.refs || {};
  const projection = options.projection || {};

  applyToolbarHidden(refs.toolbar, projection, "toolbarHidden");
  applyHidden(refs.content, projection, "contentHidden");
}

function applyHidden(element, projection, key) {
  if (!element || !Object.prototype.hasOwnProperty.call(projection, key)) return;
  element.hidden = Boolean(projection[key]);
}

function applyToolbarHidden(element, projection, key) {
  if (!element || !Object.prototype.hasOwnProperty.call(projection, key)) return;
  element.hidden = Boolean(projection[key]);
}
