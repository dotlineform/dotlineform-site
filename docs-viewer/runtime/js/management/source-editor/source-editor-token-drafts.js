import {
  normalizeCatalogueDetailId,
  serializeCatalogueImageToken,
  serializeCatalogueMediaToken
} from "./catalogue-token-parser.js";
import { readCatalogueTokenPresentation } from "./catalogue-media-support.js";

function valuesForToken(token) {
  return {
    text: token.presentation === "image" ? token.alt : token.title,
    detailId: token.detailId,
    addCaption: Boolean(token.caption),
    caption: token.caption || "",
    summary: token.summary || "",
    placement: token.placement || "full",
    fillWidth: typeof token.fillWidth === "boolean" ? token.fillWidth : true
  };
}

function sameOccurrenceTarget(left, right) {
  return ["family", "presentation", "targetType", "targetId"].every(function (key) {
    return left[key] === right[key];
  });
}

function dirty(draft) {
  return JSON.stringify(draft.values) !== JSON.stringify(draft.initialValues);
}

/** Session-owned occurrence inputs survive panel unmounts, including invalid values. */
export function createSourceEditorTokenDrafts() {
  var drafts = [];
  return {
    get: function (token, capture, registry) {
      var draft = drafts.find(function (item) {
        return item.capture.start === capture.start && sameOccurrenceTarget(item.token, token);
      });
      if (!draft) {
        draft = { token: token, capture: capture, registry: registry, values: valuesForToken(token) };
        draft.initialValues = Object.assign({}, draft.values);
        drafts.push(draft);
      } else if (draft.capture.text !== capture.text) {
        // Reselecting the same occurrence establishes its new guarded source range.
        if (!dirty(draft)) {
          draft.values = valuesForToken(token);
          draft.initialValues = Object.assign({}, draft.values);
        }
        draft.token = token;
      }
      draft.capture = capture;
      return draft;
    },
    remove: function (draft) {
      drafts = drafts.filter(function (item) { return item !== draft; });
    },
    isDirty: function () { return drafts.some(dirty); },
    clear: function () { drafts = []; },
    reconcile: function (previous, current, revision) {
      var start = 0;
      while (start < previous.length && start < current.length && previous[start] === current[start]) start += 1;
      var beforeEnd = previous.length;
      var afterEnd = current.length;
      while (beforeEnd > start && afterEnd > start && previous[beforeEnd - 1] === current[afterEnd - 1]) {
        beforeEnd -= 1;
        afterEnd -= 1;
      }
      var delta = afterEnd - beforeEnd;
      // An explicit source replacement of a whole occurrence also removes its field draft.
      drafts = drafts.filter(function (draft) {
        return start > draft.capture.start || beforeEnd < draft.capture.end;
      });
      drafts.forEach(function (draft) {
        var capture = draft.capture;
        if (capture.start >= beforeEnd) {
          capture.start += delta;
          capture.end += delta;
        }
        // Overlapping edits stay pending and fail the ordinary range check until reselected.
        if (current.slice(capture.start, capture.end) === capture.text) capture.revision = revision;
      });
    },
    prepare: async function (snapshot, adapter) {
      var replacements = [];
      for (var draft of drafts.filter(dirty)) {
        var token = draft.token;
        var values = draft.values;
        var capture = draft.capture;
        if (capture.revision !== snapshot.revision || snapshot.value.slice(capture.start, capture.end) !== capture.text) {
          throw new Error("Markdown changed at a token with pending edits. Select that occurrence again before saving.");
        }
        var detailId = normalizeCatalogueDetailId(values.detailId);
        if (detailId === null) throw new Error("Enter a positive Work Detail ID using digits only, or leave it blank.");
        var fields = {
          registry: draft.registry, targetType: token.targetType,
          targetId: token.targetId, detailId: detailId
        };
        var serialized;
        if (token.presentation === "image") {
          fields.alt = values.text;
          if (values.addCaption) Object.assign(fields, {
            caption: values.caption, summary: values.summary,
            placement: values.placement, fillWidth: values.fillWidth
          });
          serialized = serializeCatalogueImageToken(fields);
        } else {
          fields.title = values.text;
          serialized = serializeCatalogueMediaToken(fields);
        }
        if (!serialized) throw new Error(token.presentation === "image"
          ? "Enter alt text and complete the enabled caption presentation."
          : "Enter single-line link text.");
        await readCatalogueTokenPresentation(adapter, token, detailId);
        replacements.push({ capture: capture, value: serialized });
      }
      var body = snapshot.value;
      replacements.sort(function (left, right) { return right.capture.start - left.capture.start; });
      replacements.forEach(function (replacement) {
        body = body.slice(0, replacement.capture.start) + replacement.value + body.slice(replacement.capture.end);
      });
      return body;
    }
  };
}
