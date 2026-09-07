import {
  openSemanticTextTokenModal
} from "./catalogue-token-modal.js";
import {
  buildConceptToken,
  parseConceptToken,
  selectedTextForConceptTitle
} from "./concept-token-parser.js";
import {
  collectConceptTargetMatches,
  findConceptTargetByIdentity,
  loadConceptTargetSupport
} from "./concept-token-targets.js";

export const CONCEPT_TOKEN_MODAL_ID = "concept-token-add-modal";

function conceptTargetMeta(target) {
  return target.meta.slice();
}

var CONCEPT_TOKEN_MODAL_SETTINGS = {
  buildToken: buildConceptToken,
  collectMatches: collectConceptTargetMatches,
  familyLabel: "Concept",
  findByIdentity: findConceptTargetByIdentity,
  loadingMessage: "Loading Concepts…",
  loadSupport: loadConceptTargetSupport,
  modalId: CONCEPT_TOKEN_MODAL_ID,
  modalTitle: "Add concept token",
  noMatchesMessage: "No matching Concepts.",
  parseToken: parseConceptToken,
  resultsId: "docsViewerConceptTokenResults",
  resultsLabel: "Concept targets",
  searchInputId: "docsViewerConceptTokenSearch",
  searchLabel: "Search Concepts",
  selectedText: selectedTextForConceptTitle,
  targetMeta: conceptTargetMeta,
  titleInputId: "docsViewerConceptTokenTitle",
  titleOnSelect: function (target, currentTitle) {
    return String(currentTitle || "").trim() || target.title;
  },
  unavailableMessage: "Concept targets are unavailable."
};

export function openConceptTokenModal(options = {}) {
  return openSemanticTextTokenModal(CONCEPT_TOKEN_MODAL_SETTINGS, options);
}
