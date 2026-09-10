import { docsViewerLinksPresentation } from "./docs-viewer-links-presentation.js";

export const LINKS_CONTROL_ID = "document-links";

/** Own Links loading and presentation for an exact mounted document, including children.
 * Navigation invalidates pending reads; opening always reads fresh generated data.
 */
export function createDocsViewerLinksDetailAdapter() {
  var mounts = new WeakMap();
  var generation = 0;

  function project(state, busy) {
    state.context.projectControlState({ hidden: !state.target, disabled: Boolean(busy), busy: Boolean(busy) });
  }

  function setDocument(context) {
    var state = mounts.get(context.content);
    if (!state) return;
    state.version += 1;
    var target = context.target;
    state.target = target && state.context.collectionProvider.canReadLinks(target) ? Object.freeze({ ...target }) : null;
    state.title = context.title || "";
    state.presentation = null;
    project(state, false);
  }

  function releaseDocument(context) {
    var state = mounts.get(context.content);
    if (!state) return;
    mounts.delete(context.content);
    state.target = null;
    project(state, false);
  }

  function mountDocument(context) {
    releaseDocument(context);
    mounts.set(context.content, { context: context, generation: ++generation, version: 0, target: null, presentation: null });
    setDocument(context);
  }

  async function openTarget(context) {
    var state = mounts.get(context.content);
    if (!state || !state.target) return false;
    var version = ++state.version;
    var target = state.target;
    function currentMount() { return mounts.get(context.content) === state && state.version === version; }
    function isCurrent() {
      return currentMount() && (!context.invocationControl || context.invocationControl.isConnected !== false);
    }
    project(state, true);
    try {
      var payload = await state.context.collectionProvider.readLinks(target);
      if (!isCurrent()) return false;
      var data = payload ? docsViewerLinksPresentation(payload, target) : null;
      var record = { data: data, title: state.title, invocationControl: context.invocationControl };
      state.presentation = record;
      return state.context.requestContentDetail({
        kind: "links", generation: state.generation, version: version
      });
    } catch (error) {
      if (isCurrent()) state.context.showWarning(error.message || "Failed to load Links.", true);
      return false;
    } finally {
      if (currentMount()) project(state, false);
    }
  }

  function mountPresentation(context) {
    var targetContext = context.targetContext;
    var state = mounts.get(context.content);
    if (!state || !targetContext || targetContext.generation !== state.generation
      || targetContext.version !== state.version || !state.presentation) {
      throw new Error("Links target is stale or unavailable.");
    }
    var record = state.presentation;
    var data = record.data;
    var documentRef = context.document;
    var root = documentRef.createElement("section");
    root.className = "docsViewer__contentDetail docsViewer__linksDetail";
    root.setAttribute("data-docs-content-detail-view", "links");
    root.tabIndex = -1;
    var heading = documentRef.createElement("h1");
    heading.textContent = data ? data.title : record.title || "Links";
    root.appendChild(heading);
    if (!data || !data.sections.length) {
      var empty = documentRef.createElement("p");
      empty.textContent = data ? "No links." : "Links data is not available for this document.";
      root.appendChild(empty);
    }
    (data ? data.sections : []).forEach(function (group) {
      var section = documentRef.createElement("section");
      section.className = "docsViewer__linksSection";
      var label = documentRef.createElement("h2");
      label.textContent = group.label;
      var list = documentRef.createElement("ul");
      if (group.label === "Concepts") list.className = "docsViewer__linksConcepts";
      group.entries.forEach(function (entry) {
        var row = documentRef.createElement("li");
        var link = documentRef.createElement("a");
        link.href = entry.document.href;
        link.textContent = entry.document.title;
        row.appendChild(link);
        list.appendChild(row);
      });
      section.append(label, list);
      root.appendChild(section);
    });
    return {
      root: root, focusTarget: root, label: "Links", newTabTarget: "",
      invocationControl: record.invocationControl,
      restoreInvocationFocus: function () {
        if (mounts.get(context.content) !== state) return;
        var control = documentRef.querySelector('[data-docs-viewer-control="' + LINKS_CONTROL_ID + '"]');
        if (control && !control.hidden) control.focus({ preventScroll: true });
      },
      release: function () { root.remove(); }
    };
  }

  return { mountDocument, setDocument, releaseDocument, openTarget, mountPresentation };
}

export const docsViewerLinksDetailAdapter = createDocsViewerLinksDetailAdapter();
