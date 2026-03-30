#!/usr/bin/env ruby
# frozen_string_literal: true

require "cgi"
require "fileutils"
require "json"
require "optparse"
require "pathname"
require "time"
require "uri"
require "yaml"

require_relative "jekyll_markdown_renderer"

ScopeConfig = Struct.new(
  :scope_id,
  :source,
  :output,
  :viewer_base_url,
  :include_scope_param,
  keyword_init: true
)

DocRecord = Struct.new(
  :scope_id,
  :doc_id,
  :title,
  :last_updated,
  :parent_id,
  :sort_order,
  :source_path,
  :viewer_url,
  :content_url,
  :body_markdown,
  keyword_init: true
)

class DocsDataBuilder
  FRONT_MATTER_PATTERN = /\A---\s*\n(.*?)\n---\s*\n?/m.freeze
  MEDIA_TOKEN_PATTERN = /\[\[media:(.+?)\]\]/.freeze

  def initialize(scope_id:, source_dir:, output_dir:, viewer_base_url:, include_scope_param: false)
    @scope_id = scope_id.to_s
    @source_dir = Pathname(source_dir).expand_path
    @output_dir = Pathname(output_dir).expand_path
    @items_dir = @output_dir.join("by-id")
    @viewer_base_url = normalize_viewer_base_url(viewer_base_url)
    @include_scope_param = include_scope_param
    @repo_root = Pathname(__dir__).parent.realpath
    @output_url_base = output_url_base_for(@output_dir)
    @site_config = load_site_config
  end

  def run(write:)
    docs = load_docs
    validate_docs!(docs)

    index_payload = {
      generated_at: Time.now.utc.iso8601,
      docs: docs.sort_by { |doc| doc_sort_key(doc) }.map { |doc| index_entry(doc) }
    }
    item_payloads = docs.to_h { |doc| [doc.doc_id, item_entry(doc, docs)] }

    unless write
      dry_run_summary(index_payload, item_payloads)
      return {
        index_payload: index_payload,
        item_payloads: item_payloads
      }
    end

    write_outputs(index_payload, item_payloads)
    {
      index_payload: index_payload,
      item_payloads: item_payloads
    }
  end

  private

  def normalize_viewer_base_url(viewer_base_url)
    normalized = viewer_base_url.to_s.strip
    normalized = "/docs/" if normalized.empty?
    normalized = "/#{normalized}" unless normalized.start_with?("/")
    normalized.end_with?("/") ? normalized : "#{normalized}/"
  end

  def load_docs
    Dir.glob(@source_dir.join("**/*.md").to_s).sort.filter_map do |file_path|
      path = Pathname(file_path)
      relative_path = path.relative_path_from(@source_dir).to_s
      front_matter, body_markdown = parse_source(path)
      next if unpublished_doc?(front_matter)

      stem = path.basename(".md").to_s
      doc_id = (front_matter["doc_id"] || stem).to_s
      title = (front_matter["title"] || extract_title(body_markdown) || humanize(stem)).to_s
      parent_id = front_matter.key?("parent_id") ? front_matter["parent_id"].to_s : ""
      last_updated = front_matter["last_updated"] ? front_matter["last_updated"].to_s : ""
      sort_order = normalize_sort_order(front_matter["sort_order"])

      DocRecord.new(
        scope_id: @scope_id,
        doc_id: doc_id,
        title: title,
        last_updated: last_updated,
        parent_id: parent_id,
        sort_order: sort_order,
        source_path: relative_path,
        viewer_url: viewer_url_for(doc_id),
        content_url: content_url_for(doc_id),
        body_markdown: body_markdown
      )
    end
  end

  def parse_source(path)
    raw = path.read
    match = raw.match(FRONT_MATTER_PATTERN)
    return [{}, raw] unless match

    front_matter = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: false) || {}
    body = raw.sub(FRONT_MATTER_PATTERN, "")
    [front_matter, body]
  end

  def unpublished_doc?(front_matter)
    return false unless front_matter.key?("published")

    value = front_matter["published"]
    return !value if value == true || value == false

    %w[false 0 no off].include?(value.to_s.strip.downcase)
  end

  def extract_title(markdown)
    markdown.each_line do |line|
      stripped = line.strip
      return Regexp.last_match(1).strip if stripped.match(/\A#\s+(.+?)\s*\z/)
    end

    nil
  end

  def humanize(value)
    value.to_s.tr("_-", " ").split.map(&:capitalize).join(" ")
  end

  def normalize_sort_order(value)
    return nil if value.nil? || value.to_s.strip.empty?

    Integer(value)
  rescue ArgumentError, TypeError
    raise "Invalid sort_order #{value.inspect}; expected an integer"
  end

  def viewer_url_for(doc_id, anchor = nil)
    query_pairs = []
    query_pairs << "scope=#{CGI.escape(@scope_id)}" if @include_scope_param && !@scope_id.empty?
    query_pairs << "doc=#{CGI.escape(doc_id.to_s)}"
    url = "#{@viewer_base_url}?#{query_pairs.join('&')}"
    anchor.to_s.empty? ? url : "#{url}##{anchor}"
  end

  def content_url_for(doc_id)
    "#{@output_url_base}/by-id/#{CGI.escape(doc_id.to_s)}.json"
  end

  def validate_docs!(docs)
    duplicate_ids = docs.group_by(&:doc_id).select { |_doc_id, group| group.length > 1 }
    raise "Duplicate doc_id values: #{duplicate_ids.keys.join(', ')}" unless duplicate_ids.empty?

    docs.each do |doc|
      next if doc.parent_id.empty?
      next if docs.any? { |candidate| candidate.doc_id == doc.parent_id }

      raise "Unknown parent_id #{doc.parent_id.inspect} for doc #{doc.doc_id.inspect}"
    end
  end

  def index_entry(doc)
    {
      scope: doc.scope_id,
      doc_id: doc.doc_id,
      title: doc.title,
      last_updated: doc.last_updated,
      parent_id: doc.parent_id,
      sort_order: doc.sort_order,
      source_path: doc.source_path,
      viewer_url: doc.viewer_url,
      content_url: doc.content_url
    }
  end

  def item_entry(doc, docs)
    {
      scope: doc.scope_id,
      doc_id: doc.doc_id,
      title: doc.title,
      last_updated: doc.last_updated,
      parent_id: doc.parent_id,
      sort_order: doc.sort_order,
      source_path: doc.source_path,
      viewer_url: doc.viewer_url,
      content_html: rewrite_doc_links(
        JekyllMarkdownRenderer.render_string(resolve_media_tokens(doc.body_markdown)),
        current_doc: doc,
        docs: docs
      )
    }
  end

  def rewrite_doc_links(html, current_doc:, docs:)
    docs_by_id = docs.to_h { |doc| [doc.doc_id, doc] }
    docs_by_source = docs.to_h { |doc| [doc.source_path, doc] }
    docs_by_repo_path = docs.to_h do |doc|
      [@source_dir.join(doc.source_path).cleanpath.to_s, doc]
    end

    html.gsub(/href=(["'])(.*?)\1/) do
      quote = Regexp.last_match(1)
      href = Regexp.last_match(2)
      rewritten = rewrite_href(
        href,
        current_doc: current_doc,
        docs_by_id: docs_by_id,
        docs_by_source: docs_by_source,
        docs_by_repo_path: docs_by_repo_path
      )
      %(href=#{quote}#{rewritten}#{quote})
    end
  end

  def rewrite_href(href, current_doc:, docs_by_id:, docs_by_source:, docs_by_repo_path:)
    return href if href.empty? || href.start_with?("#", "mailto:")
    return href if href.match?(/\A[a-z][a-z0-9+\-.]*:/i)

    begin
      parsed = URI.parse(href)
    rescue URI::InvalidURIError
      return href
    end

    path_part = parsed.path.to_s
    query_values = CGI.parse(parsed.query.to_s)
    anchor = parsed.fragment
    return href if path_part.empty?

    viewer_doc_id = query_values.fetch("doc", []).first.to_s
    if !viewer_doc_id.empty? && viewer_path_match?(path_part)
      target_doc = docs_by_id[viewer_doc_id]
      return target_doc ? viewer_url_for(target_doc.doc_id, anchor) : href
    end

    if path_part.start_with?(@repo_root.to_s)
      target_doc = docs_by_repo_path[path_part]
      return target_doc ? viewer_url_for(target_doc.doc_id, anchor) : href
    end

    return href unless path_part.end_with?(".md")

    current_dir = Pathname(current_doc.source_path).dirname
    resolved_path = current_dir.join(path_part).cleanpath.to_s
    target_doc = docs_by_source[resolved_path]
    target_doc ? viewer_url_for(target_doc.doc_id, anchor) : href
  end

  def viewer_path_match?(path_part)
    path_part == @viewer_base_url || path_part == "/docs/" || path_part == "/library/"
  end

  def doc_sort_key(doc)
    [
      doc.sort_order.nil? ? 1 : 0,
      doc.sort_order || 0,
      doc.title.downcase,
      doc.doc_id
    ]
  end

  def write_outputs(index_payload, item_payloads)
    write_payload_set(@output_dir, @items_dir, index_payload, item_payloads)
  end

  def dry_run_summary(index_payload, item_payloads)
    puts "Dry run:"
    puts "  scope: #{@scope_id}"
    puts "  source: #{@source_dir}"
    puts "  docs: #{index_payload.fetch(:docs).length}"
    puts "  would write: #{@output_dir.join('index.json')}"
    puts "  would write: #{item_payloads.length} files under #{@items_dir}"
  end

  def write_payload_set(output_dir, items_dir, index_payload, item_payloads, label: nil)
    FileUtils.mkdir_p(items_dir)
    FileUtils.rm_f(output_dir.join("index.json"))
    FileUtils.rm_rf(items_dir)
    FileUtils.mkdir_p(items_dir)

    output_dir.join("index.json").write(JSON.pretty_generate(index_payload) + "\n")
    item_payloads.each do |doc_id, payload|
      items_dir.join("#{doc_id}.json").write(JSON.pretty_generate(payload) + "\n")
    end

    prefix = label ? "#{label}: " : ""
    puts "#{prefix}Wrote #{output_dir.join('index.json')}"
    puts "#{prefix}Wrote #{item_payloads.length} doc payloads to #{items_dir}"
  end

  def output_url_base_for(output_dir)
    relative_path = output_dir.relative_path_from(@repo_root).to_s
    "/#{relative_path}"
  end

  def load_site_config
    config_path = @repo_root.join("_config.yml")
    return {} unless config_path.exist?

    YAML.safe_load(config_path.read, permitted_classes: [Date, Time], aliases: false) || {}
  end

  def resolve_media_tokens(markdown)
    return markdown unless markdown.include?("[[media:")

    markdown.gsub(MEDIA_TOKEN_PATTERN) do
      resolve_media_url(Regexp.last_match(1))
    end
  end

  def resolve_media_url(raw_path)
    relative_path = raw_path.to_s.strip
    return "" if relative_path.empty?

    if relative_path.match?(/\A[a-z][a-z0-9+\-.]*:\/\//i)
      return relative_path
    end

    media_base = @site_config.fetch("media_base", "").to_s.strip
    clean_path = relative_path.sub(%r{\A/+}, "")
    return "/#{clean_path}" if media_base.empty?

    "#{media_base.sub(%r{/+\z}, '')}/#{clean_path}"
  end
end

options = {
  scopes: [],
  source: nil,
  output: nil,
  viewer_base_url: nil,
  write: false
}

OptionParser.new do |parser|
  parser.banner = "Usage: build_docs_data.rb [options]"

  parser.on("--scope NAME", "Limit build to a named docs scope (repeatable)") do |value|
    options[:scopes] << value.to_s.strip.downcase
  end

  parser.on("--source PATH", "Override docs source directory for a single selected scope") do |value|
    options[:source] = value
  end

  parser.on("--output PATH", "Override docs data output directory for a single selected scope") do |value|
    options[:output] = value
  end

  parser.on("--viewer-base-url URL", "Override viewer page URL base for a single selected scope") do |value|
    options[:viewer_base_url] = value
  end

  parser.on("--write", "Write generated files") do
    options[:write] = true
  end
end.parse!

scope_configs = [
  ScopeConfig.new(
    scope_id: "studio",
    source: "_docs_src",
    output: "assets/data/docs/scopes/studio",
    viewer_base_url: "/docs/",
    include_scope_param: true
  ),
  ScopeConfig.new(
    scope_id: "library",
    source: "_docs_library_src",
    output: "assets/data/docs/scopes/library",
    viewer_base_url: "/library/",
    include_scope_param: false
  )
]

selected_scopes = scope_configs.select do |config|
  options[:scopes].empty? || options[:scopes].include?(config.scope_id)
end

raise "Unknown docs scope(s): #{options[:scopes].join(', ')}" if selected_scopes.empty?

if [options[:source], options[:output], options[:viewer_base_url]].any? && selected_scopes.length != 1
  raise "--source, --output, and --viewer-base-url can only be used when exactly one scope is selected"
end

selected_scopes.each do |config|
  builder = DocsDataBuilder.new(
    scope_id: config.scope_id,
    source_dir: options[:source] || config.source,
    output_dir: options[:output] || config.output,
    viewer_base_url: options[:viewer_base_url] || config.viewer_base_url,
    include_scope_param: config.include_scope_param
  )
  builder.run(write: options[:write])
end
