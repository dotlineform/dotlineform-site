const SUBJECT_ICON_MARKUP = Object.freeze({
  detail: [
    '<svg class="docsViewerReport__projectSubjectIcon" data-project-subject-icon="detail" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '<rect x="4" y="5" width="16" height="14" rx="1"></rect>',
    '<path d="M7 15L11 11L14 14L17 10"></path>',
    "</svg>"
  ].join(""),
  work: [
    '<svg class="docsViewerReport__projectSubjectIcon" data-project-subject-icon="work" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '<rect x="4" y="10.75" width="2.5" height="2.5" rx="1"></rect>',
    '<path d="M10 12H20"></path>',
    "</svg>"
  ].join(""),
  series: [
    '<svg class="docsViewerReport__projectSubjectIcon" data-project-subject-icon="series" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '<rect x="4" y="5" width="2.5" height="2.5" rx="1"></rect>',
    '<rect x="4" y="10.75" width="2.5" height="2.5" rx="1"></rect>',
    '<rect x="4" y="16.5" width="2.5" height="2.5" rx="1"></rect>',
    '<path d="M10 6.25H20"></path>',
    '<path d="M10 12H20"></path>',
    '<path d="M10 17.75H20"></path>',
    "</svg>"
  ].join("")
});

export function appendProjectSubjectIcon(parent, kind) {
  const subjectKind = String(kind == null ? "" : kind).trim();
  if (!parent || !["folder", "work", "series", "detail"].includes(subjectKind)) return null;
  const cue = parent.ownerDocument.createElement("span");
  cue.className = "docsViewerReport__projectSubjectCue";
  cue.dataset.projectSubjectCue = subjectKind;
  cue.setAttribute("aria-hidden", "true");
  if (SUBJECT_ICON_MARKUP[subjectKind]) cue.innerHTML = SUBJECT_ICON_MARKUP[subjectKind];
  else cue.textContent = "📁";
  parent.appendChild(cue);
  return cue;
}
