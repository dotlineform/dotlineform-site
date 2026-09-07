import { normalizeManagedDocumentCollectionTarget, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
import { documentIdentityInfoField, renderDocumentIdentityControl } from "./docs-viewer-management-document-identity.js";

/** Provide document-owned Moment identity without Catalogue/Subject dependencies. */
export function createDocsViewerManagementSubscopeMoments(options = {}) {
  var collection = normalizeManagedDocumentCollectionTarget(options.collection);
  if (options.descriptor.id !== "moments" || options.descriptor.capabilities.identityKind !== "moment"
    || !collection.sub_scope || collection.stage !== "working") {
    throw new Error("Moment identity requires its configured Working collection.");
  }
  return {
    id: "moments",
    projectDetailInfo: function (context) {
      var target = normalizeManagedDocumentTarget(context.target);
      if (target.scope !== collection.scope || target.stage !== collection.stage
        || target.sub_scope !== collection.sub_scope || target.doc_id !== context.document.doc_id) {
        throw new Error("Moment identity target did not match its collection.");
      }
      return { actions: {}, fields: [documentIdentityInfoField(context.document, "moment")] };
    },
    renderDetailToolbar: function (context) {
      renderDocumentIdentityControl(context, options, "moment");
    }
  };
}
