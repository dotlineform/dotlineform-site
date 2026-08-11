import {
  openSemanticTextTokenModal
} from "./catalogue-token-modal.js";
import {
  buildTagToken,
  parseTagToken,
  selectedTextForTagTitle
} from "./tag-token-parser.js";
import {
  collectTagTargetMatches,
  findTagTargetByIdentity,
  loadTagTargetSupport
} from "./tag-token-targets.js";

export const TAG_TOKEN_MODAL_ID = "tag-token-add-modal";

function tagTargetMeta(target) {
  var aliases = target.aliases.length
    ? ["Aliases: " + target.aliases.join(", ")]
    : [];
  var context = [];
  if (target.meta[0]) context.push("Group: " + target.meta[0]);
  if (target.meta[1]) context.push("Document: " + target.meta[1]);
  return aliases.concat(context);
}

var TAG_TOKEN_MODAL_SETTINGS = {
  buildToken: buildTagToken,
  collectMatches: collectTagTargetMatches,
  familyLabel: "Tag",
  findByIdentity: findTagTargetByIdentity,
  loadingMessage: "Loading Tags…",
  loadSupport: loadTagTargetSupport,
  modalId: TAG_TOKEN_MODAL_ID,
  modalTitle: "Add tag token",
  noMatchesMessage: "No matching Tags.",
  parseToken: parseTagToken,
  resultsId: "docsViewerTagTokenResults",
  resultsLabel: "Tag targets",
  searchInputId: "docsViewerTagTokenSearch",
  searchLabel: "Search Tags and aliases",
  selectedText: selectedTextForTagTitle,
  targetMeta: tagTargetMeta,
  titleInputId: "docsViewerTagTokenTitle",
  titleOnSelect: function (target, currentTitle) {
    return String(currentTitle || "").trim() || target.title;
  },
  unavailableMessage: "Tag targets are unavailable."
};

export function openTagTokenModal(options = {}) {
  return openSemanticTextTokenModal(TAG_TOKEN_MODAL_SETTINGS, options);
}
