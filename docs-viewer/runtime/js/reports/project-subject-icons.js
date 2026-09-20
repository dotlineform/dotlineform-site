const SUBJECT_ICON_CLASSES = Object.freeze({
  folder: "docsViewer__icon--folder",
  work: "docsViewer__icon--dlf-work",
  series: "docsViewer__icon--dlf-series",
  detail: "docsViewer__icon--dlf-detail"
});

/** Append a decorative 16px saved Subject icon; the parent owns its meaning. */
export function appendProjectSubjectIcon(parent, kind) {
  const subjectKind = String(kind == null ? "" : kind).trim();
  if (!parent || !Object.hasOwn(SUBJECT_ICON_CLASSES, subjectKind)) return null;
  const cue = parent.ownerDocument.createElement("span");
  cue.className = "docsViewer__listIcon docsViewerReport__projectSubjectCue " + SUBJECT_ICON_CLASSES[subjectKind];
  cue.dataset.projectSubjectCue = subjectKind;
  cue.dataset.projectSubjectIcon = subjectKind;
  cue.setAttribute("aria-hidden", "true");
  parent.appendChild(cue);
  return cue;
}
