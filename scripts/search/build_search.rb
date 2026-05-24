#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "json"
require "optparse"
require "openssl"
require "pathname"
require "time"

DEFAULT_SCOPE = "catalogue"
SEARCH_BUILD_CONFIG_PATH = "scripts/search/build_config.json"
SEARCH_BUILD_TARGETED_POLICIES = %w[full_rebuild record_update additive_only].freeze
SEARCH_BUILD_TARGETED_POLICY_OPERATIONS = {
  "record_update" => %w[create update delete],
  "additive_only" => %w[create]
}.freeze
CATALOGUE_TARGET_KINDS = %w[moment series work].freeze
CATALOGUE_DEFAULTS = {
  schema: "search_index_v1",
  output_path: "assets/data/search/catalogue/index.json",
  series_index_path: "assets/data/series_index.json",
  works_index_path: "assets/data/works_index.json",
  moments_index_path: "assets/data/moments_index.json",
  tag_assignments_path: "studio/data/canonical/analytics/tag-assignments.json",
  tag_registry_path: "studio/data/canonical/analytics/tag-registry.json"
}.freeze

CatalogueSearchTarget = Struct.new(
  :kind,
  :id,
  keyword_init: true
)

class CatalogueSearchDataBuilder
  def initialize(
    scope:,
    output_path: nil,
    series_index_path: nil,
    works_index_path: nil,
    moments_index_path: nil,
    tag_assignments_path: nil,
    tag_registry_path: nil
  )
    @scope = normalize(scope)
    @repo_root = Pathname(__dir__).parent.parent.realpath
    @schema = CATALOGUE_DEFAULTS.fetch(:schema)
    @output_path = resolve_path(output_path || CATALOGUE_DEFAULTS.fetch(:output_path))
    @series_index_path = resolve_path(series_index_path || CATALOGUE_DEFAULTS.fetch(:series_index_path))
    @works_index_path = resolve_path(works_index_path || CATALOGUE_DEFAULTS.fetch(:works_index_path))
    @moments_index_path = resolve_path(moments_index_path || CATALOGUE_DEFAULTS.fetch(:moments_index_path))
    @tag_assignments_path = resolve_path(tag_assignments_path || CATALOGUE_DEFAULTS.fetch(:tag_assignments_path))
    @tag_registry_path = resolve_path(tag_registry_path || CATALOGUE_DEFAULTS.fetch(:tag_registry_path))
    @works_json_dir = resolve_path("assets/works/index")
    @work_search_metadata_by_id = {}
  end

  def run(write:, force:, only_records: nil)
    validate_scope!
    validate_search_build_config!
    target_records = normalize_target_catalogue_records(only_records)
    payload, diagnostics = build_catalogue_payload(target_records: target_records)
    validate_entry_source_families!(payload)
    write_payload(payload, write: write, force: force, diagnostics: diagnostics)
  end

  private

  def validate_scope!
    return if @scope == "catalogue"

    raise SystemExit, "Unsupported catalogue search scope: #{@scope}"
  end

  def validate_search_build_config!
    @search_build_config = load_json(resolve_path(SEARCH_BUILD_CONFIG_PATH))
    unless @search_build_config.is_a?(Hash)
      raise SystemExit, "Invalid search build config: expected top-level object"
    end

    version = normalize_text(@search_build_config["search_build_config_version"])
    unless version == "search_build_config_v2"
      raise SystemExit, "Invalid search build config version: #{version.empty? ? '(missing)' : version}"
    end

    source_families = @search_build_config["source_families"]
    unless source_families.is_a?(Hash) && !source_families.empty?
      raise SystemExit, "Invalid search build config: expected source_families object"
    end
    validate_source_families!(source_families)

    scopes = @search_build_config["scopes"]
    unless scopes.is_a?(Hash) && scopes.key?("catalogue")
      raise SystemExit, "Invalid search build config: expected catalogue scope"
    end
    validate_scope_build_config!(scopes.fetch("catalogue"), source_families)
  end

  def validate_source_families!(source_families)
    source_families.each do |family_id, raw_family|
      unless raw_family.is_a?(Hash)
        raise SystemExit, "Invalid search build config: source family #{family_id} must be an object"
      end

      scopes = raw_family["scopes"]
      unless scopes.is_a?(Array) && scopes.map { |scope| normalize(scope) } == ["catalogue"]
        raise SystemExit, "Invalid search build config: source family #{family_id} must be catalogue-owned"
      end
      validate_targeted_policy!(raw_family, "source family #{family_id}")
      if normalize_text(raw_family["fallback"]) != "full_rebuild"
        raise SystemExit, "Invalid search build config: source family #{family_id} fallback must be full_rebuild"
      end
    end
  end

  def validate_scope_build_config!(scope_config, source_families)
    unless scope_config.is_a?(Hash)
      raise SystemExit, "Invalid search build config: catalogue scope must be an object"
    end
    fields = scope_config["fields"]
    unless fields.is_a?(Hash) && !fields.empty?
      raise SystemExit, "Invalid search build config: catalogue scope needs fields"
    end
    validate_targeted_policy!(scope_config, "scope catalogue")

    fields.each do |field_name, field_config|
      unless field_config.is_a?(Hash)
        raise SystemExit, "Invalid search build config: field catalogue.#{field_name} must be an object"
      end
      families = Array(field_config["source_families"]).map { |family| normalize_text(family) }.reject(&:empty?)
      if families.empty?
        raise SystemExit, "Invalid search build config: field catalogue.#{field_name} needs source_families"
      end
      unknown_family = families.find { |family| !source_families.key?(family) }
      if unknown_family
        raise SystemExit, "Invalid search build config: field catalogue.#{field_name} references unknown source family #{unknown_family}"
      end
    end
  end

  def validate_targeted_policy!(config, label)
    if config.key?("targeted")
      raise SystemExit, "Invalid search build config: #{label} uses obsolete targeted boolean; use targeted_policy"
    end

    policy = normalize_text(config["targeted_policy"])
    unless SEARCH_BUILD_TARGETED_POLICIES.include?(policy)
      raise SystemExit, "Invalid search build config: #{label} targeted_policy must be one of #{SEARCH_BUILD_TARGETED_POLICIES.join(', ')}"
    end

    operations = config["targeted_operations"]
    if policy == "full_rebuild"
      if operations
        raise SystemExit, "Invalid search build config: #{label} targeted_operations is only valid for targeted policies"
      end
      return
    end

    unless operations.is_a?(Array) && operations.all? { |operation| !normalize_text(operation).empty? }
      raise SystemExit, "Invalid search build config: #{label} targeted_operations must be a non-empty string array"
    end
    unsupported_operation = operations.map { |operation| normalize_text(operation) }.find do |operation|
      !SEARCH_BUILD_TARGETED_POLICY_OPERATIONS.fetch(policy).include?(operation)
    end
    if unsupported_operation
      raise SystemExit, "Invalid search build config: #{label} targeted_operations includes unsupported #{unsupported_operation} for #{policy}"
    end
  end

  def validate_entry_source_families!(payload)
    scope_config = @search_build_config.dig("scopes", "catalogue")
    fields = scope_config.is_a?(Hash) ? scope_config["fields"] : nil
    unless fields.is_a?(Hash)
      raise SystemExit, "Invalid search build config: catalogue fields unavailable"
    end

    entries = payload.is_a?(Hash) ? payload["entries"] : nil
    return unless entries.is_a?(Array)

    emitted_fields = entries.flat_map { |entry| entry.is_a?(Hash) ? entry.keys : [] }.uniq.sort
    missing_fields = emitted_fields.reject { |field| fields.key?(field) }
    return if missing_fields.empty?

    raise SystemExit, "Invalid search build config: catalogue missing field source declarations for #{missing_fields.join(', ')}"
  end

  def build_catalogue_payload(target_records: nil)
    target_records ||= []
    series_payload = load_index_hash(@series_index_path, "series")
    works_payload = load_index_hash(@works_index_path, "works")
    moments_payload = load_index_hash(@moments_index_path, "moments")
    assignments_series = load_assignments_series
    tag_label_by_id = load_tag_label_by_id
    series_title_by_id = series_payload.to_h { |series_id, row| [series_id, normalize_text(row["title"])] }

    entries = []

    series_payload.keys.sort.each do |series_id|
      series_record = series_payload[series_id]
      assignment_row = assignments_series.fetch(series_id, {})
      series_tag_ids = assignment_tag_ids_from_rows(assignment_row["tags"])
      series_tag_labels = series_tag_ids.filter_map { |tag_id| tag_label_by_id[tag_id] }

      entries << build_catalogue_entry(
        kind: "series",
        item_id: series_id,
        title: normalize_text(series_record["title"]).empty? ? series_id : normalize_text(series_record["title"]),
        href: "/series/#{series_id}/",
        year: series_record["year"],
        display_meta: normalize_text(series_record["year_display"]),
        series_type: normalize_text(series_record["series_type"]),
        tag_ids: series_tag_ids,
        tag_labels: series_tag_labels
      )
    end

    works_payload.keys.sort.each do |work_id|
      work_record = works_payload[work_id]
      work_search_metadata = resolve_work_search_metadata(work_id)
      series_ids = normalize_string_array(work_record["series_ids"])
      series_titles = series_ids.map { |series_id| series_title_by_id.fetch(series_id, series_id) }
      work_tag_ids = collect_work_tag_ids(assignments_series, series_ids, work_id)
      work_tag_labels = work_tag_ids.filter_map { |tag_id| tag_label_by_id[tag_id] }

      entries << build_catalogue_entry(
        kind: "work",
        item_id: work_id,
        title: normalize_text(work_record["title"]).empty? ? work_id : normalize_text(work_record["title"]),
        href: "/works/#{work_id}/",
        year: work_record["year"],
        display_meta: normalize_text(work_record["year_display"]),
        series_ids: series_ids,
        series_titles: series_titles,
        medium_type: work_search_metadata["medium_type"],
        medium_caption: work_search_metadata["medium_caption"],
        tag_ids: work_tag_ids,
        tag_labels: work_tag_labels
      )
    end

    moments_payload.keys.sort.each do |moment_id|
      moment_record = moments_payload[moment_id]

      entries << build_catalogue_entry(
        kind: "moment",
        item_id: moment_id,
        title: normalize_text(moment_record["title"]).empty? ? moment_id : normalize_text(moment_record["title"]),
        href: "/moments/#{moment_id}/",
        date: normalize_text(moment_record["date"]),
        display_meta: normalize_text(moment_record["date_display"]).empty? ? normalize_text(moment_record["date"]) : normalize_text(moment_record["date_display"])
      )
    end

    ordered_entries = entries.sort_by do |entry|
      [
        normalize_text(entry["kind"]),
        numeric_aware_sort_key(entry["title"]),
        normalize_text(entry["id"])
      ]
    end

    return [build_catalogue_search_payload(ordered_entries), nil] if target_records.empty?

    build_targeted_catalogue_payload(ordered_entries, target_records)
  end

  def write_payload(payload, write:, force:, diagnostics: nil)
    count = payload.dig("header", "count")
    relative_output_path = relative_path(@output_path)
    existing_version = extract_existing_version(@output_path)
    payload_version = payload.dig("header", "version")

    targeted_changes = diagnostics && (diagnostics[:changed].to_i.positive? || diagnostics[:removed].to_i.positive?)
    if existing_version == payload_version && !force && !targeted_changes
      print_skip_message(relative_output_path, write, diagnostics)
      return payload
    end

    unless write
      print_dry_run_message(relative_output_path, count, diagnostics)
      return payload
    end

    FileUtils.mkdir_p(@output_path.dirname)
    File.write(@output_path, JSON.pretty_generate(payload) + "\n")
    print_write_message(relative_output_path, count, diagnostics)
    payload
  end

  def print_skip_message(relative_output_path, write, diagnostics)
    if diagnostics
      verb = write ? "Wrote" : "Would write"
      puts "Targeted search index JSON done. #{verb}: 0. Skipped: 1. Changed: #{diagnostics[:changed]}. Removed: #{diagnostics[:removed]}. Unchanged: #{diagnostics[:unchanged]}. Full fallback: #{diagnostics[:full_fallback]}. Path: #{relative_output_path}"
      return
    end

    if write
      puts "Search index JSON done. Wrote: 0. Skipped: 1. Path: #{relative_output_path}"
    else
      puts "Search index JSON done. Would write: 0. Skipped: 1. Path: #{relative_output_path}"
    end
  end

  def print_dry_run_message(relative_output_path, count, diagnostics)
    if diagnostics
      puts "Targeted dry run: #{count} #{@scope} search entries"
      puts "Would write: 1. Skipped: 0. Changed: #{diagnostics[:changed]}. Removed: #{diagnostics[:removed]}. Unchanged: #{diagnostics[:unchanged]}. Full fallback: #{diagnostics[:full_fallback]}. Path: #{relative_output_path}"
      return
    end

    puts "Dry run: #{count} #{@scope} search entries"
    puts "Would write: #{relative_output_path}"
  end

  def print_write_message(relative_output_path, count, diagnostics)
    if diagnostics
      puts "Targeted search index JSON done. Wrote: 1. Skipped: 0. Changed: #{diagnostics[:changed]}. Removed: #{diagnostics[:removed]}. Unchanged: #{diagnostics[:unchanged]}. Full fallback: #{diagnostics[:full_fallback]}. Path: #{relative_output_path}"
      return
    end

    puts "Wrote #{relative_output_path} with #{count} #{@scope} search entries"
  end

  def load_index_hash(path, key)
    payload = load_json(path)
    rows = payload.is_a?(Hash) ? payload[key] : nil
    unless rows.is_a?(Hash)
      raise SystemExit, "Invalid #{key} index payload: expected top-level #{key} object"
    end

    rows.transform_values { |value| value.is_a?(Hash) ? value : {} }
  end

  def load_assignments_series
    payload = load_json(@tag_assignments_path)
    series_rows = payload.is_a?(Hash) ? payload["series"] : nil
    return {} unless series_rows.is_a?(Hash)

    series_rows.transform_values { |value| value.is_a?(Hash) ? value : {} }
  end

  def load_tag_label_by_id
    payload = load_json(@tag_registry_path)
    tags = payload.is_a?(Hash) ? payload["tags"] : nil
    return {} unless tags.is_a?(Array)

    tags.each_with_object({}) do |raw_tag, acc|
      next unless raw_tag.is_a?(Hash)

      tag_id = normalize_search_text(raw_tag["tag_id"])
      label = normalize_text(raw_tag["label"])
      next if tag_id.empty? || label.empty?

      acc[tag_id] = label
    end
  end

  def load_json(path)
    unless path&.file?
      raise SystemExit, "Source JSON not found: #{relative_path(path)}"
    end

    JSON.parse(File.read(path, encoding: "utf-8"))
  rescue JSON::ParserError => e
    raise SystemExit, "Failed to parse JSON: #{relative_path(path)} (#{e.message})"
  end

  def build_targeted_catalogue_payload(entries, target_records)
    existing_payload = load_existing_search_payload
    unless existing_payload
      diagnostics = {
        changed: entries.length,
        removed: 0,
        unchanged: 0,
        full_fallback: 1
      }
      return [build_catalogue_search_payload(entries), diagnostics]
    end

    existing_entries = existing_payload["entries"]
    unless existing_entries.is_a?(Array)
      diagnostics = {
        changed: entries.length,
        removed: 0,
        unchanged: 0,
        full_fallback: 1
      }
      return [build_catalogue_search_payload(entries), diagnostics]
    end

    entry_by_key = entries.to_h { |entry| [catalogue_entry_key(entry), entry] }
    order_by_key = entries.each_with_index.to_h { |entry, index| [catalogue_entry_key(entry), index] }
    existing_by_key = existing_entries.each_with_object({}) do |entry, out|
      next unless entry.is_a?(Hash)

      entry_key = catalogue_entry_key(entry)
      next if entry_key.empty?

      out[entry_key] = entry
    end
    existing_order_by_key = existing_entries.each_with_index.to_h do |entry, index|
      [catalogue_entry_key(entry), index]
    end

    changed = 0
    unchanged = 0

    target_records.each do |target|
      target_key = catalogue_record_key(target.kind, target.id)
      next_entry = entry_by_key[target_key]
      abort "Targeted catalogue search create could not find source record #{target_key}" unless next_entry

      current_entry = existing_by_key[target_key]
      if current_entry.nil?
        existing_by_key[target_key] = next_entry
        changed += 1
      elsif current_entry == next_entry
        unchanged += 1
      else
        abort "Targeted catalogue search is additive-only; existing record #{target_key} requires a full catalogue search rebuild"
      end
    end

    merged_entries = existing_by_key.values.sort_by do |entry|
      entry_key = catalogue_entry_key(entry)
      [
        order_by_key.fetch(entry_key, entries.length + existing_order_by_key.fetch(entry_key, 0)),
        existing_order_by_key.fetch(entry_key, existing_entries.length)
      ]
    end

    payload = build_catalogue_search_payload(merged_entries)
    diagnostics = {
      changed: changed,
      removed: 0,
      unchanged: unchanged,
      full_fallback: 0
    }
    [payload, diagnostics]
  end

  def build_catalogue_search_payload(entries)
    version_payload = {
      "schema" => @schema,
      "entries" => entries
    }
    version = "blake2b-#{blake2b_payload_hash(version_payload)}"

    {
      "header" => {
        "schema" => @schema,
        "version" => version,
        "generated_at_utc" => Time.now.utc.iso8601,
        "count" => entries.length
      },
      "entries" => entries
    }
  end

  def build_catalogue_entry(
    kind:,
    item_id:,
    title:,
    href:,
    year: nil,
    date: nil,
    display_meta: nil,
    series_ids: [],
    series_titles: [],
    medium_type: nil,
    medium_caption: nil,
    series_type: nil,
    tag_ids: [],
    tag_labels: []
  )
    normalized_series_ids = normalize_string_array(series_ids)
    normalized_series_titles = normalize_string_array(series_titles)
    normalized_tag_ids = normalize_string_array(tag_ids)
    normalized_tag_labels = normalize_string_array(tag_labels)
    search_terms = build_search_tokens(
      item_id,
      title,
      display_meta,
      year.nil? ? nil : year.to_s,
      date,
      normalized_series_ids,
      normalized_series_titles,
      medium_type,
      medium_caption,
      series_type
    )

    {
      "kind" => kind,
      "id" => normalize_text(item_id),
      "title" => normalize_text(title),
      "href" => normalize_text(href),
      "year" => year,
      "date" => normalize_text(date),
      "display_meta" => normalize_text(display_meta),
      "series_ids" => normalized_series_ids,
      "series_titles" => normalized_series_titles,
      "medium_type" => normalize_text(medium_type),
      "series_type" => normalize_text(series_type),
      "tag_ids" => normalized_tag_ids,
      "tag_labels" => normalized_tag_labels,
      "search_terms" => search_terms,
      "search_text" => search_terms.join(" ")
    }.reject { |key, value| compact_catalogue_field?(key, value) }
  end

  def collect_work_tag_ids(assignments_series, series_ids, work_id)
    tag_ids = []
    seen = {}

    series_ids.each do |series_id|
      assignment_row = assignments_series.fetch(series_id, {})
      append_unique_tags(tag_ids, seen, assignment_tag_ids_from_rows(assignment_row["tags"]))
      work_rows = assignment_row["works"]
      next unless work_rows.is_a?(Hash)

      work_row = work_rows.fetch(work_id, {})
      append_unique_tags(tag_ids, seen, assignment_tag_ids_from_rows(work_row["tags"]))
    end

    tag_ids
  end

  def append_unique_tags(out, seen, tag_ids)
    tag_ids.each do |tag_id|
      next if seen[tag_id]

      seen[tag_id] = true
      out << tag_id
    end
  end

  def assignment_tag_ids_from_rows(tags_value)
    return [] unless tags_value.is_a?(Array)

    tags_value.each_with_object([]) do |raw_tag, out|
      tag_id =
        if raw_tag.is_a?(Hash)
          normalize_search_text(raw_tag["tag_id"])
        else
          normalize_search_text(raw_tag)
        end

      next if tag_id.empty? || out.include?(tag_id)

      out << tag_id
    end
  end

  def build_search_tokens(*values)
    tokens = []
    seen = {}

    values.each do |value|
      Array(value).each do |item|
        normalized = normalize_search_text(item)
        next if normalized.empty?

        ([normalized] + normalized.gsub(/[^a-z0-9]+/, " ").split).each do |candidate|
          token = normalize_search_text(candidate)
          next if token.empty? || seen[token]

          seen[token] = true
          tokens << token
        end
      end
    end

    tokens
  end

  def resolve_work_search_metadata(work_id)
    cached = @work_search_metadata_by_id[work_id]
    return cached if cached

    work_json_path = @works_json_dir.join("#{work_id}.json")
    metadata = {
      "medium_type" => "",
      "medium_caption" => ""
    }
    return metadata unless work_json_path.file?

    payload = load_json(work_json_path)
    work_payload = payload.is_a?(Hash) ? payload["work"] : nil
    return metadata unless work_payload.is_a?(Hash)

    metadata["medium_type"] = normalize_text(work_payload["medium_type"])
    metadata["medium_caption"] = normalize_text(work_payload["medium_caption"])
    @work_search_metadata_by_id[work_id] = metadata
  end

  def blake2b_payload_hash(payload)
    canonical = JSON.generate(
      canonicalize_for_hash(payload),
      ascii_only: false,
      space: nil,
      array_nl: "",
      object_nl: ""
    )
    OpenSSL::Digest.new("BLAKE2b512").digest(canonical)[0, 16].unpack1("H*")
  end

  def canonicalize_for_hash(value)
    case value
    when Hash
      value.keys.sort.each_with_object({}) do |key, out|
        out[key] = canonicalize_for_hash(value[key])
      end
    when Array
      value.map { |item| canonicalize_for_hash(item) }
    else
      value
    end
  end

  def numeric_aware_sort_key(value)
    normalize_text(value).gsub(/\d+/) { |digits| digits.rjust(3, "0") }
  end

  def normalize_string_array(values)
    Array(values).map { |value| normalize_text(value) }.reject(&:empty?)
  end

  def normalize_search_text(value)
    normalize_text(value).downcase.gsub(/\s+/, " ").strip
  end

  def normalize_text(value)
    String(value || "").strip
  end

  def normalize(value)
    normalize_text(value).downcase
  end

  def resolve_path(path)
    return nil if path.nil?

    @repo_root.join(path).expand_path
  end

  def extract_existing_version(path)
    return nil unless path&.file?

    payload = JSON.parse(File.read(path, encoding: "utf-8"))
    header = payload.is_a?(Hash) ? payload["header"] : nil
    return nil unless header.is_a?(Hash)

    normalize_text(header["version"])
  rescue JSON::ParserError
    nil
  end

  def load_existing_search_payload
    return nil unless @output_path&.file?

    payload = JSON.parse(File.read(@output_path, encoding: "utf-8"))
    return nil unless payload.is_a?(Hash)

    payload
  rescue JSON::ParserError
    nil
  end

  def normalize_target_catalogue_records(values)
    seen = {}
    Array(values).flat_map { |value| normalize_text(value).split(",") }.filter_map do |raw_record|
      record = normalize_text(raw_record)
      next if record.empty?

      kind, id = record.split(":", 2).map { |part| normalize_text(part) }
      abort "Targeted catalogue records must use kind:id form" if kind.empty? || id.empty?

      kind = normalize(kind)
      unless CATALOGUE_TARGET_KINDS.include?(kind)
        abort "Targeted catalogue record kind must be one of #{CATALOGUE_TARGET_KINDS.join(', ')}"
      end

      key = catalogue_record_key(kind, id)
      next if seen[key]

      seen[key] = true
      CatalogueSearchTarget.new(kind: kind, id: id)
    end
  end

  def catalogue_entry_key(entry)
    return "" unless entry.is_a?(Hash)

    catalogue_record_key(entry["kind"], entry["id"])
  end

  def catalogue_record_key(kind, id)
    "#{normalize(kind)}:#{normalize_text(id)}"
  end

  def compact_catalogue_field?(key, value)
    return false if %w[series_ids series_titles tag_ids tag_labels].include?(key)

    empty_scalar?(value)
  end

  def empty_scalar?(value)
    value.nil? || (value.respond_to?(:empty?) && value.empty?)
  end

  def relative_path(path)
    return "(unknown path)" if path.nil?

    path.relative_path_from(@repo_root).to_s
  rescue ArgumentError
    path.to_s
  end
end

options = {
  scope: DEFAULT_SCOPE,
  output_path: nil,
  series_index_path: nil,
  works_index_path: nil,
  moments_index_path: nil,
  tag_assignments_path: nil,
  tag_registry_path: nil,
  only_records: [],
  write: false,
  force: false
}

OptionParser.new do |parser|
  parser.banner = "Usage: ./scripts/build_search.rb [options]"

  parser.on("--scope NAME", "Catalogue search scope to build") do |value|
    options[:scope] = value
  end

  parser.on("--source-index PATH", "Docs Viewer-only source index path") do
    abort "Catalogue search does not support --source-index"
  end

  parser.on("--series-index PATH", "Canonical series index JSON path for catalogue scope") do |value|
    options[:series_index_path] = value
  end

  parser.on("--works-index PATH", "Canonical works index JSON path for catalogue scope") do |value|
    options[:works_index_path] = value
  end

  parser.on("--moments-index PATH", "Canonical moments index JSON path for catalogue scope") do |value|
    options[:moments_index_path] = value
  end

  parser.on("--tag-assignments PATH", "Tag assignments JSON path for catalogue scope") do |value|
    options[:tag_assignments_path] = value
  end

  parser.on("--tag-registry PATH", "Tag registry JSON path for catalogue scope") do |value|
    options[:tag_registry_path] = value
  end

  parser.on("--output PATH", "Generated search index output path") do |value|
    options[:output_path] = value
  end

  parser.on("--only-doc-ids IDS", "Docs Viewer-only targeted search ids") do
    abort "Catalogue search does not support --only-doc-ids"
  end

  parser.on("--only-records RECORDS", "Comma-separated kind:id records for additive catalogue search updates") do |value|
    options[:only_records] << value
  end

  parser.on("--remove-missing", "Docs Viewer-only targeted missing-record removal") do
    abort "Catalogue search does not support --remove-missing"
  end

  parser.on("--write", "Persist generated files (default is dry-run)") do
    options[:write] = true
  end

  parser.on("--force", "Write even when the content version matches") do
    options[:force] = true
  end
end.parse!(ARGV)

CatalogueSearchDataBuilder.new(
  scope: options[:scope],
  output_path: options[:output_path],
  series_index_path: options[:series_index_path],
  works_index_path: options[:works_index_path],
  moments_index_path: options[:moments_index_path],
  tag_assignments_path: options[:tag_assignments_path],
  tag_registry_path: options[:tag_registry_path]
).run(
  write: options[:write],
  force: options[:force],
  only_records: options[:only_records]
)
