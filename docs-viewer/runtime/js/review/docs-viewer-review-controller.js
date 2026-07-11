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
    var select = documentRef.createElement("select");
    select.setAttribute("aria-label", "Review package");
    var buildButton = createButton(documentRef, "Build");
    var assetsButton = createButton(documentRef, "Assets");
    canonicalLink = documentRef.createElement("a");
    canonicalLink.className = "button button--secondary";
    canonicalLink.textContent = "Open canonical";
    canonicalLink.target = "_blank";
    canonicalLink.rel = "noopener";
    canonicalLink.hidden = true;
    mount.append(select, buildButton, assetsButton, canonicalLink);

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
    var docId = String(context && context.doc && context.doc.doc_id || "").trim();
    projectCanonicalLink(docId);
  }

  return {
    mountDocumentExtras: mountDocumentExtras,
    setProvider: setProvider,
    start: start
  };
}
