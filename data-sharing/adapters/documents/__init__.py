"""Documents Data Sharing adapter package."""

from adapters.documents.adapter import (  # noqa: F401
    DocumentsDataSharingDependencies,
    apply_returned_changes,
    handlers_for,
    list_returned_packages,
    prepare_package,
    review_returned_package,
    selectable_records,
)
