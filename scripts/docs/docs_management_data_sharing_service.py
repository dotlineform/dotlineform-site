"""Docs management Data Sharing service dependencies."""

from __future__ import annotations

from analytics import tags_data_sharing_adapter
import documents_data_sharing_adapter
import docs_write_rebuild as write_rebuild
from docs_management_context import log_event, make_backup_bundle


def documents_data_sharing_dependencies() -> documents_data_sharing_adapter.DocumentsDataSharingDependencies:
    return documents_data_sharing_adapter.DocumentsDataSharingDependencies(
        log_event=log_event,
        make_backup_bundle=make_backup_bundle,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def tags_data_sharing_dependencies() -> tags_data_sharing_adapter.TagsDataSharingDependencies:
    return tags_data_sharing_adapter.TagsDataSharingDependencies(
        log_event=log_event,
    )


DATA_SHARING_HANDLERS = {
    "documents": documents_data_sharing_adapter.handlers_for(documents_data_sharing_dependencies),
    "analytics.tags": tags_data_sharing_adapter.handlers_for(tags_data_sharing_dependencies),
}
