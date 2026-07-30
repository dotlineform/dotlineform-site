import {
  reviewReturnedDocumentPackage
} from "../packages/document-package-client.js";
import {
  packageText
} from "../packages/document-package-view.js";

export function docsImportReviewHandoffResult(payload) {
  if (!payload || payload.ok !== true) {
    throw new Error("Docs Review package was not prepared.");
  }
  const packageId = packageText(payload && payload.review_package_id);
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(packageId)) {
    throw new Error("Docs Review package identity is invalid.");
  }
  const reviewUrl = `/docs-review/?package=${encodeURIComponent(packageId)}`;
  if (packageText(payload && payload.review_url) !== reviewUrl) {
    throw new Error("Docs Review package URL is invalid.");
  }
  const existing = payload && payload.review_existing === true;
  return {
    packageId,
    reviewUrl,
    existing,
    linkLabel: existing ? "Open existing review" : "Open in Docs Review"
  };
}

function closeReviewWindow(reviewWindow) {
  if (!reviewWindow || typeof reviewWindow.close !== "function") return;
  try {
    reviewWindow.close();
  } catch (_error) {
    // A failed preparation must not leave an owned blank tab behind.
  }
}

export async function openDocsImportCandidateInReview(options = {}) {
  const scope = packageText(options.scope).toLowerCase();
  const stagedFilename = packageText(options.stagedFilename);
  if (!scope || !stagedFilename) {
    throw new Error("An exact returned-package identity is required for Docs Review.");
  }
  const review = typeof options.review === "function"
    ? options.review
    : reviewReturnedDocumentPackage;
  const openWindow = typeof options.openWindow === "function"
    ? options.openWindow
    : (url, target) => window.open(url, target);
  const reviewWindow = openWindow("about:blank", "_blank");
  if (!reviewWindow) {
    throw new Error("The Docs Review tab was blocked. Allow popups and retry.");
  }
  try {
    reviewWindow.opener = null;
    const payload = await review({
      scope,
      staged_filename: stagedFilename,
      dry_run: false
    });
    const result = docsImportReviewHandoffResult(payload);
    if (reviewWindow.closed) {
      throw new Error("The Docs Review tab was closed before preparation completed.");
    }
    if (
      reviewWindow.location
      && typeof reviewWindow.location.replace === "function"
    ) {
      reviewWindow.location.replace(result.reviewUrl);
    } else {
      reviewWindow.location = result.reviewUrl;
    }
    return {
      ...result,
      payload
    };
  } catch (error) {
    closeReviewWindow(reviewWindow);
    throw error;
  }
}
