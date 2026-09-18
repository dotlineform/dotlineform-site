/** Edit the active source session, retaining field input independently of this view. */
export function createSourceMetadataView() {
  var adapter = null;
  var unsubscribe = null;
  var fields = null;

  function render(context) {
    if (!adapter || !context.mount) return;
    var session = adapter.getSessionState();
    if (!session.loaded) {
      context.mount.textContent = "Loading document metadata…";
      return;
    }
    if (fields) {
      fields.disabled = session.busy;
      return;
    }
    var metadata = adapter.getMetadataDraft();
    fields = document.createElement("fieldset");
    fields.className = "docsViewerSourceEditor__metadataFields";
    fields.disabled = session.busy;
    ["title", "summary"].forEach(function (key) {
      var label = document.createElement("label");
      label.className = "docsViewer__field" + (key === "summary" ? " docsViewer__field--textarea" : "");
      var heading = document.createElement("span");
      heading.className = "docsViewer__fieldLabel";
      heading.textContent = key === "title" ? "Title" : "Summary";
      var input = document.createElement(key === "title" ? "input" : "textarea");
      input.className = "docsViewer__fieldInput" + (key === "summary" ? " docsViewer__fieldInput--textarea" : "");
      input.value = metadata[key];
      input.required = key === "title";
      if (key === "summary") input.rows = 4;
      input.addEventListener("input", function () { adapter.setMetadataField(key, input.value); });
      label.append(heading, input);
      fields.appendChild(label);
    });
    context.mount.replaceChildren(fields);
  }

  function unmount(context) {
    if (unsubscribe) unsubscribe();
    unsubscribe = null;
    adapter = null;
    fields = null;
    if (context.mount) context.mount.replaceChildren();
  }

  return {
    mount: function (context) {
      adapter = context.sourceEditorServices.getActiveSourceEditorContextAdapter();
      if (adapter) unsubscribe = adapter.onSessionChange(function () { render(context); });
      render(context);
    },
    update: render,
    unmount: unmount,
    dispose: unmount
  };
}
