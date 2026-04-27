const DEFAULT_STUDIO_CONFIG = {
  studio_config_version: "studio_config_v1",
  updated_at_utc: "",
  paths: {
    routes: {
      studio_home: "/studio/",
      search: "/search/",
      series_tags: "/studio/series-tags/",
      series_tag_editor: "/studio/series-tag-editor/",
      build_activity: "/studio/build-activity/",
      docs_broken_links: "/studio/docs-broken-links/",
      docs_html_import: "/studio/docs-import/",
      catalogue_status: "/studio/catalogue-status/",
      catalogue_activity: "/studio/catalogue-activity/",
      bulk_add_work: "/studio/bulk-add-work/",
      catalogue_moment_import: "/studio/catalogue-moment-import/",
      catalogue_work_editor: "/studio/catalogue-work/",
      catalogue_new_work_editor: "/studio/catalogue-new-work/",
      catalogue_work_detail_editor: "/studio/catalogue-work-detail/",
      catalogue_new_work_detail_editor: "/studio/catalogue-new-work-detail/",
      catalogue_work_file_editor: "/studio/catalogue-work-file/",
      catalogue_new_work_file_editor: "/studio/catalogue-new-work-file/",
      catalogue_work_link_editor: "/studio/catalogue-work-link/",
      catalogue_new_work_link_editor: "/studio/catalogue-new-work-link/",
      catalogue_series_editor: "/studio/catalogue-series/",
      catalogue_new_series_editor: "/studio/catalogue-new-series/",
      tag_registry: "/studio/tag-registry/",
      tag_aliases: "/studio/tag-aliases/",
      tag_groups: "/studio/tag-groups/",
      series_page_base: "/series/",
      docs_page: "/docs/",
      library_page: "/library/",
      moments_page_base: "/moments/",
      works_page_base: "/works/",
      work_details_page_base: "/work_details/",
      site_map: "/site_map/"
    },
    data: {
      studio: {
        tag_registry: "/assets/studio/data/tag_registry.json",
        tag_aliases: "/assets/studio/data/tag_aliases.json",
        tag_assignments: "/assets/studio/data/tag_assignments.json",
        tag_groups: "/assets/studio/data/tag_groups.json",
        build_activity: "/assets/studio/data/build_activity.json",
        catalogue_activity: "/assets/studio/data/catalogue_activity.json",
        catalogue_works: "/assets/studio/data/catalogue/works.json",
        catalogue_work_details: "/assets/studio/data/catalogue/work_details.json",
        catalogue_series: "/assets/studio/data/catalogue/series.json",
        catalogue_work_files: "/assets/studio/data/catalogue/work_files.json",
        catalogue_work_links: "/assets/studio/data/catalogue/work_links.json",
        catalogue_lookup_work_search: "/assets/studio/data/catalogue_lookup/work_search.json",
        catalogue_lookup_series_search: "/assets/studio/data/catalogue_lookup/series_search.json",
        catalogue_lookup_work_detail_search: "/assets/studio/data/catalogue_lookup/work_detail_search.json",
        catalogue_lookup_meta: "/assets/studio/data/catalogue_lookup/meta.json",
        catalogue_lookup_work_base: "/assets/studio/data/catalogue_lookup/works/",
        catalogue_lookup_work_detail_base: "/assets/studio/data/catalogue_lookup/work_details/",
        catalogue_lookup_work_file_base: "/assets/studio/data/catalogue_lookup/work_files/",
        catalogue_lookup_work_link_base: "/assets/studio/data/catalogue_lookup/work_links/",
        catalogue_lookup_series_base: "/assets/studio/data/catalogue_lookup/series/"
      },
      site: {
        series_index: "/assets/data/series_index.json",
        works_index: "/assets/data/works_index.json"
      },
      search: {
        policy: "/assets/data/search/policy.json",
        scopes: {
          catalogue: {
            index: "/assets/data/search/catalogue/index.json"
          },
          library: {
            index: "/assets/data/search/library/index.json"
          },
          studio: {
            index: "/assets/data/search/studio/index.json"
          }
        }
      }
    }
  },
  analysis: {
    groups: {
      ordered: ["subject", "domain", "form", "theme"],
      coverage_groups: ["subject", "domain", "form", "theme"]
    },
    rag: {
      deprecated_statuses: ["deprecated", "candidate"],
      completeness: {
        group_coverage_denominator: 4,
        tag_bonus_max: 0.25,
        tag_bonus_cap_at_total_tags: 6,
        score_cap: 1
      },
      rules: {
        red: {
          if_total_tags_eq: 0,
          if_unknown_tags_gt: 0
        },
        amber: {
          if_groups_present_lte: 1,
          if_total_tags_lt: 3,
          if_deprecated_tags_gt: 0,
          if_missing_all_groups: ["form", "theme"]
        },
        green: {
          fallback: true
        }
      }
    }
  },
  ui_text: {
    series_tag_editor: {
      missing_series_id_error: "Tag Studio error: missing series id.",
      load_failed_error: "Failed to load tag data. Check /assets/studio/data/tag_registry.json, /assets/studio/data/tag_aliases.json, /assets/studio/data/tag_assignments.json, /assets/data/series_index.json, and /assets/data/works_index.json.",
      work_input_placeholder: "work_id(s) in this series",
      tag_input_placeholder: "tag slug or alias",
      add_button: "Add",
      save_button: "Save",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Offline session",
      modal_title: "Work Tag Patch Preview",
      modal_resolved_label: "Resolved work override tags",
      modal_patch_guidance_label: "Patch guidance for tag_assignments.json",
      modal_copy_button: "Copy",
      modal_close_button: "Close",
      context_hint_default: "Select one or more works to add per-work tag overrides. Series tags shown below are context only.",
      context_hint_selected: "Monochrome pills are inherited from the series. Colored pills are saved as work-only overrides.",
      chip_caption_local: "local",
      chip_caption_delete: "delete",
      restore_deleted_tag_aria_label: "Restore {tag_id}",
      series_tag_restored: "Series tag restored.",
      work_tag_restored: "Work tag restored.",
      work_tag_restore_inherited_warning: "Cannot restore {tag_id} while it is inherited from the series.",
      save_warning_unresolved: "Resolve unknown tags before saving.",
      save_status_no_changes: "No changes to save.",
      save_status_copy: "Patch guidance copied to clipboard.",
      save_status_local_failed: "Local save failed. Switched to offline mode.",
      save_result_local_failed: "Local server save failed. Changes are now staged in the offline session.",
      save_result_offline_staged: "Changes are staged in the offline session.",
      save_result_offline_cleared: "Series matches repo data. Offline session entry cleared.",
      save_result_server_available_import: "Local server now available. Apply offline changes using Series Tags > Import.",
      save_status_success_base: "Saved {saved_count} work row{saved_plural}",
      save_status_success_removed_suffix: "; removed {removed_count} row{removed_plural}",
      save_status_success_at_suffix: " at {saved_at}."
    },
    series_tags: {
      load_failed_error: "Failed to load series tag data.",
      empty_state: "none",
      table_heading_series: "series",
      table_heading_status: "status",
      table_heading_tags: "tags",
      filter_all_tags: "All tags",
      group_info_title: "Open group descriptions in a new tab",
      group_info_aria_label: "Open group descriptions in a new tab",
      session_open_button: "Session",
      import_open_button: "Import",
      session_modal_title: "Offline session",
      import_modal_title: "Import assignments",
      modal_close_button: "Close",
      session_summary_label: "Offline session",
      session_summary_value: "{count} staged series",
      session_updated_value: "Updated: {updated_at}",
      session_updated_empty: "not yet",
      session_copy_button: "Copy JSON",
      session_download_button: "Download JSON",
      session_clear_button: "Clear session",
      session_copy_success: "Offline session JSON copied.",
      session_copy_failed: "Copy failed. Select and copy manually.",
      session_download_success: "Offline session JSON download started.",
      session_clear_success: "Offline session cleared.",
      session_import_label: "Import assignments",
      session_import_choose_button: "Choose file",
      session_import_preview_button: "Preview import",
      session_import_apply_button: "Apply import",
      session_import_selected_file: "Selected: {filename}",
      session_import_no_file: "No import file selected.",
      session_import_unavailable: "Import requires the local server.",
      session_import_invalid_json: "Import file is not valid JSON.",
      session_import_preview_success: "Import preview ready.",
      session_import_preview_failed: "Import preview failed.",
      session_import_apply_without_preview: "Preview the import before applying it.",
      session_import_apply_success: "Import applied.",
      session_import_apply_failed: "Import failed.",
      session_import_resolution_label: "resolution",
      session_import_resolution_skip: "skip",
      session_import_resolution_overwrite: "overwrite",
      chip_caption_local: "local",
      chip_caption_delete: "delete",
      session_import_invalid_work_ids: "Invalid works: {work_ids}",
      session_import_status_apply: "Ready to apply.",
      session_import_status_conflict: "Conflict with current repo row.",
      session_import_status_invalid: "Invalid staged data.",
      session_import_status_missing: "Series not found in current site data."
    },
    studio_works: {
      copy_series_button: "copy series"
    },
    build_activity: {
      load_failed_error: "Failed to load build activity.",
      empty_state: "No build activity yet.",
      meta_summary: "{count} recent build entries",
      meta_summary_one: "1 recent build entry",
      status_completed: "completed",
      status_failed: "failed",
      status_other: "status unknown",
      detail_source: "source",
      detail_workbook: "workbook",
      detail_media: "media",
      detail_actions: "actions",
      detail_results: "results",
      none: "none"
    },
    docs_broken_links: {
      intro: "Run a strict docs-viewer link audit for Studio or Library docs.",
      scope_label: "scope",
      scope_option_studio: "studio",
      scope_option_library: "library",
      run_button: "Run broken links",
      idle_status: "Select a scope and run the audit.",
      service_unavailable: "Docs management service unavailable. Start bin/dev-studio to run the audit.",
      status_running: "Running docs broken-links audit…",
      status_success: "Audit complete.",
      status_success_empty: "No broken links found.",
      status_failed: "Failed to run docs broken-links audit.",
      empty_state: "No broken links found for this scope.",
      meta_summary_zero: "No broken links found.",
      meta_summary: "{count} issue(s): {not_found} not found, {wrong_title} wrong title.",
      column_problem: "problem",
      column_linked_page: "linked page",
      column_link: "link",
      column_from_page: "from page"
    },
    catalogue_status: {
      load_failed_error: "Failed to load catalogue status.",
      empty_state: "No non-published catalogue source records.",
      meta_summary: "{count} non-published source records",
      meta_summary_one: "1 non-published source record"
    },
    catalogue_activity: {
      load_failed_error: "Failed to load catalogue activity.",
      empty_state: "No catalogue activity yet.",
      meta_summary: "{count} recent catalogue entries",
      meta_summary_one: "1 recent catalogue entry",
      status_completed: "completed",
      status_failed: "failed",
      status_other: "status unknown",
      detail_affected: "affected",
      detail_log: "log",
      none: "none"
    },
    bulk_add_work: {
      page_heading: "bulk add work",
      import_heading: "import",
      mode_label: "mode",
      mode_option_works: "works",
      mode_option_work_details: "work details",
      workbook_label: "workbook",
      summary_heading: "preview summary",
      details_heading: "preview details",
      loading: "loading bulk add work…",
      empty_state: "",
      preview_button: "Preview",
      apply_button: "Import",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Unavailable",
      context_hint: "Bulk import is one-way from {workbook} into canonical JSON. Use works mode for new works and work details mode for new detail rows.",
      save_mode_unavailable_hint: "Local catalogue server unavailable. Import is disabled.",
      summary_mode: "mode",
      summary_workbook: "workbook",
      summary_candidate_rows: "candidate rows",
      summary_importable: "importable",
      summary_duplicates: "duplicates",
      summary_blocked: "blocked",
      preview_empty: "Run preview to inspect workbook rows before import.",
      section_importable: "importable",
      section_duplicates: "duplicates already in source",
      section_blocked: "blocked rows",
      section_none: "none",
      preview_status_running: "Running workbook import preview…",
      preview_status_success: "Preview ready: {importable} importable, {duplicates} duplicates, {blocked} blocked.",
      preview_blocked_warning: "Blocked rows must be fixed in {workbook} before apply.",
      preview_status_failed: "Workbook import preview failed.",
      apply_requires_preview: "Run preview for the current mode before apply.",
      apply_status_running: "Applying workbook import…",
      apply_status_success: "Workbook import completed.",
      apply_result_success: "Imported {imported} record(s); {duplicates} duplicate record(s) already existed.",
      apply_clear_workbook: "Clear the imported rows from {workbook} after you confirm the result.",
      apply_status_failed: "Workbook import failed."
    },
    catalogue_work_editor: {
      load_failed_error: "Failed to load catalogue source data for the work editor.",
      search_placeholder: "find work by id",
      search_empty: "Enter a work id.",
      search_no_match: "No matching work ids.",
      search_multiple_matches: "Choose a work from the list.",
      missing_work_param: "Search for a work by work id.",
      unknown_work_error: "Unknown work id: {work_id}.",
      open_button: "Open",
      save_button: "Save",
      build_button: "Update site now",
      delete_button: "Delete",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Unavailable",
      save_mode_unavailable: "Unavailable",
      save_mode_unavailable_hint: "Local catalogue server unavailable. Save is disabled.",
      context_loaded: "Editing source metadata for work {work_id}.",
      context_series_empty: "No series assigned.",
      dirty_warning: "Unsaved source changes.",
      save_status_loaded: "Loaded work {work_id}.",
      save_status_no_changes: "No changes to save.",
      save_status_validation_error: "Fix validation errors before saving.",
      save_status_saving: "Saving source record…",
      save_status_saving_and_updating: "Saving source record and updating site…",
      save_status_conflict: "Source record changed since this page loaded. Reload the work before saving again.",
      save_status_failed: "Source save failed.",
      save_result_success: "Source saved at {saved_at}. Public catalogue update still pending.",
      save_result_success_applied: "Saved source changes and updated the public catalogue at {saved_at}.",
      save_result_success_partial: "Source changes were saved at {saved_at}, but the public catalogue update failed. Retry Update site now.",
      save_result_unchanged: "Source already matches the current form values.",
      bulk_save_result_success: "Saved {count} work records at {saved_at}. Public catalogue update still pending.",
      bulk_save_result_success_applied: "Saved {count} work records and updated the public catalogue at {saved_at}.",
      bulk_save_result_success_partial: "Saved {count} work records at {saved_at}, but the site update failed. Retry Update site now.",
      build_preview_template: "Site update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
      build_preview_search_yes: "yes",
      build_preview_search_no: "no",
      build_preview_failed: "Build preview unavailable.",
      build_status_running: "Updating site…",
      build_status_success: "Site update completed.",
      build_status_failed: "Site update failed.",
      build_result_success: "Public catalogue updated at {completed_at}. Build Activity updated.",
      field_invalid_date: "Use YYYY-MM-DD or leave blank.",
      field_invalid_year: "Use a whole year or leave blank.",
      field_invalid_number: "Use a number or leave blank.",
      field_invalid_status: "Use blank, draft, or published.",
      field_invalid_series_id: "Use comma-separated numeric series ids.",
      field_unknown_series_id: "Unknown series id: {series_id}.",
      summary_public_link: "Open public work page",
      summary_series_label: "series",
      details_heading: "work details",
      details_new_link: "new work detail →",
      details_search_placeholder: "find detail by id",
      details_search_empty: "Enter a detail id for this work.",
      details_search_no_match: "No matching detail ids for this work.",
      details_empty: "No work details for this work.",
      details_open_label: "Open detail editor",
      details_more_count: "showing {visible} of {total}",
      details_section_blank: "root",
      details_search_results: "matching details",
      files_new_link: "new file →",
      links_new_link: "new link →",
      summary_readonly_label: "generated",
      summary_rebuild_label: "runtime",
      summary_rebuild_needed: "source saved; site update pending",
      summary_rebuild_current: "source and public catalogue are aligned in this session"
    },
    catalogue_new_work_editor: {
      create_button: "Create"
    },
    catalogue_moment_import: {
      preview_button: "Preview Source File",
      import_button: "Import + Publish Moment",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Unavailable",
      save_mode_unavailable: "Unavailable",
      save_mode_unavailable_hint: "Local catalogue server unavailable. Moment import is disabled.",
      context_hint: "Enter a staged moment markdown filename and the moment metadata. This page imports body-only prose and then runs a targeted import/rebuild for that one moment.",
      loading: "loading moment import…",
      empty_state: "Preview a source file to inspect the resolved moment metadata.",
      file_label: "moment file",
      file_placeholder: "keys.md",
      file_description: "filename only; the source file is resolved from var/docs/catalogue/import-staging/moments/",
      file_required: "Enter a moment markdown filename.",
      preview_status_loading: "Loading moment source preview…",
      preview_status_invalid: "Fix source-file issues before importing the moment.",
      preview_status_ready: "Moment source preview ready.",
      preview_status_failed: "Moment source preview failed.",
      import_status_running: "Importing moment and rebuilding catalogue search…",
      import_status_success: "Moment import completed.",
      import_status_failed: "Moment import failed.",
      source_summary: "Moment prose is imported as body-only Markdown. Metadata is stored in catalogue source JSON, not prose front matter.",
      image_guidance: "Missing images are acceptable in this phase. The public moment page already handles missing hero images cleanly.",
      metadata_field_title: "title",
      metadata_field_status: "status",
      metadata_field_date: "date",
      metadata_field_date_display: "date display",
      metadata_field_published_date: "published date",
      metadata_field_source_image_file: "source image file",
      metadata_field_image_alt: "image alt",
      preview_field_moment_id: "moment id",
      preview_field_title: "title",
      preview_field_status: "status",
      preview_field_date: "date",
      preview_field_date_display: "date display",
      preview_field_published_date: "published date",
      preview_field_image_file: "image file",
      preview_field_image_status: "image status",
      preview_field_generated_status: "generated status",
      preview_field_source_path: "source path",
      preview_missing_value: "none",
      preview_image_present: "source image found",
      preview_image_missing: "no source image found; public page will render without a hero image",
      preview_generated_present: "generated moment already exists",
      preview_generated_missing: "generated moment not found yet",
      preview_errors_intro: "Source file issues:",
      import_result_success: "Imported {moment_id}. Open the public moment page to confirm the runtime output.",
      import_result_success_link: "Open public moment",
      import_result_missing_preview: "Preview the source file before importing."
    },
    catalogue_work_detail_editor: {
      load_failed_error: "Failed to load catalogue source data for the work detail editor.",
      search_placeholder: "find detail by id",
      search_empty: "Enter a detail id.",
      search_no_match: "No matching detail ids.",
      missing_detail_param: "Search for a work detail by detail id.",
      unknown_detail_error: "Unknown detail id: {detail_uid}.",
      open_button: "Open",
      save_button: "Save",
      build_button: "Update site now",
      delete_button: "Delete",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Unavailable",
      save_mode_unavailable: "Unavailable",
      save_mode_unavailable_hint: "Local catalogue server unavailable. Save is disabled.",
      context_loaded: "Editing source metadata for detail {detail_uid}.",
      dirty_warning: "Unsaved source changes.",
      save_status_loaded: "Loaded detail {detail_uid}.",
      save_status_no_changes: "No changes to save.",
      save_status_validation_error: "Fix validation errors before saving.",
      save_status_saving: "Saving source record…",
      save_status_saving_and_updating: "Saving source record and updating site…",
      save_status_conflict: "Source record changed since this page loaded. Reload the detail before saving again.",
      save_status_failed: "Source save failed.",
      save_result_success: "Source saved at {saved_at}. Parent-work update still pending.",
      save_result_success_applied: "Saved source changes and updated the parent work output at {saved_at}.",
      save_result_success_partial: "Source changes were saved at {saved_at}, but the site update failed. Retry Update site now.",
      save_result_unchanged: "Source already matches the current form values.",
      bulk_save_result_success: "Saved {count} detail records at {saved_at}. Parent-work update still pending.",
      bulk_save_result_success_applied: "Saved {count} detail records and updated the parent work output at {saved_at}.",
      bulk_save_result_success_partial: "Saved {count} detail records at {saved_at}, but the site update failed. Retry Update site now.",
      build_preview_template: "Site update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
      build_preview_search_yes: "yes",
      build_preview_search_no: "no",
      build_preview_failed: "Build preview unavailable.",
      build_status_running: "Updating site…",
      build_status_success: "Site update completed.",
      build_status_failed: "Site update failed.",
      build_result_success: "Parent work output updated at {completed_at}. Build Activity updated.",
      field_invalid_status: "Use blank, draft, or published.",
      summary_public_link: "Open public detail page",
      summary_parent_link: "Open work editor",
      summary_section_label: "detail section",
      summary_rebuild_needed: "source saved; site update pending",
      summary_rebuild_current: "source and parent work output are aligned in this session"
    },
    catalogue_new_work_detail_editor: {
      create_button: "Create"
    },
    catalogue_new_work_file_editor: {
      create_button: "Create"
    },
    catalogue_new_work_link_editor: {
      create_button: "Create"
    },
    catalogue_work_file_editor: {
      search_placeholder: "find work file by id, filename, or work id",
      open_button: "Open",
      save_button: "Save",
      build_button: "Update site now",
      delete_button: "Delete",
      save_status_saving_and_updating: "Saving source record and updating site…",
      save_result_success: "Source saved at {saved_at}. Public catalogue update still pending.",
      save_result_success_applied: "Saved source changes and updated the public catalogue at {saved_at}.",
      save_result_success_partial: "Source changes were saved at {saved_at}, but the public catalogue update failed. Retry Update site now.",
      build_status_running: "Updating site…",
      build_status_success: "Site update completed.",
      build_status_failed: "Site update failed.",
      build_result_success: "Public catalogue updated at {completed_at}. Build Activity updated.",
      summary_rebuild_needed: "source saved; site update pending",
      summary_rebuild_current: "source and public catalogue are aligned in this session"
    },
    catalogue_work_link_editor: {
      search_placeholder: "find work link by id, label, URL, or work id",
      open_button: "Open",
      save_button: "Save",
      build_button: "Update site now",
      delete_button: "Delete",
      save_status_saving_and_updating: "Saving source record and updating site…",
      save_result_success: "Source saved at {saved_at}. Public catalogue update still pending.",
      save_result_success_applied: "Saved source changes and updated the public catalogue at {saved_at}.",
      save_result_success_partial: "Source changes were saved at {saved_at}, but the public catalogue update failed. Retry Update site now.",
      build_status_running: "Updating site…",
      build_status_success: "Site update completed.",
      build_status_failed: "Site update failed.",
      build_result_success: "Public catalogue updated at {completed_at}. Build Activity updated.",
      summary_rebuild_needed: "source saved; site update pending",
      summary_rebuild_current: "source and public catalogue are aligned in this session"
    },
    catalogue_series_editor: {
      load_failed_error: "Failed to load catalogue source data for the series editor.",
      search_placeholder: "find series by title",
      search_empty: "Enter a series title or id.",
      search_no_match: "No matching series records.",
      missing_series_param: "Search for a series by title.",
      unknown_series_error: "Unknown series id: {series_id}.",
      open_button: "Open",
      save_button: "Save",
      build_button: "Update site now",
      delete_button: "Delete",
      save_mode_template: "Save mode: {mode}",
      save_mode_local_server: "Local server",
      save_mode_offline: "Unavailable",
      save_mode_unavailable: "Unavailable",
      save_mode_unavailable_hint: "Local catalogue server unavailable. Save is disabled.",
      context_loaded: "Editing source metadata for series {series_id}.",
      dirty_warning: "Unsaved source changes.",
      save_status_loaded: "Loaded series {series_id}.",
      save_status_no_changes: "No changes to save.",
      save_status_validation_error: "Fix validation errors before saving.",
      save_status_saving: "Saving source record…",
      save_status_saving_and_updating: "Saving source record and updating site…",
      save_status_conflict: "Source record changed since this page loaded. Reload the series before saving again.",
      save_status_failed: "Source save failed.",
      save_result_success: "Source saved at {saved_at}. Public catalogue update still pending.",
      save_result_success_applied: "Saved source changes and updated the public catalogue at {saved_at}.",
      save_result_success_partial: "Source changes were saved at {saved_at}, but the site update failed. Retry Update site now.",
      save_result_unchanged: "Source already matches the current form values.",
      build_preview_template: "Site update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
      build_preview_search_yes: "yes",
      build_preview_search_no: "no",
      build_preview_failed: "Build preview unavailable.",
      build_status_running: "Updating site…",
      build_status_success: "Site update completed.",
      build_status_failed: "Site update failed.",
      build_result_success: "Public catalogue updated at {completed_at}. Build Activity updated.",
      field_invalid_status: "Use blank, draft, or published.",
      field_invalid_year: "Use a whole year or leave blank.",
      field_invalid_primary_work: "Primary work must be a current member of this series.",
      members_heading: "member works",
      members_search_placeholder: "find member work by id",
      members_search_no_match: "No matching member work ids.",
      members_empty: "No works currently belong to this series.",
      members_more_count: "showing {visible} of {total}",
      members_add_placeholder: "add work by id",
      members_add_button: "Add",
      members_add_missing: "Enter a work id to add.",
      members_add_unknown: "Unknown work id: {work_id}.",
      members_add_exists: "Work {work_id} is already in this series.",
      members_action_primary: "Make primary",
      members_action_remove: "Remove",
      members_primary_badge: "primary",
      members_position: "position {position}",
      members_remove_blocked: "Change primary_work_id before removing work {work_id}.",
      summary_public_link: "Open public series page",
      summary_member_count: "member works",
      summary_rebuild_needed: "source saved; site update pending",
      summary_rebuild_current: "source and public catalogue are aligned in this session"
    },
    catalogue_new_series_editor: {
      create_button: "Create"
    },
    search: {
      load_failed_error: "Failed to load search data.",
      loading: "loading search index…",
      prompt: "Enter a search query.",
      no_results: "No results.",
      results_count: "{count} results",
      results_count_one: "1 result",
      results_count_visible: "Showing {visible} of {count} results",
      load_more: "more",
      result_meta_separator: " • ",
      result_kind_work: "work",
      result_kind_series: "series",
      result_kind_moment: "moment"
    }
  }
};

const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
let studioConfigPromise = null;

export {
  DEFAULT_STUDIO_CONFIG
};

export async function loadStudioConfig() {
  if (!studioConfigPromise) {
    studioConfigPromise = fetch(buildAssetUrl(new URL("../data/studio_config.json", import.meta.url).href), { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => mergeConfig(DEFAULT_STUDIO_CONFIG, data))
      .catch((error) => {
        console.warn("studio_config: using defaults after config load failure", error);
        return cloneJson(DEFAULT_STUDIO_CONFIG);
      });
  }
  return studioConfigPromise;
}

export function getStudioGroups(config) {
  const fallback = DEFAULT_STUDIO_CONFIG.analysis.groups.ordered;
  return sanitizeStringArray(pathValue(config, ["analysis", "groups", "ordered"]), fallback);
}

export function getStudioCoverageGroups(config) {
  const fallback = getStudioGroups(config);
  return sanitizeStringArray(pathValue(config, ["analysis", "groups", "coverage_groups"]), fallback);
}

export function getStudioDataPath(config, key) {
  const path = pathValue(config, ["paths", "data", "studio", key]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getSiteDataPath(config, key) {
  const path = pathValue(config, ["paths", "data", "site", key]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getSearchScopeDataPath(config, scope, key = "index") {
  const normalizedScope = normalize(scope);
  const path = pathValue(config, ["paths", "data", "search", "scopes", normalizedScope, key]);
  if (typeof path === "string" && path.trim()) {
    return resolveSiteAssetPath(path);
  }

  if (normalizedScope === "catalogue") {
    const legacyPath = pathValue(config, ["paths", "data", "site", "search_index"]);
    if (typeof legacyPath === "string" && legacyPath.trim()) {
      return resolveSiteAssetPath(legacyPath);
    }
  }

  return "";
}

export function getSearchPolicyPath(config) {
  const path = pathValue(config, ["paths", "data", "search", "policy"]);
  return resolveSiteAssetPath(typeof path === "string" ? path : "");
}

export function getStudioRoute(config, key) {
  const path = pathValue(config, ["paths", "routes", key]);
  return resolveSitePath(typeof path === "string" ? path : "");
}

export function getStudioText(config, key, fallback = "", tokens = null) {
  const pathKeys = ["ui_text", ...String(key || "").split(".").filter(Boolean)];
  const value = pathValue(config, pathKeys);
  const source = typeof value === "string" ? value : fallback;
  return applyTextTokens(source, tokens);
}

export function computeStudioTagMetrics(assignedTags, registry, config) {
  const groups = getStudioGroups(config);
  const coverageGroups = getStudioCoverageGroups(config);
  const deprecatedStatuses = new Set(sanitizeStringArray(
    pathValue(config, ["analysis", "rag", "deprecated_statuses"]),
    DEFAULT_STUDIO_CONFIG.analysis.rag.deprecated_statuses
  ));
  const completenessCfg = mergeConfig(
    DEFAULT_STUDIO_CONFIG.analysis.rag.completeness,
    pathValue(config, ["analysis", "rag", "completeness"])
  );
  const counts = Object.fromEntries(groups.map((group) => [group, 0]));
  let nUnknown = 0;
  let nDeprecated = 0;
  let nTotal = 0;

  const uniqueTags = Array.from(
    new Set((Array.isArray(assignedTags) ? assignedTags : []).map((tag) => normalize(tag)).filter(Boolean))
  );

  for (const tagId of uniqueTags) {
    nTotal += 1;
    const reg = registry.get(tagId);
    if (!reg) {
      nUnknown += 1;
      continue;
    }

    if (reg.group in counts) counts[reg.group] += 1;
    if (deprecatedStatuses.has(normalize(reg.status))) nDeprecated += 1;
  }

  const presentGroups = coverageGroups.filter((group) => Number(counts[group] || 0) > 0);
  const missingGroups = coverageGroups.filter((group) => Number(counts[group] || 0) === 0);
  const groupsPresent = presentGroups.length;
  const denominator = Math.max(
    1,
    Number(completenessCfg.group_coverage_denominator) || coverageGroups.length || 1
  );
  const tagBonusCap = Math.max(1, Number(completenessCfg.tag_bonus_cap_at_total_tags) || 1);
  const tagBonusMax = Math.max(0, Number(completenessCfg.tag_bonus_max) || 0);
  const scoreCap = Math.max(0, Number(completenessCfg.score_cap) || 1);
  const completenessBase = groupsPresent / denominator;
  const tagBonus = (Math.min(nTotal, tagBonusCap) / tagBonusCap) * tagBonusMax;
  const completeness = Math.min(scoreCap, completenessBase + tagBonus);

  return {
    nTotal,
    nUnknown,
    nDeprecated,
    counts,
    groupsPresent,
    presentGroups,
    missingGroups,
    completeness
  };
}

export function computeStudioRag(metrics, config) {
  const rules = mergeConfig(
    DEFAULT_STUDIO_CONFIG.analysis.rag.rules,
    pathValue(config, ["analysis", "rag", "rules"])
  );
  const redRule = rules.red || {};
  const amberRule = rules.amber || {};
  const totalTagsEq = Number(redRule.if_total_tags_eq);
  const unknownTagsGt = Number(redRule.if_unknown_tags_gt);
  if (
    (Number.isFinite(totalTagsEq) && metrics.nTotal === totalTagsEq) ||
    (Number.isFinite(unknownTagsGt) && metrics.nUnknown > unknownTagsGt)
  ) {
    return "red";
  }

  const groupsPresentLte = Number(amberRule.if_groups_present_lte);
  const totalTagsLt = Number(amberRule.if_total_tags_lt);
  const deprecatedTagsGt = Number(amberRule.if_deprecated_tags_gt);
  const missingAllGroups = sanitizeStringArray(amberRule.if_missing_all_groups, []);
  const isMissingAll = missingAllGroups.length > 0 && missingAllGroups.every((group) => metrics.missingGroups.includes(group));
  if (
    (Number.isFinite(groupsPresentLte) && metrics.groupsPresent <= groupsPresentLte) ||
    (Number.isFinite(totalTagsLt) && metrics.nTotal < totalTagsLt) ||
    (Number.isFinite(deprecatedTagsGt) && metrics.nDeprecated > deprecatedTagsGt) ||
    isMissingAll
  ) {
    return "amber";
  }

  return "green";
}

export function buildStudioRagTooltip(metrics) {
  const groupsLabel = metrics.presentGroups.length ? metrics.presentGroups.join(", ") : "none";
  const missingLabel = metrics.missingGroups.length ? metrics.missingGroups.join(", ") : "none";
  return (
    `tags: ${metrics.nTotal}; groups: ${groupsLabel}; missing: ${missingLabel}; ` +
    `unknown: ${metrics.nUnknown}; deprecated: ${metrics.nDeprecated}; ` +
    `completeness: ${metrics.completeness.toFixed(2)}`
  );
}

function deriveSiteBasePath(importUrl) {
  const pathname = new URL(importUrl).pathname || "";
  const marker = "/assets/studio/js/";
  const index = pathname.indexOf(marker);
  if (index < 0) return "";
  return pathname.slice(0, index).replace(/\/+$/, "");
}

function resolveSitePath(path) {
  if (!path) return "";
  if (/^[a-z]+:\/\//i.test(path)) return path;
  const cleanPath = `/${String(path).replace(/^\/+/, "")}`;
  return `${SITE_BASE_PATH}${cleanPath}`.replace(/\/{2,}/g, "/");
}

function resolveSiteAssetPath(path) {
  return buildAssetUrl(resolveSitePath(path));
}

function buildAssetUrl(path) {
  const resolvedPath = String(path || "");
  if (!resolvedPath) return "";

  const assetVersion = readAssetVersion(import.meta.url);
  if (!assetVersion) return resolvedPath;

  const [base, hash = ""] = resolvedPath.split("#", 2);
  const separator = base.includes("?") ? "&" : "?";
  return `${base}${separator}v=${encodeURIComponent(assetVersion)}${hash ? `#${hash}` : ""}`;
}

function readAssetVersion(importUrl = "") {
  try {
    const importVersion = new URL(importUrl).searchParams.get("v");
    if (importVersion) return importVersion;
  } catch (_error) {
    // Ignore malformed import URLs and continue to DOM-based lookup.
  }

  if (typeof document !== "undefined") {
    const meta = document.querySelector('meta[name="dlf-asset-version"]');
    const value = meta ? String(meta.getAttribute("content") || "").trim() : "";
    if (value) return value;
  }

  return "";
}

function pathValue(obj, keys) {
  let current = obj;
  for (const key of keys) {
    if (!current || typeof current !== "object" || !(key in current)) return undefined;
    current = current[key];
  }
  return current;
}

function sanitizeStringArray(value, fallback) {
  const source = Array.isArray(value) ? value : fallback;
  const out = [];
  const seen = new Set();
  for (const raw of source) {
    const item = normalize(raw);
    if (!item || seen.has(item)) continue;
    seen.add(item);
    out.push(item);
  }
  return out;
}

function applyTextTokens(text, tokens) {
  const template = typeof text === "string" ? text : "";
  if (!tokens || typeof tokens !== "object") return template;
  return template.replace(/\{([a-z0-9_]+)\}/gi, (match, key) => {
    if (!(key in tokens)) return match;
    const value = tokens[key];
    return value == null ? "" : String(value);
  });
}

function mergeConfig(base, override) {
  const baseValue = cloneJson(base);
  if (!override || typeof override !== "object" || Array.isArray(override)) return baseValue;
  const output = baseValue;
  for (const [key, value] of Object.entries(override)) {
    if (Array.isArray(value)) {
      output[key] = value.slice();
      continue;
    }
    if (value && typeof value === "object") {
      output[key] = mergeConfig(output[key] || {}, value);
      continue;
    }
    output[key] = value;
  }
  return output;
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}
