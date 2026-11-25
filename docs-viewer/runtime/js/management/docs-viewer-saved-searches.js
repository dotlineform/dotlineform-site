import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { fetchManagementJson } from "./docs-viewer-management-client.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";

const SAVED_SEARCHES = "/docs/saved-searches";

export function renderSavedResultsButton({ document, existingRoot }) {
  if (existingRoot) return existingRoot;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "docsViewer__toolbarIconButton";
  button.title = "Saved results";
  button.append(createDocsViewerToolbarIcon(document, "docsViewer__icon--list-plus"));
  return button;
}

/** Name and save the supplied ordered document rows without opening the saved-list chooser. */
export function openSaveResults({ baseUrl, root, restoreFocus, documents }) {
  return openDocsViewerManagementModal({
    root,
    restoreFocus,
    title: "Save results",
    size: "compact",
    bodyHtml: `<p class="docsViewer__modalNote muted small">${documents.length} ${documents.length === 1 ? "document" : "documents"}</p>
      <label class="docsViewer__field" for="newSavedResultsName"><span class="docsViewer__fieldLabel">Name</span>
      <input class="docsViewer__fieldInput" id="newSavedResultsName" type="text" autocomplete="off"></label>`,
    focusSelector: "#newSavedResultsName",
    actions: [{ role: "modal-cancel", label: "Cancel" }, { role: "modal-primary", label: "Save as new" }],
    async onSubmit(api) {
      const name = api.host.querySelector("#newSavedResultsName").value.trim();
      const saved = await fetchManagementJson(SAVED_SEARCHES, "POST", { name, docs: documents }, { baseUrl });
      return { action: "saved", name: saved.name };
    }
  });
}

/** The chooser owns one filename listing. Its actions read or change only the selected file. */
export async function openSavedResults({ baseUrl, root, restoreFocus, documents, loadedName }) {
  const request = (method, path, payload) => fetchManagementJson(path, method, payload, { baseUrl });
  const { names } = await request("GET", SAVED_SEARCHES);
  const modal = { root, restoreFocus };
  const selected = names.includes(loadedName) ? loadedName : names[0];
  const choice = await openDocsViewerManagementModal({
    ...modal,
    title: "Saved results",
    bodyHtml: names.length
      ? `<label class="docsViewer__field docsViewer__field--listbox" for="savedResultsName"><span class="docsViewer__fieldLabel">Saved list</span>
          <select class="docsViewer__fieldInput docsViewer__savedResultsList" id="savedResultsName" size="10">${names.map(name =>
            `<option value="${escapeHtml(name)}"${name === selected ? " selected" : ""}>${escapeHtml(name)}</option>`).join("")}</select></label>`
      : '<p class="docsViewer__modalNote muted small">No saved lists.</p>',
    focusSelector: names.length ? "#savedResultsName"
      : documents.length ? '[data-role="save-new"]' : '[data-role="modal-cancel"]',
    actions: [
      { role: "save-new", label: "Save as new", disabled: !documents.length },
      { role: "delete-list", label: "Delete", disabled: !names.length },
      { role: "modal-cancel", label: "Close" },
      { role: "modal-primary", label: "Load", disabled: !names.length }
    ],
    onOpen(api) {
      api.host.querySelector('[data-role="save-new"]').addEventListener("click", () => api.close({ action: "save" }));
      api.host.querySelector('[data-role="delete-list"]').addEventListener("click", () => {
        api.close({ action: "delete", name: api.host.querySelector("#savedResultsName").value });
      });
    },
    async onSubmit(api) {
      const params = new URLSearchParams({ name: api.host.querySelector("#savedResultsName").value });
      const list = await request("GET", `${SAVED_SEARCHES}?${params}`);
      return { action: "load", list };
    }
  });

  if (choice.action === "save") {
    return openSaveResults({ ...modal, baseUrl, documents });
  }
  if (choice.action === "delete") {
    return openDocsViewerManagementModal({
      ...modal,
      title: "Delete saved list?",
      size: "compact",
      bodyHtml: `<p class="docsViewer__modalNote muted small">${escapeHtml(choice.name)}</p>`,
      focusSelector: '[data-role="modal-cancel"]',
      actions: [{ role: "modal-cancel", label: "Cancel" }, { role: "modal-primary", label: "Delete", tone: "danger" }],
      async onSubmit() {
        const deleted = await request("POST", `${SAVED_SEARCHES}/delete`, { name: choice.name });
        return { action: "deleted", name: deleted.name };
      }
    });
  }
  return choice;
}
