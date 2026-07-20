import {
  escapePackageHtml,
  packageCountsHtml,
  packageIssuesHtml,
  packagePathsHtml,
  packageText
} from "./document-package-view.js";

export function openDocumentPackageModal(options = {}) {
  const host = options.host;
  if (!host) return Promise.resolve({ confirmed: false });
  const restoreFocus = options.restoreFocus instanceof HTMLElement ? options.restoreFocus : null;
  const primaryLabel = packageText(options.primaryLabel);
  const cancelLabel = packageText(options.cancelLabel) || (primaryLabel ? "Cancel" : "Close");
  const titleId = `documentPackageModalTitle-${Date.now()}`;
  host.innerHTML = `
    <div class="docsPackageModal" data-package-modal>
      <button class="docsPackageModal__backdrop" type="button" data-package-modal-cancel aria-label="Close"></button>
      <div class="docsPackageModal__dialog${options.wide ? " docsPackageModal__dialog--wide" : ""}" role="dialog" aria-modal="true" aria-labelledby="${titleId}">
        <header class="docsPackageModal__header">
          <h2 id="${titleId}">${escapePackageHtml(options.title || "Document package")}</h2>
          ${packageText(options.meta) ? `<p>${escapePackageHtml(options.meta)}</p>` : ""}
        </header>
        <div class="docsPackageModal__body">${options.bodyHtml || ""}</div>
        <p class="docsPackageModal__status" data-package-modal-status role="status"></p>
        <div class="docsPackageModal__actions">
          <button class="docsPackageButton" type="button" data-package-modal-cancel>${escapePackageHtml(cancelLabel)}</button>
          ${primaryLabel ? `<button class="docsPackageButton ${options.danger ? "docsPackageButton--danger" : "docsPackageButton--primary"}" type="button" data-package-modal-primary>${escapePackageHtml(primaryLabel)}</button>` : ""}
        </div>
      </div>
    </div>
  `;
  const modal = host.querySelector("[data-package-modal]");
  const dialog = modal && modal.querySelector(".docsPackageModal__dialog");
  const primary = modal && modal.querySelector("[data-package-modal-primary]");
  const status = modal && modal.querySelector("[data-package-modal-status]");
  const focusTarget = modal && modal.querySelector(options.focusSelector || "input, textarea, select, button");

  return new Promise((resolve) => {
    let finished = false;
    function finish(result) {
      if (finished) return;
      finished = true;
      document.removeEventListener("keydown", onKeyDown);
      host.innerHTML = "";
      if (restoreFocus && document.contains(restoreFocus)) restoreFocus.focus();
      resolve(result || { confirmed: false });
    }
    function onKeyDown(event) {
      if (event.key === "Escape") finish({ confirmed: false });
      if (event.key !== "Tab" || !dialog) return;
      const nodes = Array.from(dialog.querySelectorAll("button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex='-1'])"));
      if (!nodes.length) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    modal.querySelectorAll("[data-package-modal-cancel]").forEach((node) => {
      node.addEventListener("click", () => finish({ confirmed: false }));
    });
    if (primary) {
      primary.addEventListener("click", async () => {
        if (typeof options.onSubmit !== "function") {
          finish({ confirmed: true });
          return;
        }
        primary.disabled = true;
        if (status) status.textContent = packageText(options.runningMessage) || "Working…";
        try {
          const result = await options.onSubmit({ host: modal, status, primary });
          if (result === false) {
            primary.disabled = false;
            return;
          }
          finish(result && typeof result === "object" ? result : { confirmed: true });
        } catch (error) {
          primary.disabled = false;
          if (status) {
            status.dataset.state = "error";
            status.textContent = packageText(error && error.message) || "The action failed.";
          }
        }
      });
    }
    document.addEventListener("keydown", onKeyDown);
    window.setTimeout(() => {
      if (focusTarget instanceof HTMLElement) focusTarget.focus();
    }, 0);
  });
}

export function showDocumentPackageResult(options = {}) {
  const payload = options.payload && typeof options.payload === "object" ? options.payload : {};
  const summary = packageText(payload.summary_text || options.summary);
  const bodyHtml = [
    summary ? `<p>${escapePackageHtml(summary)}</p>` : "",
    packageCountsHtml(payload.counts),
    packagePathsHtml(payload),
    packageIssuesHtml(payload)
  ].filter(Boolean).join("");
  return openDocumentPackageModal({
    host: options.host,
    restoreFocus: options.restoreFocus,
    title: options.title || (payload.ok === false ? "Document package issue" : "Document package result"),
    meta: options.meta,
    bodyHtml: bodyHtml || "<p>The action completed.</p>"
  });
}

export function confirmDocumentPackageApply(options = {}) {
  const payload = options.payload && typeof options.payload === "object" ? options.payload : {};
  const bodyHtml = [
    `<p>${escapePackageHtml(packageText(payload.summary_text) || "Apply the complete returned package to its supported canonical targets?")}</p>`,
    packageCountsHtml(payload.counts),
    packageIssuesHtml(payload)
  ].filter(Boolean).join("");
  return openDocumentPackageModal({
    host: options.host,
    restoreFocus: options.restoreFocus,
    title: options.title || "Apply returned package?",
    meta: options.meta,
    bodyHtml,
    primaryLabel: options.primaryLabel || "Apply package",
    cancelLabel: "Cancel",
    danger: true
  });
}
