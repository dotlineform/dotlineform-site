import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { buildWorkThumbPreview } from "./catalogue-media-preview.js";
import { createStudioIcon } from "./studio-icon.js";
import { openConfirmModal } from "./studio-modal.js";

const titleOrder = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function buildResultRow(state, work, galleryId, selected) {
  const isMember = work.gallery_ids.includes(galleryId);
  const row = document.createElement(isMember ? "div" : "label");
  row.className = "catalogueGalleryWorks__row";
  if (isMember) {
    const status = document.createElement("span");
    const icon = createStudioIcon(document, "circle-check");
    icon.classList.add("studioUi__icon--small");
    status.setAttribute("role", "img");
    status.setAttribute("aria-label", "Already in this Gallery");
    status.title = "Already in this Gallery";
    status.append(icon);
    row.append(status);
  } else {
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = work.work_id;
    checkbox.checked = selected;
    row.append(checkbox);
  }

  const thumb = buildWorkThumbPreview(state.mediaConfig, work.work_id, {
    mediaVersion: work.media_version, imageStaged: work.image_staged
  });
  const frame = document.createElement("span");
  frame.className = "catalogueGalleryWorks__thumb";
  if (thumb.src) {
    const image = document.createElement("img");
    image.alt = "";
    image.width = image.height = 48;
    image.loading = "lazy";
    image.decoding = "async";
    image.sizes = "48px";
    image.addEventListener("error", () => image.remove(), { once: true });
    image.srcset = thumb.srcset;
    image.src = thumb.src;
    frame.append(image);
  }

  const details = document.createElement("span");
  const title = document.createElement("strong");
  title.textContent = work.title;
  const meta = document.createElement("span");
  meta.className = "studioForm__meta";
  meta.textContent = [work.work_id, work.medium, state.seriesById.get(work.series_id).title].filter(Boolean).join(" · ");
  details.append(title, meta);
  row.append(frame, details);
  return row;
}

/** Search saved Works and retain checkbox selections across queries. */
export function openAddGalleryWorksModal(state, { galleryId, galleryTitle, restoreFocus, save }) {
  const works = [...state.workSearchById.values()]
    .sort((a, b) => titleOrder.compare(a.title, b.title));
  const selected = new Set();
  let saving = false;
  let syncControls;
  return openConfirmModal({
    root: state.root,
    restoreFocus,
    title: "Add works",
    meta: `Gallery: ${galleryTitle} (${galleryId})`,
    bodyHtml: `
      <div class="catalogueGalleryWorks">
        <input class="studioUi__input" type="search" id="catalogueGalleryWorksSearch" aria-label="Find Works by title, Work ID or Medium" placeholder="find by title, work id or medium" autocomplete="off">
        <p class="studioForm__meta" data-role="gallery-works-summary" aria-live="polite"></p>
        <div class="catalogueGalleryWorks__results" data-role="gallery-works-results" role="group" aria-label="Work search results" hidden></div>
      </div>`,
    focusSelector: "#catalogueGalleryWorksSearch",
    primaryLabel: "Add selected",
    primaryDisabled: true,
    includeStatus: true,
    submitOnEnter: false,
    canCancel: () => !saving,
    onOpen(api) {
      const search = api.host.querySelector("#catalogueGalleryWorksSearch");
      const { clearButton } = mountSearchField(search);
      const summary = api.host.querySelector('[data-role="gallery-works-summary"]');
      const results = api.host.querySelector('[data-role="gallery-works-results"]');
      const primary = api.host.querySelector('[data-role="modal-primary"]');
      const cancel = api.host.querySelector('button[data-role="modal-cancel"]');
      api.host.querySelector('[data-role="modal-status"]').setAttribute("aria-live", "polite");
      let query = "";
      let matchCount = 0;
      syncControls = () => {
        search.disabled = clearButton.disabled = results.inert = cancel.disabled = saving;
        primary.disabled = saving || !selected.size;
        api.dialog.setAttribute("aria-busy", String(saving));
      };
      function updateSummary() {
        const status = !works.length ? "No saved Works."
          : query ? matchCount ? `${matchCount} matching` : "No matching Works."
            : selected.size ? "Selected Works" : "Search for Works to add.";
        summary.textContent = selected.size ? `${status} · ${selected.size} selected` : status;
      }
      search.addEventListener("input", () => {
        query = search.value.trim().toLowerCase();
        const matches = works.filter(work => query
          ? work.work_id.includes(query) || work.title.toLowerCase().includes(query)
            || work.medium?.toLowerCase().includes(query)
          : selected.has(work.work_id));
        matchCount = matches.length;
        results.replaceChildren(...matches.map(work => buildResultRow(state, work, galleryId, selected.has(work.work_id))));
        results.hidden = !matchCount;
        results.scrollTop = 0;
        updateSummary();
      });
      results.addEventListener("change", ({ target: checkbox }) => {
        if (checkbox.checked) selected.add(checkbox.value);
        else {
          selected.delete(checkbox.value);
          if (!query) {
            checkbox.closest("label").remove();
            results.hidden = !selected.size;
            search.focus();
          }
        }
        updateSummary();
        syncControls();
      });
      updateSummary();
      search.focus();
    },
    async onSubmit(api) {
      if (saving || !selected.size) return false;
      saving = true;
      syncControls();
      api.setStatus("", "Adding selected Works…");
      try {
        return await save(galleryId, [...selected]);
      } catch (error) {
        api.setStatus("error", `Could not confirm the Gallery save. ${error.message}`);
        return false;
      } finally {
        saving = false;
        syncControls();
      }
    }
  });
}
