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
  return target.meta.slice();
}

var TAG_TOKEN_MODAL_SETTINGS = {
  buildToken: buildTagToken,
  collectMatches: collectTagTargetMatches,
  familyLabel: "Concept",
  findByIdentity: findTagTargetByIdentity,
  loadingMessage: "Loading Concepts…",
  loadSupport: loadTagTargetSupport,
  modalId: TAG_TOKEN_MODAL_ID,
  modalTitle: "Add concept token",
  noMatchesMessage: "No matching Concepts.",
  parseToken: parseTagToken,
  resultsId: "docsViewerTagTokenResults",
  resultsLabel: "Concept targets",
  searchInputId: "docsViewerTagTokenSearch",
  searchLabel: "Search Concepts",
  selectedText: selectedTextForTagTitle,
  targetMeta: tagTargetMeta,
  titleInputId: "docsViewerTagTokenTitle",
  titleOnSelect: function (target, currentTitle) {
    return String(currentTitle || "").trim() || target.title;
  },
  unavailableMessage: "Concept targets are unavailable."
};

export function openTagTokenModal(options = {}) {
  return openSemanticTextTokenModal(TAG_TOKEN_MODAL_SETTINGS, options);
}
