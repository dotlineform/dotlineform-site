#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "json"
require "optparse"
require "openssl"
require "pathname"
require "set"
require "time"

DEFAULT_SCOPE = "studio"
DOCS_SCOPE_CONFIG_PATH = "docs-viewer/config/scopes/docs_scopes.json"

SearchDocRecord = Struct.new(
  :doc_id,
  :title,
  :last_updated,
  :parent_id,
  :viewer_url,
  :viewable,
  keyword_init: true
)

class DocsViewerSearchDataBuilder
  def initialize(scope:, source_index_path: nil, output_path: nil)
    @scope = normalize(scope)
    @repo_root = Pathname(__dir__).parent.parent.realpath
    @scope_config = docs_scope_config(@scope)
    @schema = "search_index_#{@scope}_v1"
    @source_index_path = resolve_path(source_index_path || File.join(@scope_config.fetch("output"), "index.json"))
    @output_path = resolve_path(output_path || File.join("assets/data/search", @scope, "index.json"))
  end

  def run(write:, force:, only_doc_ids: nil, remove_missing: false)
    target_doc_ids = normalize_target_doc_ids(only_doc_ids)
    validate_targeted_options!(target_doc_ids, remove_missing)
    payload, diagnostics = build_docs_payload(target_doc_ids: target_doc_ids, remove_missing: remove_missing)
    write_payload(payload, write: write, force: force, diagnostics: diagnostics)
  end

  private

  def docs_scope_config(scope)
    payload = load_json(resolve_path(DOCS_SCOPE_CONFIG_PATH))
    unless payload.is_a?(Hash) && payload["schema_version"] == "docs_scopes_v1"
      raise SystemExit, "Invalid Docs Viewer scope config: expected docs_scopes_v1"
    end

    scopes = payload["scopes"]
    unless scopes.is_a?(Array)
      raise SystemExit, "Invalid Docs Viewer scope config: expected scopes array"
    end

    config = scopes.find { |item| item.is_a?(Hash) && normalize(item["scope_id"]) == scope }
    return config if config

    available = scopes.filter_map { |item| normalize(item["scope_id"]) if item.is_a?(Hash) }.reject(&:empty?)
    raise SystemExit, "Unsupported docs search scope: #{scope}. Current Docs Viewer scopes: #{available.join(', ')}"
  end

  def build_docs_payload(target_doc_ids: nil, remove_missing: false)
    docs = load_docs_index(@source_index_path)
    entries = build_docs_entries(docs)
    return [build_docs_search_payload(entries), nil] if target_doc_ids.empty?

    build_targeted_docs_payload(entries, target_doc_ids, remove_missing)
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

  def load_docs_index(path)
    payload = load_json(path)
    docs = payload.is_a?(Hash) ? payload["docs"] : nil
    unless docs.is_a?(Array)
      raise SystemExit, "Invalid docs index payload: expected top-level docs array"
    end

    manage_only_ids = manage_only_doc_ids(payload, docs)
    docs.map do |row|
      next unless row.is_a?(Hash)

      doc_id = normalize_text(row["doc_id"])
      title = normalize_text(row["title"])
      viewer_url = normalize_text(row["viewer_url"])
      next if doc_id.empty? || title.empty? || viewer_url.empty?
      next if manage_only_ids.include?(doc_id)
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

  def manage_only_doc_ids(payload, docs)
    viewer_options = payload.is_a?(Hash) ? payload["viewer_options"] : nil
    roots = viewer_options.is_a?(Hash) ? Array(viewer_options["manage_only_tree_root_ids"]).map { |value| normalize_text(value) }.reject(&:empty?) : []
    return Set.new if roots.empty?

    by_parent = Hash.new { |hash, key| hash[key] = [] }
    docs.each do |row|
      next unless row.is_a?(Hash)

      doc_id = normalize_text(row["doc_id"])
      parent_id = normalize_text(row["parent_id"])
      next if doc_id.empty? || parent_id.empty?

      by_parent[parent_id] << doc_id
    end

    hidden = Set.new(roots)
    queue = roots.dup
    until queue.empty?
      current = queue.shift
      by_parent[current].each do |child_id|
        next if hidden.include?(child_id)

        hidden.add(child_id)
        queue << child_id
      end
    end
    hidden
  end

  def boolean_field(row, key, default)
    return default unless row.key?(key)

    value = row[key]
    return value if value == true || value == false

    !%w[false 0 no off].include?(value.to_s.strip.downcase)
  end

  def build_docs_entries(docs)
    title_by_id = docs.to_h { |doc| [doc.doc_id, doc.title] }

    docs.filter_map do |doc|
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

  def build_targeted_docs_payload(entries, target_doc_ids, remove_missing)
    existing_payload = load_existing_search_payload
    unless existing_payload
      diagnostics = {
        changed: entries.length,
        removed: 0,
        unchanged: 0,
        full_fallback: 1
      }
      return [build_docs_search_payload(entries), diagnostics]
    end

    existing_entries = existing_payload["entries"]
    unless existing_entries.is_a?(Array)
      diagnostics = {
        changed: entries.length,
        removed: 0,
        unchanged: 0,
        full_fallback: 1
      }
      return [build_docs_search_payload(entries), diagnostics]
    end

    entry_by_id = entries.to_h { |entry| [normalize_text(entry["id"]), entry] }
    order_by_id = entries.each_with_index.to_h { |entry, index| [normalize_text(entry["id"]), index] }
    existing_by_id = existing_entries.each_with_object({}) do |entry, out|
      next unless entry.is_a?(Hash)

      entry_id = normalize_text(entry["id"])
      next if entry_id.empty?

      out[entry_id] = entry
    end
    existing_order_by_id = existing_entries.each_with_index.to_h do |entry, index|
      [normalize_text(entry["id"]), index]
    end

    changed = 0
    removed = 0
    unchanged = 0

    target_doc_ids.each do |doc_id|
      next_entry = entry_by_id[doc_id]
      current_entry = existing_by_id[doc_id]

      if next_entry.nil?
        unless remove_missing
          abort "Targeted docs search update for #{@scope} requires --remove-missing when affected ids may be missing or non-viewable"
        end

        if current_entry
          existing_by_id.delete(doc_id)
          removed += 1
        else
          unchanged += 1
        end
        next
      end

      if current_entry == next_entry
        unchanged += 1
      else
        existing_by_id[doc_id] = next_entry
        changed += 1
      end
    end

    merged_entries = existing_by_id.values.sort_by do |entry|
      entry_id = normalize_text(entry["id"])
      [
        order_by_id.fetch(entry_id, entries.length + existing_order_by_id.fetch(entry_id, 0)),
        existing_order_by_id.fetch(entry_id, existing_entries.length)
      ]
    end

    payload = build_docs_search_payload(merged_entries)
    diagnostics = {
      changed: changed,
      removed: removed,
      unchanged: unchanged,
      full_fallback: 0
    }
    [payload, diagnostics]
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

  def compact_join(*parts)
    parts.map { |value| normalize_text(value) }.reject(&:empty?).join(" • ")
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

  def normalize_target_doc_ids(values)
    Array(values).flat_map { |value| normalize_text(value).split(",") }.map { |value| normalize_text(value) }.reject(&:empty?).uniq
  end

  def validate_targeted_options!(target_doc_ids, remove_missing)
    return if target_doc_ids.empty? && !remove_missing

    abort "Targeted docs search updates require at least one doc id" if target_doc_ids.empty?
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

  def load_json(path)
    unless path&.file?
      raise SystemExit, "Source JSON not found: #{relative_path(path)}"
    end

    JSON.parse(File.read(path, encoding: "utf-8"))
  rescue JSON::ParserError => e
    raise SystemExit, "Failed to parse JSON: #{relative_path(path)} (#{e.message})"
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
  only_doc_ids: [],
  remove_missing: false,
  write: false,
  force: false
}

OptionParser.new do |parser|
  parser.banner = "Usage: ./scripts/build_search.rb [options]"

  parser.on("--scope NAME", "Docs Viewer search scope to build") do |value|
    options[:scope] = value
  end

  parser.on("--source-index PATH", "Canonical docs index JSON path for docs-domain scopes") do |value|
    options[:source_index_path] = value
  end

  parser.on("--output PATH", "Generated search index output path") do |value|
    options[:output_path] = value
  end

  parser.on("--only-doc-ids IDS", "Comma-separated doc ids for targeted docs-domain search updates") do |value|
    options[:only_doc_ids] << value
  end

  parser.on("--only-records RECORDS", "Catalogue-only targeted search records") do
    abort "Docs Viewer search does not support --only-records"
  end

  parser.on("--remove-missing", "Allow targeted docs-domain updates to remove missing or non-viewable ids") do
    options[:remove_missing] = true
  end

  parser.on("--write", "Persist generated files (default is dry-run)") do
    options[:write] = true
  end

  parser.on("--force", "Write even when the content version matches") do
    options[:force] = true
  end
end.parse!(ARGV)

DocsViewerSearchDataBuilder.new(
  scope: options[:scope],
  source_index_path: options[:source_index_path],
  output_path: options[:output_path]
).run(
  write: options[:write],
  force: options[:force],
  only_doc_ids: options[:only_doc_ids],
  remove_missing: options[:remove_missing]
)
