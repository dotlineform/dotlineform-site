function createButton(documentRef, label) {
  var button = documentRef.createElement("button");
  button.type = "button";
  button.className = "docsViewer__actionButton";
  button.textContent = label;
  return button;
}

export function createDocsViewerReviewViewDefinitions() {
  return {
    controls: [{
      id: "review-package-controls",
      label: "Review package",
      ownerType: "app",
      surfaceId: "app-viewer",
      appKinds: ["review"],
      renderer: "review-package-controls"
    }]
  };
}

function renderReviewPackageControls(context) {
  var mount = context.existingRoot;
  if (!mount || mount.id !== "docsViewerReviewControlsMount") {
    mount = context.document.createElement("div");
    mount.id = "docsViewerReviewControlsMount";
    mount.className = "docsViewer__reviewControls";
    mount.setAttribute("role", "group");
    mount.setAttribute("aria-label", "Review package controls");

    var select = context.document.createElement("select");
    select.className = "docsViewer__searchInput docsViewer__reviewPackageSelect";
    select.setAttribute("aria-label", "Review package");
    var buildButton = createButton(context.document, "Repair");
    buildButton.setAttribute("data-docs-viewer-review-action", "repair");
    var assetsButton = createButton(context.document, "Assets");
    assetsButton.setAttribute("data-docs-viewer-review-action", "assets");
    var importLink = context.document.createElement("a");
    importLink.className = "docsViewer__actionButton docsViewer__reviewImportLink";
    importLink.textContent = "Import";
    importLink.hidden = true;
    var canonicalLink = context.document.createElement("a");
    canonicalLink.className = "docsViewer__actionButton docsViewer__reviewCanonicalLink";
    canonicalLink.textContent = "Open canonical";
    canonicalLink.target = "_blank";
    canonicalLink.rel = "noopener";
    canonicalLink.hidden = true;
    mount.append(select, buildButton, assetsButton, importLink, canonicalLink);
  }
  return { root: mount, interactive: mount.querySelector("select") };
}

export function createDocsViewerReviewControlRenderers() {
  return { "review-package-controls": renderReviewPackageControls };
}

export function createDocsViewerReviewController(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var windowRef = settings.window || window;
  var provider = null;
  var manifest = null;
  var canonicalLink = null;
  var importLink = null;

  function projectCanonicalLink(docId) {
    if (!canonicalLink || !manifest) return;
    var sourceScope = String(manifest.source_scope || "").trim();
    var selectedDocId = String(docId || "").trim();
    canonicalLink.hidden = !(sourceScope && selectedDocId);
    canonicalLink.href = sourceScope && selectedDocId
      ? "/docs/?scope=" + encodeURIComponent(sourceScope) + "&doc=" + encodeURIComponent(selectedDocId)
      : "";
  }

  function projectImportLink() {
    if (!importLink || !manifest || !provider) return;
    var packageId = String(manifest.package_id || provider.activeCollectionId() || "").trim();
    importLink.hidden = !packageId;
    importLink.href = packageId
      ? "/docs/?import=1&review_package=" + encodeURIComponent(packageId)
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
    var select = mount.querySelector("select");
    var buildButton = mount.querySelector('[data-docs-viewer-review-action="repair"]');
    var assetsButton = mount.querySelector('[data-docs-viewer-review-action="assets"]');
    importLink = mount.querySelector(".docsViewer__reviewImportLink");
    canonicalLink = mount.querySelector(".docsViewer__reviewCanonicalLink");
    if (!select || !buildButton || !assetsButton || !importLink || !canonicalLink) {
      return Promise.reject(new Error("Docs Review package controls failed to render."));
    }

    select.addEventListener("change", function () {
      var url = new URL(windowRef.location.href);
      url.searchParams.set("package", select.value);
      url.searchParams.delete("doc");
      url.searchParams.delete("view");
      windowRef.location.assign(url.pathname + url.search);
    });
    buildButton.addEventListener("click", function () {
      buildButton.disabled = true;
      setStatus("Repairing review package generated output...", false);
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
      projectImportLink();
      var activePackage = packages.find(function (record) {
        return record.package_id === provider.activeCollectionId();
      });
      buildButton.disabled = Boolean(activePackage && activePackage.built);
      buildButton.textContent = buildButton.disabled ? "Built" : "Repair";
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
