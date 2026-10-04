/** Hold native files only in the current Work draft; Save owns every permanent write. */
import { normalizeWorkId } from "./catalogue-work-fields.js";

function safeFilename(filename) {
  if (!filename || filename !== filename.trim() || /[/\\]/.test(filename)
    || [...filename].some(character => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127)
    || filename === "." || filename === ".." || new TextEncoder().encode(filename).length > 255) {
    throw new Error("Choose a file with a safe basename of at most 255 UTF-8 bytes.");
  }
  return filename;
}

function workAttachmentId(state) {
  const workId = state.mode === "new" ? normalizeWorkId(state.draft.work_id) : state.currentWorkId;
  if (!/^[0-9]{5}$/.test(workId)) throw new Error("Enter a five-digit Work ID before adding a file.");
  return workId;
}

function attachmentFilename(state, file) {
  return safeFilename(`${workAttachmentId(state)}-${safeFilename(file.name)}`);
}

/** Open synchronously from the Add file click so Safari retains native user activation. */
export function openNativeWorkAttachment(state, options) {
  if (state.mode === "bulk" || !state.serverAvailable || state.isSaving || state.isBuilding || state.isDeleting) return;
  if (!state.attachmentInput) {
    const input = state.root.ownerDocument.createElement("input");
    input.type = "file";
    input.hidden = true;
    input.multiple = false;
    input.addEventListener("change", () => {
      const file = input.files[0];
      if (!file) return;
      try {
        const filename = attachmentFilename(state, file);
        if (!file.size) throw new Error("Choose a nonempty attachment file.");
        const next = new Map(state.pendingAttachments);
        next.set(filename, file);
        if ([...next.values()].reduce((total, item) => total + item.size, 0) > state.attachmentLimits.total_bytes) {
          throw new Error("Combined attachments exceed the 64 MiB Save limit.");
        }
        const entries = state.draft.downloads.map(entry => ({ ...entry }));
        if (!entries.some(entry => entry.filename === filename)) entries.push({ filename, label: file.name });
        state.draft.downloads = entries;
        state.pendingAttachments = next;
        options.onChange();
      } catch (error) {
        options.onError(error);
      } finally {
        input.value = "";
      }
    });
    state.root.appendChild(input);
    state.attachmentInput = input;
  }
  workAttachmentId(state);
  state.attachmentInput.value = "";
  state.attachmentInput.click();
}

/** Follow an edited New Work ID without losing labels or changing existing managed files. */
export function syncPendingAttachmentNames(state) {
  if (state.mode !== "new" || !/^[0-9]{5}$/.test(normalizeWorkId(state.draft.work_id))) return;
  const next = new Map();
  for (const [previous, file] of state.pendingAttachments) {
    const filename = attachmentFilename(state, file);
    const entry = state.draft.downloads.find(item => item.filename === previous);
    if (entry) entry.filename = filename;
    next.set(filename, file);
  }
  state.pendingAttachments = next;
}

/** Discard transient media operation state when the draft is released or Save completes. */
export function clearWorkMediaIntent(state) {
  state.pendingAttachments = new Map();
  state.regenerateImage = false;
  if (state.attachmentInput) state.attachmentInput.value = "";
}

/** Build the operation's opaque parts; filenames travel in UTF-8 JSON, not MIME headers. */
export function buildWorkSaveForm(payload, attachments, limits) {
  const files = [...attachments.values()];
  if (files.reduce((total, file) => total + file.size, 0) > limits.total_bytes) {
    throw new Error("Combined attachments exceed the 64 MiB Save limit.");
  }
  const metadata = JSON.stringify({ ...payload, attachment_names: files.map(file => file.name) });
  if (new TextEncoder().encode(metadata).length > limits.metadata_bytes) {
    throw new Error("Work Save metadata exceeds the 1 MiB limit.");
  }
  const form = new FormData();
  form.append("payload", metadata);
  files.forEach((file, index) => form.append(
    `attachment_${index}`, file.slice(0, file.size, "application/octet-stream"), file.name
  ));
  return form;
}
