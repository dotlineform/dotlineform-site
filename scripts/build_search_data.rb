#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "fileutils"
require "json"
require "optparse"
require "pathname"
require "time"

DEFAULT_SCOPE = "studio"
SCOPE_DEFAULTS = {
  "studio" => {
    source_index_path: "assets/data/docs/scopes/studio/index.json",
    output_path: "assets/data/search/studio/index.json",
    schema: "search_index_studio_v1"
  },
  "library" => {
    source_index_path: "assets/data/docs/scopes/library/index.json",
    output_path: "assets/data/search/library/index.json",
    schema: "search_index_library_v1"
  }
}.freeze

SearchDocRecord = Struct.new(
  :doc_id,
  :title,
  :last_updated,
  :parent_id,
  :viewer_url,
  keyword_init: true
)

class SearchDataBuilder
  def initialize(scope:, source_index_path:, output_path:)
    @scope = normalize(scope)
    @repo_root = Pathname(__dir__).parent.realpath
    defaults = SCOPE_DEFAULTS.fetch(@scope, {})
    resolved_source_index_path = source_index_path || defaults[:source_index_path]
    resolved_output_path = output_path || defaults[:output_path]
    @schema = defaults[:schema] || "search_index_#{@scope}_v1"
    @source_index_path = @repo_root.join(resolved_source_index_path).expand_path
    @output_path = @repo_root.join(resolved_output_path).expand_path
  end

  def run(write:)
    validate_scope!
    docs = load_docs_index
    entries = build_entries(docs)
    payload = build_payload(entries)

    unless write
      puts "Dry run: #{payload.dig('header', 'count')} #{@scope} search entries"
      puts "Would write: #{@output_path.relative_path_from(@repo_root)}"
      return payload
    end

    FileUtils.mkdir_p(@output_path.dirname)
    File.write(@output_path, JSON.pretty_generate(payload) + "\n")
    puts "Wrote #{@output_path.relative_path_from(@repo_root)} with #{payload.dig('header', 'count')} #{@scope} search entries"
    payload
  end

  private

  def validate_scope!
    return if SCOPE_DEFAULTS.key?(@scope)

    raise SystemExit, "Unsupported scope: #{@scope}. Current builder scopes: #{SCOPE_DEFAULTS.keys.join(', ')}"
  end

  def load_docs_index
    unless @source_index_path.file?
      raise SystemExit, "Docs index not found: #{@source_index_path.relative_path_from(@repo_root)}"
    end

    payload = JSON.parse(File.read(@source_index_path, encoding: "utf-8"))
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

      SearchDocRecord.new(
        doc_id: doc_id,
        title: title,
        last_updated: normalize_text(row["last_updated"]),
        parent_id: normalize_text(row["parent_id"]),
        viewer_url: viewer_url
      )
    end.compact
  rescue JSON::ParserError => e
    raise SystemExit, "Failed to parse docs index JSON: #{@source_index_path.relative_path_from(@repo_root)} (#{e.message})"
  end

  def build_entries(docs)
    title_by_id = docs.to_h { |doc| [doc.doc_id, doc.title] }

    docs.map do |doc|
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
      }.reject { |_key, value| empty_value?(value) }
    end
  end

  def build_payload(entries)
    version_source = JSON.generate(entries)
    version = "sha256-#{Digest::SHA256.hexdigest(version_source)}"

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

  def empty_value?(value)
    value.nil? || (value.respond_to?(:empty?) && value.empty?)
  end
end

options = {
  scope: DEFAULT_SCOPE,
  source_index_path: nil,
  output_path: nil,
  write: false
}

OptionParser.new do |parser|
  parser.banner = "Usage: ./scripts/build_search_data.rb [options]"

  parser.on("--scope NAME", "Search scope to build (current values: #{SCOPE_DEFAULTS.keys.join(', ')})") do |value|
    options[:scope] = value
  end

  parser.on("--source-index PATH", "Canonical source index JSON path") do |value|
    options[:source_index_path] = value
  end

  parser.on("--output PATH", "Generated search index output path") do |value|
    options[:output_path] = value
  end

  parser.on("--write", "Persist generated files (default is dry-run)") do
    options[:write] = true
  end
end.parse!(ARGV)

SearchDataBuilder.new(
  scope: options[:scope],
  source_index_path: options[:source_index_path],
  output_path: options[:output_path]
).run(write: options[:write])
