"""Tags Data Sharing adapter package."""

from data_sharing.adapters.tags.adapter import (  # noqa: F401
    TagsDataSharingDependencies,
    apply_returned_changes,
    handlers_for,
    list_returned_packages,
    prepare_package,
    review_returned_package,
)
