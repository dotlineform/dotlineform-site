# UI Text Usage Map

Generated: 2026-06-11 11:18:36 local time

Scope: `studio/app/frontend/config/ui-text/*.json` against route-scoped files under `studio/app/frontend/js/**/*.js`.

Interpretation:
- `exact`: the key or full dotted key appears as a string literal in a route-scoped frontend JS file.
- `dynamic-family`: no exact literal was found, but the key matches a known dynamic lookup family in active code.
- `not-detected`: no source reference was detected by this static scan. Treat as a cleanup candidate for human review, not proof of dead code.

Route-scoped source sets:
- `bulk_add_work`: `bulk-add-work-shell.js`, `bulk-add-work-workflow.js`, `bulk-add-work.js`, `studio-save-utils.js`
- `catalogue_field_registry_review`: `catalogue-field-registry-review.js`
- `catalogue_moment_editor`: `catalogue-editor-action-workflow.js`, `catalogue-editor-modal-formatters.js`, `catalogue-editor-readiness.js`, `catalogue-editor-route-boot.js`, `catalogue-moment-actions.js`, `catalogue-moment-editor-events.js`, `catalogue-moment-editor-state.js`, `catalogue-moment-editor.js`, `catalogue-moment-fields.js`, `catalogue-moment-form.js`, `catalogue-moment-import.js`, `catalogue-moment-sections.js`, `catalogue-moment-selection.js`, `catalogue-moment-shell.js`, `studio-save-utils.js`
- `catalogue_series_editor`: `catalogue-editor-action-workflow.js`, `catalogue-editor-modal-formatters.js`, `catalogue-editor-readiness.js`, `catalogue-editor-route-boot.js`, `catalogue-series-actions.js`, `catalogue-series-editor-events.js`, `catalogue-series-editor-state.js`, `catalogue-series-editor.js`, `catalogue-series-fields.js`, `catalogue-series-form.js`, `catalogue-series-membership.js`, `catalogue-series-sections.js`, `catalogue-series-selection.js`, `catalogue-series-shell.js`, `studio-save-utils.js`
- `catalogue_status`: `catalogue-status-shell.js`, `catalogue-status.js`
- `catalogue_work_detail_editor`: `catalogue-editor-action-workflow.js`, `catalogue-editor-modal-formatters.js`, `catalogue-editor-readiness.js`, `catalogue-editor-route-boot.js`, `catalogue-work-detail-actions.js`, `catalogue-work-detail-editor-events.js`, `catalogue-work-detail-editor-state.js`, `catalogue-work-detail-editor.js`, `catalogue-work-detail-fields.js`, `catalogue-work-detail-form.js`, `catalogue-work-detail-sections.js`, `catalogue-work-detail-selection.js`, `catalogue-work-detail-shell.js`, `studio-save-utils.js`
- `catalogue_work_editor`: `catalogue-editor-action-workflow.js`, `catalogue-editor-embedded-items.js`, `catalogue-editor-modal-formatters.js`, `catalogue-editor-readiness.js`, `catalogue-editor-route-boot.js`, `catalogue-work-action-records.js`, `catalogue-work-actions.js`, `catalogue-work-editor-events.js`, `catalogue-work-editor-modals.js`, `catalogue-work-editor-state.js`, `catalogue-work-editor.js`, `catalogue-work-fields.js`, `catalogue-work-form.js`, `catalogue-work-route-state.js`, `catalogue-work-sections.js`, `catalogue-work-selection.js`, `catalogue-work-shell.js`, `studio-save-utils.js`
- `project_state`: `project-state-shell.js`, `project-state.js`, `studio-save-utils.js`
- `studio_works`: `studio-works-shell.js`, `studio-works.js`

## Summary

| group | keys | exact | dynamic-family | not-detected |
| --- | ---: | ---: | ---: | ---: |
| `bulk_add_work` | 38 | 38 | 0 | 0 |
| `catalogue_field_registry_review` | 10 | 10 | 0 | 0 |
| `catalogue_moment_editor` | 142 | 131 | 0 | 11 |
| `catalogue_series_editor` | 126 | 124 | 1 | 1 |
| `catalogue_status` | 5 | 5 | 0 | 0 |
| `catalogue_work_detail_editor` | 120 | 105 | 14 | 1 |
| `catalogue_work_editor` | 180 | 174 | 4 | 2 |
| `project_state` | 27 | 27 | 0 | 0 |
| `studio_works` | 1 | 1 | 0 | 0 |

## Not Detected

### `catalogue_moment_editor`

| key | value |
| --- | --- |
| `import_metadata_field_title` | title |
| `import_metadata_field_status` | status |
| `import_metadata_field_date` | date |
| `import_metadata_field_date_display` | date display |
| `import_metadata_field_published_date` | published date |
| `import_metadata_field_source_image_file` | source image file |
| `import_metadata_field_image_alt` | image alt |
| `build_status_running` | Updating site... |
| `build_status_success` | Site update completed. |
| `build_status_failed` | Site update failed. |
| `build_result_success` | Public moment updated at {completed_at}. Studio Activity updated. |

### `catalogue_series_editor`

| key | value |
| --- | --- |
| `save_mode_unavailable` | Unavailable |

### `catalogue_work_detail_editor`

| key | value |
| --- | --- |
| `save_mode_unavailable` | Unavailable |

### `catalogue_work_editor`

| key | value |
| --- | --- |
| `save_mode_unavailable` | Unavailable |
| `delete_status_deleting` | Deleting source record... |

## Full Map

### `bulk_add_work`

| key | status | refs | value |
| --- | --- | --- | --- |
| `apply_button` | exact | `studio/app/frontend/js/bulk-add-work.js:223` | Import |
| `apply_clear_workbook` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:118` | Clear the imported rows from {workbook} after you confirm the result. |
| `apply_requires_preview` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:45` | Run preview for the current mode before apply. |
| `apply_result_success` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:111` | Imported {imported} record(s); {duplicates} duplicate record(s) already existed. |
| `apply_status_failed` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:129` | Workbook import failed. |
| `apply_status_running` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:97` | Applying workbook import… |
| `apply_status_success` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:107` | Workbook import completed. |
| `context_hint` | exact | `studio/app/frontend/js/bulk-add-work.js:228` | Bulk import is one-way from {workbook} into canonical JSON. Use works mode for new work... |
| `details_heading` | exact | `studio/app/frontend/js/bulk-add-work.js:219` | preview details |
| `empty_state` | exact | `studio/app/frontend/js/bulk-add-work.js:221` |  |
| `import_heading` | exact | `studio/app/frontend/js/bulk-add-work.js:213` | import |
| `loading` | exact | `studio/app/frontend/js/bulk-add-work.js:220` | loading bulk add work… |
| `mode_label` | exact | `studio/app/frontend/js/bulk-add-work.js:214` | mode |
| `mode_option_work_details` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:206`<br>`studio/app/frontend/js/bulk-add-work.js:216` | work details |
| `mode_option_works` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:207`<br>`studio/app/frontend/js/bulk-add-work.js:215` | works |
| `page_heading` | exact | `studio/app/frontend/js/bulk-add-work.js:212` | bulk add work |
| `preview_blocked_warning` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:66` | Blocked rows must be fixed in {workbook} before apply. |
| `preview_button` | exact | `studio/app/frontend/js/bulk-add-work.js:222` | Preview |
| `preview_empty` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:162` | Run preview to inspect workbook rows before import. |
| `preview_status_failed` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:88` | Workbook import preview failed. |
| `preview_status_running` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:54` | Running workbook import preview… |
| `preview_status_success` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:74` | Preview ready: {importable} importable, {duplicates} duplicates, {blocked} blocked. |
| `save_mode_local_server` | exact | `studio/app/frontend/js/studio-save-utils.js:7` | Local server |
| `save_mode_offline` | exact | `studio/app/frontend/js/studio-save-utils.js:8` | Unavailable |
| `save_mode_template` | exact | `studio/app/frontend/js/studio-save-utils.js:9` | Save mode: {mode} |
| `save_mode_unavailable_hint` | exact | `studio/app/frontend/js/bulk-add-work.js:233` | Local catalogue server unavailable. Import is disabled. |
| `section_blocked` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:191` | blocked rows |
| `section_duplicates` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:182` | duplicates already in source |
| `section_importable` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:173` | importable |
| `section_none` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:175`<br>`studio/app/frontend/js/bulk-add-work-workflow.js:184`<br>`studio/app/frontend/js/bulk-add-work-workflow.js:198` | none |
| `summary_blocked` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:150` | blocked |
| `summary_candidate_rows` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:147` | candidate rows |
| `summary_duplicates` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:149` | duplicates |
| `summary_heading` | exact | `studio/app/frontend/js/bulk-add-work.js:218` | preview summary |
| `summary_importable` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:148` | importable |
| `summary_mode` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:145` | mode |
| `summary_workbook` | exact | `studio/app/frontend/js/bulk-add-work-workflow.js:146` | workbook |
| `workbook_label` | exact | `studio/app/frontend/js/bulk-add-work.js:217` | workbook |

### `catalogue_field_registry_review`

| key | status | refs | value |
| --- | --- | --- | --- |
| `context_hint` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:122` | Read-only view of the active field-to-artifact registry used by catalogue build planning. |
| `empty_state` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:124` |  |
| `loading` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:123` | loading catalogue field registry... |
| `meta_all` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:62` | Showing full registry. |
| `meta_exact` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:67` | Showing {count} exact rule match(es) for field `{field}`. |
| `meta_partial` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:67` | Showing {count} partial rule match(es) for field search `{field}`. |
| `output_label` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:126` | registry extract |
| `page_heading` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:121` | catalogue field registry |
| `search_placeholder` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:125` | field name |
| `status_loaded` | exact | `studio/app/frontend/js/catalogue-field-registry-review.js:132` | Registry loaded. |

### `catalogue_moment_editor`

| key | status | refs | value |
| --- | --- | --- | --- |
| `build_preview_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:199` | Public update preview unavailable. |
| `build_preview_search_no` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` | no |
| `build_preview_search_yes` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` | yes |
| `build_preview_template` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64`<br>`studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` | Public update preview: moment {moment_ids}; catalogue search {search_rebuild}. |
| `build_preview_unpublished` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:105` | Public update unavailable while the moment is not published. |
| `build_result_success` | not-detected |  | Public moment updated at {completed_at}. Studio Activity updated. |
| `build_status_failed` | not-detected |  | Site update failed. |
| `build_status_running` | not-detected |  | Updating site... |
| `build_status_success` | not-detected |  | Site update completed. |
| `confirm_cancel_button` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:312`<br>`studio/app/frontend/js/catalogue-moment-actions.js:429`<br>`studio/app/frontend/js/catalogue-moment-actions.js:499` | Cancel |
| `context_loaded` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:353` | Editing source metadata for moment {moment_id}. |
| `delete_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:453` | Delete |
| `delete_confirm_button` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:498` | Delete |
| `delete_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:148` | Delete this moment and its generated files, media, and search record? |
| `delete_confirm_title` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:496` | Confirm delete |
| `delete_status_blocked` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:481` | Delete is blocked. |
| `delete_status_cancelled` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:503` | Delete cancelled. |
| `delete_status_conflict` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:515` | Source record changed since this page loaded. Reload before deleting again. |
| `delete_status_deleting` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:510` | Deleting moment, generated files, media, and search record... |
| `delete_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:516` | Moment delete failed. |
| `delete_status_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:468` | Preparing delete preview... |
| `dirty_warning` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:400`<br>`studio/app/frontend/js/catalogue-moment-editor.js:288`<br>`studio/app/frontend/js/catalogue-moment-sections.js:60` | Unsaved source changes. |
| `field_invalid_date` | exact | `studio/app/frontend/js/catalogue-moment-fields.js:100` | Use YYYY-MM-DD or leave blank. |
| `field_invalid_status` | exact | `studio/app/frontend/js/catalogue-moment-fields.js:105` | Use draft or published. |
| `field_required_date` | exact | `studio/app/frontend/js/catalogue-moment-fields.js:95` | Enter a date. |
| `field_required_published_date` | exact | `studio/app/frontend/js/catalogue-moment-fields.js:108` | Published moments require a published date. |
| `field_required_title` | exact | `studio/app/frontend/js/catalogue-moment-fields.js:92` | Enter a title. |
| `import_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:457` | Import |
| `import_context_hint` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:233` | Import a staged moment markdown file as draft source, then review and publish it from t... |
| `import_empty_state` | exact | `studio/app/frontend/js/catalogue-moment-import.js:113`<br>`studio/app/frontend/js/catalogue-moment-import.js:167` | Preview a source file to inspect the resolved moment metadata. |
| `import_file_description` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:458` | filename only; the source file is resolved from var/docs/catalogue/import-staging/moments/ |
| `import_file_label` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:454` | moment file |
| `import_file_placeholder` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:455` | keys.md |
| `import_file_required` | exact | `studio/app/frontend/js/catalogue-moment-import.js:294` | Enter a moment markdown filename. |
| `import_image_guidance` | exact | `studio/app/frontend/js/catalogue-moment-import.js:243` | Missing images are acceptable in this phase. The public moment page handles missing her... |
| `import_metadata_field_date` | not-detected |  | date |
| `import_metadata_field_date_display` | not-detected |  | date display |
| `import_metadata_field_image_alt` | not-detected |  | image alt |
| `import_metadata_field_published_date` | not-detected |  | published date |
| `import_metadata_field_source_image_file` | not-detected |  | source image file |
| `import_metadata_field_status` | not-detected |  | status |
| `import_metadata_field_title` | not-detected |  | title |
| `import_mode_loaded` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:234` | Preview the staged moment file below. |
| `import_preview_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:456` | Preview |
| `import_preview_errors_intro` | exact | `studio/app/frontend/js/catalogue-moment-import.js:183` | Source file issues: |
| `import_preview_field_date` | exact | `studio/app/frontend/js/catalogue-moment-import.js:121` | date |
| `import_preview_field_date_display` | exact | `studio/app/frontend/js/catalogue-moment-import.js:122` | date display |
| `import_preview_field_generated_status` | exact | `studio/app/frontend/js/catalogue-moment-import.js:132` | generated status |
| `import_preview_field_image_file` | exact | `studio/app/frontend/js/catalogue-moment-import.js:124` | image file |
| `import_preview_field_image_status` | exact | `studio/app/frontend/js/catalogue-moment-import.js:126` | image status |
| `import_preview_field_moment_id` | exact | `studio/app/frontend/js/catalogue-moment-import.js:118` | moment id |
| `import_preview_field_published_date` | exact | `studio/app/frontend/js/catalogue-moment-import.js:123` | published date |
| `import_preview_field_source_path` | exact | `studio/app/frontend/js/catalogue-moment-import.js:136` | source path |
| `import_preview_field_status` | exact | `studio/app/frontend/js/catalogue-moment-import.js:120` | status |
| `import_preview_field_title` | exact | `studio/app/frontend/js/catalogue-moment-import.js:119` | title |
| `import_preview_image_missing` | exact | `studio/app/frontend/js/catalogue-moment-import.js:129` | no source image found; media generation will be blocked |
| `import_preview_image_present` | exact | `studio/app/frontend/js/catalogue-moment-import.js:128` | source image found |
| `import_preview_missing_value` | exact | `studio/app/frontend/js/catalogue-moment-import.js:106`<br>`studio/app/frontend/js/catalogue-moment-import.js:144` | none |
| `import_preview_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-import.js:321` | Moment source preview failed. |
| `import_preview_status_invalid` | exact | `studio/app/frontend/js/catalogue-moment-import.js:315`<br>`studio/app/frontend/js/catalogue-moment-import.js:336` | Fix source-file issues before importing the moment. |
| `import_preview_status_loading` | exact | `studio/app/frontend/js/catalogue-moment-import.js:300` | Loading moment source preview... |
| `import_preview_status_ready` | exact | `studio/app/frontend/js/catalogue-moment-import.js:193`<br>`studio/app/frontend/js/catalogue-moment-import.js:313` | Moment source preview ready. |
| `import_result_missing_preview` | exact | `studio/app/frontend/js/catalogue-moment-import.js:332` | Preview the source file before importing. |
| `import_result_success` | exact | `studio/app/frontend/js/catalogue-moment-import.js:370` | Imported draft moment {moment_id}. |
| `import_save_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:471` | Local catalogue server unavailable. Moment import is disabled. |
| `import_source_result_summary` | exact | `studio/app/frontend/js/catalogue-moment-import.js:175` | Import writes draft prose and metadata only. Publish from this editor when ready. |
| `import_source_summary` | exact | `studio/app/frontend/js/catalogue-moment-import.js:242` | Moment prose is imported as body-only Markdown. Metadata is stored in catalogue source ... |
| `import_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-import.js:378` | Moment import failed. |
| `import_status_running` | exact | `studio/app/frontend/js/catalogue-moment-import.js:342` | Importing draft moment source... |
| `import_status_success` | exact | `studio/app/frontend/js/catalogue-moment-import.js:366` | Moment import completed. |
| `load_failed_error` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:503` | Failed to load catalogue source data for the moment editor. |
| `media_refresh_button` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:71` | Refresh media |
| `media_refresh_result_success` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:389` | Thumbnails updated; primary variants staged for publishing. |
| `media_refresh_save_first` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:60` | Save source changes before refreshing media. |
| `media_refresh_status_blocked` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:384` | Media refresh blocked. |
| `media_refresh_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:391` | Media refresh failed. |
| `media_refresh_status_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:372` | Refreshing media... |
| `media_refresh_status_success` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:388` | Media refresh completed. |
| `missing_moment_param` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:116`<br>`studio/app/frontend/js/catalogue-moment-editor.js:117` | Search for a moment by id or title. |
| `new_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:450` | New |
| `open_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:449` | Open |
| `prose_import_button` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:70` | Import staged prose |
| `prose_import_confirm_button` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:428` | Overwrite |
| `prose_import_confirm_overwrite` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:424` | Overwrite existing prose source at {target_path} with staged file {staging_path}? |
| `prose_import_confirm_title` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:420` | Confirm prose overwrite |
| `prose_import_overwrite_cancelled` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:433` | Prose import cancelled. |
| `prose_import_preview_invalid` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:414` | Staged prose is not ready to import. |
| `prose_import_preview_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:406` | Previewing staged prose... |
| `prose_import_result_success` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:168` | Prose imported to {target_path} at {completed_at}. Publish the moment or save the publi... |
| `prose_import_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:440` | Importing staged prose... |
| `prose_import_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:451` | Prose import failed. |
| `prose_import_status_success` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:177` | Prose import completed. |
| `publication_preview_publish_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:278` | Preparing publish preview... |
| `publication_preview_unpublish_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:279` | Preparing unpublish preview... |
| `publication_publish_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:327` | Publishing moment... |
| `publication_result_public_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:133` | Source status changed, but public artifacts did not finish updating. |
| `publication_result_published` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:137` | Moment is published and public output has been updated. |
| `publication_result_unpublished` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:141` | Moment is draft again and public output has been cleaned up. |
| `publication_save_first` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:261` | Save source changes before publishing. |
| `publication_status_blocked` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:294` | Publication change is blocked. |
| `publication_status_cancelled` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:316` | Publication change cancelled. |
| `publication_status_conflict` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:354` | Source record changed since this page loaded. Reload before changing publication state. |
| `publication_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:355` | Publication change failed. |
| `publication_status_invalid` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:257` | Publication is available only for draft or published moments. |
| `publication_status_public_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:147` | Publication state changed, but the public update failed. |
| `publication_status_published` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:151` | Moment published. |
| `publication_status_unpublished` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:155` | Moment unpublished. |
| `publication_status_validation_error` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:267` | Fix validation errors before changing publication state. |
| `publication_unpublish_confirm_button` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:311` | Unpublish |
| `publication_unpublish_confirm_title` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:309` | Confirm unpublish |
| `publication_unpublish_running` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:328` | Unpublishing moment... |
| `publish_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:269`<br>`studio/app/frontend/js/catalogue-moment-editor.js:452` | Publish |
| `readiness_action_busy` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:61` | Wait for the current save or public update to finish. |
| `save_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:451` | Save |
| `save_mode_local_server` | exact | `studio/app/frontend/js/studio-save-utils.js:7` | Local server |
| `save_mode_offline` | exact | `studio/app/frontend/js/studio-save-utils.js:8` | Unavailable |
| `save_mode_template` | exact | `studio/app/frontend/js/studio-save-utils.js:9` | Save mode: {mode} |
| `save_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:326`<br>`studio/app/frontend/js/catalogue-moment-editor.js:470` | Local catalogue server unavailable. Save is disabled. |
| `save_result_success` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:100`<br>`studio/app/frontend/js/catalogue-moment-actions.js:104` | Source saved at {saved_at}. |
| `save_result_success_applied` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:88` | Saved source changes and updated the public moment at {saved_at}. |
| `save_result_success_partial` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:92` | Source changes were saved at {saved_at}, but the public update failed. |
| `save_result_success_unpublished` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:96` | Source saved at {saved_at}. |
| `save_result_unchanged` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:212` | Source already matches the current form values. |
| `save_status_conflict` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:243` | Source record changed since this page loaded. Reload the moment before saving again. |
| `save_status_failed` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:245` | Source save failed. |
| `save_status_loaded` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:354` | Loaded moment {moment_id}. |
| `save_status_no_changes` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:211` | No changes to save. |
| `save_status_saving` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:222` | Saving source record... |
| `save_status_saving_and_updating` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:222` | Saving source record and updating public moment... |
| `save_status_validation_error` | exact | `studio/app/frontend/js/catalogue-moment-actions.js:207` | Fix validation errors before saving. |
| `search_empty` | exact | `studio/app/frontend/js/catalogue-moment-selection.js:61` | Enter a moment id or title. |
| `search_no_match` | exact | `studio/app/frontend/js/catalogue-moment-selection.js:43` | No matching moment records. |
| `search_placeholder` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:448` | find moment by id or title |
| `side_heading_current` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:195` | current record |
| `side_heading_import` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:231` | import preview |
| `summary_public_link` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:95` | Open public moment page |
| `summary_rebuild_current` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:99` | source and public moment are aligned in this session |
| `summary_rebuild_needed` | exact | `studio/app/frontend/js/catalogue-moment-sections.js:98` | public update failed in this session |
| `unknown_moment_error` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:340` | Unknown moment id: {moment_id}. |
| `unpublish_button` | exact | `studio/app/frontend/js/catalogue-moment-editor.js:268` | Unpublish |
| `unpublish_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` | Unpublish this moment? |
| `unpublish_confirm_dirty_note` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` | Unsaved form changes will be discarded. |

### `catalogue_series_editor`

| key | status | refs | value |
| --- | --- | --- | --- |
| `build_preview_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:245` | Build preview unavailable. |
| `build_preview_search_no` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` | no |
| `build_preview_search_yes` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` | yes |
| `build_preview_template` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64`<br>`studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` | Site update preview: work {work_ids}; series {series_ids}; catalogue search {search_reb... |
| `build_result_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:149` | Public catalogue updated at {completed_at}. Studio Activity updated. |
| `build_status_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:101`<br>`studio/app/frontend/js/catalogue-series-actions.js:489` | Site update failed. |
| `build_status_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:476` | Updating site… |
| `build_status_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:128`<br>`studio/app/frontend/js/catalogue-series-actions.js:155` | Site update completed. |
| `confirm_cancel_button` | exact | `studio/app/frontend/js/catalogue-series-actions.js:291`<br>`studio/app/frontend/js/catalogue-series-actions.js:559`<br>`studio/app/frontend/js/catalogue-series-actions.js:649` | Cancel |
| `context_loaded` | exact | `studio/app/frontend/js/catalogue-series-editor.js:264` | Editing source metadata for series {series_id}. |
| `create_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:203` | Create |
| `create_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-series-editor.js:195` | Local catalogue server unavailable. Create is disabled. |
| `create_result_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:458` | Created draft series {series_id}. Opening edit mode... |
| `create_status_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:461` | Draft series create failed. |
| `create_status_saving` | exact | `studio/app/frontend/js/catalogue-series-actions.js:433` | Creating draft series... |
| `create_status_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:459` | Created draft series {series_id}. |
| `create_status_validation_error` | exact | `studio/app/frontend/js/catalogue-series-actions.js:424` | Fix validation errors before creating the draft series. |
| `delete_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:443` | Delete |
| `delete_confirm_button` | exact | `studio/app/frontend/js/catalogue-series-actions.js:648` | Delete |
| `delete_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:148` | Delete this source record? |
| `delete_confirm_title` | exact | `studio/app/frontend/js/catalogue-series-actions.js:646` | Confirm delete |
| `delete_status_blocked` | exact | `studio/app/frontend/js/catalogue-series-actions.js:631` | Delete is blocked. |
| `delete_status_cancelled` | exact | `studio/app/frontend/js/catalogue-series-actions.js:653` | Delete cancelled. |
| `delete_status_conflict` | exact | `studio/app/frontend/js/catalogue-series-actions.js:665` | Source record changed since this page loaded. Reload before deleting again. |
| `delete_status_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:666` | Source delete failed. |
| `delete_status_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:618`<br>`studio/app/frontend/js/catalogue-series-actions.js:660` | Preparing delete preview... |
| `dirty_warning` | exact | `studio/app/frontend/js/catalogue-series-editor.js:189` | Unsaved source changes. |
| `field_duplicate_series_id` | exact | `studio/app/frontend/js/catalogue-series-fields.js:155` | Series id already exists. |
| `field_invalid_primary_work` | exact | `studio/app/frontend/js/catalogue-series-fields.js:203` | Primary work must be a current member of this series. |
| `field_invalid_series_type` | exact | `studio/app/frontend/js/catalogue-series-fields.js:166` | Choose a listed series type. |
| `field_invalid_status` | exact | `studio/app/frontend/js/catalogue-series-fields.js:192` | Use blank, draft, or published. |
| `field_invalid_year` | exact | `studio/app/frontend/js/catalogue-series-fields.js:178` | Use a whole year. |
| `field_required_primary_work_publish` | exact | `studio/app/frontend/js/catalogue-series-fields.js:201` | Published series must have a primary work that belongs to this series. |
| `field_required_series_id` | exact | `studio/app/frontend/js/catalogue-series-fields.js:153` | Enter a series id. |
| `field_required_series_type` | exact | `studio/app/frontend/js/catalogue-series-fields.js:164` | Choose a series type. |
| `field_required_title` | exact | `studio/app/frontend/js/catalogue-series-fields.js:159` | Enter a title. |
| `field_required_year` | exact | `studio/app/frontend/js/catalogue-series-fields.js:176` | Enter a year. |
| `field_required_year_display` | exact | `studio/app/frontend/js/catalogue-series-fields.js:182` | Enter a year display. |
| `load_failed_error` | dynamic-family | `showCatalogueEditorInitError(..., namespace)` in catalogue-editor-route-boot.js | Failed to load catalogue source data for the series editor. |
| `members_action_primary` | exact | `studio/app/frontend/js/catalogue-series-membership.js:156` | Make primary |
| `members_action_remove` | exact | `studio/app/frontend/js/catalogue-series-membership.js:157` | Remove |
| `members_add_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:447` | Add |
| `members_add_exists` | exact | `studio/app/frontend/js/catalogue-series-membership.js:220` | Work {work_id} is already in this series. |
| `members_add_missing` | exact | `studio/app/frontend/js/catalogue-series-membership.js:210` | Enter a work id to add. |
| `members_add_placeholder` | exact | `studio/app/frontend/js/catalogue-series-editor.js:446` | add work by id |
| `members_add_unknown` | exact | `studio/app/frontend/js/catalogue-series-membership.js:215` | Unknown work id: {work_id}. |
| `members_empty` | exact | `studio/app/frontend/js/catalogue-series-membership.js:189` | No works currently belong to this series. |
| `members_heading` | exact | `studio/app/frontend/js/catalogue-series-editor.js:444` | member works |
| `members_more_count` | exact | `studio/app/frontend/js/catalogue-series-membership.js:176` | showing {visible} of {total} |
| `members_position` | exact | `studio/app/frontend/js/catalogue-series-membership.js:146` | position {position} |
| `members_primary_badge` | exact | `studio/app/frontend/js/catalogue-series-membership.js:153` | primary |
| `members_remove_blocked` | exact | `studio/app/frontend/js/catalogue-series-membership.js:245` | Change primary_work_id before removing work {work_id}. |
| `members_search_no_match` | exact | `studio/app/frontend/js/catalogue-series-membership.js:184` | No matching member work ids. |
| `members_search_placeholder` | exact | `studio/app/frontend/js/catalogue-series-editor.js:445` | find member work by id |
| `missing_series_param` | exact | `studio/app/frontend/js/catalogue-series-editor.js:333` | Search for a series by title. |
| `new_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:440` | New |
| `new_context_loaded` | exact | `studio/app/frontend/js/catalogue-series-editor.js:301` | Creating a draft series source record. |
| `new_meta` | exact | `studio/app/frontend/js/catalogue-series-sections.js:95` | draft source record |
| `new_runtime_state` | exact | `studio/app/frontend/js/catalogue-series-sections.js:110` | Public site update is unavailable until the draft series exists. |
| `new_series_id_label` | exact | `studio/app/frontend/js/catalogue-series-editor.js:91` | New series id |
| `new_series_id_placeholder` | exact | `studio/app/frontend/js/catalogue-series-editor.js:90` | new series id |
| `new_summary_next` | exact | `studio/app/frontend/js/catalogue-series-sections.js:107` | Create the draft, then add member works, set primary_work_id, and publish when ready. |
| `new_summary_next_label` | exact | `studio/app/frontend/js/catalogue-series-sections.js:106` | next step |
| `new_summary_series_id_label` | exact | `studio/app/frontend/js/catalogue-series-sections.js:98` | series id |
| `new_summary_status` | exact | `studio/app/frontend/js/catalogue-series-sections.js:103` | draft source record; not published |
| `new_summary_status_label` | exact | `studio/app/frontend/js/catalogue-series-sections.js:102` | status |
| `open_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:439` | Open |
| `prose_import_button` | exact | `studio/app/frontend/js/catalogue-series-sections.js:77` | Import staged prose |
| `prose_import_confirm_button` | exact | `studio/app/frontend/js/catalogue-series-actions.js:290` | Overwrite |
| `prose_import_confirm_overwrite` | exact | `studio/app/frontend/js/catalogue-series-actions.js:280` | Overwrite existing prose source at {target_path} with staged file {staging_path}? |
| `prose_import_confirm_title` | exact | `studio/app/frontend/js/catalogue-series-actions.js:288` | Confirm prose overwrite |
| `prose_import_overwrite_cancelled` | exact | `studio/app/frontend/js/catalogue-series-actions.js:295` | Prose import cancelled. |
| `prose_import_preview_invalid` | exact | `studio/app/frontend/js/catalogue-series-actions.js:271` | Staged prose is not ready to import. |
| `prose_import_preview_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:262` | Previewing staged prose… |
| `prose_import_result_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:206` | Prose imported to {target_path} at {completed_at}. The next site update will publish it. |
| `prose_import_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:302` | Importing staged prose… |
| `prose_import_status_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:314` | Prose import failed. |
| `prose_import_status_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:215` | Prose import completed. |
| `publication_preview_publish_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:524` | Preparing publish preview… |
| `publication_preview_unpublish_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:525` | Preparing unpublish preview… |
| `publication_publish_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:574` | Publishing series… |
| `publication_result_public_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:170` | Source status changed, but public artifacts did not finish updating. |
| `publication_result_published` | exact | `studio/app/frontend/js/catalogue-series-actions.js:174` | Series and attached draft works are published, and public catalogue output has been upd... |
| `publication_result_unpublished` | exact | `studio/app/frontend/js/catalogue-series-actions.js:178` | Series is draft again and public catalogue output has been cleaned up. |
| `publication_save_first` | exact | `studio/app/frontend/js/catalogue-series-actions.js:504` | Save source changes before publishing. |
| `publication_status_blocked` | exact | `studio/app/frontend/js/catalogue-series-actions.js:540` | Publication change is blocked. |
| `publication_status_cancelled` | exact | `studio/app/frontend/js/catalogue-series-actions.js:563` | Publication change cancelled. |
| `publication_status_conflict` | exact | `studio/app/frontend/js/catalogue-series-actions.js:605` | Source record changed since this page loaded. Reload before changing publication state. |
| `publication_status_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:606` | Publication change failed. |
| `publication_status_invalid` | exact | `studio/app/frontend/js/catalogue-series-actions.js:500` | Publication is available only for draft or published series. |
| `publication_status_public_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:184` | Publication state changed, but the public update failed. |
| `publication_status_published` | exact | `studio/app/frontend/js/catalogue-series-actions.js:188` | Series published. |
| `publication_status_unpublished` | exact | `studio/app/frontend/js/catalogue-series-actions.js:192` | Series unpublished. |
| `publication_status_validation_error` | exact | `studio/app/frontend/js/catalogue-series-actions.js:512` | Fix validation errors before changing publication state. |
| `publication_unpublish_confirm_button` | exact | `studio/app/frontend/js/catalogue-series-actions.js:558` | Unpublish |
| `publication_unpublish_confirm_title` | exact | `studio/app/frontend/js/catalogue-series-actions.js:556` | Confirm unpublish |
| `publication_unpublish_running` | exact | `studio/app/frontend/js/catalogue-series-actions.js:575` | Unpublishing series… |
| `publish_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:150`<br>`studio/app/frontend/js/catalogue-series-editor.js:442` | Publish |
| `save_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:204`<br>`studio/app/frontend/js/catalogue-series-editor.js:441` | Save |
| `save_mode_local_server` | exact | `studio/app/frontend/js/studio-save-utils.js:7` | Local server |
| `save_mode_offline` | exact | `studio/app/frontend/js/studio-save-utils.js:8` | Unavailable |
| `save_mode_template` | exact | `studio/app/frontend/js/studio-save-utils.js:9` | Save mode: {mode} |
| `save_mode_unavailable` | not-detected |  | Unavailable |
| `save_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-series-editor.js:451` | Local catalogue server unavailable. Save is disabled. |
| `save_result_success` | exact | `studio/app/frontend/js/catalogue-series-actions.js:119` | Source saved at {saved_at}. Public catalogue update still pending. |
| `save_result_success_applied` | exact | `studio/app/frontend/js/catalogue-series-actions.js:107` | Saved source changes and updated the public catalogue at {saved_at}. |
| `save_result_success_partial` | exact | `studio/app/frontend/js/catalogue-series-actions.js:111` | Source changes were saved at {saved_at}, but the public update failed. |
| `save_result_unchanged` | exact | `studio/app/frontend/js/catalogue-series-actions.js:123`<br>`studio/app/frontend/js/catalogue-series-actions.js:344` | Source already matches the current form values. |
| `save_status_conflict` | exact | `studio/app/frontend/js/catalogue-series-actions.js:405` | Source record changed since this page loaded. Reload the series before saving again. |
| `save_status_failed` | exact | `studio/app/frontend/js/catalogue-series-actions.js:406` | Source save failed. |
| `save_status_loaded` | exact | `studio/app/frontend/js/catalogue-series-actions.js:136`<br>`studio/app/frontend/js/catalogue-series-editor.js:199`<br>`studio/app/frontend/js/catalogue-series-editor.js:265` | Loaded series {series_id}. |
| `save_status_no_changes` | exact | `studio/app/frontend/js/catalogue-series-actions.js:343` | No changes to save. |
| `save_status_saving` | exact | `studio/app/frontend/js/catalogue-series-actions.js:356` | Saving source record… |
| `save_status_saving_and_updating` | exact | `studio/app/frontend/js/catalogue-series-actions.js:355` | Saving source record and updating site… |
| `save_status_validation_error` | exact | `studio/app/frontend/js/catalogue-series-actions.js:338` | Fix validation errors before saving. |
| `search_empty` | exact | `studio/app/frontend/js/catalogue-series-selection.js:94` | Enter a series title or id. |
| `search_no_match` | exact | `studio/app/frontend/js/catalogue-series-selection.js:85` | No matching series records. |
| `search_placeholder` | exact | `studio/app/frontend/js/catalogue-series-editor.js:85`<br>`studio/app/frontend/js/catalogue-series-editor.js:438` | find series by title |
| `summary_member_count` | exact | `studio/app/frontend/js/catalogue-series-sections.js:128` | member works |
| `summary_public_link` | exact | `studio/app/frontend/js/catalogue-series-sections.js:122` | Open public series page |
| `summary_rebuild_current` | exact | `studio/app/frontend/js/catalogue-series-sections.js:134` | source and public catalogue are aligned in this session |
| `summary_rebuild_needed` | exact | `studio/app/frontend/js/catalogue-series-sections.js:133` | public update failed in this session |
| `unknown_series_error` | exact | `studio/app/frontend/js/catalogue-series-selection.js:101` | Unknown series id: {series_id}. |
| `unpublish_button` | exact | `studio/app/frontend/js/catalogue-series-editor.js:149` | Unpublish |
| `unpublish_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` | Unpublish this series? |
| `unpublish_confirm_dirty_note` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` | Unsaved form changes will be discarded. |

### `catalogue_status`

| key | status | refs | value |
| --- | --- | --- | --- |
| `empty_state` | exact | `studio/app/frontend/js/catalogue-status.js:177` | No draft {family} records. |
| `load_failed_error` | exact | `studio/app/frontend/js/catalogue-status.js:291` | Failed to load catalogue drafts. |
| `meta_summary` | exact | `studio/app/frontend/js/catalogue-status.js:174` | {count} draft {family} records |
| `meta_summary_one` | exact | `studio/app/frontend/js/catalogue-status.js:173` | 1 draft {family} record |
| `server_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-status.js:230` | Local catalogue server unavailable. Catalogue drafts are disabled. |

### `catalogue_work_detail_editor`

| key | status | refs | value |
| --- | --- | --- | --- |
| `build_preview_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:368` | Public update preview unavailable. |
| `build_preview_search_no` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` | no |
| `build_preview_search_yes` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` | yes |
| `build_preview_template` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64`<br>`studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` | Public update preview: work {work_ids}; series {series_ids}; catalogue search {search_r... |
| `build_preview_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:346` | Public update unavailable while the detail is not published. |
| `build_result_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:269` | Parent work output updated at {completed_at}. Studio Activity updated. |
| `build_status_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:166`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:214`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:562` | Site update failed. |
| `build_status_running` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:520` | Updating site… |
| `build_status_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:193`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:241`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:275` | Site update completed. |
| `bulk_save_result_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:232` | Saved {count} detail records at {saved_at}. |
| `bulk_save_result_success_applied` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:220` | Saved {count} detail records and updated the parent work output at {saved_at}. |
| `bulk_save_result_success_partial` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:224` | Saved {count} detail records at {saved_at}, but the public update failed. |
| `bulk_save_result_success_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:228` | Saved {count} draft detail records at {saved_at}. |
| `confirm_cancel_button` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:634`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:762` | Cancel |
| `context_loaded` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:195` | Editing source metadata for detail {detail_uid}. |
| `create_button` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:331` | Create |
| `create_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:316` | Local catalogue server unavailable. Create is disabled. |
| `create_result_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:501` | Created draft detail {detail_uid}. Opening edit mode... |
| `create_status_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:504` | Draft detail create failed. |
| `create_status_saving` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:481` | Creating draft detail... |
| `create_status_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:502` | Created draft detail {detail_uid}. |
| `create_status_validation_error` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:472` | Fix validation errors before creating the draft detail. |
| `delete_button` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:492` | Delete |
| `delete_confirm_button` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:761` | Delete |
| `delete_confirm_title` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:759` | Confirm delete |
| `dirty_warning` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:310` | Unsaved source changes. |
| `field_duplicate_detail_id` | exact | `studio/app/frontend/js/catalogue-work-detail-fields.js:205` | Detail id already exists for this work. |
| `field_invalid_sort_order` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:160`<br>`studio/app/frontend/js/catalogue-work-detail-fields.js:216` | Use a whole number or leave blank. |
| `field_invalid_status` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:172` | Use blank, draft, or published. |
| `field_label_detail_id` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | detail row id |
| `field_label_detail_uid` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | detail id |
| `field_label_details_subfolder` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | details subfolder |
| `field_label_height_px` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | height px |
| `field_label_project_filename` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | project filename |
| `field_label_published_date` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | published date |
| `field_label_section_id` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | section id |
| `field_label_section_title` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | section title |
| `field_label_sort_order` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | section sort order |
| `field_label_status` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | status |
| `field_label_title` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | title |
| `field_label_width_px` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | width px |
| `field_label_work_id` | dynamic-family | `field_label_${field.key}` in catalogue-work-detail-form.js | work id |
| `field_parent_work_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-fields.js:198` | Publish the parent work before adding work details. |
| `field_required_detail_id` | exact | `studio/app/frontend/js/catalogue-work-detail-fields.js:203` | Enter a detail id. |
| `field_required_section_title` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:164`<br>`studio/app/frontend/js/catalogue-work-detail-editor.js:167`<br>`studio/app/frontend/js/catalogue-work-detail-fields.js:212` | Enter a section title. |
| `field_required_title` | exact | `studio/app/frontend/js/catalogue-work-detail-fields.js:209` | Enter a title. |
| `field_required_work_id` | exact | `studio/app/frontend/js/catalogue-work-detail-fields.js:194` | Enter a parent work id. |
| `field_unknown_work_id` | exact | `studio/app/frontend/js/catalogue-work-detail-fields.js:196` | Unknown work id: {work_id}. |
| `load_failed_error` | dynamic-family | `showCatalogueEditorInitError(..., namespace)` in catalogue-editor-route-boot.js | Failed to load catalogue source data for the work detail editor. |
| `media_refresh_button` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:135` | Refresh media |
| `media_refresh_result_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:713` | Thumbnails updated; primary variants staged for publishing. |
| `media_refresh_save_first` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:132` | Save source changes before refreshing media. |
| `media_refresh_status_blocked` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:708` | Media refresh blocked. |
| `media_refresh_status_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:718` | Media refresh failed. |
| `media_refresh_status_running` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:696` | Refreshing media… |
| `media_refresh_status_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:712` | Media refresh completed. |
| `missing_detail_param` | exact | `studio/app/frontend/js/catalogue-work-detail-selection.js:269` | Search for a work detail by detail id. |
| `new_context_loaded` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:238` | Creating a draft detail under work {work_id}. |
| `new_context_parent_missing` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:232` | Open new detail mode from a parent work editor or provide a work id. |
| `new_context_parent_unknown` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:234` | Cannot create a detail because parent work {work_id} was not found. |
| `new_context_parent_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:236` | Publish work {work_id} before adding work details. |
| `new_runtime_state` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:176` | Public site update is unavailable until the draft detail exists. |
| `new_summary_detail_id_label` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:164` | detail id |
| `new_summary_next` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:173` | Create the draft, then continue editing or publish from edit mode. |
| `new_summary_next_label` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:172` | next step |
| `new_summary_parent_label` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:158` | parent work |
| `new_summary_status` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:169` | draft source record; not published |
| `new_summary_status_label` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:168` | status |
| `open_button` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:489` | Open |
| `publication_preview_publish_running` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:599` | Preparing publish preview… |
| `publication_preview_unpublish_running` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:600` | Preparing unpublish preview… |
| `publication_publish_running` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:649` | Publishing detail… |
| `publication_result_public_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:290` | Source status changed, but public artifacts did not finish updating. |
| `publication_result_published` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:294` | Detail is published and parent work output has been updated. |
| `publication_result_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:298` | Detail is draft again and public output has been cleaned up. |
| `publication_save_first` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:579` | Save source changes before publishing. |
| `publication_status_blocked` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:615` | Publication change is blocked. |
| `publication_status_cancelled` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:638` | Publication change cancelled. |
| `publication_status_conflict` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:678` | Source record changed since this page loaded. Reload before changing publication state. |
| `publication_status_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:679` | Publication change failed. |
| `publication_status_invalid` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:575` | Publication is available only for draft or published details. |
| `publication_status_public_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:304` | Publication state changed, but the public update failed. |
| `publication_status_published` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:308` | Detail published. |
| `publication_status_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:312` | Detail unpublished. |
| `publication_status_validation_error` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:587` | Fix validation errors before changing publication state. |
| `publication_unpublish_confirm_button` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:633` | Unpublish |
| `publication_unpublish_confirm_title` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:631` | Confirm unpublish |
| `publication_unpublish_running` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:650` | Unpublishing detail… |
| `publish_button` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:129`<br>`studio/app/frontend/js/catalogue-work-detail-editor.js:491` | Publish |
| `readiness_action_busy` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:133` | Wait for the current save or public update to finish. |
| `save_button` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:332`<br>`studio/app/frontend/js/catalogue-work-detail-editor.js:490` | Save |
| `save_mode_local_server` | exact | `studio/app/frontend/js/studio-save-utils.js:7` | Local server |
| `save_mode_offline` | exact | `studio/app/frontend/js/studio-save-utils.js:8` | Unavailable |
| `save_mode_template` | exact | `studio/app/frontend/js/studio-save-utils.js:9` | Save mode: {mode} |
| `save_mode_unavailable` | not-detected |  | Unavailable |
| `save_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:496` | Local catalogue server unavailable. Save is disabled. |
| `save_result_success` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:184` | Source saved at {saved_at}. |
| `save_result_success_applied` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:172` | Saved source changes and updated the parent work output at {saved_at}. |
| `save_result_success_partial` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:176` | Source changes were saved at {saved_at}, but the public update failed. |
| `save_result_success_unpublished` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:180` | Source saved at {saved_at}. |
| `save_result_unchanged` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:188`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:236`<br>`studio/app/frontend/js/catalogue-work-detail-actions.js:396` | Source already matches the current form values. |
| `save_status_conflict` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:454` | Source record changed since this page loaded. Reload the detail before saving again. |
| `save_status_failed` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:455` | Source save failed. |
| `save_status_loaded` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:201`<br>`studio/app/frontend/js/catalogue-work-detail-editor.js:196`<br>`studio/app/frontend/js/catalogue-work-detail-editor.js:324` | Loaded detail {detail_uid}. |
| `save_status_no_changes` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:395` | No changes to save. |
| `save_status_saving` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:409` | Saving source record… |
| `save_status_saving_and_updating` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:408` | Saving source record and updating site… |
| `save_status_validation_error` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:389` | Fix validation errors before saving. |
| `search_empty` | exact | `studio/app/frontend/js/catalogue-work-detail-selection.js:150`<br>`studio/app/frontend/js/catalogue-work-detail-selection.js:155`<br>`studio/app/frontend/js/catalogue-work-detail-selection.js:192` | Enter a detail id. |
| `search_no_match` | exact | `studio/app/frontend/js/catalogue-work-detail-selection.js:139` | No matching detail ids. |
| `search_placeholder` | exact | `studio/app/frontend/js/catalogue-work-detail-editor.js:488` | find detail id(s): 00001-001, 00001-003-005 |
| `summary_parent_link` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:222` | Open work editor |
| `summary_public_link` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:216` | Open public detail page |
| `summary_rebuild_current` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:205`<br>`studio/app/frontend/js/catalogue-work-detail-sections.js:235` | source and parent work output are aligned in this session |
| `summary_rebuild_needed` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:204`<br>`studio/app/frontend/js/catalogue-work-detail-sections.js:234` | public update failed in this session |
| `summary_section_label` | exact | `studio/app/frontend/js/catalogue-work-detail-sections.js:228` | detail section |
| `unknown_detail_error` | exact | `studio/app/frontend/js/catalogue-work-detail-selection.js:165`<br>`studio/app/frontend/js/catalogue-work-detail-selection.js:200` | Unknown detail id: {detail_uid}. |
| `unpublish_button` | exact | `studio/app/frontend/js/catalogue-work-detail-actions.js:128` | Unpublish |
| `unpublish_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` | Unpublish this detail? |
| `unpublish_confirm_dirty_note` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` | Unsaved form changes will be discarded. |

### `catalogue_work_editor`

| key | status | refs | value |
| --- | --- | --- | --- |
| `build_preview_button` | exact | `studio/app/frontend/js/catalogue-work-sections.js:272` | Preview update |
| `build_preview_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:601`<br>`studio/app/frontend/js/catalogue-work-actions.js:649` | Public update preview unavailable. |
| `build_preview_modal_artifacts` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:123` | Artifacts: {artifacts}. |
| `build_preview_modal_changed_fields` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:119` | Changed fields: {fields}. |
| `build_preview_modal_close` | exact | `studio/app/frontend/js/catalogue-work-editor-modals.js:124` | Close |
| `build_preview_modal_reasons_heading` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:126` | Reasons: |
| `build_preview_modal_rules` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:122` | Rules: {rules}. |
| `build_preview_modal_title` | exact | `studio/app/frontend/js/catalogue-work-editor-modals.js:116` | Public update preview |
| `build_preview_no_changes` | exact | `studio/app/frontend/js/catalogue-work-actions.js:625` | No unsaved changes to preview. |
| `build_preview_no_result` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:100` | No public update work selected. |
| `build_preview_search_no` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` | no |
| `build_preview_search_yes` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` | yes |
| `build_preview_server_unavailable` | exact | `studio/app/frontend/js/catalogue-work-actions.js:612` | Local catalogue server unavailable. |
| `build_preview_status_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:631` | Preparing public update preview... |
| `build_preview_template` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64`<br>`studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` | Public update preview: work {work_ids}; series {series_ids}; catalogue search {search_r... |
| `build_preview_unpublished` | exact | `studio/app/frontend/js/catalogue-work-actions.js:578`<br>`studio/app/frontend/js/catalogue-work-actions.js:616` | Public update unavailable while the work is not published. |
| `build_result_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:336` | Public catalogue updated at {completed_at}. Studio Activity updated. |
| `build_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:237`<br>`studio/app/frontend/js/catalogue-work-actions.js:285`<br>`studio/app/frontend/js/catalogue-work-actions.js:778` | Site update failed. |
| `build_status_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:738` | Updating site… |
| `build_status_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:264`<br>`studio/app/frontend/js/catalogue-work-actions.js:308`<br>`studio/app/frontend/js/catalogue-work-actions.js:342` | Site update completed. |
| `bulk_build_preview` | exact | `studio/app/frontend/js/catalogue-work-actions.js:560`<br>`studio/app/frontend/js/catalogue-work-editor.js:370` | Public update preview: {count} published work scope(s) will be updated. |
| `bulk_save_result_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:299` | Saved {count} work records at {saved_at}. |
| `bulk_save_result_success_applied` | exact | `studio/app/frontend/js/catalogue-work-actions.js:291` | Saved {count} work records and updated public catalogue output for published records at... |
| `bulk_save_result_success_partial` | exact | `studio/app/frontend/js/catalogue-work-actions.js:295` | Saved {count} work records at {saved_at}, but the public update failed. |
| `bulk_status_loaded` | exact | `studio/app/frontend/js/catalogue-work-actions.js:316`<br>`studio/app/frontend/js/catalogue-work-editor.js:392`<br>`studio/app/frontend/js/catalogue-work-route-state.js:176` | Loaded {count} work records. |
| `confirm_cancel_button` | exact | `studio/app/frontend/js/catalogue-work-actions.js:699`<br>`studio/app/frontend/js/catalogue-work-actions.js:850`<br>`studio/app/frontend/js/catalogue-work-actions.js:975` | Cancel |
| `context_series_empty` | exact | `studio/app/frontend/js/catalogue-work-sections.js:130` | No series assigned. |
| `create_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:398` | Create |
| `create_result_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:541` | Created draft work {work_id}. Opening edit mode... |
| `create_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:544` | Draft work create failed. |
| `create_status_saving` | exact | `studio/app/frontend/js/catalogue-work-actions.js:519` | Creating draft work... |
| `create_status_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:542` | Created draft work {work_id}. |
| `create_status_validation_error` | exact | `studio/app/frontend/js/catalogue-work-actions.js:510` | Fix validation errors before creating the draft work. |
| `delete_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:545` | Delete |
| `delete_confirm_button` | exact | `studio/app/frontend/js/catalogue-work-actions.js:974` | Delete |
| `delete_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:148` | Delete this source record? |
| `delete_confirm_title` | exact | `studio/app/frontend/js/catalogue-work-actions.js:972` | Confirm delete |
| `delete_status_blocked` | exact | `studio/app/frontend/js/catalogue-work-actions.js:957` | Delete is blocked. |
| `delete_status_cancelled` | exact | `studio/app/frontend/js/catalogue-work-actions.js:979` | Delete cancelled. |
| `delete_status_conflict` | exact | `studio/app/frontend/js/catalogue-work-actions.js:989` | Source record changed since this page loaded. Reload before deleting again. |
| `delete_status_deleting` | not-detected |  | Deleting source record... |
| `delete_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:990` | Source delete failed. |
| `delete_status_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:944`<br>`studio/app/frontend/js/catalogue-work-actions.js:984` | Preparing delete preview... |
| `details_empty` | exact | `studio/app/frontend/js/catalogue-work-sections.js:349` | No work details for this work. |
| `details_heading` | exact | `studio/app/frontend/js/catalogue-work-editor.js:534` | work details |
| `details_more_count` | exact | `studio/app/frontend/js/catalogue-work-sections.js:381` | showing {visible} of {total} |
| `details_new_link` | exact | `studio/app/frontend/js/catalogue-work-editor.js:535` | new work detail → |
| `details_new_unavailable_draft` | exact | `studio/app/frontend/js/catalogue-work-sections.js:569` | Publish this work before adding work details. |
| `details_search_no_match` | exact | `studio/app/frontend/js/catalogue-work-sections.js:374` | No matching detail ids for this work. |
| `details_search_placeholder` | exact | `studio/app/frontend/js/catalogue-work-editor.js:536` | find detail by id |
| `details_search_results` | exact | `studio/app/frontend/js/catalogue-work-sections.js:368` | matching details |
| `details_section_blank` | exact | `studio/app/frontend/js/catalogue-work-sections.js:125` | root |
| `dirty_warning` | exact | `studio/app/frontend/js/catalogue-work-editor.js:380` | Unsaved source changes. |
| `entry_modal_cancel_button` | exact | `studio/app/frontend/js/catalogue-work-editor-modals.js:96`<br>`studio/app/frontend/js/catalogue-work-editor-modals.js:147` | Cancel |
| `entry_modal_delete_button` | exact | `studio/app/frontend/js/catalogue-work-editor-modals.js:95` | Delete |
| `entry_modal_save_button` | exact | `studio/app/frontend/js/catalogue-work-editor-modals.js:148` | Save |
| `field_duplicate_work_id` | exact | `studio/app/frontend/js/catalogue-work-editor.js:190` | Work id already exists. |
| `field_invalid_date` | exact | `studio/app/frontend/js/catalogue-work-editor.js:248`<br>`studio/app/frontend/js/catalogue-work-editor.js:298` | Use YYYY-MM-DD or leave blank. |
| `field_invalid_number` | exact | `studio/app/frontend/js/catalogue-work-editor.js:214`<br>`studio/app/frontend/js/catalogue-work-editor.js:263`<br>`studio/app/frontend/js/catalogue-work-editor.js:309` | Use a number or leave blank. |
| `field_invalid_series_id` | exact | `studio/app/frontend/js/catalogue-work-editor.js:223`<br>`studio/app/frontend/js/catalogue-work-editor.js:282`<br>`studio/app/frontend/js/catalogue-work-editor.js:318` | Use comma-separated numeric series ids. |
| `field_invalid_status` | exact | `studio/app/frontend/js/catalogue-work-editor.js:241`<br>`studio/app/frontend/js/catalogue-work-editor.js:293` | Use blank, draft, or published. |
| `field_invalid_year` | exact | `studio/app/frontend/js/catalogue-work-editor.js:208`<br>`studio/app/frontend/js/catalogue-work-editor.js:255`<br>`studio/app/frontend/js/catalogue-work-editor.js:303` | Use a whole year or leave blank. |
| `field_required_series_ids` | exact | `studio/app/frontend/js/catalogue-work-editor.js:196` | Select at least one series. |
| `field_required_title` | dynamic-family | `field_required_${fieldKey}` in catalogue-work-editor.js | Enter title. |
| `field_required_work_id` | exact | `studio/app/frontend/js/catalogue-work-editor.js:188` | Enter a work id. |
| `field_required_year` | dynamic-family | `field_required_${fieldKey}` in catalogue-work-editor.js | Enter year. |
| `field_required_year_display` | dynamic-family | `field_required_${fieldKey}` in catalogue-work-editor.js | Enter year display. |
| `field_unknown_series_id` | exact | `studio/app/frontend/js/catalogue-work-editor.js:228`<br>`studio/app/frontend/js/catalogue-work-editor.js:275`<br>`studio/app/frontend/js/catalogue-work-editor.js:323` | Unknown series id: {series_id}. |
| `files_add_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:538` | Add file |
| `files_add_modal_title` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:25` | Add download |
| `files_delete_button` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:23` | Delete |
| `files_delete_modal_body` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:39` | Delete download {label}? |
| `files_delete_modal_title` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:37` | Delete download |
| `files_edit_button` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:21` | Edit |
| `files_edit_modal_title` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:27` | Edit download |
| `files_empty` | exact | `studio/app/frontend/js/catalogue-work-sections.js:415` | No downloads for this work. |
| `files_filename_label` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:29` | filename |
| `files_heading` | exact | `studio/app/frontend/js/catalogue-work-editor.js:537` | downloads |
| `files_invalid_filename` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:33` | Each download needs a filename. |
| `files_invalid_label` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:35` | Each download needs a label. |
| `files_label_label` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:31` | label |
| `links_add_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:540` | Add link |
| `links_add_modal_title` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:59` | Add link |
| `links_delete_button` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:57` | Delete |
| `links_delete_modal_body` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:73` | Delete link {label}? |
| `links_delete_modal_title` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:71` | Delete link |
| `links_edit_button` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:55` | Edit |
| `links_edit_modal_title` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:61` | Edit link |
| `links_empty` | exact | `studio/app/frontend/js/catalogue-work-sections.js:442` | No links for this work. |
| `links_heading` | exact | `studio/app/frontend/js/catalogue-work-editor.js:539` | links |
| `links_invalid_label` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:69` | Each link needs a label. |
| `links_invalid_url` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:67` | Each link needs a URL. |
| `links_label_label` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:65` | label |
| `links_url_label` | exact | `studio/app/frontend/js/catalogue-editor-embedded-items.js:63` | URL |
| `load_failed_error` | dynamic-family | `showCatalogueEditorInitError(..., namespace)` in catalogue-editor-route-boot.js | Failed to load catalogue source data for the work editor. |
| `load_requested_work_failed` | exact | `studio/app/frontend/js/catalogue-work-selection.js:291` | Failed to load the requested work. |
| `media_refresh_button` | exact | `studio/app/frontend/js/catalogue-work-sections.js:317` | Refresh media |
| `media_refresh_result_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:926` | Thumbnails updated; primary variants staged for publishing. |
| `media_refresh_save_first` | exact | `studio/app/frontend/js/catalogue-work-sections.js:313` | Save source changes before refreshing media. |
| `media_refresh_status_blocked` | exact | `studio/app/frontend/js/catalogue-work-actions.js:921` | Media refresh blocked. |
| `media_refresh_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:931` | Media refresh failed. |
| `media_refresh_status_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:910` | Refreshing media… |
| `media_refresh_status_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:925` | Media refresh completed. |
| `missing_work_param` | exact | `studio/app/frontend/js/catalogue-work-route-state.js:243` | Search for a work by work id. |
| `new_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:542` | New |
| `new_meta` | exact | `studio/app/frontend/js/catalogue-work-sections.js:458` | Creating a draft work. |
| `new_runtime_state` | exact | `studio/app/frontend/js/catalogue-work-sections.js:469` | Public site update is unavailable until the draft exists. |
| `new_status_loaded` | exact | `studio/app/frontend/js/catalogue-work-route-state.js:211` | Creating a draft work source record. |
| `new_summary_next` | exact | `studio/app/frontend/js/catalogue-work-sections.js:466` | Create the draft, then continue editing or publish from edit mode. |
| `new_summary_next_label` | exact | `studio/app/frontend/js/catalogue-work-sections.js:465` | next step |
| `new_summary_status` | exact | `studio/app/frontend/js/catalogue-work-sections.js:462` | draft source record; not published |
| `new_summary_status_label` | exact | `studio/app/frontend/js/catalogue-work-sections.js:461` | status |
| `new_work_id_label` | exact | `studio/app/frontend/js/catalogue-work-route-state.js:204` | New work id |
| `new_work_id_placeholder` | exact | `studio/app/frontend/js/catalogue-work-route-state.js:203` | new work id |
| `open_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:541` | Open |
| `prose_import_button` | exact | `studio/app/frontend/js/catalogue-work-sections.js:316` | Import staged prose |
| `prose_import_confirm_button` | exact | `studio/app/frontend/js/catalogue-work-actions.js:698` | Overwrite |
| `prose_import_confirm_overwrite` | exact | `studio/app/frontend/js/catalogue-work-actions.js:685` | Overwrite existing prose source at {target_path} with staged file {staging_path}? |
| `prose_import_confirm_title` | exact | `studio/app/frontend/js/catalogue-work-actions.js:696` | Confirm prose overwrite |
| `prose_import_overwrite_cancelled` | exact | `studio/app/frontend/js/catalogue-work-actions.js:703` | Prose import cancelled. |
| `prose_import_preview_invalid` | exact | `studio/app/frontend/js/catalogue-work-actions.js:678` | Staged prose is not ready to import. |
| `prose_import_preview_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:669` | Previewing staged prose… |
| `prose_import_result_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:393` | Prose imported to {target_path} at {completed_at}. The next site update will publish it. |
| `prose_import_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:709` | Importing staged prose… |
| `prose_import_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:721` | Prose import failed. |
| `prose_import_status_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:402` | Prose import completed. |
| `publication_preview_publish_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:815` | Preparing publish preview… |
| `publication_preview_unpublish_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:816` | Preparing unpublish preview… |
| `publication_publish_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:865` | Publishing work… |
| `publication_result_public_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:357` | Source status changed, but public artifacts did not finish updating. |
| `publication_result_published` | exact | `studio/app/frontend/js/catalogue-work-actions.js:361` | Work is published and public catalogue output has been updated. |
| `publication_result_unpublished` | exact | `studio/app/frontend/js/catalogue-work-actions.js:365` | Work is draft again and public catalogue output has been cleaned up. |
| `publication_save_first` | exact | `studio/app/frontend/js/catalogue-work-actions.js:795` | Save source changes before publishing. |
| `publication_status_blocked` | exact | `studio/app/frontend/js/catalogue-work-actions.js:831` | Publication change is blocked. |
| `publication_status_cancelled` | exact | `studio/app/frontend/js/catalogue-work-actions.js:854` | Publication change cancelled. |
| `publication_status_conflict` | exact | `studio/app/frontend/js/catalogue-work-actions.js:892` | Source record changed since this page loaded. Reload before changing publication state. |
| `publication_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:893` | Publication change failed. |
| `publication_status_invalid` | exact | `studio/app/frontend/js/catalogue-work-actions.js:791` | Publication is available only for draft or published works. |
| `publication_status_public_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:371` | Publication state changed, but the public update failed. |
| `publication_status_published` | exact | `studio/app/frontend/js/catalogue-work-actions.js:375` | Work published. |
| `publication_status_unpublished` | exact | `studio/app/frontend/js/catalogue-work-actions.js:379` | Work unpublished. |
| `publication_status_validation_error` | exact | `studio/app/frontend/js/catalogue-work-actions.js:803` | Fix validation errors before changing publication state. |
| `publication_unpublish_confirm_button` | exact | `studio/app/frontend/js/catalogue-work-actions.js:849` | Unpublish |
| `publication_unpublish_confirm_title` | exact | `studio/app/frontend/js/catalogue-work-actions.js:847` | Confirm unpublish |
| `publication_unpublish_running` | exact | `studio/app/frontend/js/catalogue-work-actions.js:866` | Unpublishing work… |
| `publish_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:343`<br>`studio/app/frontend/js/catalogue-work-editor.js:544` | Publish |
| `readiness_action_busy` | exact | `studio/app/frontend/js/catalogue-work-sections.js:310`<br>`studio/app/frontend/js/catalogue-work-sections.js:314` | Wait for the current save or public update to finish. |
| `readiness_save_first` | exact | `studio/app/frontend/js/catalogue-work-sections.js:309` | Save source changes before importing prose. |
| `save_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:399`<br>`studio/app/frontend/js/catalogue-work-editor.js:543` | Save |
| `save_mode_local_server` | exact | `studio/app/frontend/js/studio-save-utils.js:7` | Local server |
| `save_mode_offline` | exact | `studio/app/frontend/js/studio-save-utils.js:8` | Unavailable |
| `save_mode_template` | exact | `studio/app/frontend/js/studio-save-utils.js:9` | Save mode: {mode} |
| `save_mode_unavailable` | not-detected |  | Unavailable |
| `save_mode_unavailable_hint` | exact | `studio/app/frontend/js/catalogue-work-editor.js:385`<br>`studio/app/frontend/js/catalogue-work-editor.js:592` | Local catalogue server unavailable. Save is disabled. |
| `save_result_success` | exact | `studio/app/frontend/js/catalogue-work-actions.js:255` | Source saved at {saved_at}. |
| `save_result_success_applied` | exact | `studio/app/frontend/js/catalogue-work-actions.js:243` | Saved source changes and updated the public catalogue at {saved_at}. |
| `save_result_success_partial` | exact | `studio/app/frontend/js/catalogue-work-actions.js:247` | Source changes were saved at {saved_at}, but the public update failed. |
| `save_result_success_unpublished` | exact | `studio/app/frontend/js/catalogue-work-actions.js:251` | Source saved at {saved_at}. |
| `save_result_unchanged` | exact | `studio/app/frontend/js/catalogue-work-actions.js:259`<br>`studio/app/frontend/js/catalogue-work-actions.js:303`<br>`studio/app/frontend/js/catalogue-work-actions.js:429` | Source already matches the current form values. |
| `save_status_conflict` | exact | `studio/app/frontend/js/catalogue-work-actions.js:492` | Source record changed since this page loaded. Reload the work before saving again. |
| `save_status_failed` | exact | `studio/app/frontend/js/catalogue-work-actions.js:493` | Source save failed. |
| `save_status_loaded` | exact | `studio/app/frontend/js/catalogue-work-actions.js:272`<br>`studio/app/frontend/js/catalogue-work-actions.js:640`<br>`studio/app/frontend/js/catalogue-work-editor.js:393`<br>`studio/app/frontend/js/catalogue-work-route-state.js:143` |  |
| `save_status_no_changes` | exact | `studio/app/frontend/js/catalogue-work-actions.js:428` | No changes to save. |
| `save_status_saving` | exact | `studio/app/frontend/js/catalogue-work-actions.js:441` | Saving source record… |
| `save_status_saving_and_updating` | exact | `studio/app/frontend/js/catalogue-work-actions.js:440` | Saving source record and updating parent work output… |
| `save_status_validation_error` | exact | `studio/app/frontend/js/catalogue-work-actions.js:422`<br>`studio/app/frontend/js/catalogue-work-actions.js:620` | Fix validation errors before saving. |
| `search_empty` | exact | `studio/app/frontend/js/catalogue-work-selection.js:152`<br>`studio/app/frontend/js/catalogue-work-selection.js:157`<br>`studio/app/frontend/js/catalogue-work-selection.js:197` | Enter a work id. |
| `search_no_match` | exact | `studio/app/frontend/js/catalogue-work-selection.js:141` | No matching work ids. |
| `search_placeholder` | exact | `studio/app/frontend/js/catalogue-work-editor.js:123` | find work id(s): 00001, 00003-00005 |
| `series_picker_empty` | exact | `studio/app/frontend/js/catalogue-work-form.js:128` | No series selected. |
| `series_picker_label` | exact | `studio/app/frontend/js/catalogue-work-form.js:231`<br>`studio/app/frontend/js/catalogue-work-form.js:323` | Find series by title |
| `series_picker_placeholder` | exact | `studio/app/frontend/js/catalogue-work-form.js:230`<br>`studio/app/frontend/js/catalogue-work-form.js:322` | find series by title |
| `summary_public_link` | exact | `studio/app/frontend/js/catalogue-work-sections.js:545` | Open public work page |
| `summary_rebuild_current` | exact | `studio/app/frontend/js/catalogue-work-sections.js:517`<br>`studio/app/frontend/js/catalogue-work-sections.js:558` | source and public catalogue are aligned in this session |
| `summary_rebuild_needed` | exact | `studio/app/frontend/js/catalogue-work-sections.js:516`<br>`studio/app/frontend/js/catalogue-work-sections.js:557` | public update failed in this session |
| `summary_series_label` | exact | `studio/app/frontend/js/catalogue-work-sections.js:511`<br>`studio/app/frontend/js/catalogue-work-sections.js:551` | series |
| `unknown_work_error` | exact | `studio/app/frontend/js/catalogue-work-selection.js:167`<br>`studio/app/frontend/js/catalogue-work-selection.js:207` | Unknown work id: {work_id}. |
| `unpublish_button` | exact | `studio/app/frontend/js/catalogue-work-editor.js:342` | Unpublish |
| `unpublish_confirm_default` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` | Unpublish this work? |
| `unpublish_confirm_dirty_note` | exact | `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` | Unsaved form changes will be discarded. |

### `project_state`

| key | status | refs | value |
| --- | --- | --- | --- |
| `context_hint` | exact | `studio/app/frontend/js/project-state.js:247` | Scan source project folders and primary images against works.json, then write the Markd... |
| `empty_state` | exact | `studio/app/frontend/js/project-state.js:243` |  |
| `include_subfolders_label` | exact | `studio/app/frontend/js/project-state.js:240` | include sub-folders |
| `loading` | exact | `studio/app/frontend/js/project-state.js:242` | loading project state... |
| `open_button` | exact | `studio/app/frontend/js/project-state.js:245` | Open file |
| `open_failed` | exact | `studio/app/frontend/js/project-state.js:158` | Could not open the Markdown report. |
| `output_label` | exact | `studio/app/frontend/js/project-state.js:238` | output |
| `page_heading` | exact | `studio/app/frontend/js/project-state.js:236` | project state |
| `run_button` | exact | `studio/app/frontend/js/project-state.js:244` | Run |
| `run_heading` | exact | `studio/app/frontend/js/project-state.js:237` | report |
| `run_result_success` | exact | `studio/app/frontend/js/project-state.js:134` | Report written to {path}. |
| `run_status_failed` | exact | `studio/app/frontend/js/project-state.js:140` | Project-state report failed. |
| `run_status_running` | exact | `studio/app/frontend/js/project-state.js:106` | Running project-state report... |
| `run_status_success` | exact | `studio/app/frontend/js/project-state.js:129` | Project-state report updated. |
| `save_mode_local_server` | exact | `studio/app/frontend/js/studio-save-utils.js:7` | Local server |
| `save_mode_offline` | exact | `studio/app/frontend/js/studio-save-utils.js:8` | Unavailable |
| `save_mode_template` | exact | `studio/app/frontend/js/studio-save-utils.js:9` | Save mode: {mode} |
| `server_unavailable_hint` | exact | `studio/app/frontend/js/project-state.js:251` | Local catalogue server unavailable. Report generation and report opening are disabled. |
| `source_label` | exact | `studio/app/frontend/js/project-state.js:239` | source |
| `summary_catalogue_folders` | exact | `studio/app/frontend/js/project-state.js:75` | catalogue folders |
| `summary_catalogue_images` | exact | `studio/app/frontend/js/project-state.js:78` | primary images in works.json |
| `summary_heading` | exact | `studio/app/frontend/js/project-state.js:241` | summary |
| `summary_include_subfolders` | exact | `studio/app/frontend/js/project-state.js:73` | include sub-folders |
| `summary_source_folders` | exact | `studio/app/frontend/js/project-state.js:74` | source folders |
| `summary_source_images` | exact | `studio/app/frontend/js/project-state.js:77` | source images |
| `summary_unrepresented_folders` | exact | `studio/app/frontend/js/project-state.js:76` | folders not in works.json |
| `summary_unrepresented_images` | exact | `studio/app/frontend/js/project-state.js:79` | extra images in represented folders |

### `studio_works`

| key | status | refs | value |
| --- | --- | --- | --- |
| `copy_series_button` | exact | `studio/app/frontend/js/studio-works.js:478` | copy series |

## Exact Reference Details

### `bulk_add_work`

- `apply_button`
  - `studio/app/frontend/js/bulk-add-work.js:223` `applyButton.textContent = t(state, "apply_button", "Import");`
- `apply_clear_workbook`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:118` `text: text(options, "apply_clear_workbook", "Clear the imported rows from {workbook} af...`
- `apply_requires_preview`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:45` `text: text(options, "apply_requires_preview", "Run preview for the current mode before ...`
- `apply_result_success`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:111` `text: text(options, "apply_result_success", "Imported {imported} record(s); {duplicates...`
- `apply_status_failed`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:129` `text: `${text(options, "apply_status_failed", "Workbook import failed.")} ${normalizeBu...`
- `apply_status_running`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:97` `text: text(options, "apply_status_running", "Applying workbook import...")`
- `apply_status_success`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:107` `text: text(options, "apply_status_success", "Workbook import completed.")`
- `context_hint`
  - `studio/app/frontend/js/bulk-add-work.js:228` `t(state, "context_hint", "Bulk import is one-way from {workbook} into canonical JSON. U...`
- `details_heading`
  - `studio/app/frontend/js/bulk-add-work.js:219` `detailsHeadingNode.textContent = t(state, "details_heading", "preview details");`
- `empty_state`
  - `studio/app/frontend/js/bulk-add-work.js:221` `emptyNode.textContent = t(state, "empty_state", "");`
- `import_heading`
  - `studio/app/frontend/js/bulk-add-work.js:213` `importHeadingNode.textContent = t(state, "import_heading", "import");`
- `loading`
  - `studio/app/frontend/js/bulk-add-work.js:220` `loadingNode.textContent = t(state, "loading", "loading bulk add work…");`
- `mode_label`
  - `studio/app/frontend/js/bulk-add-work.js:214` `modeLabelNode.textContent = t(state, "mode_label", "mode");`
- `mode_option_work_details`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:206` `if (mode === "work_details") return text(options, "mode_option_work_details", "work det...`
  - `studio/app/frontend/js/bulk-add-work.js:216` `workDetailsOptionNode.textContent = t(state, "mode_option_work_details", "work details");`
- `mode_option_works`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:207` `return text(options, "mode_option_works", "works");`
  - `studio/app/frontend/js/bulk-add-work.js:215` `worksOptionNode.textContent = t(state, "mode_option_works", "works");`
- `page_heading`
  - `studio/app/frontend/js/bulk-add-work.js:212` `pageHeadingNode.textContent = t(state, "page_heading", "bulk add work");`
- `preview_blocked_warning`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:66` `text: text(options, "preview_blocked_warning", "Blocked rows must be fixed in {workbook...`
- `preview_button`
  - `studio/app/frontend/js/bulk-add-work.js:222` `previewButton.textContent = t(state, "preview_button", "Preview");`
- `preview_empty`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:162` `return `<p class="tagStudioForm__meta">${escapeHtml(text(options, "preview_empty", "Run...`
- `preview_status_failed`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:88` `text: `${text(options, "preview_status_failed", "Workbook import preview failed.")} ${n...`
- `preview_status_running`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:54` `text: text(options, "preview_status_running", "Running workbook import preview...")`
- `preview_status_success`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:74` `text: text(options, "preview_status_success", "Preview ready: {importable} importable, ...`
- `save_mode_local_server`
  - `studio/app/frontend/js/studio-save-utils.js:7` `? studioText(config, "save_mode_local_server", "Local server")`
- `save_mode_offline`
  - `studio/app/frontend/js/studio-save-utils.js:8` `: studioText(config, "save_mode_offline", "Offline session");`
- `save_mode_template`
  - `studio/app/frontend/js/studio-save-utils.js:9` `return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });`
- `save_mode_unavailable_hint`
  - `studio/app/frontend/js/bulk-add-work.js:233` `unavailableText: () => t(state, "save_mode_unavailable_hint", "Local catalogue server u...`
- `section_blocked`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:191` `<h3 class="tagStudioForm__key">${escapeHtml(text(options, "section_blocked", "blocked r...`
- `section_duplicates`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:182` `<h3 class="tagStudioForm__key">${escapeHtml(text(options, "section_duplicates", "duplic...`
- `section_importable`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:173` `<h3 class="tagStudioForm__key">${escapeHtml(text(options, "section_importable", "import...`
- `section_none`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:175` `<p class="tagStudioForm__meta">${escapeHtml(importableIds.length ? importableIds.join("...`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:184` `<p class="tagStudioForm__meta">${escapeHtml(Array.isArray(duplicates.sample_ids) && dup...`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:198` `${(!blocked.count) ? `<p class="tagStudioForm__meta">${escapeHtml(text(options, "sectio...`
- `summary_blocked`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:150` `{ label: text(options, "summary_blocked", "blocked"), value: String(Number(summary.bloc...`
- `summary_candidate_rows`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:147` `{ label: text(options, "summary_candidate_rows", "candidate rows"), value: String(Numbe...`
- `summary_duplicates`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:149` `{ label: text(options, "summary_duplicates", "duplicates"), value: String(Number(summar...`
- `summary_heading`
  - `studio/app/frontend/js/bulk-add-work.js:218` `summaryHeadingNode.textContent = t(state, "summary_heading", "preview summary");`
- `summary_importable`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:148` `{ label: text(options, "summary_importable", "importable"), value: String(Number(summar...`
- `summary_mode`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:145` `{ label: text(options, "summary_mode", "mode"), value: modeLabel(state, preview && prev...`
- `summary_workbook`
  - `studio/app/frontend/js/bulk-add-work-workflow.js:146` `{ label: text(options, "summary_workbook", "workbook"), value: bulkAddWorkWorkbookPath(...`
- `workbook_label`
  - `studio/app/frontend/js/bulk-add-work.js:217` `workbookLabelNode.textContent = t(state, "workbook_label", "workbook");`

### `catalogue_field_registry_review`

- `context_hint`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:122` `contextNode.textContent = t(state, "context_hint", "Read-only view of the active field-...`
- `empty_state`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:124` `emptyNode.textContent = t(state, "empty_state", "");`
- `loading`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:123` `loadingNode.textContent = t(state, "loading", "loading catalogue field registry...");`
- `meta_all`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:62` `meta: t(state, "meta_all", "Showing full registry.")`
- `meta_exact`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:67` `const metaKey = matches.mode === "exact" ? "meta_exact" : "meta_partial";`
- `meta_partial`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:67` `const metaKey = matches.mode === "exact" ? "meta_exact" : "meta_partial";`
- `output_label`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:126` `outputLabelNode.textContent = t(state, "output_label", "registry extract");`
- `page_heading`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:121` `headingNode.textContent = t(state, "page_heading", "catalogue field registry");`
- `search_placeholder`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:125` `searchNode.placeholder = t(state, "search_placeholder", "field name");`
- `status_loaded`
  - `studio/app/frontend/js/catalogue-field-registry-review.js:132` `setTextWithState(statusNode, t(state, "status_loaded", "Registry loaded."), "success");`

### `catalogue_moment_editor`

- `build_preview_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:199` `setTextWithState(context, state.buildImpactNode, t(state, context, "build_preview_faile...`
- `build_preview_search_no`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` `: lookupText(options, "build_preview_search_no", "no");`
- `build_preview_search_yes`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` `? lookupText(options, "build_preview_search_yes", "yes")`
- `build_preview_template`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64` `"build_preview_template",`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` `"build_preview_template",`
- `build_preview_unpublished`
  - `studio/app/frontend/js/catalogue-moment-sections.js:105` `state.buildImpactNode.textContent = text(options, "build_preview_unpublished", "Public ...`
- `confirm_cancel_button`
  - `studio/app/frontend/js/catalogue-moment-actions.js:312` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-moment-actions.js:429` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-moment-actions.js:499` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
- `context_loaded`
  - `studio/app/frontend/js/catalogue-moment-editor.js:353` `setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata...`
- `delete_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:453` `state.deleteButton.textContent = t(state, "delete_button", "Delete");`
- `delete_confirm_button`
  - `studio/app/frontend/js/catalogue-moment-actions.js:498` `primaryLabel: t(state, context, "delete_confirm_button", "Delete"),`
- `delete_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:148` `\|\| lookupText(options, "delete_confirm_default", options.defaultText \|\| "Delete this so...`
- `delete_confirm_title`
  - `studio/app/frontend/js/catalogue-moment-actions.js:496` `title: t(state, context, "delete_confirm_title", "Confirm delete"),`
- `delete_status_blocked`
  - `studio/app/frontend/js/catalogue-moment-actions.js:481` `fallback: t(state, context, "delete_status_blocked", "Delete is blocked.")`
- `delete_status_cancelled`
  - `studio/app/frontend/js/catalogue-moment-actions.js:503` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_cancelled"...`
- `delete_status_conflict`
  - `studio/app/frontend/js/catalogue-moment-actions.js:515` `? t(state, context, "delete_status_conflict", "Source record changed since this page lo...`
- `delete_status_deleting`
  - `studio/app/frontend/js/catalogue-moment-actions.js:510` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_deleting",...`
- `delete_status_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:516` `: `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeTex...`
- `delete_status_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:468` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", ...`
- `dirty_warning`
  - `studio/app/frontend/js/catalogue-moment-actions.js:400` `setTextWithState(context, state.statusNode, t(state, context, "dirty_warning", "Unsaved...`
  - `studio/app/frontend/js/catalogue-moment-editor.js:288` `message: t(state, "dirty_warning", "Unsaved source changes.")`
  - `studio/app/frontend/js/catalogue-moment-sections.js:60` `? (mediaAction ? text(options, "media_refresh_save_first", "Save source changes before ...`
- `field_invalid_date`
  - `studio/app/frontend/js/catalogue-moment-fields.js:100` `errors.set(key, t("field_invalid_date", "Use YYYY-MM-DD or leave blank."));`
- `field_invalid_status`
  - `studio/app/frontend/js/catalogue-moment-fields.js:105` `errors.set("status", t("field_invalid_status", "Use draft or published."));`
- `field_required_date`
  - `studio/app/frontend/js/catalogue-moment-fields.js:95` `errors.set("date", t("field_required_date", "Enter a date."));`
- `field_required_published_date`
  - `studio/app/frontend/js/catalogue-moment-fields.js:108` `errors.set("published_date", t("field_required_published_date", "Published moments requ...`
- `field_required_title`
  - `studio/app/frontend/js/catalogue-moment-fields.js:92` `errors.set("title", t("field_required_title", "Enter a title."));`
- `import_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:457` `state.importApplyButton.textContent = t(state, "import_button", "Import");`
- `import_context_hint`
  - `studio/app/frontend/js/catalogue-moment-editor.js:233` `setTextWithState(state.contextNode, t(state, "import_context_hint", "Import a staged mo...`
- `import_empty_state`
  - `studio/app/frontend/js/catalogue-moment-import.js:113` `<p class="tagStudioForm__meta">${escapeHtml(text(context, "import_empty_state", "Previe...`
  - `studio/app/frontend/js/catalogue-moment-import.js:167` `<p class="tagStudioForm__meta">${escapeHtml(text(context, "import_empty_state", "Previe...`
- `import_file_description`
  - `studio/app/frontend/js/catalogue-moment-editor.js:458` `state.importFileDescriptionNode.textContent = t(state, "import_file_description", "file...`
- `import_file_label`
  - `studio/app/frontend/js/catalogue-moment-editor.js:454` `state.importFileLabelNode.textContent = t(state, "import_file_label", "moment file");`
- `import_file_placeholder`
  - `studio/app/frontend/js/catalogue-moment-editor.js:455` `state.importFileNode.placeholder = t(state, "import_file_placeholder", "keys.md");`
- `import_file_required`
  - `studio/app/frontend/js/catalogue-moment-import.js:294` `setTextWithState(context, state.importStatusNode, text(context, "import_file_required",...`
- `import_image_guidance`
  - `studio/app/frontend/js/catalogue-moment-import.js:243` `state.importImageGuidanceNode.textContent = text(context, "import_image_guidance", "Mis...`
- `import_mode_loaded`
  - `studio/app/frontend/js/catalogue-moment-editor.js:234` `setTextWithState(state.statusNode, t(state, "import_mode_loaded", "Preview the staged m...`
- `import_preview_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:456` `state.importPreviewButton.textContent = t(state, "import_preview_button", "Preview");`
- `import_preview_errors_intro`
  - `studio/app/frontend/js/catalogue-moment-import.js:183` `<p class="tagStudioForm__meta">${escapeHtml(text(context, "import_preview_errors_intro"...`
- `import_preview_field_date`
  - `studio/app/frontend/js/catalogue-moment-import.js:121` `{ label: text(context, "import_preview_field_date", "date"), value: preview.date },`
- `import_preview_field_date_display`
  - `studio/app/frontend/js/catalogue-moment-import.js:122` `{ label: text(context, "import_preview_field_date_display", "date display"), value: pre...`
- `import_preview_field_generated_status`
  - `studio/app/frontend/js/catalogue-moment-import.js:132` `label: text(context, "import_preview_field_generated_status", "generated status"),`
- `import_preview_field_image_file`
  - `studio/app/frontend/js/catalogue-moment-import.js:124` `{ label: text(context, "import_preview_field_image_file", "image file"), value: preview...`
- `import_preview_field_image_status`
  - `studio/app/frontend/js/catalogue-moment-import.js:126` `label: text(context, "import_preview_field_image_status", "image status"),`
- `import_preview_field_moment_id`
  - `studio/app/frontend/js/catalogue-moment-import.js:118` `{ label: text(context, "import_preview_field_moment_id", "moment id"), value: preview.m...`
- `import_preview_field_published_date`
  - `studio/app/frontend/js/catalogue-moment-import.js:123` `{ label: text(context, "import_preview_field_published_date", "published date"), value:...`
- `import_preview_field_source_path`
  - `studio/app/frontend/js/catalogue-moment-import.js:136` `label: text(context, "import_preview_field_source_path", "source path"),`
- `import_preview_field_status`
  - `studio/app/frontend/js/catalogue-moment-import.js:120` `{ label: text(context, "import_preview_field_status", "status"), value: preview.status },`
- `import_preview_field_title`
  - `studio/app/frontend/js/catalogue-moment-import.js:119` `{ label: text(context, "import_preview_field_title", "title"), value: preview.title },`
- `import_preview_image_missing`
  - `studio/app/frontend/js/catalogue-moment-import.js:129` `: text(context, "import_preview_image_missing", "no source image found; media generatio...`
- `import_preview_image_present`
  - `studio/app/frontend/js/catalogue-moment-import.js:128` `? text(context, "import_preview_image_present", "source image found")`
- `import_preview_missing_value`
  - `studio/app/frontend/js/catalogue-moment-import.js:106` `missingText: text(context, "import_preview_missing_value", "none")`
  - `studio/app/frontend/js/catalogue-moment-import.js:144` `<span class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(normalize...`
- `import_preview_status_failed`
  - `studio/app/frontend/js/catalogue-moment-import.js:321` `setTextWithState(context, state.importStatusNode, `${text(context, "import_preview_stat...`
- `import_preview_status_invalid`
  - `studio/app/frontend/js/catalogue-moment-import.js:315` `setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_...`
  - `studio/app/frontend/js/catalogue-moment-import.js:336` `setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_...`
- `import_preview_status_loading`
  - `studio/app/frontend/js/catalogue-moment-import.js:300` `setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_...`
- `import_preview_status_ready`
  - `studio/app/frontend/js/catalogue-moment-import.js:193` `<p class="tagStudioForm__meta">${escapeHtml(text(context, "import_preview_status_ready"...`
  - `studio/app/frontend/js/catalogue-moment-import.js:313` `setTextWithState(context, state.importStatusNode, text(context, "import_preview_status_...`
- `import_result_missing_preview`
  - `studio/app/frontend/js/catalogue-moment-import.js:332` `setTextWithState(context, state.importStatusNode, text(context, "import_result_missing_...`
- `import_result_success`
  - `studio/app/frontend/js/catalogue-moment-import.js:370` `text(context, "import_result_success", "Imported draft moment {moment_id}.", { moment_i...`
- `import_save_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-moment-editor.js:471` `setTextWithState(state.importStatusNode, t(state, "import_save_mode_unavailable_hint", ...`
- `import_source_result_summary`
  - `studio/app/frontend/js/catalogue-moment-import.js:175` `\|\| text(context, "import_source_result_summary", "Import writes draft prose and metadat...`
- `import_source_summary`
  - `studio/app/frontend/js/catalogue-moment-import.js:242` `state.importSourceSummaryNode.textContent = text(context, "import_source_summary", "Mom...`
- `import_status_failed`
  - `studio/app/frontend/js/catalogue-moment-import.js:378` `setTextWithState(context, state.importStatusNode, `${text(context, "import_status_faile...`
- `import_status_running`
  - `studio/app/frontend/js/catalogue-moment-import.js:342` `setTextWithState(context, state.importStatusNode, text(context, "import_status_running"...`
- `import_status_success`
  - `studio/app/frontend/js/catalogue-moment-import.js:366` `setTextWithState(context, state.statusNode, text(context, "import_status_success", "Mom...`
- `load_failed_error`
  - `studio/app/frontend/js/catalogue-moment-editor.js:503` `emptyNode.textContent = t(state, "load_failed_error", "Failed to load catalogue source ...`
- `media_refresh_button`
  - `studio/app/frontend/js/catalogue-moment-sections.js:71` `${mediaAction ? `<div class="catalogueReadiness__actions"><button type="button" class="...`
- `media_refresh_result_success`
  - `studio/app/frontend/js/catalogue-moment-actions.js:389` `setTextWithState(context, state.resultNode, t(state, context, "media_refresh_result_suc...`
- `media_refresh_save_first`
  - `studio/app/frontend/js/catalogue-moment-sections.js:60` `? (mediaAction ? text(options, "media_refresh_save_first", "Save source changes before ...`
- `media_refresh_status_blocked`
  - `studio/app/frontend/js/catalogue-moment-actions.js:384` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_blo...`
- `media_refresh_status_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:391` `setTextWithState(context, state.statusNode, `${t(state, context, "media_refresh_status_...`
- `media_refresh_status_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:372` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_run...`
- `media_refresh_status_success`
  - `studio/app/frontend/js/catalogue-moment-actions.js:388` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_suc...`
- `missing_moment_param`
  - `studio/app/frontend/js/catalogue-moment-editor.js:116` `state.emptyNode.textContent = t(state, "missing_moment_param", "Search for a moment by ...`
  - `studio/app/frontend/js/catalogue-moment-editor.js:117` `setTextWithState(state.statusNode, t(state, "missing_moment_param", "Search for a momen...`
- `new_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:450` `state.newButton.textContent = t(state, "new_button", "New");`
- `open_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:449` `state.openButton.textContent = t(state, "open_button", "Open");`
- `prose_import_button`
  - `studio/app/frontend/js/catalogue-moment-sections.js:70` `${proseAction ? `<div class="catalogueReadiness__actions"><button type="button" class="...`
- `prose_import_confirm_button`
  - `studio/app/frontend/js/catalogue-moment-actions.js:428` `primaryLabel: t(state, context, "prose_import_confirm_button", "Overwrite"),`
- `prose_import_confirm_overwrite`
  - `studio/app/frontend/js/catalogue-moment-actions.js:424` `"prose_import_confirm_overwrite",`
- `prose_import_confirm_title`
  - `studio/app/frontend/js/catalogue-moment-actions.js:420` `title: t(state, context, "prose_import_confirm_title", "Confirm prose overwrite"),`
- `prose_import_overwrite_cancelled`
  - `studio/app/frontend/js/catalogue-moment-actions.js:433` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_overwrite_c...`
- `prose_import_preview_invalid`
  - `studio/app/frontend/js/catalogue-moment-actions.js:414` `throw new Error(errors \|\| t(state, context, "prose_import_preview_invalid", "Staged pro...`
- `prose_import_preview_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:406` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_preview_run...`
- `prose_import_result_success`
  - `studio/app/frontend/js/catalogue-moment-actions.js:168` `text: t(state, context, "prose_import_result_success", "Prose imported to {target_path}...`
- `prose_import_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:440` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_running", "...`
- `prose_import_status_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:451` `setTextWithState(context, state.statusNode, `${t(state, context, "prose_import_status_f...`
- `prose_import_status_success`
  - `studio/app/frontend/js/catalogue-moment-actions.js:177` `text: t(state, context, "prose_import_status_success", "Prose import completed."),`
- `publication_preview_publish_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:278` `? t(state, context, "publication_preview_publish_running", "Preparing publish preview...")`
- `publication_preview_unpublish_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:279` `: t(state, context, "publication_preview_unpublish_running", "Preparing unpublish previ...`
- `publication_publish_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:327` `? t(state, context, "publication_publish_running", "Publishing moment...")`
- `publication_result_public_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:133` `text: t(state, context, "publication_result_public_failed", "Source status changed, but...`
- `publication_result_published`
  - `studio/app/frontend/js/catalogue-moment-actions.js:137` `text: t(state, context, "publication_result_published", "Moment is published and public...`
- `publication_result_unpublished`
  - `studio/app/frontend/js/catalogue-moment-actions.js:141` `text: t(state, context, "publication_result_unpublished", "Moment is draft again and pu...`
- `publication_save_first`
  - `studio/app/frontend/js/catalogue-moment-actions.js:261` `setTextWithState(context, state.statusNode, t(state, context, "publication_save_first",...`
- `publication_status_blocked`
  - `studio/app/frontend/js/catalogue-moment-actions.js:294` `fallback: t(state, context, "publication_status_blocked", "Publication change is blocke...`
- `publication_status_cancelled`
  - `studio/app/frontend/js/catalogue-moment-actions.js:316` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_cance...`
- `publication_status_conflict`
  - `studio/app/frontend/js/catalogue-moment-actions.js:354` `? t(state, context, "publication_status_conflict", "Source record changed since this pa...`
- `publication_status_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:355` `: `${t(state, context, "publication_status_failed", "Publication change failed.")} ${no...`
- `publication_status_invalid`
  - `studio/app/frontend/js/catalogue-moment-actions.js:257` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_inval...`
- `publication_status_public_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:147` `text: `${t(state, context, "publication_status_public_failed", "Publication state chang...`
- `publication_status_published`
  - `studio/app/frontend/js/catalogue-moment-actions.js:151` `text: t(state, context, "publication_status_published", "Moment published."),`
- `publication_status_unpublished`
  - `studio/app/frontend/js/catalogue-moment-actions.js:155` `text: t(state, context, "publication_status_unpublished", "Moment unpublished."),`
- `publication_status_validation_error`
  - `studio/app/frontend/js/catalogue-moment-actions.js:267` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_valid...`
- `publication_unpublish_confirm_button`
  - `studio/app/frontend/js/catalogue-moment-actions.js:311` `primaryLabel: t(state, context, "publication_unpublish_confirm_button", "Unpublish"),`
- `publication_unpublish_confirm_title`
  - `studio/app/frontend/js/catalogue-moment-actions.js:309` `title: t(state, context, "publication_unpublish_confirm_title", "Confirm unpublish"),`
- `publication_unpublish_running`
  - `studio/app/frontend/js/catalogue-moment-actions.js:328` `: t(state, context, "publication_unpublish_running", "Unpublishing moment..."),`
- `publish_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:269` `: t(state, "publish_button", "Publish");`
  - `studio/app/frontend/js/catalogue-moment-editor.js:452` `state.publicationButton.textContent = t(state, "publish_button", "Publish");`
- `readiness_action_busy`
  - `studio/app/frontend/js/catalogue-moment-sections.js:61` `: text(options, "readiness_action_busy", "Wait for the current save or public update to...`
- `save_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:451` `state.saveButton.textContent = t(state, "save_button", "Save");`
- `save_mode_local_server`
  - `studio/app/frontend/js/studio-save-utils.js:7` `? studioText(config, "save_mode_local_server", "Local server")`
- `save_mode_offline`
  - `studio/app/frontend/js/studio-save-utils.js:8` `: studioText(config, "save_mode_offline", "Offline session");`
- `save_mode_template`
  - `studio/app/frontend/js/studio-save-utils.js:9` `return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });`
- `save_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-moment-editor.js:326` `setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalo...`
  - `studio/app/frontend/js/catalogue-moment-editor.js:470` `setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalo...`
- `save_result_success`
  - `studio/app/frontend/js/catalogue-moment-actions.js:100` `text: t(state, context, "save_result_success", "Source saved at {saved_at}.", savedAt),`
  - `studio/app/frontend/js/catalogue-moment-actions.js:104` `text: t(state, context, "save_result_success", "Source saved at {saved_at}.", savedAt),`
- `save_result_success_applied`
  - `studio/app/frontend/js/catalogue-moment-actions.js:88` `text: t(state, context, "save_result_success_applied", "Saved source changes and update...`
- `save_result_success_partial`
  - `studio/app/frontend/js/catalogue-moment-actions.js:92` `text: t(state, context, "save_result_success_partial", "Source changes were saved at {s...`
- `save_result_success_unpublished`
  - `studio/app/frontend/js/catalogue-moment-actions.js:96` `text: t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}....`
- `save_result_unchanged`
  - `studio/app/frontend/js/catalogue-moment-actions.js:212` `setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", ...`
- `save_status_conflict`
  - `studio/app/frontend/js/catalogue-moment-actions.js:243` `setTextWithState(context, state.statusNode, t(state, context, "save_status_conflict", "...`
- `save_status_failed`
  - `studio/app/frontend/js/catalogue-moment-actions.js:245` `setTextWithState(context, state.statusNode, `${t(state, context, "save_status_failed", ...`
- `save_status_loaded`
  - `studio/app/frontend/js/catalogue-moment-editor.js:354` `setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded moment {momen...`
- `save_status_no_changes`
  - `studio/app/frontend/js/catalogue-moment-actions.js:211` `setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes",...`
- `save_status_saving`
  - `studio/app/frontend/js/catalogue-moment-actions.js:222` `applyBuild ? t(state, context, "save_status_saving_and_updating", "Saving source record...`
- `save_status_saving_and_updating`
  - `studio/app/frontend/js/catalogue-moment-actions.js:222` `applyBuild ? t(state, context, "save_status_saving_and_updating", "Saving source record...`
- `save_status_validation_error`
  - `studio/app/frontend/js/catalogue-moment-actions.js:207` `setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_e...`
- `search_empty`
  - `studio/app/frontend/js/catalogue-moment-selection.js:61` `text(context, "search_empty", "Enter a moment id or title."),`
- `search_no_match`
  - `studio/app/frontend/js/catalogue-moment-selection.js:43` `state.popupListNode.innerHTML = `<p class="tagStudio__popupEmpty">${escapeHtml(text(con...`
- `search_placeholder`
  - `studio/app/frontend/js/catalogue-moment-editor.js:448` `state.searchNode.placeholder = t(state, "search_placeholder", "find moment by id or tit...`
- `side_heading_current`
  - `studio/app/frontend/js/catalogue-moment-editor.js:195` `state.sideHeadingNode.textContent = t(state, "side_heading_current", "current record");`
- `side_heading_import`
  - `studio/app/frontend/js/catalogue-moment-editor.js:231` `state.sideHeadingNode.textContent = t(state, "side_heading_import", "import preview");`
- `summary_public_link`
  - `studio/app/frontend/js/catalogue-moment-sections.js:95` `<p class="tagStudioForm__impact"><a href="${escapeHtml(publicUrl)}">${escapeHtml(text(o...`
- `summary_rebuild_current`
  - `studio/app/frontend/js/catalogue-moment-sections.js:99` `: text(options, "summary_rebuild_current", "source and public moment are aligned in thi...`
- `summary_rebuild_needed`
  - `studio/app/frontend/js/catalogue-moment-sections.js:98` `? text(options, "summary_rebuild_needed", "public update failed in this session")`
- `unknown_moment_error`
  - `studio/app/frontend/js/catalogue-moment-editor.js:340` `setTextWithState(state.statusNode, t(state, "unknown_moment_error", "Unknown moment id:...`
- `unpublish_button`
  - `studio/app/frontend/js/catalogue-moment-editor.js:268` `? t(state, "unpublish_button", "Unpublish")`
- `unpublish_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` `\|\| lookupText(options, "unpublish_confirm_default", options.defaultText \|\| "Unpublish t...`
- `unpublish_confirm_dirty_note`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` `? lookupText(options, "unpublish_confirm_dirty_note", "Unsaved form changes will be dis...`

### `catalogue_series_editor`

- `build_preview_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:245` ``${t(state, context, "build_preview_failed", "Build preview unavailable.")} ${normalize...`
- `build_preview_search_no`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` `: lookupText(options, "build_preview_search_no", "no");`
- `build_preview_search_yes`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` `? lookupText(options, "build_preview_search_yes", "yes")`
- `build_preview_template`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64` `"build_preview_template",`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` `"build_preview_template",`
- `build_result_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:149` `text: t(state, context, "build_result_success", "Public catalogue updated at {completed...`
- `build_status_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:101` `const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")...`
  - `studio/app/frontend/js/catalogue-series-actions.js:489` `setTextWithState(context, state.statusNode, `${t(state, context, "build_status_failed",...`
- `build_status_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:476` `setTextWithState(context, state.statusNode, t(state, context, "build_status_running", "...`
- `build_status_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:128` `text: t(state, context, "build_status_success", "Site update completed."),`
  - `studio/app/frontend/js/catalogue-series-actions.js:155` `text: t(state, context, "build_status_success", "Site update completed."),`
- `confirm_cancel_button`
  - `studio/app/frontend/js/catalogue-series-actions.js:291` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-series-actions.js:559` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-series-actions.js:649` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
- `context_loaded`
  - `studio/app/frontend/js/catalogue-series-editor.js:264` `setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata...`
- `create_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:203` `? t(state, "create_button", "Create")`
- `create_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-series-editor.js:195` `firstError \|\| (state.serverAvailable ? "" : t(state, "create_mode_unavailable_hint", "L...`
- `create_result_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:458` `setTextWithState(context, state.resultNode, t(state, context, "create_result_success", ...`
- `create_status_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:461` `setTextWithState(context, state.statusNode, `${t(state, context, "create_status_failed"...`
- `create_status_saving`
  - `studio/app/frontend/js/catalogue-series-actions.js:433` `setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "...`
- `create_status_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:459` `setTextWithState(context, state.statusNode, t(state, context, "create_status_success", ...`
- `create_status_validation_error`
  - `studio/app/frontend/js/catalogue-series-actions.js:424` `seriesIdError \|\| t(state, context, "create_status_validation_error", "Fix validation er...`
- `delete_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:443` `deleteButton.textContent = t(state, "delete_button", "Delete");`
- `delete_confirm_button`
  - `studio/app/frontend/js/catalogue-series-actions.js:648` `primaryLabel: t(state, context, "delete_confirm_button", "Delete"),`
- `delete_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:148` `\|\| lookupText(options, "delete_confirm_default", options.defaultText \|\| "Delete this so...`
- `delete_confirm_title`
  - `studio/app/frontend/js/catalogue-series-actions.js:646` `title: t(state, context, "delete_confirm_title", "Confirm delete"),`
- `delete_status_blocked`
  - `studio/app/frontend/js/catalogue-series-actions.js:631` `fallback: t(state, context, "delete_status_blocked", "Delete is blocked.")`
- `delete_status_cancelled`
  - `studio/app/frontend/js/catalogue-series-actions.js:653` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_cancelled"...`
- `delete_status_conflict`
  - `studio/app/frontend/js/catalogue-series-actions.js:665` `? t(state, context, "delete_status_conflict", "Source record changed since this page lo...`
- `delete_status_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:666` `: `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeTex...`
- `delete_status_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:618` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", ...`
  - `studio/app/frontend/js/catalogue-series-actions.js:660` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", ...`
- `dirty_warning`
  - `studio/app/frontend/js/catalogue-series-editor.js:189` `message: t(state, "dirty_warning", "Unsaved source changes.")`
- `field_duplicate_series_id`
  - `studio/app/frontend/js/catalogue-series-fields.js:155` `errors.set("series_id", t("field_duplicate_series_id", "Series id already exists."));`
- `field_invalid_primary_work`
  - `studio/app/frontend/js/catalogue-series-fields.js:203` `errors.set("primary_work_id", t("field_invalid_primary_work", "Primary work must be a c...`
- `field_invalid_series_type`
  - `studio/app/frontend/js/catalogue-series-fields.js:166` `errors.set("series_type", t("field_invalid_series_type", "Choose a listed series type."));`
- `field_invalid_status`
  - `studio/app/frontend/js/catalogue-series-fields.js:192` `errors.set("status", t("field_invalid_status", "Use blank, draft, or published."));`
- `field_invalid_year`
  - `studio/app/frontend/js/catalogue-series-fields.js:178` `errors.set("year", t("field_invalid_year", "Use a whole year."));`
- `field_required_primary_work_publish`
  - `studio/app/frontend/js/catalogue-series-fields.js:201` `errors.set("primary_work_id", t("field_required_primary_work_publish", "Published serie...`
- `field_required_series_id`
  - `studio/app/frontend/js/catalogue-series-fields.js:153` `errors.set("series_id", t("field_required_series_id", "Enter a series id."));`
- `field_required_series_type`
  - `studio/app/frontend/js/catalogue-series-fields.js:164` `errors.set("series_type", t("field_required_series_type", "Choose a series type."));`
- `field_required_title`
  - `studio/app/frontend/js/catalogue-series-fields.js:159` `errors.set("title", t("field_required_title", "Enter a title."));`
- `field_required_year`
  - `studio/app/frontend/js/catalogue-series-fields.js:176` `errors.set("year", t("field_required_year", "Enter a year."));`
- `field_required_year_display`
  - `studio/app/frontend/js/catalogue-series-fields.js:182` `errors.set("year_display", t("field_required_year_display", "Enter a year display."));`
- `members_action_primary`
  - `studio/app/frontend/js/catalogue-series-membership.js:156` `${isPrimary ? "" : `<button type="button" class="tagStudio__button" data-member-primary...`
- `members_action_remove`
  - `studio/app/frontend/js/catalogue-series-membership.js:157` `<button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-me...`
- `members_add_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:447` `memberAddButton.textContent = t(state, "members_add_button", "Add");`
- `members_add_exists`
  - `studio/app/frontend/js/catalogue-series-membership.js:220` `setTextWithState(options, state.membersStatusNode, text(options, "members_add_exists", ...`
- `members_add_missing`
  - `studio/app/frontend/js/catalogue-series-membership.js:210` `setTextWithState(options, state.membersStatusNode, text(options, "members_add_missing",...`
- `members_add_placeholder`
  - `studio/app/frontend/js/catalogue-series-editor.js:446` `memberAddNode.placeholder = t(state, "members_add_placeholder", "add work by id");`
- `members_add_unknown`
  - `studio/app/frontend/js/catalogue-series-membership.js:215` `setTextWithState(options, state.membersStatusNode, text(options, "members_add_unknown",...`
- `members_empty`
  - `studio/app/frontend/js/catalogue-series-membership.js:189` `blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(text(options, "members_empty",...`
- `members_heading`
  - `studio/app/frontend/js/catalogue-series-editor.js:444` `membersHeadingNode.textContent = t(state, "members_heading", "member works");`
- `members_more_count`
  - `studio/app/frontend/js/catalogue-series-membership.js:176` `? text(options, "members_more_count", "showing {visible} of {total}", { visible: String...`
- `members_position`
  - `studio/app/frontend/js/catalogue-series-membership.js:146` `const positionText = text(options, "members_position", "position {position}", { positio...`
- `members_primary_badge`
  - `studio/app/frontend/js/catalogue-series-membership.js:153` `${isPrimary ? `<span class="tagStudioForm__meta">${escapeHtml(text(options, "members_pr...`
- `members_remove_blocked`
  - `studio/app/frontend/js/catalogue-series-membership.js:245` `setTextWithState(options, state.membersStatusNode, text(options, "members_remove_blocke...`
- `members_search_no_match`
  - `studio/app/frontend/js/catalogue-series-membership.js:184` `blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(text(options, "members_search_...`
- `members_search_placeholder`
  - `studio/app/frontend/js/catalogue-series-editor.js:445` `memberSearchNode.placeholder = t(state, "members_search_placeholder", "find member work...`
- `missing_series_param`
  - `studio/app/frontend/js/catalogue-series-editor.js:333` `setTextWithState(state.contextNode, t(state, "missing_series_param", "Search for a seri...`
- `new_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:440` `newButton.textContent = t(state, "new_button", "New");`
- `new_context_loaded`
  - `studio/app/frontend/js/catalogue-series-editor.js:301` `setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft se...`
- `new_meta`
  - `studio/app/frontend/js/catalogue-series-sections.js:95` `state.metaNode.textContent = text(state, options, "new_meta", "draft source record");`
- `new_runtime_state`
  - `studio/app/frontend/js/catalogue-series-sections.js:110` `state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "Public ...`
- `new_series_id_label`
  - `studio/app/frontend/js/catalogue-series-editor.js:91` `state.searchNode.setAttribute("aria-label", t(state, "new_series_id_label", "New series...`
- `new_series_id_placeholder`
  - `studio/app/frontend/js/catalogue-series-editor.js:90` `state.searchNode.placeholder = t(state, "new_series_id_placeholder", "new series id");`
- `new_summary_next`
  - `studio/app/frontend/js/catalogue-series-sections.js:107` `<div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state...`
- `new_summary_next_label`
  - `studio/app/frontend/js/catalogue-series-sections.js:106` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_next_...`
- `new_summary_series_id_label`
  - `studio/app/frontend/js/catalogue-series-sections.js:98` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_serie...`
- `new_summary_status`
  - `studio/app/frontend/js/catalogue-series-sections.js:103` `<div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state...`
- `new_summary_status_label`
  - `studio/app/frontend/js/catalogue-series-sections.js:102` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_statu...`
- `open_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:439` `openButton.textContent = t(state, "open_button", "Open");`
- `prose_import_button`
  - `studio/app/frontend/js/catalogue-series-sections.js:77` `const proseActionLabel = text(state, options, "prose_import_button", "Import staged pro...`
- `prose_import_confirm_button`
  - `studio/app/frontend/js/catalogue-series-actions.js:290` `primaryLabel: t(state, context, "prose_import_confirm_button", "Overwrite"),`
- `prose_import_confirm_overwrite`
  - `studio/app/frontend/js/catalogue-series-actions.js:280` `"prose_import_confirm_overwrite",`
- `prose_import_confirm_title`
  - `studio/app/frontend/js/catalogue-series-actions.js:288` `title: t(state, context, "prose_import_confirm_title", "Confirm prose overwrite"),`
- `prose_import_overwrite_cancelled`
  - `studio/app/frontend/js/catalogue-series-actions.js:295` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_overwrite_c...`
- `prose_import_preview_invalid`
  - `studio/app/frontend/js/catalogue-series-actions.js:271` `throw new Error(errors \|\| t(state, context, "prose_import_preview_invalid", "Staged pro...`
- `prose_import_preview_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:262` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_preview_run...`
- `prose_import_result_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:206` `text: t(state, context, "prose_import_result_success", "Prose imported to {target_path}...`
- `prose_import_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:302` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_running", "...`
- `prose_import_status_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:314` ``${t(state, context, "prose_import_status_failed", "Prose import failed.")} ${normalize...`
- `prose_import_status_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:215` `text: t(state, context, "prose_import_status_success", "Prose import completed."),`
- `publication_preview_publish_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:524` `? t(state, context, "publication_preview_publish_running", "Preparing publish preview…")`
- `publication_preview_unpublish_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:525` `: t(state, context, "publication_preview_unpublish_running", "Preparing unpublish previ...`
- `publication_publish_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:574` `? t(state, context, "publication_publish_running", "Publishing series…")`
- `publication_result_public_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:170` `text: t(state, context, "publication_result_public_failed", "Source status changed, but...`
- `publication_result_published`
  - `studio/app/frontend/js/catalogue-series-actions.js:174` `text: t(state, context, "publication_result_published", "Series and attached draft work...`
- `publication_result_unpublished`
  - `studio/app/frontend/js/catalogue-series-actions.js:178` `text: t(state, context, "publication_result_unpublished", "Series is draft again and pu...`
- `publication_save_first`
  - `studio/app/frontend/js/catalogue-series-actions.js:504` `setTextWithState(context, state.statusNode, t(state, context, "publication_save_first",...`
- `publication_status_blocked`
  - `studio/app/frontend/js/catalogue-series-actions.js:540` `fallback: t(state, context, "publication_status_blocked", "Publication change is blocke...`
- `publication_status_cancelled`
  - `studio/app/frontend/js/catalogue-series-actions.js:563` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_cance...`
- `publication_status_conflict`
  - `studio/app/frontend/js/catalogue-series-actions.js:605` `? t(state, context, "publication_status_conflict", "Source record changed since this pa...`
- `publication_status_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:606` `: `${t(state, context, "publication_status_failed", "Publication change failed.")} ${no...`
- `publication_status_invalid`
  - `studio/app/frontend/js/catalogue-series-actions.js:500` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_inval...`
- `publication_status_public_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:184` `text: `${t(state, context, "publication_status_public_failed", "Publication state chang...`
- `publication_status_published`
  - `studio/app/frontend/js/catalogue-series-actions.js:188` `text: t(state, context, "publication_status_published", "Series published."),`
- `publication_status_unpublished`
  - `studio/app/frontend/js/catalogue-series-actions.js:192` `text: t(state, context, "publication_status_unpublished", "Series unpublished."),`
- `publication_status_validation_error`
  - `studio/app/frontend/js/catalogue-series-actions.js:512` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_valid...`
- `publication_unpublish_confirm_button`
  - `studio/app/frontend/js/catalogue-series-actions.js:558` `primaryLabel: t(state, context, "publication_unpublish_confirm_button", "Unpublish"),`
- `publication_unpublish_confirm_title`
  - `studio/app/frontend/js/catalogue-series-actions.js:556` `title: t(state, context, "publication_unpublish_confirm_title", "Confirm unpublish"),`
- `publication_unpublish_running`
  - `studio/app/frontend/js/catalogue-series-actions.js:575` `: t(state, context, "publication_unpublish_running", "Unpublishing series…")`
- `publish_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:150` `: t(state, "publish_button", "Publish");`
  - `studio/app/frontend/js/catalogue-series-editor.js:442` `publicationButton.textContent = t(state, "publish_button", "Publish");`
- `save_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:204` `: t(state, "save_button", "Save");`
  - `studio/app/frontend/js/catalogue-series-editor.js:441` `saveButton.textContent = t(state, "save_button", "Save");`
- `save_mode_local_server`
  - `studio/app/frontend/js/studio-save-utils.js:7` `? studioText(config, "save_mode_local_server", "Local server")`
- `save_mode_offline`
  - `studio/app/frontend/js/studio-save-utils.js:8` `: studioText(config, "save_mode_offline", "Offline session");`
- `save_mode_template`
  - `studio/app/frontend/js/studio-save-utils.js:9` `return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });`
- `save_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-series-editor.js:451` `setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue se...`
- `save_result_success`
  - `studio/app/frontend/js/catalogue-series-actions.js:119` `text: t(state, context, "save_result_success", "Source saved at {saved_at}. Public cata...`
- `save_result_success_applied`
  - `studio/app/frontend/js/catalogue-series-actions.js:107` `text: t(state, context, "save_result_success_applied", "Saved source changes and update...`
- `save_result_success_partial`
  - `studio/app/frontend/js/catalogue-series-actions.js:111` `text: t(state, context, "save_result_success_partial", "Source changes were saved at {s...`
- `save_result_unchanged`
  - `studio/app/frontend/js/catalogue-series-actions.js:123` `text: t(state, context, "save_result_unchanged", "Source already matches the current fo...`
  - `studio/app/frontend/js/catalogue-series-actions.js:344` `setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", ...`
- `save_status_conflict`
  - `studio/app/frontend/js/catalogue-series-actions.js:405` `? t(state, context, "save_status_conflict", "Source record changed since this page load...`
- `save_status_failed`
  - `studio/app/frontend/js/catalogue-series-actions.js:406` `: `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(er...`
- `save_status_loaded`
  - `studio/app/frontend/js/catalogue-series-actions.js:136` `text: t(state, context, "save_status_loaded", "Loaded series {series_id}.", loadedSeries),`
  - `studio/app/frontend/js/catalogue-series-editor.js:199` `setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {serie...`
  - `studio/app/frontend/js/catalogue-series-editor.js:265` `setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded series {serie...`
- `save_status_no_changes`
  - `studio/app/frontend/js/catalogue-series-actions.js:343` `setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes",...`
- `save_status_saving`
  - `studio/app/frontend/js/catalogue-series-actions.js:356` `: t(state, context, "save_status_saving", "Saving source record…")`
- `save_status_saving_and_updating`
  - `studio/app/frontend/js/catalogue-series-actions.js:355` `? t(state, context, "save_status_saving_and_updating", "Saving source record and updati...`
- `save_status_validation_error`
  - `studio/app/frontend/js/catalogue-series-actions.js:338` `setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_e...`
- `search_empty`
  - `studio/app/frontend/js/catalogue-series-selection.js:94` `renderSeriesSearchMatches(state, [], text(context, "search_empty", "Enter a series titl...`
- `search_no_match`
  - `studio/app/frontend/js/catalogue-series-selection.js:85` `renderSeriesSearchMatches(state, [], text(context, "search_no_match", "No matching seri...`
- `search_placeholder`
  - `studio/app/frontend/js/catalogue-series-editor.js:85` `state.searchNode.placeholder = t(state, "search_placeholder", "find series by title");`
  - `studio/app/frontend/js/catalogue-series-editor.js:438` `searchNode.placeholder = t(state, "search_placeholder", "find series by title");`
- `summary_member_count`
  - `studio/app/frontend/js/catalogue-series-sections.js:128` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_member_co...`
- `summary_public_link`
  - `studio/app/frontend/js/catalogue-series-sections.js:122` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_public_li...`
- `summary_rebuild_current`
  - `studio/app/frontend/js/catalogue-series-sections.js:134` `: text(state, options, "summary_rebuild_current", "source and public catalogue are alig...`
- `summary_rebuild_needed`
  - `studio/app/frontend/js/catalogue-series-sections.js:133` `? text(state, options, "summary_rebuild_needed", "source saved; site update pending")`
- `unknown_series_error`
  - `studio/app/frontend/js/catalogue-series-selection.js:101` `else renderSeriesSearchMatches(state, [], text(context, "unknown_series_error", "Unknow...`
- `unpublish_button`
  - `studio/app/frontend/js/catalogue-series-editor.js:149` `? t(state, "unpublish_button", "Unpublish")`
- `unpublish_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` `\|\| lookupText(options, "unpublish_confirm_default", options.defaultText \|\| "Unpublish t...`
- `unpublish_confirm_dirty_note`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` `? lookupText(options, "unpublish_confirm_dirty_note", "Unsaved form changes will be dis...`

### `catalogue_status`

- `empty_state`
  - `studio/app/frontend/js/catalogue-status.js:177` `state.emptyNode.textContent = getStudioText(state.config, "catalogue_status.empty_state...`
- `load_failed_error`
  - `studio/app/frontend/js/catalogue-status.js:291` `loadingNode.textContent = getStudioText(config, "catalogue_status.load_failed_error", "...`
- `meta_summary`
  - `studio/app/frontend/js/catalogue-status.js:174` `: getStudioText(state.config, "catalogue_status.meta_summary", "{count} draft {family} ...`
- `meta_summary_one`
  - `studio/app/frontend/js/catalogue-status.js:173` `? getStudioText(state.config, "catalogue_status.meta_summary_one", "1 draft {family} re...`
- `server_unavailable_hint`
  - `studio/app/frontend/js/catalogue-status.js:230` `loadingNode.textContent = getStudioText(config, "catalogue_status.server_unavailable_hi...`

### `catalogue_work_detail_editor`

- `build_preview_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:368` ``${t(state, context, "build_preview_failed", "Build preview unavailable.")} ${normalize...`
- `build_preview_search_no`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` `: lookupText(options, "build_preview_search_no", "no");`
- `build_preview_search_yes`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` `? lookupText(options, "build_preview_search_yes", "yes")`
- `build_preview_template`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64` `"build_preview_template",`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` `"build_preview_template",`
- `build_preview_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:346` `setTextWithState(context, state.buildImpactNode, t(state, context, "build_preview_unpub...`
- `build_result_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:269` `text: t(state, context, "build_result_success", "Parent work output updated at {complet...`
- `build_status_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:166` `const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")...`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:214` `const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")...`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:562` ``${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(err...`
- `build_status_running`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:520` `setTextWithState(context, state.statusNode, t(state, context, "build_status_running", "...`
- `build_status_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:193` `text: t(state, context, "build_status_success", "Site update completed."),`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:241` `text: t(state, context, "build_status_success", "Site update completed."),`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:275` `text: t(state, context, "build_status_success", "Site update completed."),`
- `bulk_save_result_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:232` `text: t(state, context, "bulk_save_result_success", "Saved {count} detail records at {s...`
- `bulk_save_result_success_applied`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:220` `text: t(state, context, "bulk_save_result_success_applied", "Saved {count} detail recor...`
- `bulk_save_result_success_partial`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:224` `text: t(state, context, "bulk_save_result_success_partial", "Saved {count} detail recor...`
- `bulk_save_result_success_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:228` `text: t(state, context, "bulk_save_result_success_unpublished", "Saved {count} draft de...`
- `confirm_cancel_button`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:634` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:762` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
- `context_loaded`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:195` `setTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata...`
- `create_button`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:331` `? t(state, "create_button", "Create")`
- `create_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:316` `firstError \|\| (state.serverAvailable ? "" : t(state, "create_mode_unavailable_hint", "L...`
- `create_result_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:501` `setTextWithState(context, state.resultNode, t(state, context, "create_result_success", ...`
- `create_status_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:504` `const message = `${t(state, context, "create_status_failed", "Draft detail create faile...`
- `create_status_saving`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:481` `setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "...`
- `create_status_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:502` `setTextWithState(context, state.statusNode, t(state, context, "create_status_success", ...`
- `create_status_validation_error`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:472` `workIdError \|\| t(state, context, "create_status_validation_error", "Fix validation erro...`
- `delete_button`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:492` `deleteButton.textContent = t(state, "delete_button", "Delete");`
- `delete_confirm_button`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:761` `primaryLabel: t(state, context, "delete_confirm_button", "Delete"),`
- `delete_confirm_title`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:759` `title: t(state, context, "delete_confirm_title", "Confirm delete"),`
- `dirty_warning`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:310` `message: t(state, "dirty_warning", "Unsaved source changes.")`
- `field_duplicate_detail_id`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:205` `errors.set("detail_id", t("field_duplicate_detail_id", "Detail id already exists for th...`
- `field_invalid_sort_order`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:160` `errors.set("sort_order", t(state, "field_invalid_sort_order", "Use a whole number or le...`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:216` `errors.set("sort_order", t("field_invalid_sort_order", "Use a whole number or leave bla...`
- `field_invalid_status`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:172` `errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));`
- `field_parent_work_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:198` `errors.set("work_id", t("field_parent_work_unpublished", "Publish the parent work befor...`
- `field_required_detail_id`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:203` `errors.set("detail_id", t("field_required_detail_id", "Enter a detail id."));`
- `field_required_section_title`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:164` `errors.set("section_title", t(state, "field_required_section_title", "Enter a section t...`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:167` `errors.set("section_title", t(state, "field_required_section_title", "Enter a section t...`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:212` `errors.set("section_title", t("field_required_section_title", "Enter a section title."));`
- `field_required_title`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:209` `errors.set("title", t("field_required_title", "Enter a title."));`
- `field_required_work_id`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:194` `errors.set("work_id", t("field_required_work_id", "Enter a parent work id."));`
- `field_unknown_work_id`
  - `studio/app/frontend/js/catalogue-work-detail-fields.js:196` `errors.set("work_id", t("field_unknown_work_id", "Unknown work id: {work_id}.", { work_...`
- `media_refresh_button`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:135` `const mediaActionLabel = text(state, options, "media_refresh_button", "Refresh media");`
- `media_refresh_result_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:713` `setTextWithState(context, state.resultNode, t(state, context, "media_refresh_result_suc...`
- `media_refresh_save_first`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:132` `? text(state, options, "media_refresh_save_first", "Save source changes before refreshi...`
- `media_refresh_status_blocked`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:708` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_blo...`
- `media_refresh_status_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:718` ``${t(state, context, "media_refresh_status_failed", "Media refresh failed.")} ${normali...`
- `media_refresh_status_running`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:696` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_run...`
- `media_refresh_status_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:712` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_suc...`
- `missing_detail_param`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:269` `context.setTextWithState(state.contextNode, text(context, "missing_detail_param", "Sear...`
- `new_context_loaded`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:238` `setTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft de...`
- `new_context_parent_missing`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:232` `setTextWithState(state.contextNode, t(state, "new_context_parent_missing", "Open new de...`
- `new_context_parent_unknown`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:234` `setTextWithState(state.contextNode, t(state, "new_context_parent_unknown", "Cannot crea...`
- `new_context_parent_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:236` `setTextWithState(state.contextNode, t(state, "new_context_parent_unpublished", "Publish...`
- `new_runtime_state`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:176` `state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "public ...`
- `new_summary_detail_id_label`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:164` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_detai...`
- `new_summary_next`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:173` `<div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state...`
- `new_summary_next_label`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:172` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_next_...`
- `new_summary_parent_label`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:158` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_paren...`
- `new_summary_status`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:169` `<div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state...`
- `new_summary_status_label`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:168` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_statu...`
- `open_button`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:489` `openButton.textContent = t(state, "open_button", "Open");`
- `publication_preview_publish_running`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:599` `? t(state, context, "publication_preview_publish_running", "Preparing publish preview…")`
- `publication_preview_unpublish_running`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:600` `: t(state, context, "publication_preview_unpublish_running", "Preparing unpublish previ...`
- `publication_publish_running`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:649` `? t(state, context, "publication_publish_running", "Publishing detail…")`
- `publication_result_public_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:290` `text: t(state, context, "publication_result_public_failed", "Source status changed, but...`
- `publication_result_published`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:294` `text: t(state, context, "publication_result_published", "Detail is published and parent...`
- `publication_result_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:298` `text: t(state, context, "publication_result_unpublished", "Detail is draft again and pu...`
- `publication_save_first`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:579` `setTextWithState(context, state.statusNode, t(state, context, "publication_save_first",...`
- `publication_status_blocked`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:615` `fallback: t(state, context, "publication_status_blocked", "Publication change is blocke...`
- `publication_status_cancelled`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:638` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_cance...`
- `publication_status_conflict`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:678` `? t(state, context, "publication_status_conflict", "Source record changed since this pa...`
- `publication_status_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:679` `: `${t(state, context, "publication_status_failed", "Publication change failed.")} ${no...`
- `publication_status_invalid`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:575` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_inval...`
- `publication_status_public_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:304` `text: `${t(state, context, "publication_status_public_failed", "Publication state chang...`
- `publication_status_published`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:308` `text: t(state, context, "publication_status_published", "Detail published."),`
- `publication_status_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:312` `text: t(state, context, "publication_status_unpublished", "Detail unpublished."),`
- `publication_status_validation_error`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:587` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_valid...`
- `publication_unpublish_confirm_button`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:633` `primaryLabel: t(state, context, "publication_unpublish_confirm_button", "Unpublish"),`
- `publication_unpublish_confirm_title`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:631` `title: t(state, context, "publication_unpublish_confirm_title", "Confirm unpublish"),`
- `publication_unpublish_running`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:650` `: t(state, context, "publication_unpublish_running", "Unpublishing detail…")`
- `publish_button`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:129` `: t(state, context, "publish_button", "Publish");`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:491` `publicationButton.textContent = t(state, "publish_button", "Publish");`
- `readiness_action_busy`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:133` `: text(state, options, "readiness_action_busy", "Wait for the current save or rebuild t...`
- `save_button`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:332` `: t(state, "save_button", "Save");`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:490` `saveButton.textContent = t(state, "save_button", "Save");`
- `save_mode_local_server`
  - `studio/app/frontend/js/studio-save-utils.js:7` `? studioText(config, "save_mode_local_server", "Local server")`
- `save_mode_offline`
  - `studio/app/frontend/js/studio-save-utils.js:8` `: studioText(config, "save_mode_offline", "Offline session");`
- `save_mode_template`
  - `studio/app/frontend/js/studio-save-utils.js:9` `return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });`
- `save_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:496` `setTextWithState(statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue se...`
- `save_result_success`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:184` `text: t(state, context, "save_result_success", "Source saved at {saved_at}. Parent-work...`
- `save_result_success_applied`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:172` `text: t(state, context, "save_result_success_applied", "Saved source changes and update...`
- `save_result_success_partial`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:176` `text: t(state, context, "save_result_success_partial", "Source changes were saved at {s...`
- `save_result_success_unpublished`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:180` `text: t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}....`
- `save_result_unchanged`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:188` `text: t(state, context, "save_result_unchanged", "Source already matches the current fo...`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:236` `text: t(state, context, "save_result_unchanged", "Source already matches the current fo...`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:396` `setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", ...`
- `save_status_conflict`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:454` `? t(state, context, "save_status_conflict", "Source record changed since this page load...`
- `save_status_failed`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:455` `: `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(er...`
- `save_status_loaded`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:201` `text: t(state, context, "save_status_loaded", "Loaded detail {detail_uid}.", loadedDeta...`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:196` `setTextWithState(state.statusNode, t(state, "save_status_loaded", "Loaded detail {detai...`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:324` `: t(state, "save_status_loaded", "Loaded detail {detail_uid}.", { detail_uid: state.cur...`
- `save_status_no_changes`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:395` `setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes",...`
- `save_status_saving`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:409` `: t(state, context, "save_status_saving", "Saving source record…")`
- `save_status_saving_and_updating`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:408` `? t(state, context, "save_status_saving_and_updating", "Saving source record and updati...`
- `save_status_validation_error`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:389` `setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_e...`
- `search_empty`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:150` `renderWorkDetailSearchMatches(state, [], normalizeText(error && error.message) \|\| text(...`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:155` `renderWorkDetailSearchMatches(state, [], text(context, "search_empty", "Enter a detail ...`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:192` `renderWorkDetailSearchMatches(state, [], text(context, "search_empty", "Enter a detail ...`
- `search_no_match`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:139` `renderWorkDetailSearchMatches(state, [], text(context, "search_no_match", "No matching ...`
- `search_placeholder`
  - `studio/app/frontend/js/catalogue-work-detail-editor.js:488` `searchNode.placeholder = t(state, "search_placeholder", "find detail id(s): 00001-001, ...`
- `summary_parent_link`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:222` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_parent_li...`
- `summary_public_link`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:216` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_public_li...`
- `summary_rebuild_current`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:205` `: text(state, options, "summary_rebuild_current", "source and parent work output are al...`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:235` `: text(state, options, "summary_rebuild_current", "source and parent work output are al...`
- `summary_rebuild_needed`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:204` `? text(state, options, "summary_rebuild_needed", "public update failed in this session")`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:234` `? text(state, options, "summary_rebuild_needed", "public update failed in this session")`
- `summary_section_label`
  - `studio/app/frontend/js/catalogue-work-detail-sections.js:228` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_section_l...`
- `unknown_detail_error`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:165` `renderWorkDetailSearchMatches(state, [], text(context, "unknown_detail_error", "Unknown...`
  - `studio/app/frontend/js/catalogue-work-detail-selection.js:200` `else renderWorkDetailSearchMatches(state, [], text(context, "unknown_detail_error", "Un...`
- `unpublish_button`
  - `studio/app/frontend/js/catalogue-work-detail-actions.js:128` `? t(state, context, "unpublish_button", "Unpublish")`
- `unpublish_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` `\|\| lookupText(options, "unpublish_confirm_default", options.defaultText \|\| "Unpublish t...`
- `unpublish_confirm_dirty_note`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` `? lookupText(options, "unpublish_confirm_dirty_note", "Unsaved form changes will be dis...`

### `catalogue_work_editor`

- `build_preview_button`
  - `studio/app/frontend/js/catalogue-work-sections.js:272` `<button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-ac...`
- `build_preview_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:601` ``${t(state, context, "build_preview_failed", "Public update preview unavailable.")} ${n...`
  - `studio/app/frontend/js/catalogue-work-actions.js:649` ``${t(state, context, "build_preview_failed", "Public update preview unavailable.")} ${n...`
- `build_preview_modal_artifacts`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:123` `lookupText(options, "build_preview_modal_artifacts", "Artifacts: {artifacts}.", { artif...`
- `build_preview_modal_changed_fields`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:119` `lookupText(options, "build_preview_modal_changed_fields", "Changed fields: {fields}.", {`
- `build_preview_modal_close`
  - `studio/app/frontend/js/catalogue-work-editor-modals.js:124` `closeLabel: lookupText(text, "build_preview_modal_close", "Close"),`
- `build_preview_modal_reasons_heading`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:126` `? `${lookupText(options, "build_preview_modal_reasons_heading", "Reasons:")}\n${explana...`
- `build_preview_modal_rules`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:122` `lookupText(options, "build_preview_modal_rules", "Rules: {rules}.", { rules }),`
- `build_preview_modal_title`
  - `studio/app/frontend/js/catalogue-work-editor-modals.js:116` `title: lookupText(text, "build_preview_modal_title", "Public update preview"),`
- `build_preview_no_changes`
  - `studio/app/frontend/js/catalogue-work-actions.js:625` `setTextWithState(context, state.statusNode, t(state, context, "build_preview_no_changes...`
- `build_preview_no_result`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:100` `\|\| lookupText(options, "build_preview_no_result", "No public update work selected.");`
- `build_preview_search_no`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:57` `: lookupText(options, "build_preview_search_no", "no");`
- `build_preview_search_yes`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:56` `? lookupText(options, "build_preview_search_yes", "yes")`
- `build_preview_server_unavailable`
  - `studio/app/frontend/js/catalogue-work-actions.js:612` `setTextWithState(context, state.statusNode, t(state, context, "build_preview_server_una...`
- `build_preview_status_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:631` `setTextWithState(context, state.statusNode, t(state, context, "build_preview_status_run...`
- `build_preview_template`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:64` `"build_preview_template",`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:76` `"build_preview_template",`
- `build_preview_unpublished`
  - `studio/app/frontend/js/catalogue-work-actions.js:578` `setTextWithState(context, state.buildImpactNode, t(state, context, "build_preview_unpub...`
  - `studio/app/frontend/js/catalogue-work-actions.js:616` `setTextWithState(context, state.statusNode, t(state, context, "build_preview_unpublishe...`
- `build_result_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:336` `text: t(state, context, "build_result_success", "Public catalogue updated at {completed...`
- `build_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:237` `const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")...`
  - `studio/app/frontend/js/catalogue-work-actions.js:285` `const statusFailed = `${t(state, context, "build_status_failed", "Site update failed.")...`
  - `studio/app/frontend/js/catalogue-work-actions.js:778` ``${t(state, context, "build_status_failed", "Site update failed.")} ${normalizeText(err...`
- `build_status_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:738` `setTextWithState(context, state.statusNode, t(state, context, "build_status_running", "...`
- `build_status_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:264` `text: t(state, context, "build_status_success", "Site update completed."),`
  - `studio/app/frontend/js/catalogue-work-actions.js:308` `text: t(state, context, "build_status_success", "Site update completed."),`
  - `studio/app/frontend/js/catalogue-work-actions.js:342` `text: t(state, context, "build_status_success", "Site update completed."),`
- `bulk_build_preview`
  - `studio/app/frontend/js/catalogue-work-actions.js:560` `? t(state, context, "bulk_build_preview", "Public update preview: {count} published wor...`
  - `studio/app/frontend/js/catalogue-work-editor.js:370` `t(state, "bulk_build_preview", "Public update preview: {count} published work scope(s) ...`
- `bulk_save_result_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:299` `text: t(state, context, "bulk_save_result_success", "Saved {count} work records at {sav...`
- `bulk_save_result_success_applied`
  - `studio/app/frontend/js/catalogue-work-actions.js:291` `text: t(state, context, "bulk_save_result_success_applied", "Saved {count} work records...`
- `bulk_save_result_success_partial`
  - `studio/app/frontend/js/catalogue-work-actions.js:295` `text: t(state, context, "bulk_save_result_success_partial", "Saved {count} work records...`
- `bulk_status_loaded`
  - `studio/app/frontend/js/catalogue-work-actions.js:316` `text: t(state, context, "bulk_status_loaded", "Loaded {count} work records.", loadedCou...`
  - `studio/app/frontend/js/catalogue-work-editor.js:392` `? t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state....`
  - `studio/app/frontend/js/catalogue-work-route-state.js:176` `text(options, "bulk_status_loaded", "Loaded {count} work records.", { count: String(wor...`
- `confirm_cancel_button`
  - `studio/app/frontend/js/catalogue-work-actions.js:699` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-work-actions.js:850` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-work-actions.js:975` `cancelLabel: t(state, context, "confirm_cancel_button", "Cancel"),`
- `context_series_empty`
  - `studio/app/frontend/js/catalogue-work-sections.js:130` `return escapeHtml(text(state, options, "context_series_empty", "No series assigned."));`
- `create_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:398` `? t(state, "create_button", "Create")`
- `create_result_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:541` `setTextWithState(context, state.resultNode, t(state, context, "create_result_success", ...`
- `create_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:544` `setTextWithState(context, state.statusNode, `${t(state, context, "create_status_failed"...`
- `create_status_saving`
  - `studio/app/frontend/js/catalogue-work-actions.js:519` `setTextWithState(context, state.statusNode, t(state, context, "create_status_saving", "...`
- `create_status_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:542` `setTextWithState(context, state.statusNode, t(state, context, "create_status_success", ...`
- `create_status_validation_error`
  - `studio/app/frontend/js/catalogue-work-actions.js:510` `workIdError \|\| t(state, context, "create_status_validation_error", "Fix validation erro...`
- `delete_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:545` `elements.deleteButton.textContent = t(state, "delete_button", "Delete");`
- `delete_confirm_button`
  - `studio/app/frontend/js/catalogue-work-actions.js:974` `primaryLabel: t(state, context, "delete_confirm_button", "Delete"),`
- `delete_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:148` `\|\| lookupText(options, "delete_confirm_default", options.defaultText \|\| "Delete this so...`
- `delete_confirm_title`
  - `studio/app/frontend/js/catalogue-work-actions.js:972` `title: t(state, context, "delete_confirm_title", "Confirm delete"),`
- `delete_status_blocked`
  - `studio/app/frontend/js/catalogue-work-actions.js:957` `fallback: t(state, context, "delete_status_blocked", "Delete is blocked.")`
- `delete_status_cancelled`
  - `studio/app/frontend/js/catalogue-work-actions.js:979` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_cancelled"...`
- `delete_status_conflict`
  - `studio/app/frontend/js/catalogue-work-actions.js:989` `? t(state, context, "delete_status_conflict", "Source record changed since this page lo...`
- `delete_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:990` `: `${t(state, context, "delete_status_failed", "Source delete failed.")} ${normalizeTex...`
- `delete_status_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:944` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", ...`
  - `studio/app/frontend/js/catalogue-work-actions.js:984` `setTextWithState(context, state.statusNode, t(state, context, "delete_status_running", ...`
- `details_empty`
  - `studio/app/frontend/js/catalogue-work-sections.js:349` `state.detailsResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(...`
- `details_heading`
  - `studio/app/frontend/js/catalogue-work-editor.js:534` `elements.detailsHeadingNode.textContent = t(state, "details_heading", "work details");`
- `details_more_count`
  - `studio/app/frontend/js/catalogue-work-sections.js:381` `? text(state, options, "details_more_count", "showing {visible} of {total}", {`
- `details_new_link`
  - `studio/app/frontend/js/catalogue-work-editor.js:535` `elements.newDetailLinkNode.textContent = t(state, "details_new_link", "new work detail ...`
- `details_new_unavailable_draft`
  - `studio/app/frontend/js/catalogue-work-sections.js:569` `state.newDetailLinkNode.title = text(state, options, "details_new_unavailable_draft", "...`
- `details_search_no_match`
  - `studio/app/frontend/js/catalogue-work-sections.js:374` `blocks.push(`<p class="tagStudioForm__meta">${escapeHtml(text(state, options, "details_...`
- `details_search_placeholder`
  - `studio/app/frontend/js/catalogue-work-editor.js:536` `elements.detailSearchNode.placeholder = t(state, "details_search_placeholder", "find de...`
- `details_search_results`
  - `studio/app/frontend/js/catalogue-work-sections.js:368` `<h3 class="tagStudioForm__key">${escapeHtml(text(state, options, "details_search_result...`
- `details_section_blank`
  - `studio/app/frontend/js/catalogue-work-sections.js:125` `return normalizeText(sectionKey) \|\| text(state, options, "details_section_blank", "root");`
- `dirty_warning`
  - `studio/app/frontend/js/catalogue-work-editor.js:380` `message: t(state, "dirty_warning", "Unsaved source changes.")`
- `entry_modal_cancel_button`
  - `studio/app/frontend/js/catalogue-work-editor-modals.js:96` `cancelLabel: lookupText(text, "entry_modal_cancel_button", "Cancel"),`
  - `studio/app/frontend/js/catalogue-work-editor-modals.js:147` `{ role: ENTRY_CANCEL_ROLE, label: lookupText(text, "entry_modal_cancel_button", "Cancel...`
- `entry_modal_delete_button`
  - `studio/app/frontend/js/catalogue-work-editor-modals.js:95` `primaryLabel: lookupText(text, "entry_modal_delete_button", "Delete"),`
- `entry_modal_save_button`
  - `studio/app/frontend/js/catalogue-work-editor-modals.js:148` `{ role: ENTRY_SAVE_ROLE, label: lookupText(text, "entry_modal_save_button", "Save"), pr...`
- `field_duplicate_work_id`
  - `studio/app/frontend/js/catalogue-work-editor.js:190` `errors.set("work_id", t(state, "field_duplicate_work_id", "Work id already exists."));`
- `field_invalid_date`
  - `studio/app/frontend/js/catalogue-work-editor.js:248` `errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave bl...`
  - `studio/app/frontend/js/catalogue-work-editor.js:298` `errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave bl...`
- `field_invalid_number`
  - `studio/app/frontend/js/catalogue-work-editor.js:214` `errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));`
  - `studio/app/frontend/js/catalogue-work-editor.js:263` `errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));`
  - `studio/app/frontend/js/catalogue-work-editor.js:309` `errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));`
- `field_invalid_series_id`
  - `studio/app/frontend/js/catalogue-work-editor.js:223` `errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numer...`
  - `studio/app/frontend/js/catalogue-work-editor.js:282` `normalizeText(error && error.message) \|\| t(state, "field_invalid_series_id", "Use comma...`
  - `studio/app/frontend/js/catalogue-work-editor.js:318` `errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numer...`
- `field_invalid_status`
  - `studio/app/frontend/js/catalogue-work-editor.js:241` `errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));`
  - `studio/app/frontend/js/catalogue-work-editor.js:293` `errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));`
- `field_invalid_year`
  - `studio/app/frontend/js/catalogue-work-editor.js:208` `errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));`
  - `studio/app/frontend/js/catalogue-work-editor.js:255` `errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));`
  - `studio/app/frontend/js/catalogue-work-editor.js:303` `errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));`
- `field_required_series_ids`
  - `studio/app/frontend/js/catalogue-work-editor.js:196` `errors.set("series_ids", t(state, "field_required_series_ids", "Enter at least one seri...`
- `field_required_work_id`
  - `studio/app/frontend/js/catalogue-work-editor.js:188` `errors.set("work_id", t(state, "field_required_work_id", "Enter a work id."));`
- `field_unknown_series_id`
  - `studio/app/frontend/js/catalogue-work-editor.js:228` `errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {serie...`
  - `studio/app/frontend/js/catalogue-work-editor.js:275` `errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {serie...`
  - `studio/app/frontend/js/catalogue-work-editor.js:323` `errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {serie...`
- `files_add_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:538` `elements.newFileLinkNode.textContent = t(state, "files_add_button", "Add file");`
- `files_add_modal_title`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:25` `addTitleKey: "files_add_modal_title",`
- `files_delete_button`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:23` `deleteButtonKey: "files_delete_button",`
- `files_delete_modal_body`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:39` `deleteBodyKey: "files_delete_modal_body",`
- `files_delete_modal_title`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:37` `deleteTitleKey: "files_delete_modal_title",`
- `files_edit_button`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:21` `editButtonKey: "files_edit_button",`
- `files_edit_modal_title`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:27` `editTitleKey: "files_edit_modal_title",`
- `files_empty`
  - `studio/app/frontend/js/catalogue-work-sections.js:415` `state.filesResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(st...`
- `files_filename_label`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:29` `firstLabelKey: "files_filename_label",`
- `files_heading`
  - `studio/app/frontend/js/catalogue-work-editor.js:537` `elements.filesHeadingNode.textContent = t(state, "files_heading", "downloads");`
- `files_invalid_filename`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:33` `missingFirstKey: "files_invalid_filename",`
- `files_invalid_label`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:35` `missingSecondKey: "files_invalid_label",`
- `files_label_label`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:31` `secondLabelKey: "files_label_label",`
- `links_add_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:540` `elements.newLinkLinkNode.textContent = t(state, "links_add_button", "Add link");`
- `links_add_modal_title`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:59` `addTitleKey: "links_add_modal_title",`
- `links_delete_button`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:57` `deleteButtonKey: "links_delete_button",`
- `links_delete_modal_body`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:73` `deleteBodyKey: "links_delete_modal_body",`
- `links_delete_modal_title`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:71` `deleteTitleKey: "links_delete_modal_title",`
- `links_edit_button`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:55` `editButtonKey: "links_edit_button",`
- `links_edit_modal_title`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:61` `editTitleKey: "links_edit_modal_title",`
- `links_empty`
  - `studio/app/frontend/js/catalogue-work-sections.js:442` `state.linksResultsNode.innerHTML = `<p class="tagStudioForm__meta">${escapeHtml(text(st...`
- `links_heading`
  - `studio/app/frontend/js/catalogue-work-editor.js:539` `elements.linksHeadingNode.textContent = t(state, "links_heading", "links");`
- `links_invalid_label`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:69` `missingSecondKey: "links_invalid_label",`
- `links_invalid_url`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:67` `missingFirstKey: "links_invalid_url",`
- `links_label_label`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:65` `secondLabelKey: "links_label_label",`
- `links_url_label`
  - `studio/app/frontend/js/catalogue-editor-embedded-items.js:63` `firstLabelKey: "links_url_label",`
- `load_requested_work_failed`
  - `studio/app/frontend/js/catalogue-work-selection.js:291` ``${text(context, "load_requested_work_failed", "Failed to load the requested work.")} $...`
- `media_refresh_button`
  - `studio/app/frontend/js/catalogue-work-sections.js:317` `const mediaActionLabel = text(state, options, "media_refresh_button", "Refresh media");`
- `media_refresh_result_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:926` `setTextWithState(context, state.resultNode, t(state, context, "media_refresh_result_suc...`
- `media_refresh_save_first`
  - `studio/app/frontend/js/catalogue-work-sections.js:313` `? text(state, options, "media_refresh_save_first", "Save source changes before refreshi...`
- `media_refresh_status_blocked`
  - `studio/app/frontend/js/catalogue-work-actions.js:921` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_blo...`
- `media_refresh_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:931` ``${t(state, context, "media_refresh_status_failed", "Media refresh failed.")} ${normali...`
- `media_refresh_status_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:910` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_run...`
- `media_refresh_status_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:925` `setTextWithState(context, state.statusNode, t(state, context, "media_refresh_status_suc...`
- `missing_work_param`
  - `studio/app/frontend/js/catalogue-work-route-state.js:243` `callback(options, "setTextWithState", state.statusNode, text(options, "missing_work_par...`
- `new_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:542` `elements.newButton.textContent = t(state, "new_button", "New");`
- `new_meta`
  - `studio/app/frontend/js/catalogue-work-sections.js:458` `state.metaNode.textContent = text(state, options, "new_meta", "Creating a draft work.");`
- `new_runtime_state`
  - `studio/app/frontend/js/catalogue-work-sections.js:469` `state.runtimeStateNode.textContent = text(state, options, "new_runtime_state", "public ...`
- `new_status_loaded`
  - `studio/app/frontend/js/catalogue-work-route-state.js:211` `callback(options, "setTextWithState", state.statusNode, text(options, "new_status_loade...`
- `new_summary_next`
  - `studio/app/frontend/js/catalogue-work-sections.js:466` `<div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state...`
- `new_summary_next_label`
  - `studio/app/frontend/js/catalogue-work-sections.js:465` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_next_...`
- `new_summary_status`
  - `studio/app/frontend/js/catalogue-work-sections.js:462` `<div class="tagStudio__input tagStudio__input--readonlyDisplay">${escapeHtml(text(state...`
- `new_summary_status_label`
  - `studio/app/frontend/js/catalogue-work-sections.js:461` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "new_summary_statu...`
- `new_work_id_label`
  - `studio/app/frontend/js/catalogue-work-route-state.js:204` `state.searchNode.setAttribute("aria-label", text(options, "new_work_id_label", "New wor...`
- `new_work_id_placeholder`
  - `studio/app/frontend/js/catalogue-work-route-state.js:203` `state.searchNode.placeholder = text(options, "new_work_id_placeholder", "new work id");`
- `open_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:541` `elements.openButton.textContent = t(state, "open_button", "Open");`
- `prose_import_button`
  - `studio/app/frontend/js/catalogue-work-sections.js:316` `const proseActionLabel = text(state, options, "prose_import_button", "Import staged pro...`
- `prose_import_confirm_button`
  - `studio/app/frontend/js/catalogue-work-actions.js:698` `primaryLabel: t(state, context, "prose_import_confirm_button", "Overwrite"),`
- `prose_import_confirm_overwrite`
  - `studio/app/frontend/js/catalogue-work-actions.js:685` `"prose_import_confirm_overwrite",`
- `prose_import_confirm_title`
  - `studio/app/frontend/js/catalogue-work-actions.js:696` `title: t(state, context, "prose_import_confirm_title", "Confirm prose overwrite"),`
- `prose_import_overwrite_cancelled`
  - `studio/app/frontend/js/catalogue-work-actions.js:703` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_overwrite_c...`
- `prose_import_preview_invalid`
  - `studio/app/frontend/js/catalogue-work-actions.js:678` `throw new Error(errors \|\| t(state, context, "prose_import_preview_invalid", "Staged pro...`
- `prose_import_preview_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:669` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_preview_run...`
- `prose_import_result_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:393` `text: t(state, context, "prose_import_result_success", "Prose imported to {target_path}...`
- `prose_import_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:709` `setTextWithState(context, state.statusNode, t(state, context, "prose_import_running", "...`
- `prose_import_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:721` ``${t(state, context, "prose_import_status_failed", "Prose import failed.")} ${normalize...`
- `prose_import_status_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:402` `text: t(state, context, "prose_import_status_success", "Prose import completed."),`
- `publication_preview_publish_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:815` `? t(state, context, "publication_preview_publish_running", "Preparing publish preview…")`
- `publication_preview_unpublish_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:816` `: t(state, context, "publication_preview_unpublish_running", "Preparing unpublish previ...`
- `publication_publish_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:865` `? t(state, context, "publication_publish_running", "Publishing work…")`
- `publication_result_public_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:357` `text: t(state, context, "publication_result_public_failed", "Source status changed, but...`
- `publication_result_published`
  - `studio/app/frontend/js/catalogue-work-actions.js:361` `text: t(state, context, "publication_result_published", "Work is published and public c...`
- `publication_result_unpublished`
  - `studio/app/frontend/js/catalogue-work-actions.js:365` `text: t(state, context, "publication_result_unpublished", "Work is draft again and publ...`
- `publication_save_first`
  - `studio/app/frontend/js/catalogue-work-actions.js:795` `setTextWithState(context, state.statusNode, t(state, context, "publication_save_first",...`
- `publication_status_blocked`
  - `studio/app/frontend/js/catalogue-work-actions.js:831` `fallback: t(state, context, "publication_status_blocked", "Publication change is blocke...`
- `publication_status_cancelled`
  - `studio/app/frontend/js/catalogue-work-actions.js:854` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_cance...`
- `publication_status_conflict`
  - `studio/app/frontend/js/catalogue-work-actions.js:892` `? t(state, context, "publication_status_conflict", "Source record changed since this pa...`
- `publication_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:893` `: `${t(state, context, "publication_status_failed", "Publication change failed.")} ${no...`
- `publication_status_invalid`
  - `studio/app/frontend/js/catalogue-work-actions.js:791` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_inval...`
- `publication_status_public_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:371` `text: `${t(state, context, "publication_status_public_failed", "Publication state chang...`
- `publication_status_published`
  - `studio/app/frontend/js/catalogue-work-actions.js:375` `text: t(state, context, "publication_status_published", "Work published."),`
- `publication_status_unpublished`
  - `studio/app/frontend/js/catalogue-work-actions.js:379` `text: t(state, context, "publication_status_unpublished", "Work unpublished."),`
- `publication_status_validation_error`
  - `studio/app/frontend/js/catalogue-work-actions.js:803` `setTextWithState(context, state.statusNode, t(state, context, "publication_status_valid...`
- `publication_unpublish_confirm_button`
  - `studio/app/frontend/js/catalogue-work-actions.js:849` `primaryLabel: t(state, context, "publication_unpublish_confirm_button", "Unpublish"),`
- `publication_unpublish_confirm_title`
  - `studio/app/frontend/js/catalogue-work-actions.js:847` `title: t(state, context, "publication_unpublish_confirm_title", "Confirm unpublish"),`
- `publication_unpublish_running`
  - `studio/app/frontend/js/catalogue-work-actions.js:866` `: t(state, context, "publication_unpublish_running", "Unpublishing work…")`
- `publish_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:343` `: t(state, "publish_button", "Publish");`
  - `studio/app/frontend/js/catalogue-work-editor.js:544` `elements.publicationButton.textContent = t(state, "publish_button", "Publish");`
- `readiness_action_busy`
  - `studio/app/frontend/js/catalogue-work-sections.js:310` `: text(state, options, "readiness_action_busy", "Wait for the current save or public up...`
  - `studio/app/frontend/js/catalogue-work-sections.js:314` `: text(state, options, "readiness_action_busy", "Wait for the current save or public up...`
- `readiness_save_first`
  - `studio/app/frontend/js/catalogue-work-sections.js:309` `? text(state, options, "readiness_save_first", "Save source changes before importing pr...`
- `save_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:399` `: t(state, "save_button", "Save");`
  - `studio/app/frontend/js/catalogue-work-editor.js:543` `elements.saveButton.textContent = t(state, "save_button", "Save");`
- `save_mode_local_server`
  - `studio/app/frontend/js/studio-save-utils.js:7` `? studioText(config, "save_mode_local_server", "Local server")`
- `save_mode_offline`
  - `studio/app/frontend/js/studio-save-utils.js:8` `: studioText(config, "save_mode_offline", "Offline session");`
- `save_mode_template`
  - `studio/app/frontend/js/studio-save-utils.js:9` `return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });`
- `save_mode_unavailable_hint`
  - `studio/app/frontend/js/catalogue-work-editor.js:385` `state.serverAvailable ? "" : t(state, "save_mode_unavailable_hint", "Local catalogue se...`
  - `studio/app/frontend/js/catalogue-work-editor.js:592` `setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalo...`
- `save_result_success`
  - `studio/app/frontend/js/catalogue-work-actions.js:255` `text: t(state, context, "save_result_success", "Source saved at {saved_at}.", savedAt),`
- `save_result_success_applied`
  - `studio/app/frontend/js/catalogue-work-actions.js:243` `text: t(state, context, "save_result_success_applied", "Saved source changes and update...`
- `save_result_success_partial`
  - `studio/app/frontend/js/catalogue-work-actions.js:247` `text: t(state, context, "save_result_success_partial", "Source changes were saved at {s...`
- `save_result_success_unpublished`
  - `studio/app/frontend/js/catalogue-work-actions.js:251` `text: t(state, context, "save_result_success_unpublished", "Source saved at {saved_at}....`
- `save_result_unchanged`
  - `studio/app/frontend/js/catalogue-work-actions.js:259` `text: t(state, context, "save_result_unchanged", "Source already matches the current fo...`
  - `studio/app/frontend/js/catalogue-work-actions.js:303` `text: t(state, context, "save_result_unchanged", "Source already matches the current fo...`
  - `studio/app/frontend/js/catalogue-work-actions.js:429` `setTextWithState(context, state.resultNode, t(state, context, "save_result_unchanged", ...`
- `save_status_conflict`
  - `studio/app/frontend/js/catalogue-work-actions.js:492` `? t(state, context, "save_status_conflict", "Source record changed since this page load...`
- `save_status_failed`
  - `studio/app/frontend/js/catalogue-work-actions.js:493` `: `${t(state, context, "save_status_failed", "Source save failed.")} ${normalizeText(er...`
- `save_status_loaded`
  - `studio/app/frontend/js/catalogue-work-actions.js:272` `text: t(state, context, "save_status_loaded", "Loaded work {work_id}.", loadedWork),`
  - `studio/app/frontend/js/catalogue-work-actions.js:640` `setTextWithState(context, state.statusNode, t(state, context, "save_status_loaded", "Lo...`
  - `studio/app/frontend/js/catalogue-work-editor.js:393` `: t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWork...`
  - `studio/app/frontend/js/catalogue-work-route-state.js:143` `text(options, "save_status_loaded", "Loaded work {work_id}.", { work_id: workId })`
- `save_status_no_changes`
  - `studio/app/frontend/js/catalogue-work-actions.js:428` `setTextWithState(context, state.statusNode, t(state, context, "save_status_no_changes",...`
- `save_status_saving`
  - `studio/app/frontend/js/catalogue-work-actions.js:441` `: t(state, context, "save_status_saving", "Saving source record…")`
- `save_status_saving_and_updating`
  - `studio/app/frontend/js/catalogue-work-actions.js:440` `? t(state, context, "save_status_saving_and_updating", "Saving source record and updati...`
- `save_status_validation_error`
  - `studio/app/frontend/js/catalogue-work-actions.js:422` `setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_e...`
  - `studio/app/frontend/js/catalogue-work-actions.js:620` `setTextWithState(context, state.statusNode, t(state, context, "save_status_validation_e...`
- `search_empty`
  - `studio/app/frontend/js/catalogue-work-selection.js:152` `renderWorkSearchMatches(state, [], normalizeText(error && error.message) \|\| text(contex...`
  - `studio/app/frontend/js/catalogue-work-selection.js:157` `renderWorkSearchMatches(state, [], text(context, "search_empty", "Enter a work id."));`
  - `studio/app/frontend/js/catalogue-work-selection.js:197` `renderWorkSearchMatches(state, [], text(context, "search_empty", "Enter a work id."));`
- `search_no_match`
  - `studio/app/frontend/js/catalogue-work-selection.js:141` `renderWorkSearchMatches(state, [], text(context, "search_no_match", "No matching work i...`
- `search_placeholder`
  - `studio/app/frontend/js/catalogue-work-editor.js:123` `state.searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, ...`
- `series_picker_empty`
  - `studio/app/frontend/js/catalogue-work-form.js:128` `: `<span class="tagStudioForm__meta">${escapeHtml(formText(options, "series_picker_empt...`
- `series_picker_label`
  - `studio/app/frontend/js/catalogue-work-form.js:231` `searchInput.setAttribute("aria-label", formText(options, "series_picker_label", "Find s...`
  - `studio/app/frontend/js/catalogue-work-form.js:323` `state.seriesPicker.searchInput.setAttribute("aria-label", formText(options, "series_pic...`
- `series_picker_placeholder`
  - `studio/app/frontend/js/catalogue-work-form.js:230` `searchInput.placeholder = formText(options, "series_picker_placeholder", "find series b...`
  - `studio/app/frontend/js/catalogue-work-form.js:322` `state.seriesPicker.searchInput.placeholder = formText(options, "series_picker_placehold...`
- `summary_public_link`
  - `studio/app/frontend/js/catalogue-work-sections.js:545` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_public_li...`
- `summary_rebuild_current`
  - `studio/app/frontend/js/catalogue-work-sections.js:517` `: text(state, options, "summary_rebuild_current", "source and public catalogue are alig...`
  - `studio/app/frontend/js/catalogue-work-sections.js:558` `: text(state, options, "summary_rebuild_current", "source and public catalogue are alig...`
- `summary_rebuild_needed`
  - `studio/app/frontend/js/catalogue-work-sections.js:516` `? text(state, options, "summary_rebuild_needed", "public update failed in this session")`
  - `studio/app/frontend/js/catalogue-work-sections.js:557` `? text(state, options, "summary_rebuild_needed", "public update failed in this session")`
- `summary_series_label`
  - `studio/app/frontend/js/catalogue-work-sections.js:511` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_series_la...`
  - `studio/app/frontend/js/catalogue-work-sections.js:551` `<span class="tagStudioForm__label">${escapeHtml(text(state, options, "summary_series_la...`
- `unknown_work_error`
  - `studio/app/frontend/js/catalogue-work-selection.js:167` `renderWorkSearchMatches(state, [], text(context, "unknown_work_error", "Unknown work id...`
  - `studio/app/frontend/js/catalogue-work-selection.js:207` `renderWorkSearchMatches(state, [], text(context, "unknown_work_error", "Unknown work id...`
- `unpublish_button`
  - `studio/app/frontend/js/catalogue-work-editor.js:342` `? t(state, "unpublish_button", "Unpublish")`
- `unpublish_confirm_default`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:139` `\|\| lookupText(options, "unpublish_confirm_default", options.defaultText \|\| "Unpublish t...`
- `unpublish_confirm_dirty_note`
  - `studio/app/frontend/js/catalogue-editor-modal-formatters.js:141` `? lookupText(options, "unpublish_confirm_dirty_note", "Unsaved form changes will be dis...`

### `project_state`

- `context_hint`
  - `studio/app/frontend/js/project-state.js:247` `setTextWithState(contextNode, t(state, "context_hint", "Scan source project folders and...`
- `empty_state`
  - `studio/app/frontend/js/project-state.js:243` `emptyNode.textContent = t(state, "empty_state", "");`
- `include_subfolders_label`
  - `studio/app/frontend/js/project-state.js:240` `includeSubfoldersLabelNode.textContent = t(state, "include_subfolders_label", "include ...`
- `loading`
  - `studio/app/frontend/js/project-state.js:242` `loadingNode.textContent = t(state, "loading", "loading project state...");`
- `open_button`
  - `studio/app/frontend/js/project-state.js:245` `openButton.textContent = t(state, "open_button", "Open file");`
- `open_failed`
  - `studio/app/frontend/js/project-state.js:158` ``${t(state, "open_failed", "Could not open the Markdown source file.")} ${normalizeText...`
- `output_label`
  - `studio/app/frontend/js/project-state.js:238` `outputLabelNode.textContent = t(state, "output_label", "output");`
- `page_heading`
  - `studio/app/frontend/js/project-state.js:236` `pageHeadingNode.textContent = t(state, "page_heading", "project state");`
- `run_button`
  - `studio/app/frontend/js/project-state.js:244` `runButton.textContent = t(state, "run_button", "Run");`
- `run_heading`
  - `studio/app/frontend/js/project-state.js:237` `runHeadingNode.textContent = t(state, "run_heading", "report");`
- `run_result_success`
  - `studio/app/frontend/js/project-state.js:134` `t(state, "run_result_success", "Report written to {path}.", { path: state.outputPath }),`
- `run_status_failed`
  - `studio/app/frontend/js/project-state.js:140` ``${t(state, "run_status_failed", "Project-state report failed.")} ${normalizeText(error...`
- `run_status_running`
  - `studio/app/frontend/js/project-state.js:106` `setTextWithState(state.statusNode, t(state, "run_status_running", "Running project-stat...`
- `run_status_success`
  - `studio/app/frontend/js/project-state.js:129` `t(state, "run_status_success", "Project-state report updated."),`
- `save_mode_local_server`
  - `studio/app/frontend/js/studio-save-utils.js:7` `? studioText(config, "save_mode_local_server", "Local server")`
- `save_mode_offline`
  - `studio/app/frontend/js/studio-save-utils.js:8` `: studioText(config, "save_mode_offline", "Offline session");`
- `save_mode_template`
  - `studio/app/frontend/js/studio-save-utils.js:9` `return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });`
- `server_unavailable_hint`
  - `studio/app/frontend/js/project-state.js:251` `unavailableText: () => t(state, "server_unavailable_hint", "Local catalogue server unav...`
- `source_label`
  - `studio/app/frontend/js/project-state.js:239` `sourceLabelNode.textContent = t(state, "source_label", "source");`
- `summary_catalogue_folders`
  - `studio/app/frontend/js/project-state.js:75` `{ label: t(state, "summary_catalogue_folders", "catalogue folders"), value: summaryValu...`
- `summary_catalogue_images`
  - `studio/app/frontend/js/project-state.js:78` `{ label: t(state, "summary_catalogue_images", "primary images in works.json"), value: s...`
- `summary_heading`
  - `studio/app/frontend/js/project-state.js:241` `summaryHeadingNode.textContent = t(state, "summary_heading", "summary");`
- `summary_include_subfolders`
  - `studio/app/frontend/js/project-state.js:73` `{ label: t(state, "summary_include_subfolders", "include sub-folders"), value: summary ...`
- `summary_source_folders`
  - `studio/app/frontend/js/project-state.js:74` `{ label: t(state, "summary_source_folders", "source folders"), value: summaryValue(summ...`
- `summary_source_images`
  - `studio/app/frontend/js/project-state.js:77` `{ label: t(state, "summary_source_images", "source images"), value: summaryValue(summar...`
- `summary_unrepresented_folders`
  - `studio/app/frontend/js/project-state.js:76` `{ label: t(state, "summary_unrepresented_folders", "folders not in works.json"), value:...`
- `summary_unrepresented_images`
  - `studio/app/frontend/js/project-state.js:79` `{ label: t(state, "summary_unrepresented_images", "extra images in represented folders"...`

### `studio_works`

- `copy_series_button`
  - `studio/app/frontend/js/studio-works.js:478` `copySeriesButton.textContent = worksText("copy_series_button", "copy series");`

