function createButton(documentRef, label) {
  var button = documentRef.createElement("button");
  button.type = "button";
  button.className = "button button--secondary";
  button.textContent = label;
  return button;
}

export function createDocsViewerReviewController(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var windowRef = settings.window || window;
  var provider = null;
  var manifest = null;
  var canonicalLink = null;
  var currentDoc = null;
  var parentDialog = null;
  var parentSelect = null;
  var parentRevision = "";

  function flattenDocs(records, output) {
    (records || []).forEach(function (record) {
      output.push(record);
      flattenDocs(record.children, output);
    });
    return output;
  }

  function editParent() {
    if (!provider || !currentDoc || !parentDialog || !parentSelect) return;
    Promise.all([provider.readIndex(), provider.readSource(currentDoc.doc_id)]).then(function (results) {
      var docs = flattenDocs(results[0].docs, []);
      parentRevision = results[1].source_revision;
      parentSelect.textContent = "";
      [{ doc_id: "", title: "Root" }].concat(docs.filter(function (doc) {
        return doc.doc_id !== currentDoc.doc_id;
      })).forEach(function (doc) {
        var option = documentRef.createElement("option");
        option.value = doc.doc_id;
        option.textContent = doc.doc_id ? doc.doc_id + " — " + (doc.title || doc.doc_id) : doc.title;
        option.selected = doc.doc_id === String(currentDoc.parent_id || "");
        parentSelect.appendChild(option);
      });
      parentDialog.showModal();
    }).catch(function (error) {
      setStatus(error.message || "Review parent update failed.", true);
    });
  }

  function createParentDialog() {
    parentDialog = documentRef.createElement("dialog");
    parentDialog.className = "docsViewer__reviewParentDialog";
    var form = documentRef.createElement("form");
    form.method = "dialog";
    var heading = documentRef.createElement("h2");
    heading.textContent = "Review parent";
    parentSelect = documentRef.createElement("select");
    parentSelect.setAttribute("aria-label", "Parent document");
    var actions = documentRef.createElement("div");
    actions.className = "docsViewer__reviewParentActions";
    var cancel = createButton(documentRef, "Cancel");
    cancel.type = "submit";
    cancel.value = "cancel";
    var save = createButton(documentRef, "Save parent");
    save.type = "submit";
    save.value = "save";
    actions.append(cancel, save);
    form.append(heading, parentSelect, actions);
    parentDialog.appendChild(form);
    documentRef.body.appendChild(parentDialog);
    parentDialog.addEventListener("close", function () {
      if (parentDialog.returnValue !== "save" || !currentDoc || !parentRevision) return;
      setStatus("Updating review parent...", false);
      provider.writeParent(currentDoc.doc_id, parentRevision, parentSelect.value).then(function (payload) {
        setStatus(payload.summary_text || "Review parent updated.", false);
        windowRef.location.reload();
      }).catch(function (error) {
        setStatus(error.message || "Review parent update failed.", true);
      });
    });
  }

  function projectCanonicalLink(docId) {
    if (!canonicalLink || !manifest) return;
    var sourceScope = String(manifest.source_scope || "").trim();
    var selectedDocId = String(docId || "").trim();
    canonicalLink.hidden = !(sourceScope && selectedDocId);
    canonicalLink.href = sourceScope && selectedDocId
      ? "/docs/?scope=" + encodeURIComponent(sourceScope) + "&doc=" + encodeURIComponent(selectedDocId)
      : "";
  }

  function setStatus(message, isError) {
    var status = documentRef.getElementById("docsViewerStatus");
    if (!status) return;
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function setProvider(value) {
    provider = value;
  }

  function start() {
    var mount = documentRef.getElementById("docsViewerReviewControlsMount");
    if (!mount || !provider) return Promise.resolve(null);
    mount.textContent = "";
    createParentDialog();
    var select = documentRef.createElement("select");
    select.setAttribute("aria-label", "Review package");
    var buildButton = createButton(documentRef, "Build");
    var assetsButton = createButton(documentRef, "Assets");
    var parentButton = createButton(documentRef, "Parent");
    canonicalLink = documentRef.createElement("a");
    canonicalLink.className = "button button--secondary";
    canonicalLink.textContent = "Open canonical";
    canonicalLink.target = "_blank";
    canonicalLink.rel = "noopener";
    canonicalLink.hidden = true;
    mount.append(select, buildButton, assetsButton, parentButton, canonicalLink);

    select.addEventListener("change", function () {
      var url = new URL(windowRef.location.href);
      url.searchParams.set("package", select.value);
      url.searchParams.delete("doc");
      url.searchParams.delete("view");
      windowRef.location.assign(url.pathname + url.search);
    });
    buildButton.addEventListener("click", function () {
      buildButton.disabled = true;
      setStatus("Building review package...", false);
      provider.build().then(function (payload) {
        setStatus(payload.summary_text || "Review package built.", false);
        windowRef.location.reload();
      }).catch(function (error) {
        setStatus(error.message || "Review build failed.", true);
        buildButton.disabled = false;
      });
    });
    assetsButton.addEventListener("click", function () {
      provider.readAssetInventory().then(function (payload) {
        var names = Object.keys(payload.inventories || {});
        setStatus(names.length ? "Package inventories: " + names.join(", ") + "." : "No package asset inventories.", false);
      }).catch(function (error) {
        setStatus(error.message || "Asset inventory read failed.", true);
      });
    });
    parentButton.addEventListener("click", editParent);

    return Promise.all([provider.listCollections(), provider.readManifest()]).then(function (results) {
      var packages = results[0];
      manifest = results[1].manifest || {};
      packages.forEach(function (record) {
        var option = documentRef.createElement("option");
        option.value = record.package_id;
        option.textContent = record.title || record.package_id;
        option.selected = record.package_id === provider.activeCollectionId();
        select.appendChild(option);
      });
      projectCanonicalLink(new URLSearchParams(windowRef.location.search).get("doc"));
      return results;
    }).catch(function (error) {
      setStatus(error.message || "Docs Review package discovery failed.", true);
      return null;
    });
  }

  function mountDocumentExtras(context) {
    currentDoc = context && context.doc ? context.doc : null;
    var docId = String(context && context.doc && context.doc.doc_id || "").trim();
    projectCanonicalLink(docId);
  }

  return {
    mountDocumentExtras: mountDocumentExtras,
    setProvider: setProvider,
    start: start
  };
}
