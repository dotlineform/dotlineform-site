#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "json"
require "optparse"
require "openssl"
require "pathname"
require "time"

DEFAULT_SCOPE = "studio"
SCOPE_DEFAULTS = {
  "catalogue" => {
    kind: :catalogue,
    schema: "search_index_v1",
    output_path: "assets/data/search/catalogue/index.json",
    series_index_path: "assets/data/series_index.json",
    works_index_path: "assets/data/works_index.json",
    moments_index_path: "assets/data/moments_index.json",
    tag_assignments_path: "assets/studio/data/tag_assignments.json",
    tag_registry_path: "assets/studio/data/tag_registry.json"
  },
  "studio" => {
    kind: :docs,
    schema: "search_index_studio_v1",
    output_path: "assets/data/search/studio/index.json",
    source_index_path: "assets/data/docs/scopes/studio/index.json"
  },
  "library" => {
    kind: :docs,
    schema: "search_index_library_v1",
    output_path: "assets/data/search/library/index.json",
    source_index_path: "assets/data/docs/scopes/library/index.json"
  }
}.freeze

SearchDocRecord = Struct.new(
  :doc_id,
  :title,
  :last_updated,
  :parent_id,
  :viewer_url,
  :viewable,
  keyword_init: true
)

class SearchDataBuilder
  def initialize(
    scope:,
    source_index_path: nil,
    output_path: nil,
    series_index_path: nil,
    works_index_path: nil,
    moments_index_path: nil,
    tag_assignments_path: nil,
    tag_registry_path: nil
  )
    @scope = normalize(scope)
    @repo_root = Pathname(__dir__).parent.realpath
    @defaults = SCOPE_DEFAULTS.fetch(@scope, {})
    @kind = @defaults[:kind]
    @schema = @defaults[:schema] || "search_index_#{@scope}_v1"
    @output_path = resolve_path(output_path || @defaults[:output_path])
    @source_index_path = resolve_path(source_index_path || @defaults[:source_index_path]) if @kind == :docs
    @series_index_path = resolve_path(series_index_path || @defaults[:series_index_path]) if @kind == :catalogue
    @works_index_path = resolve_path(works_index_path || @defaults[:works_index_path]) if @kind == :catalogue
    @moments_index_path = resolve_path(moments_index_path || @defaults[:moments_index_path]) if @kind == :catalogue
    @tag_assignments_path = resolve_path(tag_assignments_path || @defaults[:tag_assignments_path]) if @kind == :catalogue
    @tag_registry_path = resolve_path(tag_registry_path || @defaults[:tag_registry_path]) if @kind == :catalogue
    @works_json_dir = resolve_path("assets/works/index") if @kind == :catalogue
    @work_search_metadata_by_id = {}
  end

  def run(write:, force:)
    validate_scope!
    payload = @kind == :catalogue ? build_catalogue_payload : build_docs_payload
    write_payload(payload, write: write, force: force)
  end

  private

  def validate_scope!
    return if SCOPE_DEFAULTS.key?(@scope)

    raise SystemExit, "Unsupported scope: #{@scope}. Current builder scopes: #{SCOPE_DEFAULTS.keys.join(', ')}"
  end

  def build_docs_payload
    docs = load_docs_index(@source_index_path)
    entries = build_docs_entries(docs)
    build_docs_search_payload(entries)
  end

  def build_catalogue_payload
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

    build_catalogue_search_payload(ordered_entries)
  end

  def write_payload(payload, write:, force:)
    count = payload.dig("header", "count")
    relative_output_path = relative_path(@output_path)
    existing_version = extract_existing_version(@output_path)
    payload_version = payload.dig("header", "version")

    if existing_version == payload_version && !force
      if write
        puts "Search index JSON done. Wrote: 0. Skipped: 1. Path: #{relative_output_path}"
      else
        puts "Search index JSON done. Would write: 0. Skipped: 1. Path: #{relative_output_path}"
      end
      return payload
    end

    unless write
      puts "Dry run: #{count} #{@scope} search entries"
      puts "Would write: #{relative_output_path}"
      return payload
    end

    FileUtils.mkdir_p(@output_path.dirname)
    File.write(@output_path, JSON.pretty_generate(payload) + "\n")
    puts "Wrote #{relative_output_path} with #{count} #{@scope} search entries"
    payload
  end

  def load_docs_index(path)
    payload = load_json(path)
    docs = payload.is_a?(Hash) ? payload["docs"] : nil
    unless docs.is_a?(Array)
      raise SystemExit, "Invalid docs index payload: expected top-level docs array"
    end

    docs.map do |row|
      next unless row.is_a?(Hash)

      doc_id = normalize_text(row["doc_id"])
      title = normalize_text(row["title"])
      viewer_url = normalize_text(row["viewer_url"])
      next if doc_id.empty? || title.empty? || viewer_url.empty?
      next unless boolean_field(row, "viewable", true)

      SearchDocRecord.new(
        doc_id: doc_id,
        title: title,
        last_updated: normalize_text(row["last_updated"]),
        parent_id: normalize_text(row["parent_id"]),
        viewer_url: viewer_url,
        viewable: true
      )
    end.compact
  end

  def boolean_field(row, key, default)
    return default unless row.key?(key)

    value = row[key]
    return value if value == true || value == false

    !%w[false 0 no off].include?(value.to_s.strip.downcase)
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

  def build_docs_entries(docs)
    title_by_id = docs.to_h { |doc| [doc.doc_id, doc.title] }

    docs.filter_map do |doc|
      next if doc.doc_id == "_archive"

      parent_title = doc.parent_id.empty? ? "" : normalize_text(title_by_id[doc.parent_id])
      display_meta = compact_join(doc.last_updated, parent_title)
      search_terms = build_search_tokens(doc.doc_id, doc.title, parent_title, doc.last_updated)

      {
        "id" => doc.doc_id,
        "kind" => "doc",
        "title" => doc.title,
        "href" => doc.viewer_url,
        "last_updated" => doc.last_updated,
        "parent_id" => doc.parent_id,
        "parent_title" => parent_title,
        "display_meta" => display_meta,
        "search_terms" => search_terms,
        "search_text" => search_terms.join(" ")
      }.reject { |_key, value| empty_scalar?(value) }
    end
  end

  def build_docs_search_payload(entries)
    version_payload = {
      "schema" => @schema,
      "entries" => entries
    }
    version = "blake2b-#{blake2b_payload_hash(version_payload)}"

    {
      "header" => {
        "schema" => @schema,
        "scope" => @scope,
        "version" => version,
        "generated_at_utc" => Time.now.utc.iso8601,
        "count" => entries.length
      },
      "entries" => entries
    }
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

  def compact_join(*parts)
    parts.map { |value| normalize_text(value) }.reject(&:empty?).join(" • ")
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
  source_index_path: nil,
  output_path: nil,
  series_index_path: nil,
  works_index_path: nil,
  moments_index_path: nil,
  tag_assignments_path: nil,
  tag_registry_path: nil,
  write: false,
  force: false
}

OptionParser.new do |parser|
  parser.banner = "Usage: ./scripts/build_search.rb [options]"

  parser.on("--scope NAME", "Search scope to build (current values: #{SCOPE_DEFAULTS.keys.join(', ')})") do |value|
    options[:scope] = value
  end

  parser.on("--source-index PATH", "Canonical docs index JSON path for docs-domain scopes") do |value|
    options[:source_index_path] = value
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

  parser.on("--write", "Persist generated files (default is dry-run)") do
    options[:write] = true
  end

  parser.on("--force", "Write even when the content version matches") do
    options[:force] = true
  end
end.parse!(ARGV)

SearchDataBuilder.new(
  scope: options[:scope],
  source_index_path: options[:source_index_path],
  output_path: options[:output_path],
  series_index_path: options[:series_index_path],
  works_index_path: options[:works_index_path],
  moments_index_path: options[:moments_index_path],
  tag_assignments_path: options[:tag_assignments_path],
  tag_registry_path: options[:tag_registry_path]
).run(write: options[:write], force: options[:force])
